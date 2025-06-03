import logging
import shutil
import webbrowser

import dearpygui.dearpygui as dpg

from Code.app_vars import AppConfig
from Code.loc import Localization as loc

logger = logging.getLogger(__name__)


class ExperimentalTab:
    @classmethod
    def create(cls) -> None:
        with dpg.tab(
            label=loc.get_string("experimental-tab-label"),
            parent="main_tab_bar",
            tag="experimental_tab",
        ):
            dpg.add_text(
                "Всё что находится в данной вкладке является эксперементальными функциями, сделанными для тестов. Они могут как и помочь, так и нет."
            )
            dpg.add_text(
                "В случае ошибок связанных с функциями из этой вкладки просьба сразу писать в Issues основного репозитория"
            )
            dpg.add_button(
                label="Открыть репозиторий",
                callback=lambda: webbrowser.open(
                    "https://github.com/themanyfaceddemon/Barotrauma_Modding_Tool/issues",
                    2,
                ),
            )

            dpg.add_separator()
            dpg.add_separator()

            dpg.add_checkbox(
                label="Кеширование аддонов",
                callback=cls._on_cash_toggle,
            )

    @classmethod
    def _on_cash_toggle(cls, sender, app_data, user_data):
        AppConfig.set("experimental-cash", app_data)

        if app_data:
            path = AppConfig.get_data_root_path() / ".cash"
            path.mkdir(exist_ok=True)
            with open((path / ".bmtm"), "w") as f:
                f.write("v1")
        else:
            path = AppConfig.get_data_root_path() / ".cash"
            if path.exists():
                shutil.rmtree(path)

    @classmethod
    def destroy(cls) -> None:
        if dpg.does_item_exist("experimental_tab"):
            dpg.delete_item("experimental_tab")
