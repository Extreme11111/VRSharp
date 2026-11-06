"""Check VRSharp collision settings in a host project's Engine INI layers."""
import argparse
from collections import defaultdict
from pathlib import Path
import re
import sys

SECTION = "/script/engine.collisionprofile"
ARRAYS = ("defaultchannelresponses", "profiles")
REQUIRED = {
    "defaultchannelresponses": ("3DWidget", "VRPlayer", "VRGrabCheck", "VRHand"),
    "profiles": ("VRPlayer", "VRHand"),
}
REFERENCE = Path(__file__).resolve().parents[1] / "Examples/VRSharpLab/DefaultEngine.ini"


def read_arrays(paths):
    arrays = {key: [] for key in ARRAYS}
    for path in paths:
        section = ""
        for raw_line in path.read_text(encoding="utf-8-sig").splitlines():
            line = raw_line.strip()
            if not line or line.startswith((";", "#")):
                continue
            if line.startswith("["):
                section = line[1:].partition("]")[0].casefold()
                continue
            if section != SECTION:
                continue
            key, sep, value = line.partition("=")
            key, value = key.strip().casefold(), value.strip()
            op = key[0] if key and key[0] in "+.-!" else ""
            if op:
                key = key[1:].strip()
            if not sep or key not in arrays:
                continue
            entries = arrays[key]
            if op == "!":
                entries.clear()
            elif op == "-":
                if value in entries:
                    entries.remove(value)
            elif op == "." or (op == "+" and value not in entries):
                entries.append(value)
            elif not op:
                entries[:] = [value]
    return arrays


def tuple_items(value):
    """Split a UE struct/list into top-level members, preserving nested tuples."""
    if not value:
        return []
    if not value.startswith("(") or not value.endswith(")"):
        raise ValueError(f"Expected a collision tuple: {value[:120]}")
    inner = value[1:-1]
    depth, start = 0, 0
    items = []
    for token in re.finditer(r'"(?:\\.|[^"\\])*"|[(),]', inner):
        if token.group() == "(":
            depth += 1
        elif token.group() == ")":
            depth -= 1
        elif token.group() == "," and depth == 0:
            items.append(inner[start:token.start()].strip())
            start = token.end()
        if depth < 0:
            raise ValueError(f"Unbalanced collision tuple: {value[:120]}")
    if depth:
        raise ValueError(f"Unbalanced collision tuple: {value[:120]}")
    items.append(inner[start:].strip())
    return items


def fields(value):
    result = {}
    for member in tuple_items(value):
        key, sep, entry = member.partition("=")
        if not sep:
            raise ValueError(f"Expected a collision field: {member[:120]}")
        result[key.strip().casefold()] = entry.strip().strip('"')
    return result


def index_named(entries):
    by_name = defaultdict(list)
    for value in entries:
        entry = fields(value)
        if not entry.get("name"):
            raise ValueError(f"Collision entry is missing Name: {value[:120]}")
        by_name[entry["name"].casefold()].append(entry)
    return by_name


def check(paths):
    reference = read_arrays([REFERENCE])
    host = read_arrays(paths)
    issues = []
    for key, names in REQUIRED.items():
        expected = index_named(reference[key])
        actual = index_named(host[key])
        for name in names:
            wanted = expected[name.casefold()][0]
            entries = actual.get(name.casefold(), [])
            if not entries:
                issues.append(f"{name}: missing from {key}.")
            elif len(entries) != 1:
                issues.append(f"{name}: multiple definitions in {key}.")
            else:
                current = entries[0]
                keys = ("channel", "defaultresponse", "btracetype", "bstaticobject") if key == ARRAYS[0] else (
                    "collisionenabled", "objecttypename")
                for setting in keys:
                    found = current.get(setting, "<missing>")
                    if found.casefold() != wanted[setting].casefold():
                        issues.append(f"{name}: {setting} is {found}, expected {wanted[setting]}.")
                if key == "profiles":
                    responses = {}
                    for value in tuple_items(current.get("customresponses", "")):
                        response = fields(value)
                        channel = response.get("channel", "").casefold()
                        if channel in responses:
                            issues.append(f"{name}: duplicate response for {channel}.")
                        responses[channel] = response.get("response", "").casefold()
                    for value in tuple_items(wanted["customresponses"]):
                        response = fields(value)
                        channel = response["channel"]
                        if responses.get(channel.casefold()) != response["response"].casefold():
                            issues.append(f"{name}: expected {response['response']} response to {channel}.")
            if key == ARRAYS[0]:
                slot = wanted["channel"]
                conflicts = sorted({entry["name"] for other, definitions in actual.items()
                                    if other != name.casefold() for entry in definitions
                                    if entry.get("channel", "").casefold() == slot.casefold()})
                if conflicts:
                    issues.append(f"{slot} reserved by VRSharp for {name}: also used by {', '.join(conflicts)}.")
    return issues


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("engine_ini", type=Path, nargs="+", help="DefaultEngine.ini and optional override layers, in order")
    args = parser.parse_args()
    try:
        issues = check(args.engine_ini)
    except (OSError, UnicodeError, ValueError) as exc:
        print(f"Cannot check collision configuration: {exc}", file=sys.stderr)
        return 2
    if issues:
        for issue in issues:
            print(issue, file=sys.stderr)
        print("Review host collision mappings and serialized Blueprint channels before remapping.", file=sys.stderr)
        return 1
    print("VRSharp collision channels and required profiles match the reference in the supplied layers.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
