import logging
import os
import platform
import string
import subprocess
from pathlib import Path
from typing import List

import requests

from Code.app_vars import AppConfig

logger = logging.getLogger("GameProcessor")


class Game:
    _EXECUTABLES = {
        "Windows": "Barotrauma.exe",
        "Darwin": "Barotrauma.app/Contents/MacOS/Barotrauma",
        "Linux": "Barotrauma",
    }

    _LUA = {
        "Windows": (
            "https://github.com/Luatrauma/Luatrauma.AutoUpdater/releases/download/latest/Luatrauma.AutoUpdater.win-x64.exe",
            "Luatrauma.AutoUpdater.win-x64.exe",
        ),
        "Darwin": (
            "https://github.com/Luatrauma/Luatrauma.AutoUpdater/releases/download/latest/Luatrauma.AutoUpdater.osx-x64",
            "Luatrauma.AutoUpdater.osx-x64",
        ),
        "Linux": (
            "https://github.com/Luatrauma/Luatrauma.AutoUpdater/releases/download/latest/Luatrauma.AutoUpdater.linux-x64",
            "Luatrauma.AutoUpdater.linux-x64",
        ),
    }

    @staticmethod
    def run_game(install_lua: bool = False, skip_intro: bool = False):
        if install_lua:
            Game.download_update_lua()

        parms = ["-skipintro"] if skip_intro else []
        Game.run_exec(parms)

    @staticmethod
    def download_update_lua():
        lua = Game._LUA.get(platform.system(), None)
        if not lua:
            raise RuntimeError("Unknown operating system")

        game_path = AppConfig.get_game_path()
        if game_path is None:
            return

        url = lua[0]
        exec_file = lua[1]

        updater_path = game_path / exec_file

        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()
            # total_size = int(response.headers.get("Content-Length", 0))
            downloaded_size = 0
            chunk_size = 4092
            with open(updater_path, "wb") as file:
                for i, chunk in enumerate(response.iter_content(chunk_size=chunk_size)):
                    file.write(chunk)
                    downloaded_size += len(chunk)  # TODO: Loading bar

            if platform.system() in ["Darwin", "Linux"]:
                subprocess.run(["chmod", "+x", str(updater_path)], check=True)

            result = subprocess.run([str(updater_path)], cwd=str(game_path))

            return result.returncode == 0

        except requests.RequestException as e:
            logger.error(f"Network error while downloading updater: {e}")
            return False

        except subprocess.CalledProcessError as e:
            logger.error(f"Error setting execute permissions: {e}")
            return False

        except Exception as e:
            logger.error(f"Unexpected error during download or execution: {e}")
            return False

    @staticmethod
    def run_exec(parms: List[str] = []):
        try:
            exec_file = Game._EXECUTABLES.get(platform.system())
            if exec_file is None:
                raise RuntimeError("Unknown operating system")

            game_path = AppConfig.get_game_path()
            if game_path is None:
                return

            executable_path = game_path / exec_file
            if not executable_path.exists():
                logger.error(f"Executable not found: {executable_path}")
                return

            subprocess.run([str(executable_path)] + parms, cwd=str(game_path))

        except Exception as e:
            logger.error(f"Error running the game: {e}")

    @staticmethod
    def search_all_games_on_all_drives() -> List[Path]:
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

        found_paths: List[Path] = []

        for drive in drives:
            logger.debug(f"Processing drive: {drive}")
            dirs_to_visit = [drive]

            while dirs_to_visit:
                current_dir = dirs_to_visit.pop()
                logger.debug(f"Processing directory: {current_dir}")

                if Game._is_system_directory(current_dir):
                    logger.debug(f"Ignoring system folder: {current_dir}")
                    continue

                try:
                    for entry in current_dir.iterdir():
                        if entry.is_dir():
                            if Game._should_ignore_directory(
                                entry, current_dir, game_name
                            ):
                                continue

                            if entry.name.lower() == game_name:
                                logger.debug(f"Match found: {entry}")
                                found_paths.append(entry)
                            else:
                                dirs_to_visit.append(entry)

                except PermissionError:
                    logger.debug(f"Access to directory {current_dir} denied")

                except Exception as e:
                    logger.debug(f"Error processing directory {current_dir}: {e}")

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

    @staticmethod
    def _is_system_directory(path):
        if platform.system() == "Windows":
            system_dirs = [
                Path("C:\\Windows"),
                Path("C:\\Program Files"),
                Path("C:\\Program Files (x86)"),
            ]
            return path in system_dirs or path.is_relative_to(Path("C:\\Windows"))

        else:
            system_dirs = [
                Path("/usr"),
                Path("/etc"),
                Path("/bin"),
                Path("/sys"),
                Path("/sbin"),
                Path("/proc"),
                Path("/dev"),
                Path("/run"),
                Path("/tmp"),
                Path("/var"),
                Path("/boot"),
                Path("/lib"),
                Path("/lib64"),
                Path("/opt"),
                Path("/lost+found"),
                Path("/snap"),
                Path("/srv"),
            ]

            return path in system_dirs

    @staticmethod
    def _should_ignore_directory(entry, current_dir, game_name):
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
