import atexit
import logging
from collections import defaultdict, deque
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import List, Optional

from Code.app_vars import AppConfig
from Code.loc import Localization as loc
from Code.package.dataclasses import ModUnit
from Code.xml_object import XMLBuilder, XMLComment, XMLElement

logger = logging.getLogger(__name__)


class HashManager:
    _bmtm = {}

    @classmethod
    def init(cls):
        if AppConfig.get("experimental-hash", False):
            atexit.register(cls._on_exit)

    @classmethod
    def get_mod(cls, mod_name, hash) -> Optional["ModUnit"]:
        pass

    @classmethod
    def _on_load(cls):
        pass

    @classmethod
    def _on_exit(cls):
        pass
