import argparse
import json
from .mapping import classify_nace, load_mapping


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="IAF–NACE classifier CLI")
    parser.add_argument("code", help="NACE code to classify, e.g. 24.46 or 47")
    parser.add_argument(
        "--mapping", "-m", default=None, help="Path to mapping JSON (defaults to repo file)"
    )
    parser.add_argument("--json", action="store_true", help="Output JSON instead of plain text")
    args = parser.parse_args(argv)

    mapping = load_mapping(args.mapping)
    result = classify_nace(args.code, mapping)

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        if not result:
            print("No match found")
            return 1
        print(
            f"NACE {result['nace_code']} -> IAF {result['codigo_iaf']}"
            + (f" ({result['nombre_iaf']})" if result.get("nombre_iaf") else "")
            + f" [pattern: {result['matched_pattern']}]"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

