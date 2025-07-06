import shutil
import tempfile
from pathlib import Path

import dearpygui.dearpygui as dpg

from Code.app_config import AppConfig


class FontManager:
    @staticmethod
    def _safe_font(path: Path, size: int):
        """
        Workaround for DPG Windows+Unicode font path bug.
        Copies font to ASCII-only temp path.
        """
        with tempfile.NamedTemporaryFile(delete=False, suffix=path.suffix) as tmp:
            tmp_path = Path(tmp.name)
            tmp.close()
            shutil.copy(path, tmp_path)
        try:
            return dpg.font(str(tmp_path), size)
        finally:
            tmp_path.unlink(missing_ok=True)

    @staticmethod
    def load_fonts():
        default_font_path = (
            AppConfig.get_data_root_path() / "fonts/Monocraft/Monocraft.otf"
        )

        with dpg.font_registry():
            with FontManager._safe_font(default_font_path, 13) as default_font:
                dpg.add_font_range_hint(dpg.mvFontRangeHint_Default)
                dpg.add_font_range_hint(dpg.mvFontRangeHint_Cyrillic)

                # Greek character range
                dpg.add_font_range(0x0391, 0x03C9)

                # Range of upper and lower numerical indices
                dpg.add_font_range(0x2070, 0x209F)

        dpg.bind_font(default_font)
