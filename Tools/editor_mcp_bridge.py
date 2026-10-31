"""UE game-thread endpoint for the local stdio MCP adapter (no UE restart)."""
import contextlib
import io
import json
import os
from pathlib import Path
import runpy
import time
import traceback
import unreal

_root = Path(unreal.Paths.project_dir()).resolve()
_queue = _root / "Saved" / "EditorMcp"
_queue.mkdir(parents=True, exist_ok=True)
if "_vrsharp_mcp_tick" in globals():
    unreal.unregister_slate_post_tick_callback(_vrsharp_mcp_tick)
_last_poll = 0.0
_processing = False


def _process_vrsharp_mcp(_delta):
    global _last_poll, _processing
    now = time.monotonic()
    if _processing or now - _last_poll < 0.05:
        return
    _last_poll = now
    for request in _queue.glob("*.request.json"):
        # Blueprint compilation/save can pump nested Slate ticks: claim once before executing.
        running = request.with_name(request.name.replace(".request.json", ".running.json"))
        request.replace(running)
        _processing = True
        output = io.StringIO()
        result = {"project": str(_root), "success": False}
        try:
            data = json.loads(running.read_text(encoding="utf-8"))
            script = (_root / data["script"]).resolve()
            if not script.is_relative_to(_root / "Tools") or script.suffix != ".py":
                raise ValueError("Editor scripts must be .py files inside this project's Tools directory")
            with contextlib.redirect_stdout(output), contextlib.redirect_stderr(output):
                runpy.run_path(str(script), run_name="__main__")
            result["success"] = True
        except Exception:
            result["traceback"] = traceback.format_exc()
        result["output"] = output.getvalue()
        response = request.with_name(request.name.replace(".request.json", ".response.json"))
        temporary = response.with_suffix(".tmp")
        temporary.write_text(json.dumps(result, ensure_ascii=False), encoding="utf-8")
        os.replace(temporary, response)
        running.unlink()
        _processing = False


_vrsharp_mcp_tick = unreal.register_slate_post_tick_callback(_process_vrsharp_mcp)
unreal.log("VRSharp local MCP editor endpoint ready")
