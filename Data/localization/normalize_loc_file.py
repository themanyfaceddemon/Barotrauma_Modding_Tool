import logging
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


def read_loc_file(file_path: Path):
    entries = []
    current_key = None

    with file_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            if "=" in line:
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip()

                if not key.startswith("."):
                    current_key = key
                    entries.append((key, value, []))
                elif current_key:
                    entries[-1][2].append((key, value))

    return entries


def normalize_loc_file(file_path: Path):
    entries = read_loc_file(file_path)

    entries.sort(key=lambda x: x[0])

    with file_path.open("w", encoding="utf-8") as f:
        for key, value, subentries in entries:
            f.write(f"{key} = {value}\n")
            for sub_key, sub_value in sorted(subentries, key=lambda x: x[0]):
                f.write(f"    {sub_key} = {sub_value}\n")


def normalize_loc_files_in_directory(directory_path: str):
    directory = Path(directory_path)

    for loc_file in directory.rglob("*.loc"):
        logger.info(f"Normalizing file: {loc_file}")
        normalize_loc_file(loc_file)

    logger.info("Localization normalization complete.")


if __name__ == "__main__":
    input_directory = "Data/localization"
    normalize_loc_files_in_directory(input_directory)
