"""Run a recipe and look at the result.

    python -m factory run recipes/default.yaml                          # summary + truth
    python -m factory run recipes/default.yaml --log M1                 # one station, every production
    python -m factory run recipes/default.yaml --log M1 --production PO-1003
    python -m factory run recipes/default.yaml --log all
    python -m factory run recipes/default.yaml --jsonl M1               # structured log lines
"""

import argparse

from .factory import Factory

# Rough rule of thumb for this kind of text; the real count depends on the tokenizer.
CHARS_PER_TOKEN = 3.3


def main() -> None:
    parser = argparse.ArgumentParser(prog="python -m factory")
    commands = parser.add_subparsers(dest="command", required=True)
    run = commands.add_parser("run", help="simulate a recipe")
    run.add_argument("recipe")
    run.add_argument("--log", metavar="STATION", help="print the log of a station, or 'all'")
    run.add_argument("--jsonl", metavar="STATION", help="print a station log as JSON lines")
    run.add_argument("--production", help="only this production")
    args = parser.parse_args()

    factory = Factory.from_yaml(args.recipe).run()

    if args.log:
        station = None if args.log == "all" else args.log
        print("\n".join(factory.logbook.text(station, args.production)))
        return
    if args.jsonl:
        print(factory.logbook.jsonl(args.jsonl, args.production))
        return

    recipe = factory.recipe
    print(f"{recipe.name}")
    ids = [production.id for production in recipe.productions]
    print(f"{'':<8}" + "".join(f"{i:>10}" for i in ids) + f"{'all':>10}   (~tokens)")
    grand = 0
    for station_id in factory.stations:
        sizes = [len("\n".join(factory.logbook.text(station_id, i))) for i in ids]
        grand += sum(sizes)
        print(f"{station_id:<8}" + "".join(f"{round(n / CHARS_PER_TOKEN):>10}" for n in sizes)
              + f"{round(sum(sizes) / CHARS_PER_TOKEN):>10}")
    print(f"{'total':<8}" + f"{round(grand / CHARS_PER_TOKEN):>{10 * len(ids) + 10}}\n")
    print(factory.truth().model_dump_json(indent=2))


if __name__ == "__main__":
    main()
