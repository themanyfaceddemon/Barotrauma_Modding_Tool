import dearpygui.dearpygui as dpg


class ThemesManager:
    theme_att_id = 0

    @classmethod
    def init(cls) -> None:
        with dpg.theme() as main:
            with dpg.theme_component(dpg.mvButton, enabled_state=False):
                dpg.add_theme_color(dpg.mvThemeCol_Text, [170, 170, 170])
                dpg.add_theme_color(dpg.mvThemeCol_Button, [51, 51, 55])
                dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, [51, 51, 55])
                dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, [51, 51, 55])

        with dpg.theme(tag="btn_error"):
            with dpg.theme_component(dpg.mvButton):
                dpg.add_theme_color(dpg.mvThemeCol_Text, [255, 200, 200])
                dpg.add_theme_color(dpg.mvThemeCol_Button, [80, 30, 30])
                dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, [120, 40, 40])
                dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, [160, 50, 50])

        with dpg.theme(tag="btn_warning"):
            with dpg.theme_component(dpg.mvButton):
                dpg.add_theme_color(dpg.mvThemeCol_Text, [255, 240, 180])
                dpg.add_theme_color(dpg.mvThemeCol_Button, [80, 70, 20])
                dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, [120, 100, 30])
                dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, [160, 130, 40])

        with dpg.theme(tag="btn_selected"):
            with dpg.theme_component(dpg.mvButton):
                dpg.add_theme_color(dpg.mvThemeCol_Text, [200, 220, 255])
                dpg.add_theme_color(dpg.mvThemeCol_Button, [40, 50, 80])
                dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, [60, 70, 110])
                dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, [80, 90, 130])

        dpg.bind_theme(main)
