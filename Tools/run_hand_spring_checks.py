"""Drive the production C# tracking entry point in Chaos via MCP, without hardware input."""
import json
import math
from pathlib import Path
import time
import unreal

_root = Path(unreal.Paths.project_dir()).resolve()
_level = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
_started = time.monotonic()
_world = None
_hands = []
_cases = [(fps, mass) for fps in (30, 60, 90, 120) for mass in (0.45, 2.0, 5.0)]
_case = -1
_elapsed = 0.0
_samples = []
_results = []
_old_fps = unreal.SystemLibrary.get_console_variable_float_value("t.MaxFPS")
_engines = [obj for obj in unreal.ObjectIterator(unreal.load_class(None, "/Script/Engine.Engine")) if not obj.get_name().startswith("Default__")]
assert len(_engines) == 1
_engine = _engines[0]
_old_fixed = _engine.get_editor_property("bUseFixedFrameRate")
_old_fixed_rate = _engine.get_editor_property("FixedFrameRate")
_performance = unreal.get_default_object(unreal.load_class(None, "/Script/UnrealEd.EditorPerformanceSettings"))
_old_throttle = _performance.get_editor_property("bThrottleCPUWhenNotForeground")
_performance.set_editor_property("bThrottleCPUWhenNotForeground", False)


def _finish(error=None):
    unreal.unregister_slate_post_tick_callback(_handle)
    if _world:
        unreal.SystemLibrary.execute_console_command(_world, "t.MaxFPS " + str(_old_fps))
    _performance.set_editor_property("bThrottleCPUWhenNotForeground", _old_throttle)
    _engine.set_editor_property("bUseFixedFrameRate", _old_fixed)
    _engine.set_editor_property("FixedFrameRate", _old_fixed_rate)
    report = {"cases": _results, "error": error, "vr_hardware_tested": False,
              "clock": "UE fixed frame rate supplies the actual game/Chaos delta; renderer wall FPS may be lower"}
    report["passed"] = error is None and len(_results) == len(_cases) and all(row["passed"] for row in _results)
    (_root / "Saved/Tests/HandSpring-Physics-20261017.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    _level.editor_request_end_play()
    unreal.log("VRSharp hand spring Chaos checks completed: " + str(report["passed"]) + "; error=" + str(error))


def _next_case():
    global _case, _elapsed, _samples
    _case += 1
    _elapsed = 0.0
    _samples = []
    if _case == len(_cases):
        _finish()
        return False
    fps, mass = _cases[_case]
    _engine.set_editor_property("FixedFrameRate", float(fps))
    _engine.set_editor_property("bUseFixedFrameRate", True)
    unreal.SystemLibrary.execute_console_command(_world, "t.MaxFPS " + str(fps))
    for index, (actor, body) in enumerate(_hands):
        # The collision shape contributes 0.449 kg; change only the transient PIE root mass.
        body.set_mass_override_in_kg("", mass - 0.449, True)
        actor.set_actor_location_and_rotation(unreal.Vector(100, index * 100, 2000), unreal.Rotator(0, 0, 0), False, True)
        body.set_physics_linear_velocity(unreal.Vector(), False)
        body.set_physics_angular_velocity_in_radians(unreal.Vector(), False)
    return True


def _tick(_slate_dt):
    global _world, _elapsed
    try:
        if not _world:
            if time.monotonic() - _started < 0.5:
                return
            world = unreal.EditorLevelLibrary.get_game_world()
            if not world:
                if time.monotonic() - _started > 15:
                    _finish("PIE world failed to start")
                return
            _world = world
            pawn = unreal.GameplayStatics.get_player_pawn(_world, 0)
            pawn.set_actor_tick_enabled(False)
            pawn.get_editor_property("BodyCapsule").set_simulate_physics(False)
            for side in ("Left", "Right"):
                cls = unreal.load_asset("/VRSharp/Blueprints/BP_VRSharpHand" + side).generated_class()
                actors = [a for a in unreal.GameplayStatics.get_all_actors_of_class(_world, cls) if a.get_class() == cls]
                if len(actors) != 1:
                    raise RuntimeError("Unexpected hand count for " + side)
                actor = actors[0]
                actor.set_actor_tick_enabled(False)
                _hands.append((actor, actor.get_editor_property("HandRigidbody")))
            _next_case()
            return
        dt = unreal.GameplayStatics.get_world_delta_seconds(_world)
        if dt <= 0:
            return
        _elapsed += dt
        # Warm-up, a continuous translation/rotation, then a sharp stop.
        ramp_time = min(max(_elapsed - 0.25, 0), 0.3)
        target_x = 100 + 40 * ramp_time
        target_yaw = 150 * ramp_time
        half_angle = math.radians(target_yaw) / 2
        sign = -1 if len(_samples) % 2 else 1  # Same rotation, alternating quaternion representation.
        quat = unreal.Quat(0, 0, sign * math.sin(half_angle), sign * math.cos(half_angle))
        errors = []
        masses = []
        for index, (actor, body) in enumerate(_hands):
            position = body.get_world_location()
            rotation = body.get_world_rotation()
            position_error = math.sqrt((position.x - target_x) ** 2 + (position.y - index * 100) ** 2 + (position.z - 2000) ** 2)
            angle_error = max(abs((rotation.yaw - target_yaw + 180) % 360 - 180), abs(rotation.pitch), abs(rotation.roll))
            if not math.isfinite(position_error + angle_error) or position_error > 100:
                raise RuntimeError("Unstable response: " + str((position_error, angle_error)))
            actor.call_method("UpdateTracking", args=(unreal.Vector(target_x, index * 100, 2000), quat, dt))
            errors.append([position_error, angle_error])
            masses.append(body.get_mass())
        _samples.append({"t": _elapsed, "dt": dt, "errors": errors, "masses": masses})
        if _elapsed >= 1.3:
            tail = [row for row in _samples if row["t"] > 1.05]
            final_pos = [max(row["errors"][hand][0] for row in tail) for hand in (0, 1)]
            final_angle = [max(row["errors"][hand][1] for row in tail) for hand in (0, 1)]
            fps, mass = _cases[_case]
            actual_mass = _samples[-1]["masses"]
            measured_fps = 1 / (sum(row["dt"] for row in tail) / len(tail))
            row = {"requested_fps": fps, "measured_fps": measured_fps, "requested_mass": mass,
                   "actual_mass": actual_mass, "final_position_error_cm": final_pos,
                   "final_rotation_error_deg": final_angle,
                   "max_position_error_cm": [max(s["errors"][i][0] for s in _samples) for i in (0, 1)],
                   "samples": _samples}
            row["passed"] = measured_fps >= fps * 0.7 and max(final_pos) < 0.25 and max(final_angle) < 0.5 and max(abs(m - mass) for m in actual_mass) < 0.001
            _results.append(row)
            if measured_fps < fps * 0.7:
                _finish("Editor is throttled: requested " + str(fps) + " FPS, measured " + str(measured_fps))
                return
            _next_case()
    except Exception as error:
        _finish(str(error))


_handle = unreal.register_slate_post_tick_callback(_tick)
_level.editor_request_begin_play()
print("Started 12 Chaos scenarios (30/60/90/120 FPS, 0.45/2/5 kg, both hands)")
