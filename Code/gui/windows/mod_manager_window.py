from typing import Literal

import dearpygui.dearpygui as dpg

from Code.handlers import ModManager
from Code.loc import Localization
from Code.package import ModUnit

from .base_window import BaseWindow


class ModManagerWindow(BaseWindow):
    _window_name = "mod_manager_window"

    @classmethod
    def _update_for_lang(cls) -> None:
        pass

    @classmethod
    def _on_window_resize(cls, app_data: tuple[int, int, int, int]) -> None:
        if not dpg.does_item_exist(cls._window_name):
            return

        dpg.set_item_pos(cls._window_name, [round(app_data[2] * 0.2), 0])
        dpg.set_item_width(cls._window_name, round(app_data[2] * 0.8))
        dpg.set_item_height(cls._window_name, app_data[3])

        pre_calc_width = round(round(app_data[2] * 0.8) * 0.5) - 12
        for tag in ["active", "inactive"]:
            if dpg.does_item_exist(f"input_{tag}"):
                dpg.set_item_width(f"input_{tag}", pre_calc_width)

            if dpg.does_item_exist(f"mod_fild_{tag}"):
                dpg.set_item_width(f"mod_fild_{tag}", pre_calc_width)
                children = dpg.get_item_children(f"mod_fild_{tag}", 1)
                if not children:
                    continue

                for child in children:
                    if not dpg.does_item_exist(child):
                        continue

                    dpg.set_item_width(child, pre_calc_width - 16)

    @classmethod
    def _rebuild_mod_units(cls) -> None:
        for tag, mod_list in [
            ("active", ModManager.active_mods),
            ("inactive", ModManager.inactive_mods),
        ]:
            if dpg.does_item_exist(f"mod_fild_{tag}"):
                dpg.delete_item(f"mod_fild_{tag}", children_only=True)
                assert tag in ("active", "inactive")
                for mod in mod_list:
                    cls._buld_mod_unit(tag, mod)

    @classmethod
    def _buld_mod_unit(
        cls,
        parent: Literal["active", "inactive"],
        mod: ModUnit,
    ) -> None:
        dpg.add_button(
            label=mod.name,
            tag=mod.id,
            parent=f"mod_fild_{parent}",
            user_data=mod,
            payload_type="MOD",
        )

    @classmethod
    def _on_search(cls, sender, app_data, user_data) -> None:
        parent_tag = f"mod_fild_{user_data}"
        children = dpg.get_item_children(parent_tag, 1)
        if not children:
            return

        query = app_data.lower()
        for child in children:
            if not dpg.does_item_exist(child):
                continue

            name = dpg.get_item_label(child)
            if name is None:
                continue

            name = name.lower()
            dpg.configure_item(child, show=query in name)

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
            with dpg.group(horizontal=True):
                for tag in ["active", "inactive"]:
                    with dpg.group():
                        dpg.add_input_text(
                            tag=f"input_{tag}",
                            hint="Поикс...",
                            user_data=tag,
                            callback=cls._on_search,
                        )
                        dpg.add_child_window(tag=f"mod_fild_{tag}", no_scrollbar=True)

        cls._rebuild_mod_units()

        super().create()
