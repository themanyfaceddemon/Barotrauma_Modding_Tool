import logging
import os
import platform
import queue
import string
import time
from concurrent.futures import ThreadPoolExecutor, wait
from pathlib import Path
from typing import List

logger = logging.getLogger(__name__)


class Finder:
    _SYSTEM_DIRS = {
        "Windows": [
            "C:\\Windows",
            "C:\\Program Files",
            "C:\\Program Files (x86)",
        ],
        "Linux": [
            "/usr",
            "/etc",
            "/bin",
            "/sys",
            "/sbin",
            "/proc",
            "/dev",
            "/run",
            "/tmp",
            "/var",
            "/boot",
            "/lib",
            "/lib64",
            "/opt",
            "/lost+found",
            "/snap",
            "/srv",
        ],
        "Darwin": [
            "/usr",
            "/etc",
            "/bin",
            "/sbin",
            "/System",
            "/Library",
        ],
    }
    _SYSTEM_DIRS = [Path(p) for p in _SYSTEM_DIRS.get(platform.system(), [])]

    @classmethod
    def _is_system_dir(cls, path: Path) -> bool:
        path = path.resolve()
        for sys_dir in cls._SYSTEM_DIRS:
            try:
                if path == sys_dir or path.is_relative_to(sys_dir):
                    return True
            except ValueError:
                continue
        return False

    @classmethod
    def _should_ignore_directory(
        cls,
        entry: Path,
        current_dir: Path,
        game_name: str,
    ) -> bool:
        ignored_directories = {
            "appdata",
            "temp",
            "cache",
            "logs",
            "backup",
            "bin",
            "obj",
            "history",
            "httpcache",
            "venv",
            "tmp",
            "programdata",
        }

        entry_name_lower = entry.name.lower()

        if entry_name_lower != ".steam" and (
            entry_name_lower.startswith((".", "_", "$", "~"))
            or entry_name_lower in ignored_directories
        ):
            logger.debug(f"Ignoring directory: {entry}")
            return True

        expected_structure = {
            ".steam": "steam",
            "steam": "steamapps",
            "steamapps": "common",
            "common": game_name.lower(),
        }

        expected_entry = expected_structure.get(current_dir.name.lower())
        if expected_entry and entry_name_lower != expected_entry:
            logger.debug(
                f"Ignoring directory: {entry} (in {current_dir.name}, not {expected_entry})"
            )
            return True

        return False

    @classmethod
    def search(cls) -> List[Path]:
        game_name = "barotrauma"

        if platform.system() == "Windows":
            drives = [
                Path(f"{drive}:\\")
                for drive in string.ascii_uppercase
                if Path(f"{drive}:\\").exists() and os.access(f"{drive}:\\", os.R_OK)
            ]
        else:
            drives = [
                Path(mount_point)
                for mount_point in Path("/mnt").glob("*")
                if mount_point.is_dir()
            ]

        logger.debug(f"Found drives: {len(drives)}")

        task_queue = queue.Queue()

        for drive in drives:
            task_queue.put(drive)

        found_paths: List[Path] = []

        def process_directory():
            nonlocal found_paths
            while not task_queue.empty():
                try:
                    current_dir = task_queue.get(timeout=3)
                    logger.debug(f"Processing directory: {current_dir}")
                    dirs_to_visit = [current_dir]

                    while dirs_to_visit:
                        dir_to_visit = dirs_to_visit.pop()
                        logger.debug(f"Processing directory: {dir_to_visit}")

                        if cls._is_system_dir(dir_to_visit):
                            logger.debug(f"Skipping system folder: {dir_to_visit}")
                            continue

                        try:
                            for entry in dir_to_visit.iterdir():
                                if entry.is_dir():
                                    if cls._should_ignore_directory(
                                        entry, dir_to_visit, game_name
                                    ):
                                        continue

                                    if entry.name.lower() == game_name:
                                        logger.debug(f"Match found: {entry}")
                                        found_paths.append(entry)
                                    else:
                                        dirs_to_visit.append(entry)
                        except PermissionError:
                            logger.debug(f"Access to directory {dir_to_visit} denied")
                        except Exception as e:
                            logger.debug(
                                f"Error processing directory {dir_to_visit}: {e}"
                            )

                except queue.Empty:
                    return

        start_time = time.time()

        with ThreadPoolExecutor() as executor:
            futures = []
            while not task_queue.empty():
                futures.append(executor.submit(process_directory))

            wait(futures)

        end_time = time.time()
        elapsed_time = end_time - start_time
        logger.debug(f"Total time taken: {elapsed_time:.2f} seconds")

        executable_name = (
            "barotrauma.exe" if platform.system() == "Windows" else "barotrauma"
        )

        valid_paths: List[Path] = []
        for path in found_paths:
            for exec_file in path.rglob("[Bb]arotrauma*"):
                if exec_file.name.lower() == executable_name:
                    logger.debug(f"Verified executable in path: {exec_file}")
                    valid_paths.append(path)

        return valid_paths
