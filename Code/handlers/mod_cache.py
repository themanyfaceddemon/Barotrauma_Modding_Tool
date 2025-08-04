import hashlib
import logging
import pickle
from pathlib import Path
from typing import TYPE_CHECKING, Any

from Code.app_config import AppConfig

if TYPE_CHECKING:
    from Code.package.dataclasses import ModUnit

logger = logging.getLogger(__name__)


class ModCache:
    _cache_dir: Path = AppConfig._data_root / ".cache"
    _cache: dict[str, Any] = {}

    @classmethod
    def initialize(cls):
        cls._cache_dir.mkdir(exist_ok=True)

    @classmethod
    def calculate_mod_hash(cls, mod_path: Path) -> str:
        hasher = hashlib.sha256()

        files = []
        for ext in ("*.xml", "*.lua", "*.cs"):
            files.extend(sorted(mod_path.rglob(ext)))

        for file in files:
            try:
                rel_path = str(file.relative_to(mod_path))
                hasher.update(rel_path.encode())

                with open(file, "rb") as f:
                    while chunk := f.read(8192):
                        hasher.update(chunk)

            except Exception as e:
                logger.error(f"Error calculating hash for {file}: {e}")
                continue

        return hasher.hexdigest()

    @classmethod
    def get_cache_path(cls, mod_id: str) -> Path:
        return cls._cache_dir / f"{mod_id}.bmt_cache"

    @classmethod
    def load_cached_mod(
        cls,
        mod_id: str,
        current_hash: str,
    ) -> Any | None:
        if not AppConfig.get("enable_performance_hash", False):
            return None

        cache_path = cls.get_cache_path(mod_id)
        if not cache_path.exists():
            return None

        try:
            with open(cache_path, "rb") as f:
                cached_data = pickle.load(f)

            if cached_data.get("hash") == current_hash:
                logger.debug(f"Cache hit for mod {mod_id}")
                return cached_data.get("data")

            else:
                logger.debug(f"Cache miss for mod {mod_id} (hash mismatch)")
                return None

        except Exception as e:
            logger.error(f"Error loading cache for mod {mod_id}: {e}")
            return None

    @classmethod
    def save_mod_cache(cls, mod_id: str, mod_hash: str, mod_unit: "ModUnit"):
        if not AppConfig.get("enable_performance_hash", False):
            return

        cache_path = cls.get_cache_path(mod_id)
        try:
            cache_data = {"hash": mod_hash, "data": mod_unit}
            with open(cache_path, "wb") as f:
                pickle.dump(cache_data, f)

            logger.debug(f"Cached mod {mod_id}")

        except Exception as e:
            logger.error(f"Error saving cache for mod {mod_id}: {e}")
