import logging
import os
import subprocess
import threading
from pathlib import Path
from typing import List

import requests
from bs4 import BeautifulSoup

from Code.app_vars import AppConfig

from .steam_cmd_installer import SteamCMDInstaller

logger = logging.getLogger(__name__)


class SteamCMDControl:
    _GAME_ID: int = 602960
    _cmd_ready_event = threading.Event()
    _cmd_initialized = False

    @classmethod
    def init(cls):
        if cls._cmd_initialized:
            return

        def init_steamcmd():
            try:
                SteamCMDInstaller.install()
                cls._run_cmd("")
                cls._cmd_initialized = True
                cls._cmd_ready_event.set()
                logger.info("SteamCMD initialized successfully.")

            except Exception as e:
                logger.error(f"Failed to initialize SteamCMD: {e}")
                cls._cmd_ready_event.set()

        thread = threading.Thread(target=init_steamcmd)
        thread.daemon = True
        thread.start()

    @classmethod
    def _run_cmd(cls, command: str) -> None:
        exec_file = AppConfig.get_steam_cmd_exec()
        if not exec_file.exists():
            raise RuntimeError(
                "steamcmd not found. Please ensure SteamCMD is installed."
            )

        if AppConfig.get("anonymous_download_mod", True) is True:
            cred = "+login anonymous "
        else:
            cred = f"+login {os.getenv('BTM_STEAM_CREDENTIALS')} "

        command.strip()

        try:
            if command:
                subprocess.run([str(exec_file), cred, command, "+quit"], check=True)
            else:
                subprocess.run([str(exec_file), cred, "+quit"], check=True)

        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Error running SteamCMD with command '{command}': {e}")

    @classmethod
    def run_cmd(cls, command: str) -> None:
        cls._cmd_ready_event.wait()
        if not cls._cmd_initialized:
            raise RuntimeError("SteamCMD is not initialized.")

        cls._run_cmd(command)

    @classmethod
    def download_item(cls, item_id: int | str):
        cls.run_cmd(f"workshop_download_item {cls._GAME_ID} {item_id}")

        return (
            AppConfig.get_steam_cmd_path()
            / "steamapps/workshop/content"
            / str(cls._GAME_ID)
            / str(item_id)
        )

    @classmethod
    def download_collection(cls, item_id: int | str) -> List[Path]:
        try:
            response = requests.get(AppConfig.steam_item_url + str(item_id))
            response.raise_for_status()

        except requests.RequestException as e:
            logger.error(f"Error fetching collection data: {e}")
            return []

        soup = BeautifulSoup(response.text, "html.parser")
        items = soup.find_all("div", class_="collectionItem")

        download_ids = [
            item.get("id").split("_")[1] for item in items if item.get("id")
        ]

        download_paths = []
        for item_id in download_ids:
            try:
                download_paths.append(cls.download_item(item_id))

            except Exception as e:
                logger.error(f"Error downloading item {item_id}: {e}")

        return download_paths


# TODO обновление модов
# установку порядка (по сути почти сделано) и прочее.
# Ебаная баробуба не позволяет ссылаться ни на что кроме как на "LocalMods" или "%LocalAppData%" при установке модов
# TODO починить загрузку модификаций, ибо стим смд ДЕЛАЛИ ЕБАНЫЕ ПИДОРАСЫ СУКА КАК У МЕНЯ ГОРИТ ОЧКО
