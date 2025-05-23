import json
import logging
import webbrowser

import dearpygui.dearpygui as dpg
import requests

import Code.dpg_tools as dpg_tools
from Code.app_vars import AppConfig
from Code.game import Game
from Code.handlers import ModManager
from Code.loc import Localization as loc

from .gui_meta_create import GUIMetaTab
from .mods_tab import ModsTab
from .settings_tab import SettingsTab

logger = logging.getLogger(__name__)


class AppInterface:
    @staticmethod
    def initialize():
        AppInterface._create_viewport_menu_bar()
        AppInterface._create_main_window()
        SettingsTab.create()
        ModsTab.create()
        GUIMetaTab.create()

        dpg.set_value("main_tab_bar", "mod_tab")

        dpg.set_viewport_resize_callback(AppInterface._res_callback)
        dpg_tools.rc_windows()

    @staticmethod
    def _res_callback() -> None:
        dpg_tools.rc_windows()

        AppConfig.set(
            "last_viewport_size",
            f"{dpg.get_viewport_width()} {dpg.get_viewport_height()}",
        )

    @staticmethod
    def _create_main_window():
        with dpg.window(
            no_move=True,
            no_resize=True,
            no_title_bar=True,
            tag="main_window",
        ):
            dpg.add_tab_bar(tag="main_tab_bar")

    @staticmethod
    def _create_viewport_menu_bar():
        dpg.add_viewport_menu_bar(tag="main_view_bar")

        dpg.add_menu_item(
            label=loc.get_string("menu-bar-start-game"),
            parent="main_view_bar",
            callback=AppInterface.start_game,
        )

        dpg.add_menu_item(
            label=loc.get_string("cac-window-name"),
            parent="main_view_bar",
            callback=AppInterface.create_cac_window,
        )

        is_latest = None
        try:
            response = requests.get(AppConfig.github_api_url + "/releases/latest")
            if response.status_code == 200:
                latest_release = response.json()
                is_latest = AppConfig.version == latest_release["tag_name"]

        except Exception:
            pass

        if is_latest is True:
            label = loc.get_string("base-yes")

        elif is_latest is False:
            label = loc.get_string("base-no")

        else:
            label = loc.get_string("base-unknown")

        dpg.add_menu_item(
            label=(loc.get_string("cur-version-latest") + " " + label),
            parent="main_view_bar",
            callback=lambda: webbrowser.open(
                AppConfig.github_user_url + "/releases/latest"
            ),
            enabled=(is_latest is False),
        )

        if AppConfig.get("debug", False):
            dpg.add_menu_item(
                label="Console",
                parent="main_view_bar",
                callback=AppInterface._setup_console,
            )

    @staticmethod
    def _process_command(sender, app_data, user_data):
        try:
            command = app_data.strip()
            if command:
                try:
                    exec_result = eval(command, globals())
                    if exec_result is not None:
                        AppInterface._append_console_output(
                            f"> {command}\n{exec_result}"
                        )

                    else:
                        AppInterface._append_console_output(f"> {command}")

                except SyntaxError:
                    exec(command, globals())
                    AppInterface._append_console_output(f"> {command}")

        except Exception as e:
            AppInterface._append_console_output(f"Error: {e}")

        finally:
            dpg.set_value(sender, "")
            dpg.focus_item(sender)

    @staticmethod
    def _append_console_output(text):
        dpg.add_text(text, parent="console_output", wrap=0)
        dpg.set_y_scroll("console_window", dpg.get_y_scroll_max("console_window"))

    @staticmethod
    def _setup_console():
        if dpg.does_item_exist("debug_console"):
            dpg.delete_item("debug_console")

        with dpg.window(label="Debug Console", tag="debug_console", width=1, height=1):
            with dpg.child_window(
                label="Output", tag="console_window", autosize_x=True, autosize_y=True
            ):
                with dpg.group(tag="console_output"):
                    dpg.add_text("Debug Console Initialized")

            dpg.add_input_text(
                label="Command",
                on_enter=True,
                callback=AppInterface._process_command,
            )

        dpg_tools.rc_windows()

    @staticmethod
    def start_game():
        ModManager.save_mods()

        game_dir = AppConfig.get("barotrauma_dir", None)
        if game_dir is None:
            AppInterface.show_error(loc.get_string("error-game-dir-not-set"))
            return

        skip_intro = AppConfig.get("game_config_skip_intro", False)
        auto_install_lua = AppConfig.get("game_config_auto_lua", False)
        try:
            Game.run_game(auto_install_lua, skip_intro)  # type: ignore

        except Exception as err:
            AppInterface.show_error(err)

    @staticmethod
    def show_error(message):
        with dpg.window(label="Error"):
            dpg.add_text(message)

    @staticmethod
    def create_cac_window():
        if dpg.does_item_exist("cac_window"):
            dpg.focus_item("cac_window")
            return

        contributors_path = AppConfig.get_data_root_path() / "contributors.json"

        try:
            with open(contributors_path, "r", encoding="utf-8") as f:
                contributors_data = json.load(f)

        except Exception as e:
            logger.error(f"{contributors_path} just fuck up: {e}")
            return

        category_config = {
            "сaс-devs": {
                "name_field": "name",
                "info_field": "role",
                "info_process": lambda val: loc.get_string(val),
            },
            "сaс-translators": {
                "name_field": "name",
                "info_field": "code",
                "info_process": lambda val: loc.get_string(
                    "cac-translators-thx", lang_code=loc.get_string(f"lang_code-{val}")
                ),
            },
            "cac-special-thanks": {
                "name_field": "to",
                "info_field": "desc",
                "info_process": lambda val: loc.get_string(val),
            },
        }

        with dpg.window(
            label=loc.get_string("cac-window-name"),
            tag="cac_window",
            no_collapse=True,
            no_move=True,
            no_resize=True,
        ):
            for category_label, contributors_list in contributors_data.items():
                with dpg.collapsing_header(
                    label=loc.get_string(category_label), default_open=True
                ):
                    if isinstance(contributors_list, list):
                        for contributor in contributors_list:
                            with dpg.group(horizontal=True):
                                config = category_config.get(category_label)
                                if config:
                                    name = contributor.get(
                                        config["name_field"],
                                        loc.get_string("base-unknown"),
                                    )
                                    info_val = contributor.get(config["info_field"], "")
                                    info_text = (
                                        config["info_process"](info_val)
                                        if info_val
                                        else ""
                                    )
                                    dpg.add_text(name, color=(0, 150, 255))
                                    if info_text:
                                        dpg.add_text(
                                            f"- {info_text}",
                                            color=(200, 200, 200),
                                            wrap=0,
                                        )

            dpg_tools.rc_windows()

    @staticmethod
    def rebuild_interface():
        current_tab = dpg.get_value("main_tab_bar")

        dpg.delete_item("main_tab_bar", children_only=True)

        SettingsTab.create()
        ModsTab.create()

        dpg.set_value("main_tab_bar", current_tab)

        dpg.delete_item("main_view_bar")
        AppInterface._create_viewport_menu_bar()

        dpg_tools.rc_windows()
