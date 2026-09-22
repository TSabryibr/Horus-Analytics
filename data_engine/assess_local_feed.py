from __future__ import annotations

from data_engine.local_feed_selector import compare_local_sources, format_quality_report


def main() -> None:
    report = compare_local_sources()
    print(format_quality_report(report))


if __name__ == "__main__":
    main()
