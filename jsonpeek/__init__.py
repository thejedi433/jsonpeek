#!/usr/bin/env python3
"""CLI tool to inspect JSON structure - show keys, types, counts."""
import json
import sys
import argparse
from pathlib import Path


def get_type_name(v):
    if v is None:
        return "null"
    if isinstance(v, bool):
        return "bool"
    if isinstance(v, int):
        return "int"
    if isinstance(v, float):
        return "float"
    if isinstance(v, str):
        return "str"
    if isinstance(v, list):
        return "list"
    if isinstance(v, dict):
        return "dict"
    return type(v).__name__


def resolve_path(data, path):
    """Navigate into data using dot-separated path with [N] indices."""
    if not path:
        return data
    for part in path.split('.'):
        if not part:
            continue
        # Check for index like [0]
        if part.endswith(']') and '[' in part:
            key, idx = part[:-1].split('[', 1)
            if key:
                if isinstance(data, dict):
                    data = data[key]
                else:
                    raise KeyError(key)
            data = data[int(idx)]
        else:
            if isinstance(data, dict):
                data = data[part]
            else:
                raise TypeError(f"Cannot index into {type(data).__name__} with '{part}'")
    return data


def describe(data, depth=0, max_depth=2, max_items=3):
    """Recursively describe structure."""
    if depth > max_depth:
        return "..."
    if isinstance(data, dict):
        if not data:
            return "{}"
        lines = [f"dict({len(data)} keys):"]
        for i, (k, v) in enumerate(data.items()):
            prefix = "  " * (depth + 1)
            if i >= max_items:
                lines.append(f"{prefix}... ({len(data) - max_items} more)")
                break
            lines.append(f"{prefix}{k}: {describe(v, depth+1, max_depth, max_items)}")
        return "\n".join(lines)
    if isinstance(data, list):
        if not data:
            return "[]"
        sample = describe(data[0], depth+1, max_depth, max_items)
        return f"list[{len(data)}] of {sample}"
    if isinstance(data, str):
        preview = data[:40] + "..." if len(data) > 40 else data
        return f"str: {preview!r}"
    return f"{get_type_name(data)}: {data}"


def show_keys(data, path=""):
    """Show top-level keys of object at path."""
    obj = resolve_path(data, path)
    if isinstance(obj, dict):
        for k in obj:
            print(f"  {k}: {get_type_name(obj[k])}")
    elif isinstance(obj, list):
        print(f"list with {len(obj)} items")
        if obj:
            print(f"First item type: {get_type_name(obj[0])}")
            if isinstance(obj[0], dict):
                print("Keys of first item:")
                for k in obj[0]:
                    print(f"  {k}: {get_type_name(obj[0][k])}")
    else:
        print(f"{get_type_name(obj)}: {obj}")


def count_types(data):
    """Count occurrences of each type recursively."""
    counts = {}
    def walk(v):
        t = get_type_name(v)
        counts[t] = counts.get(t, 0) + 1
        if isinstance(v, dict):
            for val in v.values():
                walk(val)
        elif isinstance(v, list):
            for item in v:
                walk(item)
    walk(data)
    return counts


def main(argv=None):
    parser = argparse.ArgumentParser(description="Inspect JSON structure")
    parser.add_argument("file", nargs="?", help="JSON file (default: stdin)")
    parser.add_argument("-p", "--path", default="", help="Dot-path to navigate (e.g. 'data.items[0]')")
    parser.add_argument("-k", "--keys", action="store_true", help="Show keys at path")
    parser.add_argument("-d", "--describe", action="store_true", help="Describe structure")
    parser.add_argument("-t", "--types", action="store_true", help="Count types")
    parser.add_argument("--depth", type=int, default=2, help="Max describe depth")
    args = parser.parse_args(argv)

    if args.file:
        data = json.loads(Path(args.file).read_text())
    else:
        data = json.loads(sys.stdin.read())

    if args.keys:
        show_keys(data, args.path)
    elif args.types:
        try:
            obj = resolve_path(data, args.path)
        except (KeyError, TypeError, IndexError) as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1
        for t, c in sorted(count_types(obj).items(), key=lambda x: -x[1]):
            print(f"  {t}: {c}")
    else:
        try:
            obj = resolve_path(data, args.path)
        except (KeyError, TypeError, IndexError) as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1
        print(f"Type: {get_type_name(obj)}")
        if isinstance(obj, dict):
            print(f"Keys: {len(obj)}")
        elif isinstance(obj, list):
            print(f"Length: {len(obj)}")
        print()
        print(describe(obj, max_depth=args.depth))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())  # pragma: no cover
