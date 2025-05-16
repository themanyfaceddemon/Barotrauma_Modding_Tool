import logging
import platform
import tarfile
import zipfile
from pathlib import Path
from typing import Union

import requests

from Code.app_vars import AppConfig

logger = logging.getLogger(__name__)


class SteamCMDInstaller:
    _DOWNLOAD_URL = {
        "Windows": "https://steamcdn-a.akamaihd.net/client/installer/steamcmd.zip",
        "Linux": "https://steamcdn-a.akamaihd.net/client/installer/steamcmd_linux.tar.gz",
        "Darwin": "https://steamcdn-a.akamaihd.net/client/installer/steamcmd_osx.tar.gz",
    }
    _ARCHIVE_NAME = (
        "steamcmd.zip" if platform.system() == "Windows" else "steamcmd.tar.gz"
    )

    @classmethod
    def _download_steamcmd(cls) -> Union[Path, None]:
        install_dir = AppConfig.get_steam_cmd_path()
        archive_path = install_dir / cls._ARCHIVE_NAME

        if AppConfig.get_steam_cmd_exec().exists():
            logger.info("SteamCMD archive already exists. Skipping download.")
            return None

        url = cls._DOWNLOAD_URL.get(platform.system(), None)
        if url is None:
            raise RuntimeError("Unknown operating system.")

        response = requests.get(url, stream=True)
        if response.status_code != 200:
            raise Exception(f"Download error: {response.status_code}")

        with open(archive_path, "wb") as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)

        return archive_path

    @classmethod
    def _extract_archive(cls, archive_path: Path):
        install_dir = str(AppConfig.get_steam_cmd_path())
        archive_path_str = str(archive_path)
        if archive_path_str.endswith(".zip"):
            with zipfile.ZipFile(archive_path, "r") as zip_ref:
                zip_ref.extractall(install_dir)

        elif archive_path_str.endswith(".tar.gz"):
            with tarfile.open(archive_path, "r:gz") as tar_ref:
                tar_ref.extractall(install_dir)

        else:
            raise Exception("Unknown archive format.")

        archive_path.unlink()

    @classmethod
    def install(cls):
        try:
            archive_path = cls._download_steamcmd()
            if archive_path:
                cls._extract_archive(archive_path)

        except Exception as e:
            logger.error(f"Error during installation: {e}")
