import atexit
import json
import logging
import platform
from pathlib import Path
from typing import Any, Dict, Final, Optional


class AppConfig:
    user_config: Dict[str, Any] = {}
    version: Final[str] = "0.2.0"

    _root: Path = Path(__file__).parents[1]
    _data_root: Path = _root / "Data"
    _user_data_path: Path = Path()

    xml_system_dirs = [
        "filelist.xml",
        "metadata.xml",
        "modparts.xml",
        "file_list.xml",
        "files_list.xml",
        "runconfig.xml",
    ]

    @classmethod
    def init(cls, debug=False) -> None:
        AppConfig.get_hash_path().mkdir(parents=True, exist_ok=True)

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
                logging.error(f"Error while decoding user_config.json: {err}")

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
            logging.error("Game path not set!")
            return

        else:
            game_path = Path(game_path)

        if not game_path.exists():
            logging.error(f"Game path dont exists!\n|Path: {game_path}")
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
    def get_hash_path(cls) -> Path:
        return cls._data_root / ".hash"

    @classmethod
    def set_steam_mods_path(cls) -> None:
        if platform.system() == "Windows":
            path_to_mod = (
                Path.home()
                / "AppData"
                / "Local"
                / "Daedalic Entertainment GmbH"
                / "Barotrauma"
                / "WorkshopMods"
                / "Installed"
            )

        elif platform.system() == "Linux":
            path_to_mod = (
                Path.home()
                / ".local"
                / "share"
                / "Daedalic Entertainment GmbH"
                / "Barotrauma"
                / "WorkshopMods"
                / "Installed"
            )

        elif platform.system() == "Darwin":
            path_to_mod = (
                Path.home()
                / "Library"
                / "Application Support"
                / "Daedalic Entertainment GmbH"
                / "Barotrauma"
                / "WorkshopMods"
                / "Installed"
            )

        else:
            raise RuntimeError("Unknown operating system")

        AppConfig.set("steam_mod_dir", str(path_to_mod))
