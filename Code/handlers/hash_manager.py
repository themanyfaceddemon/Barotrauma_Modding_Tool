import hashlib
import pickle
from pathlib import Path

# from Code.app_vars import AppConfig
# from Code.xml_object import XMLElement


class HashManager:
    # @staticmethod
    # def update_loaded_mods(path: Path, loaded_mods: XMLElement):
    #    pass

    @staticmethod
    def _get_str_hash(data: str):
        return hashlib.md5(data.encode()).hexdigest()

    @staticmethod
    def _hash_file(file_path: Path) -> str:
        md5_hash = hashlib.md5()
        with file_path.open("rb") as f:
            while chunk := f.read(4096):
                md5_hash.update(chunk)
        return md5_hash.hexdigest()

    @staticmethod
    def _hash_directory(directory_path: Path) -> str:
        combined_hash = hashlib.md5()

        for file_path in sorted(directory_path.rglob("*")):
            if file_path.is_file():
                file_hash = HashManager._hash_file(file_path)
                combined_hash.update(file_hash.encode())

        return combined_hash.hexdigest()
