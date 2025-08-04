import logging
import platform
import subprocess

import requests

from Code.app_config import AppConfig

logger = logging.getLogger(__name__)


class Updater:
    _luatrauma_url = (
        "https://github.com/Luatrauma/Luatrauma.AutoUpdater/releases/download/latest"
    )
    _LUA = {
        "Windows": "Luatrauma.AutoUpdater.win-x64.exe",
        "Darwin": "Luatrauma.AutoUpdater.osx-x64",
        "Linux": "Luatrauma.AutoUpdater.linux-x64",
    }

    @classmethod
    def download(cls) -> bool:
        lua_pe = cls._LUA.get(platform.system(), None)
        if not lua_pe:
            raise RuntimeError("Unknown operating system")

        game_path = AppConfig.get_game_path()
        if game_path is None:
            return False

        url = cls._luatrauma_url + "/" + lua_pe
        updater_path = game_path / lua_pe

        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()
            # total_size = int(response.headers.get("Content-Length", 0))
            # downloaded_size = 0
            chunk_size = 4092
            with open(updater_path, "wb") as file:
                for i, chunk in enumerate(response.iter_content(chunk_size=chunk_size)):
                    file.write(chunk)
                    # downloaded_size += len(chunk)  # TODO: Loading bar

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
