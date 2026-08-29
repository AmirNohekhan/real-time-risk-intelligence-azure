import argparse
import json

import pandas as pd

from risk_platform.config import Settings
from risk_platform.data.synthetic import generate_dataset, write_dataset
from risk_platform.monitoring.drift import drift_report, write_report
from risk_platform.training import train


def main() -> None:
    parser = argparse.ArgumentParser(prog="risk-platform")
    commands = parser.add_subparsers(dest="command", required=True)
    generate = commands.add_parser("generate")
    generate.add_argument("--count", type=int, default=5000)
    generate.add_argument("--seed", type=int, default=42)
    commands.add_parser("train")
    commands.add_parser("drift")
    args = parser.parse_args()
    settings = Settings()
    raw_path = settings.data_dir / "raw/events/year=2025/events.parquet"
    if args.command == "generate":
        path = write_dataset(generate_dataset(args.count, args.seed), raw_path)
        print(path)
    elif args.command == "train":
        if not raw_path.exists():
            write_dataset(generate_dataset(), raw_path)
        bundle = train(
            pd.read_parquet(raw_path),
            settings.model_path,
            settings.false_negative_cost,
            settings.false_positive_cost,
        )
        print(json.dumps({"model_version": bundle.version, "metrics": bundle.metrics}, indent=2))
    else:
        frame = pd.read_parquet(raw_path)
        midpoint = len(frame) // 2
        report = drift_report(frame.iloc[:midpoint], frame.iloc[midpoint:])
        out = settings.data_dir / "monitoring/drift.json"
        write_report(report, out)
        print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
