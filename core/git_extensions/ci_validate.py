from __future__ import annotations

import json
import sys
from pathlib import Path

try:
    import jsonschema
except Exception:
    print("jsonschema package not installed; install via pip to run validation", file=sys.stderr)
    sys.exit(2)


def validate_matrix(path: Path) -> int:
    schema = json.loads((Path(__file__).parent / "schemas" / "matrix.schema.json").read_text(encoding="utf-8"))
    data = json.loads(path.read_text(encoding="utf-8"))
    try:
        jsonschema.validate(instance=data, schema=schema)
        print(f"OK: {path}")
        return 0
    except jsonschema.ValidationError as e:
        print(f"ERROR: matrix schema validation failed: {e}")
        return 1


def main(argv):
    if len(argv) != 2:
        print("Usage: python -m core.git_extensions.ci_validate <matrix.json>")
        return 2
    p = Path(argv[1])
    if not p.exists():
        print(f"No such file: {p}", file=sys.stderr)
        return 2
    return validate_matrix(p)


if __name__ == "__main__":
    sys.exit(main(sys.argv))

