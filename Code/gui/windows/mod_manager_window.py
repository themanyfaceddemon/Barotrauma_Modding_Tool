import dearpygui.dearpygui as dpg

from Code.loc import Localization

from .base_window import BaseWindow


class ModManagerWindow(BaseWindow):
    _window_name = "mod_manager_window"

    @classmethod
    def _on_window_resize(cls, app_data: tuple[int, int, int, int]) -> None:
        if not dpg.does_item_exist(cls._window_name):
            return

        dpg.set_item_pos(cls._window_name, [round(app_data[2] * 0.2), 0])
        dpg.set_item_width(cls._window_name, round(app_data[2] * 0.8))
        dpg.set_item_height(cls._window_name, app_data[3])

    @classmethod
    def create(cls) -> None:
        if dpg.does_item_exist(cls._window_name):
            dpg.focus_item(cls._window_name)
            return

        with dpg.window(
            tag=cls._window_name,
            label=Localization.get_string("mod_manager_window_name"),
            on_close=cls._on_window_close,
            no_move=True,
            no_resize=True,
            no_collapse=True,
            pos=[0, 0],
        ):
            pass

        super().create()

    @classmethod
    def rebuild(cls) -> None:
        pass
