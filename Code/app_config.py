import atexit
import json
import logging
import platform
from pathlib import Path
from typing import Any, Dict, Final, Optional

logger = logging.getLogger(__name__)


class AppConfig:
    user_config: Dict[str, Any] = {}
    version: Final[str] = "0.3.0 beta"
    app_name: Final[str] = "Barotrauma Modding Tool"
    app_github: Final[str] = (
        "https://github.com/themanyfaceddemon/Barotrauma_Modding_Tool"
    )
    app_github_api: Final[str] = (
        "https://api.github.com/repos/themanyfaceddemon/Barotrauma_Modding_Tool"
    )

    _root: Path = Path(__file__).parents[1]
    _data_root: Path = _root / "Data"
    _user_data_path: Path = Path()

    xml_system_dirs = [
        "filelist.xml",  # Vanila barotrauma
        "file_list.xml",  # Luatrauma
        "files_list.xml",  # Luatrauma
        "runconfig.xml",  # Luatrauma
        "metadata.xml",  # Barotrauma modding tool
        "modparts.xml",  # Barotrauma modding tool
    ]

    @classmethod
    def init(cls, debug=False) -> None:
        if platform.system() == "Windows":
            cls._user_data_path = (
                Path.home() / "AppData" / "Roaming" / "BarotraumaModdingTool"
            )

        elif platform.system() == "Linux":
            cls._user_data_path = Path.home() / ".config" / "BarotraumaModdingTool"

        elif platform.system() == "Darwin":
            cls._user_data_path = (
                Path.home()
                / "Library"
                / "Application Support"
                / "BarotraumaModdingTool"
            )

        else:
            raise RuntimeError("Unknown operating system")

        cls._user_data_path.mkdir(parents=True, exist_ok=True)
        cls._load_user_config()
        cls.set("debug", debug)
        atexit.register(cls._save_user_config)

    @classmethod
    def _load_user_config(cls) -> None:
        config_path = cls._user_data_path / "config.json"

        if config_path.exists():
            try:
                with open(config_path, "r", encoding="utf-8") as file:
                    cls.user_config = json.load(file)

            except json.JSONDecodeError as err:
                logger.error(f"Error while decoding user_config.json: {err}")

    @classmethod
    def _save_user_config(cls) -> None:
        config_path = cls._user_data_path / "config.json"
        cls.user_config.pop("debug")

        with open(config_path, "w", encoding="utf-8") as file:
            json.dump(cls.user_config, file, indent=4, sort_keys=True)

    @classmethod
    def get(cls, key: str, default=None) -> Optional[Any]:
        return cls.user_config.get(key, default)

    @classmethod
    def set(cls, key: str, value: Any) -> None:
        cls.user_config[key] = value

    @classmethod
    def get_data_root_path(cls) -> Path:
        return cls._data_root

    @classmethod
    def get_game_path(cls) -> Optional[Path]:
        game_path = cls.user_config.get("barotrauma_dir")

        if game_path is None:
            return

        else:
            game_path = Path(game_path)

        if not game_path.exists():
            logger.error(f"Game path dont exists!\n|Path: {game_path}")
            return

        return game_path

    @classmethod
    def get_steam_mod_path(cls) -> Optional[Path]:
        path = cls.user_config.get("steam_mod_dir")
        if path is None:
            return None

        return Path(path)

    @classmethod
    def get_local_mod_path(cls) -> Optional[Path]:
        gp = cls.get_game_path()
        if gp is None:
            return None

        return Path(gp, "LocalMods")

    @classmethod
    def set_steam_mods_path(cls) -> None:
        if platform.system() == "Windows":
            path_to_mod = Path.home() / "AppData/Local"

        elif platform.system() == "Linux":
            path_to_mod = Path.home() / ".local/share"

        elif platform.system() == "Darwin":
            path_to_mod = Path.home() / "Library/Application Support"

        else:
            raise RuntimeError("Unknown operating system")

        path_to_mod = (
            path_to_mod
            / "Daedalic Entertainment GmbH/Barotrauma/WorkshopMods/Installed"
        )

        AppConfig.set("steam_mod_dir", str(path_to_mod))
