"""Official MCP SDK stdio server for scripts dispatched to the UE game thread."""
import asyncio
import json
import os
from pathlib import Path
import uuid
from mcp.server.fastmcp import FastMCP

ROOT = Path(__file__).resolve().parent.parent
QUEUE = ROOT / "Saved" / "EditorMcp"
mcp = FastMCP("VRSharp Editor")


@mcp.tool()
async def run_editor_script(script: str) -> dict:
    """Run a project Tools/*.py script inside the connected Unreal Editor on its game thread."""
    path = (ROOT / script).resolve()
    if not path.is_relative_to(ROOT / "Tools") or path.suffix != ".py" or not path.is_file():
        raise ValueError("Expected an existing Python script under project Tools")
    QUEUE.mkdir(parents=True, exist_ok=True)
    stem = uuid.uuid4().hex
    request = QUEUE / (stem + ".request.json")
    response = QUEUE / (stem + ".response.json")
    temporary = request.with_suffix(".tmp")
    temporary.write_text(json.dumps({"script": str(path.relative_to(ROOT))}), encoding="utf-8")
    os.replace(temporary, request)
    for _ in range(600):
        if response.exists():
            result = json.loads(response.read_text(encoding="utf-8"))
            response.unlink()
            return result
        await asyncio.sleep(0.1)
    # Remove an unconsumed command so it cannot mutate the editor later after a timeout.
    request.unlink(missing_ok=True)
    raise TimeoutError("UE did not respond in 60 seconds; check editor modal/PIE state")


if __name__ == "__main__":
    mcp.run(transport="stdio")
