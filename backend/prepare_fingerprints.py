from pathlib import Path

from fingerprint_cleaner import clean_fingerprints


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SOURCE = PROJECT_ROOT / "data" / "fingerprints.csv"
DEFAULT_OUTPUT = PROJECT_ROOT / "data" / "fingerprints_clean.csv"


def main():
    stats = clean_fingerprints(DEFAULT_SOURCE, DEFAULT_OUTPUT)

    print(f"Wrote {stats['rows']} cleaned fingerprint rows to {stats['output_path']}")
    for anchor, count in stats["imputed"].items():
        print(f"{anchor}: imputed {count} missing values")


if __name__ == "__main__":
    main()
