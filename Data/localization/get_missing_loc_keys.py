import logging
import sys
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


def read_loc_file(file_path):
    loc_dict = {}
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            if "=" in line:
                key, _ = line.split("=", 1)
                loc_dict[key.strip()] = None

    return loc_dict


def collect_keys_from_language(language_folder: Path):
    all_keys = set()

    for loc_file in language_folder.rglob("*.loc"):
        loc_dict = read_loc_file(loc_file)
        all_keys.update(loc_dict.keys())

    return all_keys


def compare_keys_between_languages(input_directory: str):
    language_keys = {}
    input_path = Path(input_directory)

    for language_folder in input_path.iterdir():
        if language_folder.is_dir():
            all_keys = collect_keys_from_language(language_folder)
            language_keys[language_folder.name] = all_keys

    all_keys = set()
    for keys in language_keys.values():
        all_keys.update(keys)

    comparison_result = {}
    for key in all_keys:
        comparison_result[key] = {
            language: key in keys for language, keys in language_keys.items()
        }

    return comparison_result


def generate_report(comparison_result):
    report = []
    for key, languages in comparison_result.items():
        missing_languages = [
            language for language, present in languages.items() if not present
        ]
        if missing_languages:
            report.append(f"Key '{key}' is missing in: {', '.join(missing_languages)}")

    return report


def main():
    input_directory = "Data/localization"
    logger.info(f"Checking keys in: {input_directory}")

    comparison_result = compare_keys_between_languages(input_directory)
    report = generate_report(comparison_result)

    if report:
        logger.warning("Missing keys found:")
        for line in report:
            logger.warning(line)
        sys.exit(1)

    logger.info("All keys are present across all languages.")
    sys.exit(0)


if __name__ == "__main__":
    main()
