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
_cube = None
_grabbable = None
_offsets = []
_rotations = []
_cases = [(fps, count) for fps in (30, 120) for count in (1, 2)]
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
    (_root / "Saved/Tests/HandSpring-Grip-20261017.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
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
    fps, count = _cases[_case]
    _engine.set_editor_property("FixedFrameRate", float(fps))
    _engine.set_editor_property("bUseFixedFrameRate", True)
    for actor, body in reversed(_hands):
        actor.call_method("Release")
    _cube.set_actor_location_and_rotation(unreal.Vector(100, 0, 2000), unreal.Rotator(), False, True)
    cube_body = _cube.get_component_by_class(unreal.StaticMeshComponent)
    cube_body.set_simulate_physics(True)
    cube_body.set_enable_gravity(False)
    if not cube_body.is_simulating_physics():
        raise RuntimeError("Test cube did not create a dynamic body")
    cube_body.set_mass_override_in_kg("", 1.0, True)
    cube_body.set_physics_linear_velocity(unreal.Vector(), False)
    cube_body.set_physics_angular_velocity_in_radians(unreal.Vector(), False)
    _offsets.clear()
    _rotations.clear()
    for index, (actor, body) in enumerate(_hands):
        actor.set_actor_location_and_rotation(unreal.Vector(100, -60 if index == 0 else 60, 2000), unreal.Rotator(), False, True)
        body.set_physics_linear_velocity(unreal.Vector(), False)
        body.set_physics_angular_velocity_in_radians(unreal.Vector(), False)
        if index < count:
            actor.call_method("GrabWithGrabbable", args=(_grabbable, unreal.Vector(100, 0, 2000)))
            if actor.get_attach_parent_actor() != _cube:
                raise RuntimeError("Real grip acquisition failed for hand " + str(index))
        pos = actor.get_actor_location()
        _offsets.append(unreal.Vector(pos.x - 100, pos.y, pos.z - 2000))
        _rotations.append(actor.get_actor_transform().rotation)
    return True


def _tick(_slate_dt):
    global _world, _elapsed, _cube, _grabbable
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
            candidates = [a for a in unreal.GameplayStatics.get_all_actors_of_class(_world, unreal.Actor) if "SpecificGrabCube" in a.get_name() or "SpecificGrabCube" in a.get_actor_label()]
            if len(candidates) != 1:
                raise RuntimeError("SpecificGrabCube candidates: " + str([a.get_actor_label() for a in candidates]))
            _cube = candidates[0]
            components = _cube.get_components_by_class(unreal.ActorComponent)
            _grabbable = next(c for c in components if "Grabbable" in c.get_class().get_name())
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
        fps, count = _cases[_case]
        quat = unreal.Quat(0, 0, math.sin(half_angle), math.cos(half_angle))
        for index, (actor, body) in enumerate(_hands):
            if index >= count:
                continue
            off = quat.rotate_vector(_offsets[index])
            target = unreal.Vector(target_x + off.x, off.y, 2000 + off.z)
            # Quaternion composition, independent of Python operator bindings.
            a, b = quat, _rotations[index]
            rot = unreal.Quat(a.w*b.x+a.x*b.w+a.y*b.z-a.z*b.y,
                              a.w*b.y-a.x*b.z+a.y*b.w+a.z*b.x,
                              a.w*b.z+a.x*b.y-a.y*b.x+a.z*b.w,
                              a.w*b.w-a.x*b.x-a.y*b.y-a.z*b.z)
            pos = body.get_world_location()
            error = math.sqrt((pos.x-target.x)**2+(pos.y-target.y)**2+(pos.z-target.z)**2)
            if not math.isfinite(error) or error > 300:
                raise RuntimeError("Unstable welded grip: " + str(error))
            actor.call_method("UpdateTracking", args=(target, rot, dt))
            errors.append(error)
        _samples.append({"t": _elapsed, "dt": dt, "position_errors_cm": errors, "cube": str(_cube.get_actor_location()), "v": str(_cube.get_component_by_class(unreal.StaticMeshComponent).get_physics_linear_velocity()), "handv": str(_hands[0][1].get_physics_linear_velocity_at_point(_hands[0][1].get_world_location())), "sim": _cube.get_component_by_class(unreal.StaticMeshComponent).is_simulating_physics()})
        if _elapsed >= 3.0:
            tail = [row for row in _samples if row["t"] > 2.5]
            final_error = max(max(row["position_errors_cm"]) for row in tail)
            _results.append({"simulation_hz": fps, "hand_count": count,
                             "final_position_error_cm": final_error, "offsets": [str(o) for o in _offsets], "inertia": str(_cube.get_component_by_class(unreal.StaticMeshComponent).get_inertia_tensor()), "mass": _cube.get_component_by_class(unreal.StaticMeshComponent).get_mass(),
                             "passed": final_error < 1.0, "samples": _samples})
            _next_case()
    except Exception as error:
        _finish(str(error))


_handle = unreal.register_slate_post_tick_callback(_tick)
_level.editor_request_begin_play()
print("Started real single/two-hand welded-grip checks at 30/120 Hz")
