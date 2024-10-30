import logging
import sys
from pathlib import Path

import dearpygui.dearpygui as dpg

import Code.dpg_tools as dpg_tools
from Code.app_vars import AppGlobalsAndConfig
from Code.loc import Localization as loc
from Code.package import ModLoader, Package

from .fonts_setup import FontManager


class App:
    dragged_mod_id = None
    active_mod_search_text = ""
    inactive_mod_search_text = ""

    def __init__(self):
        self.initialize_app()
        self.create_windows()
        self.setup_menu_bar()
        sys.excepthook = self.global_exception_handler
        dpg.set_viewport_resize_callback(lambda: App.resize_main_window())
        App.resize_main_window()

    def initialize_app(self):
        dpg.create_context()
        FontManager.load_fonts()
        self._setup_viewport()
        dpg.setup_dearpygui()
        dpg.show_viewport()

    def _setup_viewport(self):
        dpg.create_viewport(
            title=loc.get_string("viewport-name"),
            width=600,
            min_width=600,
            height=400,
            min_height=400,
        )

    def create_windows(self):
        self.create_barotrauma_win()
        ModLoader.load()
        ModLoader.process_errors()

        with dpg.window(
            no_move=True,
            no_resize=True,
            no_title_bar=True,
            tag="main_window",
        ):
            with dpg.group(horizontal=True):
                dpg.add_button(
                    label="Sort active mods",
                    callback=self.sort_active_mods,
                    tag="sort_button",
                )
                with dpg.tooltip("sort_button"):
                    dpg.add_text("Sorts active mods alphabetically.")

                dpg.add_button(
                    label="Set Barotrauma Directory",
                    callback=self.show_barotrauma_win,
                    tag="set_dir_button",
                )
                with dpg.tooltip("set_dir_button"):
                    dpg.add_text("Set the path to your Barotrauma installation.")

            with dpg.group(horizontal=True):
                dpg.add_text("Directory Found:", color=(100, 150, 250))
                dpg.add_text(
                    str(AppGlobalsAndConfig.get("barotrauma_dir", "Not Set")),
                    tag="directory_status_text",
                    color=(200, 200, 250),
                )

            with dpg.group(horizontal=True):
                dpg.add_text("Enable CS Scripting:", color=(100, 150, 250))
                dpg.add_text(
                    "Yes" if AppGlobalsAndConfig.get("enable_cs_scripting") else "No",
                    tag="cs_scripting_status",
                    color=(0, 255, 0)
                    if AppGlobalsAndConfig.get("enable_cs_scripting")
                    else (255, 0, 0),
                )

            with dpg.group(horizontal=True):
                dpg.add_text("Lua Installed:", color=(100, 150, 250))
                dpg.add_text(
                    "Yes" if AppGlobalsAndConfig.get("has_lua") else "No",
                    tag="lua_status",
                    color=(0, 255, 0)
                    if AppGlobalsAndConfig.get("has_lua")
                    else (255, 0, 0),
                )

            with dpg.group(horizontal=True):
                dpg.add_text("Mods with errors: 0", tag="error_count_text")
                dpg.add_text("|")
                dpg.add_text("Mods with warnings: 0", tag="warning_count_text")

            dpg.add_separator()

            with dpg.group(horizontal=True):
                with dpg.group():
                    dpg.add_text("Active Mods")
                    dpg.add_input_text(
                        tag="active_mod_search_tag",
                        hint="Search...",
                        callback=self.on_search_changed,
                        user_data="active",
                    )
                    with dpg.child_window(
                        tag="active_mods_child",
                        drop_callback=self.on_mod_dropped,
                        user_data="active",
                        payload_type="MOD_DRAG",
                    ):
                        pass

                with dpg.group():
                    dpg.add_text("Inactive Mods")
                    dpg.add_input_text(
                        tag="inactive_mod_search_tag",
                        hint="Search...",
                        callback=self.on_search_changed,
                        user_data="inactive",
                    )
                    with dpg.child_window(
                        tag="inactive_mods_child",
                        drop_callback=self.on_mod_dropped,
                        user_data="inactive",
                        payload_type="MOD_DRAG",
                    ):
                        pass

        self.render_mods()

    def on_search_changed(self, sender, app_data, user_data):
        if user_data == "active":
            self.active_mod_search_text = app_data.lower()
        elif user_data == "inactive":
            self.inactive_mod_search_text = app_data.lower()
        self.render_mods()

    def render_mods(self):
        ModLoader.process_errors()
        dpg.delete_item("active_mods_child", children_only=True)
        for mod in ModLoader.active_mods:
            if self.active_mod_search_text in mod.identifier.name.lower():
                self.add_movable_mod(mod, "active", "active_mods_child")

        dpg.delete_item("inactive_mods_child", children_only=True)
        for mod in ModLoader.inactive_mods:
            if self.inactive_mod_search_text in mod.identifier.name.lower():
                self.add_movable_mod(mod, "inactive", "inactive_mods_child")

        error_count, warning_count = self.count_mods_with_issues()
        dpg.set_value("error_count_text", f"Mods with errors: {error_count}")
        dpg.set_value("warning_count_text", f"Mods with warnings: {warning_count}")

    def add_movable_mod(self, mod: Package, status: str, parent):
        mod_group_tag = f"{mod.identifier.id}_{status}_group"
        mod_name_tag = f"{mod.identifier.id}_{status}_text"

        with dpg.group(tag=mod_group_tag, parent=parent):
            dpg.add_text(
                mod.identifier.name,
                tag=mod_name_tag,
                drop_callback=self.on_mod_dropped,
                payload_type="MOD_DRAG",
                user_data={"mod_id": mod.identifier.id, "status": status},
            )

            with dpg.popup(parent=mod_name_tag):
                with dpg.group(horizontal=True):
                    dpg.add_text("Author:", color=[0, 102, 204])
                    dpg.add_text(mod.metadata.meta.get("author", "Unknown"))

                with dpg.group(horizontal=True):
                    dpg.add_text("License:", color=[169, 169, 169])
                    dpg.add_text(
                        mod.metadata.meta.get("license", "Not specified"),
                        color=[169, 169, 169],
                    )

                with dpg.group(horizontal=True):
                    dpg.add_text("Game version:", color=[34, 139, 34])
                    dpg.add_text(mod.metadata.game_version)

                with dpg.group(horizontal=True):
                    dpg.add_text("Mod version:", color=[34, 139, 34])
                    dpg.add_text(mod.metadata.mod_version)

                if mod.metadata.errors:
                    dpg.add_text("Errors:", color=[255, 0, 0])
                    for error in mod.metadata.errors[:3]:
                        dpg.add_text(error, wrap=0, bullet=True)

                    if len(mod.metadata.errors) > 3:
                        dpg.add_text(
                            "See full details...", color=[255, 255, 0], bullet=True
                        )

                if mod.metadata.warnings:
                    dpg.add_text("Warnings:", color=[255, 255, 0])
                    for warning in mod.metadata.warnings[:3]:
                        dpg.add_text(warning, wrap=0, bullet=True)

                    if len(mod.metadata.warnings) > 3:
                        dpg.add_text(
                            "See full details...", color=[255, 255, 0], bullet=True
                        )

                dpg.add_button(
                    label="Show full details",
                    callback=lambda: self.show_details_window(mod),
                )

            with dpg.drag_payload(
                parent=mod_name_tag,
                payload_type="MOD_DRAG",
                drag_data={"mod_id": mod.identifier.id, "status": status},
            ):
                dpg.add_text(mod.identifier.name)

            if mod.metadata.errors:
                dpg.configure_item(mod_name_tag, color=[255, 0, 0])
            elif mod.metadata.warnings:
                dpg.configure_item(mod_name_tag, color=[255, 255, 0])
            else:
                dpg.configure_item(mod_name_tag, color=[255, 255, 255])

            dpg.add_separator()

    def show_details_window(self, mod: Package):
        title = f"MOD: {mod.identifier.name} - Full Details"
        window_tag = f"{mod.identifier.id}_full_details_window"

        if dpg.does_item_exist(window_tag):
            dpg.delete_item(window_tag)

        with dpg.window(
            label=title,
            width=400,
            height=300,
            tag=window_tag,
            on_close=lambda: dpg.delete_item(window_tag),
        ):
            with dpg.group(horizontal=True):
                with dpg.group():
                    with dpg.group(horizontal=True):
                        dpg.add_text("Mod name:", color=[0, 102, 204])
                        dpg.add_text(mod.identifier.name)

                    with dpg.group(horizontal=True):
                        dpg.add_text("Author:", color=[0, 102, 204])
                        dpg.add_text(mod.metadata.meta.get("author", "Unknown"))

                    with dpg.group(horizontal=True):
                        dpg.add_text("License:", color=[169, 169, 169])
                        dpg.add_text(
                            mod.metadata.meta.get("license", "Not specified"),
                            color=[169, 169, 169],
                        )

                    with dpg.group(horizontal=True):
                        dpg.add_text("Is local mod:")
                        dpg.add_text("yes" if mod.metadata.local else "no")

                with dpg.group():
                    with dpg.group(horizontal=True):
                        dpg.add_text("ModLoader ID:", color=[34, 139, 34])
                        dpg.add_text(mod.identifier.id)

                    with dpg.group(horizontal=True):
                        dpg.add_text("Game version:", color=[34, 139, 34])
                        dpg.add_text(mod.metadata.game_version)

                    with dpg.group(horizontal=True):
                        dpg.add_text("Mod version:", color=[34, 139, 34])
                        dpg.add_text(mod.metadata.mod_version)
            dpg.add_separator()

            if mod.metadata.errors:
                dpg.add_text("Errors:", color=[255, 0, 0])
                for error in mod.metadata.errors:
                    dpg.add_text(error, wrap=0, bullet=True)
                dpg.add_separator()

            if mod.metadata.warnings:
                dpg.add_text("Warnings:", color=[255, 255, 0])
                for warning in mod.metadata.warnings:
                    dpg.add_text(warning, wrap=0, bullet=True)
                dpg.add_separator()

    def on_mod_dropped(self, sender, app_data, user_data):
        drag_data = app_data
        dragged_mod_id = drag_data["mod_id"]
        dragged_mod_status = drag_data["status"]

        sender_type = dpg.get_item_type(sender)

        if sender_type == "mvAppItemType::mvText":
            target_mod_data = dpg.get_item_user_data(sender)
            target_mod_id = target_mod_data["mod_id"]  # type: ignore
            target_mod_status = target_mod_data["status"]  # type: ignore

            if dragged_mod_status != target_mod_status:
                if target_mod_status == "active":
                    ModLoader.activate_mod(dragged_mod_id)
                else:
                    ModLoader.deactivate_mod(dragged_mod_id)
                dragged_mod_status = target_mod_status

            if dragged_mod_status == "active":
                ModLoader.swap_active_mods(dragged_mod_id, target_mod_id)
            else:
                ModLoader.swap_inactive_mods(dragged_mod_id, target_mod_id)

        elif sender_type == "mvAppItemType::mvChildWindow":
            target_status = dpg.get_item_user_data(sender)
            if dragged_mod_status != target_status:
                if target_status == "active":
                    ModLoader.activate_mod(dragged_mod_id)
                else:
                    ModLoader.deactivate_mod(dragged_mod_id)
                dragged_mod_status = target_status

            if dragged_mod_status == "active":
                ModLoader.move_active_mod_to_end(dragged_mod_id)
            else:
                ModLoader.move_inactive_mod_to_end(dragged_mod_id)

        else:
            logging.warning(f"Unknown drop target: {sender}")

        self.render_mods()

    @classmethod
    def run(cls) -> None:
        dpg.start_dearpygui()
        dpg.destroy_context()

    @classmethod
    def stop(cls) -> None:
        dpg.stop_dearpygui()

    @staticmethod
    def global_exception_handler(exctype, value, traceback_obj):
        logging.error("Exception occurred", exc_info=(exctype, value, traceback_obj))

    def setup_menu_bar(self):
        pass

    def sort_active_mods(self):
        ModLoader.sort()
        self.render_mods()

    def create_barotrauma_win(self):
        with dpg.window(
            modal=True,
            no_resize=True,
            no_move=True,
            no_collapse=True,
            no_title_bar=True,
            tag="barotrauma_set_dir_win",
            show=False,
        ):
            dpg.add_text("Barotrauma Path Settings", color=(200, 200, 250))

            dpg.add_input_text(
                hint="Enter Barotrauma Path",
                callback=self.validate_barotrauma_path,
                tag="barotrauma_input_path",
                width=300,
            )

            with dpg.group(horizontal=True):
                dpg.add_text("Current Path:", color=(100, 150, 250))
                dpg.add_text(
                    AppGlobalsAndConfig.get("barotrauma_dir", "Not Set"),  # type: ignore
                    tag="barotrauma_cur_path_text",
                    color=(200, 200, 250),
                )

            with dpg.group(horizontal=True):
                dpg.add_text("Valid Path:", color=(100, 150, 250))
                dpg.add_text(
                    "Not Defined", tag="barotrauma_cur_path_valid", color=(255, 0, 0)
                )

            dpg.add_separator()

            dpg.add_button(
                label="Close",
                callback=lambda: dpg.hide_item("barotrauma_set_dir_win"),
                width=150,
            )

    def show_barotrauma_win(self):
        dpg.show_item("barotrauma_set_dir_win")

    def validate_barotrauma_path(self, sender, app_data, user_data):
        try:
            path = Path(app_data)

            if path.exists() and (path / "config_player.xml").exists():
                dpg.set_value("barotrauma_cur_path_valid", "True")

                dpg.configure_item("barotrauma_cur_path_valid", color=[0, 255, 0])

                AppGlobalsAndConfig.set("barotrauma_dir", str(path))

                ModLoader.load()
                self.render_mods()
                return

        except Exception as e:
            print(f"Path validation error: {e}")

        finally:
            path = AppGlobalsAndConfig.get("barotrauma_dir", "Not Set")
            enable_cs_scripting = AppGlobalsAndConfig.get("enable_cs_scripting")
            has_lua = AppGlobalsAndConfig.get("has_lua")

            dpg.set_value("cs_scripting_status", "Yes" if enable_cs_scripting else "No")
            dpg.configure_item(
                "cs_scripting_status",
                color=[0, 255, 0] if enable_cs_scripting else [255, 0, 0],
            )

            dpg.set_value("lua_status", "Yes" if has_lua else "No")
            dpg.configure_item(
                "lua_status", color=[0, 255, 0] if has_lua else [255, 0, 0]
            )

            dpg.set_value(
                "barotrauma_cur_path_text",
                path,
            )
            dpg.set_value(
                "directory_status_text",
                path,
            )

        dpg.set_value("barotrauma_cur_path_valid", "Fasle")
        dpg.configure_item("barotrauma_cur_path_valid", color=[255, 0, 0])

    @staticmethod
    def resize_main_window():
        viewport_width = dpg.get_viewport_width() - 40
        viewport_height = dpg.get_viewport_height() - 80
        dpg.configure_item("main_window", width=viewport_width, height=viewport_height)
        dpg.configure_item(
            "barotrauma_set_dir_win", width=viewport_width, height=viewport_height
        )
        dpg.configure_item("active_mods_child", width=(viewport_width / 2))
        dpg.configure_item("active_mod_search_tag", width=(viewport_width / 2))
        dpg.configure_item("inactive_mods_child", width=(viewport_width / 2))
        dpg.configure_item("inactive_mod_search_tag", width=(viewport_width / 2))
        dpg_tools.center_window("main_window")

    def count_mods_with_issues(self):
        error_count = 0
        warning_count = 0

        for mod in ModLoader.active_mods:
            if mod.metadata.errors:
                error_count += 1
            if mod.metadata.warnings:
                warning_count += 1

        return error_count, warning_count
