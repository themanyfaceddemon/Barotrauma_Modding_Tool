import logging
import threading
from pathlib import Path

import dearpygui.dearpygui as dpg

import Code.dpg_tools as dpg_tools
from Code.app_vars import AppConfig
from Code.game import Game
from Code.handlers import ModManager
from Code.loc import Localization as loc

from .experimental_tab import ExperimentalTab
from .mods_tab import ModsTab

logger = logging.getLogger(__name__)


class SettingsTab:
    @classmethod
    def create(cls) -> None:
        with dpg.tab(
            label=loc.get_string("settings-tab-label"),
            parent="main_tab_bar",
            tag="settings_tab",
        ):
            dpg.add_text(
                loc.get_string("label-barotrauma-path-settings"),
                color=(200, 200, 250),
                wrap=0,
            )

            dpg.add_input_text(
                hint=loc.get_string("hint-enter-barotrauma-path"),
                callback=cls._validate_barotrauma_path,
                tag="barotrauma_input_path",
                width=300,
            )

            with dpg.group(horizontal=True):
                dpg.add_text(
                    loc.get_string("label-current-path"), color=(100, 150, 250)
                )
                dpg.add_text(
                    AppConfig.get("barotrauma_dir", loc.get_string("base-not-set")),  # type: ignore
                    tag="barotrauma_cur_path_text",
                    color=(200, 200, 250),
                )

            with dpg.group(horizontal=True):
                dpg.add_text(loc.get_string("label-valid-path"), color=(100, 150, 250))
                dpg.add_text(
                    loc.get_string("label-not-defined"),
                    tag="barotrauma_cur_path_valid",
                    color=(255, 0, 0),
                )

            dpg.add_separator()
            dpg.add_button(
                label=loc.get_string("btn-search-game-fold"),
                callback=cls._find_game_window,
            )

            dpg.add_separator()
            dpg.add_separator()

            dpg.add_text(
                loc.get_string("settings-app-checkboxs"),
                color=(200, 200, 250),
                wrap=0,
            )
            with dpg.group(horizontal=True):
                with dpg.group():
                    dpg.add_checkbox(
                        label=loc.get_string("setting-toggle-install-lua"),
                        tag="settings_install_lua",
                        default_value=AppConfig.get("game_config_auto_lua", False),  # type: ignore
                        callback=lambda s, a: AppConfig.set("game_config_auto_lua", a),
                    )

                    dpg.add_checkbox(
                        label=loc.get_string("setting-toggle-skip-intro"),
                        tag="settings_skip_intro",
                        default_value=AppConfig.get("game_config_skip_intro", False),  # type: ignore
                        callback=lambda s, a: AppConfig.set(
                            "game_config_skip_intro", a
                        ),
                    )

                with dpg.group():
                    dpg.add_checkbox(
                        label=loc.get_string("menu-toggle-experimental"),
                        default_value=AppConfig.get("experimental", False),  # type: ignore
                        callback=cls._on_exp_ch,
                    )
            dpg.add_separator()
            dpg.add_separator()

            dpg.add_text(
                loc.get_string("settings-app-visual"),
                color=(200, 200, 250),
                wrap=0,
            )
            loc_dict = {
                "eng": loc.get_string("lang_code-eng"),
                "rus": loc.get_string("lang_code-rus"),
                "ger": loc.get_string("lang_code-ger"),
            }

            dpg.add_combo(
                items=list(loc_dict.values()),
                label=loc.get_string("menu-language"),
                default_value=loc_dict[AppConfig.get("lang", "eng")],  # type: ignore
                callback=lambda s, a: cls._on_language_changed(a, loc_dict),
                tag="language_selector",
            )

    @staticmethod
    def _on_exp_ch(sender, app_data, user_data):
        AppConfig.set("experimental", app_data)
        if app_data:
            ExperimentalTab.create()
        else:
            ExperimentalTab.destroy()

    @staticmethod
    def _on_language_changed(
        selected_language: str, language_map: dict[str, str]
    ) -> None:
        new_lang = next(
            code for code, name in language_map.items() if name == selected_language
        )

        loc.change_language(new_lang)

        from Code.app.app_interface import AppInterface

        AppInterface.rebuild_interface()

    @staticmethod
    def _validate_barotrauma_path(sender, app_data, user_data):
        path = None
        try:
            path = Path(app_data)

            if path.exists() and (path / "config_player.xml").exists():
                if dpg.does_item_exist("barotrauma_cur_path_valid"):
                    dpg.set_value("barotrauma_cur_path_valid", "True")
                    dpg.configure_item("barotrauma_cur_path_valid", color=[0, 255, 0])

                AppConfig.set("barotrauma_dir", str(path))
                AppConfig.set_steam_mods_path()
                logger.info(f"Valid path set: {path}")

                ModManager.load_mods()
                ModManager.load_cslua_config()
                ModsTab.render_mods()
                return
            else:
                logger.warning(f"Invalid path or missing 'config_player.xml': {path}")

        except Exception as e:
            logger.error(f"Path validation error: {e}", exc_info=True)

        finally:
            if path is None:
                path = AppConfig.get("barotrauma_dir", loc.get_string("base-not-set"))

            has_cs = AppConfig.get("has_cs")
            has_lua = AppConfig.get("has_lua")

            dpg.set_value(
                "cs_scripting_status",
                loc.get_string("base-yes") if has_cs else loc.get_string("base-no"),
            )
            dpg.configure_item(
                "cs_scripting_status",
                color=[0, 255, 0] if has_cs else [255, 0, 0],
            )

            dpg.set_value(
                "lua_status",
                loc.get_string("base-yes") if has_lua else loc.get_string("base-no"),
            )
            dpg.configure_item(
                "lua_status", color=[0, 255, 0] if has_lua else [255, 0, 0]
            )

            dpg.set_value("barotrauma_cur_path_text", path)
            dpg.set_value("directory_status_text", path)

            logging.debug(f"Path set for display: {path}")

        if dpg.does_item_exist("barotrauma_cur_path_valid"):
            dpg.set_value("barotrauma_cur_path_valid", "False")
            dpg.configure_item("barotrauma_cur_path_valid", color=[255, 0, 0])
        logger.error("Path validation failed and marked as invalid.")

    @classmethod
    def _find_game_window(cls):
        with dpg.window(
            modal=True,
            tag="find_game_window",
            no_move=True,
            no_resize=True,
            no_collapse=True,
            no_title_bar=True,
        ):
            dpg.add_text(loc.get_string("warning-exp-game-1"), wrap=0)
            dpg.add_separator()
            with dpg.group(horizontal=True):
                dpg.add_button(
                    label=loc.get_string("base-start"),
                    callback=lambda s, a: cls._start_search(),
                )

                dpg.add_button(
                    label=loc.get_string("base-close"),
                    callback=lambda s, a: dpg.delete_item("find_game_window"),
                )

        dpg_tools.rc_windows()

    @classmethod
    def _start_search(cls):
        threading.Thread(target=cls._run_search, daemon=True).start()

    @classmethod
    def _run_search(cls):
        dpg.delete_item("find_game_window", children_only=True)
        dpg.add_text(
            loc.get_string("search-exp-game"),
            parent="find_game_window",
            wrap=400,
            color=(150, 150, 150),
        )
        dpg.add_loading_indicator(style=2, parent="find_game_window")

        results = Game.search_all_games_on_all_drives()
        dpg.delete_item("find_game_window", children_only=True)

        if results:
            dpg.add_text(
                loc.get_string("search-exp-game-done"),
                parent="find_game_window",
                wrap=0,
            )
            dpg.add_separator(parent="find_game_window")
            for path in results:
                dpg.add_button(
                    label=str(path),
                    parent="find_game_window",
                    user_data=path,
                    callback=cls._select_and_close,
                )
        else:
            dpg.add_text(
                loc.get_string("search-exp-game-none"),
                parent="find_game_window",
                wrap=0,
            )
            dpg.add_separator(parent="find_game_window")
            dpg.add_button(
                label=loc.get_string("base-close"),
                callback=lambda s, a: dpg.delete_item("find_game_window"),
                parent="find_game_window",
            )

    @classmethod
    def _select_and_close(cls, sender, app_data, user_data):
        dpg.set_value("barotrauma_input_path", str(user_data))
        threading.Thread(
            target=cls._validate_barotrauma_path,
            args=(None, str(user_data), None),
            daemon=True,
        ).start()
        dpg.delete_item("find_game_window")
