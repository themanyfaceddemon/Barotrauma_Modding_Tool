import logging
import os
import subprocess
import threading

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
    def download_item(cls, item_id: int):
        cls.run_cmd(f"workshop_download_item {cls._GAME_ID} {item_id}")

        return (
            AppConfig.get_steam_cmd_path()
            / "steamapps/workshop/content"
            / str(cls._GAME_ID)
            / str(item_id)
        )
