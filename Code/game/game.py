import logging
import platform
import subprocess
from typing import List

from Code.app_config import AppConfig

from .updater import Updater

logger = logging.getLogger(__name__)


class Game:
    _EXECUTABLES = {
        "Windows": "Barotrauma.exe",
        "Darwin": "Barotrauma.app/Contents/MacOS/Barotrauma",
        "Linux": "Barotrauma",
    }

    @classmethod
    def run(cls, install_lua: bool = False, skip_intro: bool = False):
        if install_lua:
            Updater.download()

        args = ["-skipintro"] if skip_intro else []
        cls._run_pe(args)

    @classmethod
    def is_valid_exec(cls) -> bool:
        exec_file = cls._EXECUTABLES.get(platform.system())
        if exec_file is None:
            return False

        game_path = AppConfig.get_game_path()
        if game_path is None:
            return False

        executable_path = game_path / exec_file
        if not executable_path.exists():
            return False

        return True

    @classmethod
    def _run_pe(cls, parms: List[str] = []):
        try:
            exec_file = cls._EXECUTABLES.get(platform.system())
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
