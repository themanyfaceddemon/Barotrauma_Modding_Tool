import atexit
import platform
import shutil
import tempfile
import uuid
from pathlib import Path

import dearpygui.dearpygui as dpg

from Code.app_config import AppConfig


class FontManager:
    _ascii_temp_dir = None

    @staticmethod
    def _get_ascii_temp_dir() -> Path:
        if FontManager._ascii_temp_dir:
            return FontManager._ascii_temp_dir

        base_temp = Path(tempfile.gettempdir())
        if any(ord(c) > 127 for c in str(base_temp)):
            # Deamon: This is total bullshit, but we can have user named with non-ASCII characters,
            # which essentially breaks the attempt to use the temp directory over the knee
            ascii_dir = Path("C:/dpg_font_cache")
            ascii_dir.mkdir(exist_ok=True)
            FontManager._ascii_temp_dir = ascii_dir

            def cleanup():
                try:
                    shutil.rmtree(ascii_dir)

                except Exception:
                    pass

            atexit.register(cleanup)

            return ascii_dir
        else:
            FontManager._ascii_temp_dir = base_temp
            return base_temp

    @staticmethod
    def safe_font(path: Path, size: int):
        if platform.system() != "Windows":
            return dpg.font(str(path), size)

        # Deamon: This shit looks like malware behavior,
        # but it’s the only way to work around Windows bullshit and its Unicode path shenanigans.
        # The only one I found
        temp_dir = FontManager._get_ascii_temp_dir()
        tmp_path = temp_dir / f"{uuid.uuid4().hex}{path.suffix}"
        shutil.copy(path, tmp_path)
        return dpg.font(str(tmp_path), size)

    @staticmethod
    def load_fonts():
        default_font_path = (
            AppConfig.get_data_root_path() / "fonts/Monocraft/Monocraft.otf"
        )

        with dpg.font_registry():
            with FontManager.safe_font(default_font_path, 13) as default_font:
                dpg.add_font_range_hint(dpg.mvFontRangeHint_Default)
                dpg.add_font_range_hint(dpg.mvFontRangeHint_Cyrillic)

                # Greek character range
                dpg.add_font_range(0x0391, 0x03C9)

                # Range of upper and lower numerical indices
                dpg.add_font_range(0x2070, 0x209F)

        dpg.bind_font(default_font)
