import dearpygui.dearpygui as dpg

from Code.app_config import AppConfig
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
    def _build_lang_ch_content(cls, parent) -> None:
        i = 1
        groop = dpg.add_group(horizontal=True, parent=parent)
        for lang_code in Localization.get_all_lang_code():
            if i >= 3:
                i = 1
                groop = dpg.add_group(horizontal=True, parent=parent)

            dpg.add_image_button(
                f"{lang_code}_btn_img",
                callback=cls._on_lang_btn,
                user_data=lang_code,
                parent=groop,
            )
            i += 1

    @classmethod
    def _build_game_ch_content(cls, parent) -> None:
        with dpg.group(horizontal=True, parent=parent):
            with dpg.group():
                dpg.add_text(Localization.get_string("settings_game_auto_lua"))
                dpg.add_text(Localization.get_string("settings_game_skip_intro"))

            with dpg.group():
                dpg.add_checkbox(
                    default_value=AppConfig.get("game_config_auto_lua", False),  # type: ignore
                    callback=lambda s, a: AppConfig.set("game_config_auto_lua", a),
                )
                dpg.add_checkbox(
                    default_value=AppConfig.get("game_config_skip_intro", False),  # type: ignore
                    callback=lambda s, a: AppConfig.set("game_config_skip_intro", a),
                )

    @classmethod
    def _build_etc_ch_content(cls, parent) -> None:
        with dpg.group(horizontal=True, parent=parent):
            with dpg.group():
                with dpg.group(horizontal=True):
                    dpg.add_text(Localization.get_string("settings_performance_hash"))
                    dpg.add_text(Localization.get_string("info_popup"))
                with dpg.tooltip(dpg.last_container()):
                    dpg.add_text(
                        Localization.get_string("settings_performance_hash_info")
                    )

            with dpg.group():
                dpg.add_checkbox(
                    default_value=AppConfig.get("enabel_performance_hash", False),  # type: ignore
                    callback=lambda s, a: AppConfig.set("enabel_performance_hash", a),
                )

    @classmethod
    def _build_content(cls) -> None:
        with dpg.collapsing_header(
            label=Localization.get_string("settings_lang_str"),
            parent=cls._window_name,
            default_open=True,
            leaf=True,
        ) as ch:
            cls._build_lang_ch_content(ch)
        dpg.add_separator(parent=cls._window_name)

        ###
        with dpg.collapsing_header(
            label=Localization.get_string("settings_game_str"),
            parent=cls._window_name,
            default_open=True,
            leaf=True,
        ) as ch:
            cls._build_game_ch_content(ch)
        dpg.add_separator(parent=cls._window_name)

        ###
        with dpg.collapsing_header(
            label=Localization.get_string("settings_etc_str"),
            parent=cls._window_name,
            default_open=True,
            leaf=True,
        ) as ch:
            cls._build_etc_ch_content(ch)
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
