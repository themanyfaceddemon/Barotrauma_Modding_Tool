import dearpygui.dearpygui as dpg

from Code.dpg_tools import ViewportResizeManager
from Code.loc import Localization

from .base_window import BaseWindow


class SettingsWindow(BaseWindow):
    _window_name = "settings_window"

    @classmethod
    def _on_window_resize(cls, app_data: tuple[int, int, int, int]) -> None:
        if not dpg.does_item_exist(cls._window_name):
            return

        dpg.set_item_pos(cls._window_name, [round(app_data[2] * 0.2), 0])
        dpg.set_item_width(cls._window_name, round(app_data[2] * 0.8))
        dpg.set_item_height(cls._window_name, app_data[3])

    @classmethod
    def _update_for_lang(cls) -> None:
        for id_ in dpg.get_item_children(cls._window_name, 1) or []:
            if dpg.does_item_exist(id_):
                dpg.delete_item(id_)

        cls._build_content()
        dpg.set_item_label(
            cls._window_name, Localization.get_string("settings_window_name")
        )

    @classmethod
    def _on_lang_btn(cls, sender, app_data, user_data) -> None:
        Localization.change_language(user_data)

    @classmethod
    def _build_btns(cls) -> None:
        i = 1
        groop = dpg.add_group(horizontal=True, parent=cls._window_name)
        for lang_code in Localization.get_all_lang_code():
            if i >= 3:
                i = 1
                groop = dpg.add_group(horizontal=True, parent=cls._window_name)

            dpg.add_image_button(
                f"{lang_code}_btn_img",
                callback=cls._on_lang_btn,
                user_data=lang_code,
                parent=groop,
            )
            i += 1

    @classmethod
    def _build_content(cls) -> None:
        dpg.add_text(
            Localization.get_string("settings_lang_str"), parent=cls._window_name
        )
        cls._build_btns()
        dpg.add_separator(parent=cls._window_name)

    @classmethod
    def create(cls) -> None:
        if dpg.does_item_exist(cls._window_name):
            dpg.focus_item(cls._window_name)
            return

        with dpg.window(
            tag=cls._window_name,
            label=Localization.get_string("settings_window_name"),
            on_close=cls._on_window_close,
            no_move=True,
            no_resize=True,
            no_collapse=True,
            pos=[0, 0],
        ):
            cls._build_content()

        ViewportResizeManager.add_callback(cls._window_name, cls._on_window_resize)
        Localization.add_callback(cls._update_for_lang)
