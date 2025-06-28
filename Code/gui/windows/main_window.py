from collections.abc import Callable
from dataclasses import dataclass

import dearpygui.dearpygui as dpg

from Code.dpg_tools import ViewportResizeManager
from Code.loc import Localization as loc

from .base_window import BaseWindow


@dataclass
class _ButtonInfo:
    id: int
    label: str
    func: Callable


class MainWindow(BaseWindow):
    _window_name = "main_window"
    _btn_order: list[str] = []
    _dict_of_btn: dict[str, _ButtonInfo] = {}

    @classmethod
    def _on_window_resize(cls, app_data: tuple[int, int, int, int]) -> None:
        if dpg.does_item_exist(cls._window_name):
            item_width = int(app_data[2] * 0.2)

            dpg.set_item_width(cls._window_name, item_width)
            dpg.set_item_height(cls._window_name, app_data[3])

            to_delete = []
            for key, btn_info in cls._dict_of_btn.items():
                if dpg.does_item_exist(btn_info.id):
                    dpg.set_item_width(btn_info.id, item_width - 16)
                else:
                    to_delete.append(key)

            for key in to_delete:
                del cls._dict_of_btn[key]

    @classmethod
    def create(cls) -> None:
        with dpg.window(
            tag=cls._window_name,
            on_close=cls._on_window_close,
            no_move=True,
            no_title_bar=True,
            pos=[0, 0],
        ):
            pass

        ViewportResizeManager.add_callback(cls._window_name, cls._on_window_resize)

    @classmethod
    def add_button(cls, name: str, label_id: str, func: Callable) -> None:
        if name in cls._dict_of_btn:
            return

        btn_id = dpg.add_button(label=loc.get_string(label_id), callback=func)
        cls._dict_of_btn[name] = _ButtonInfo(int(btn_id), label_id, func)
        cls._btn_order.append(name)

    @classmethod
    def rebuild_buttons(cls) -> None:
        for btn_id in dpg.get_item_children(cls._window_name, 1) or []:
            dpg.delete_item(btn_id)

        for key in cls._btn_order:
            btn_info = cls._dict_of_btn[key]
            new_id = dpg.add_button(
                label=loc.get_string(btn_info.label), callback=btn_info.func
            )
            btn_info.id = int(new_id)

    @classmethod
    def remove_button(cls, name: str) -> None:
        btn_info = cls._dict_of_btn.pop(name, None)
        if btn_info is None:
            return

        if dpg.does_item_exist(btn_info.id):
            dpg.delete_item(btn_info.id)

        if name in cls._btn_order:
            cls._btn_order.remove(name)
