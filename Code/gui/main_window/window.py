import dearpygui.dearpygui as dpg


def create_window() -> None:
    with dpg.window(tag="main_window", no_title_bar=True):
        dpg.add_button(label="bruh")

    dpg.set_primary_window("main_window", True)
