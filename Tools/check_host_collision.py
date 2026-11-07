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
CUSTOM_SLOTS = tuple(f"ECC_GameTraceChannel{i}" for i in range(1, 19))
CUSTOM_SLOT_KEYS = {slot.casefold() for slot in CUSTOM_SLOTS}


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


def channel_owners(channels):
    owners = defaultdict(list)
    for entries in channels.values():
        for entry in entries:
            owners[entry.get("channel", "").casefold()].append(entry["name"])
    return owners


def plan_channels(reference, host):
    key = ARRAYS[0]
    actual = index_named(host[key])
    owners = channel_owners(actual)
    reference_lines = {fields(value)["name"].casefold(): value for value in reference[key]}
    missing = []
    selected = {}
    issues = []
    for name in REQUIRED[key]:
        value = reference_lines[name.casefold()]
        legacy = fields(value)["channel"]
        entries = actual.get(name.casefold(), [])
        if not entries:
            missing.append((name, legacy, value))
            continue
        slot = entries[0].get("channel", "<missing>")
        if len(entries) != 1 or slot.casefold() not in CUSTOM_SLOT_KEYS or len(owners[slot.casefold()]) != 1:
            issues.append(f"{name}: resolve the existing definitions or occupied slot ({slot}) before planning.")
        else:
            selected[name] = (legacy, slot, "keep")

    free = [slot for slot in CUSTOM_SLOTS if slot.casefold() not in owners]
    preferred = {legacy for _, legacy, _ in missing}
    fallback = iter(slot for slot in free if slot not in preferred)
    additions = []
    for name, legacy, value in missing:
        slot = legacy if legacy in free else next(fallback, None)
        if slot is None:
            issues.append(f"{name}: no free custom collision slot in the supplied layers.")
            continue
        selected[name] = (legacy, slot, "add")
        additions.append("+DefaultChannelResponses=" + value.replace(f"Channel={legacy},", f"Channel={slot},", 1))

    if issues:
        return issues, []
    lines = []
    for name in REQUIRED[key]:
        legacy, slot, action = selected[name]
        lines.append(f"{name}: {legacy} -> {slot} ({action})")
    if additions:
        lines.extend(["", "Review these entries for [/Script/Engine.CollisionProfile]:", *additions, ""])
    lines.append("Review the required profiles separately and rerun the check after migration.")
    return [], lines


def check(reference, host, allow_remapped=False):
    issues = []
    for key, names in REQUIRED.items():
        expected = index_named(reference[key])
        actual = index_named(host[key])
        owners = channel_owners(actual) if key == ARRAYS[0] else {}
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
                    if setting == "channel" and allow_remapped:
                        if found.casefold() not in CUSTOM_SLOT_KEYS:
                            issues.append(f"{name}: channel {found} is not a project custom collision slot.")
                    elif found.casefold() != wanted[setting].casefold():
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
            if key == ARRAYS[0] and (not allow_remapped or len(entries) == 1):
                slot = entries[0].get("channel", "<missing>") if allow_remapped else wanted["channel"]
                conflicts = sorted({owner for owner in owners.get(slot.casefold(), []) if owner.casefold() != name.casefold()})
                if conflicts and allow_remapped:
                    issues.append(f"{name}: {slot} also used by {', '.join(conflicts)}.")
                elif conflicts:
                    issues.append(f"{slot} reserved by VRSharp for {name}: also used by {', '.join(conflicts)}.")
    return issues


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--plan", action="store_true", help="propose free slots for missing channels")
    mode.add_argument("--allow-remapped-channels", action="store_true", help="check valid, unique custom slots instead of fixed reference slots")
    parser.add_argument("engine_ini", type=Path, nargs="+", help="DefaultEngine.ini and optional override layers, in order")
    args = parser.parse_args()
    try:
        reference = read_arrays([REFERENCE])
        host = read_arrays(args.engine_ini)
        if args.plan:
            issues, lines = plan_channels(reference, host)
        else:
            issues = check(reference, host, args.allow_remapped_channels)
            lines = ["VRSharp collision channels and required profiles passed in the supplied layers."]
    except (OSError, UnicodeError, ValueError) as exc:
        print(f"Cannot check collision configuration: {exc}", file=sys.stderr)
        return 2
    if issues:
        for issue in issues:
            print(issue, file=sys.stderr)
        print("Review host collision mappings and serialized Blueprint channels before remapping.", file=sys.stderr)
        return 1
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    sys.exit(main())
