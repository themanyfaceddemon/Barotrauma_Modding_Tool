import dearpygui.dearpygui as dpg

WINDOWS_CFG = {  # magic value
    "main_window": (1.0, True),
    "find_game_window": (1.0, True),
    "cac_window": (1.0, True),
    "debug_console": (1.0, True),
    "active_mod_search_tag": (0.5, False),
    "active_mods_child": (0.5, False),
    "inactive_mod_search_tag": (0.5, False),
    "inactive_mods_child": (0.5, False),
}


def rc_windows():
    global WINDOWS_CFG

    viewport_width = dpg.get_viewport_width() - 40
    viewport_height = dpg.get_viewport_height() - 80

    vp_client_width = dpg.get_viewport_client_width()
    vp_client_height = dpg.get_viewport_client_height()

    for tag, info in WINDOWS_CFG.items():
        if not dpg.does_item_exist(tag):
            continue

        width = int(viewport_width * info[0])
        height = int(viewport_height * info[0])
        dpg.configure_item(tag, width=width, height=height)

        if info[1]:
            x_pos = (vp_client_width - width) // 2
            y_pos = (vp_client_height - height) // 2
            dpg.set_item_pos(tag, [x_pos, y_pos])
