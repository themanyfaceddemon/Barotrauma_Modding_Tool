import dearpygui.dearpygui as dpg

from Code.dpg_tools import ViewportResizeManager


class BaseWindow:
    _window_name: str = ""

    @classmethod
    def _on_window_close(cls) -> None:
        ViewportResizeManager.remove_callback(cls._window_name)

    @classmethod
    def _on_window_resize(cls, app_data: tuple[int, int, int, int]) -> None:
        pass

    @classmethod
    def create(cls) -> None:
        with dpg.window(
            tag=cls._window_name,
            on_close=cls._on_window_close,
            no_move=True,
            no_title_bar=True,
        ):
            pass

        ViewportResizeManager.add_callback(cls._window_name, cls._on_window_resize)

    @classmethod
    def rebuild(cls) -> None:
        if dpg.does_item_exist(cls._window_name):
            dpg.delete_item(cls._window_name)

        cls.create()

    @classmethod
    def delete(cls) -> None:
        cls._on_window_close()
        if dpg.does_item_exist(cls._window_name):
            dpg.delete_item(cls._window_name)
