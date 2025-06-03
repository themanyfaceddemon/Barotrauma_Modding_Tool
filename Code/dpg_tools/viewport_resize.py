import logging
from collections.abc import Callable
from typing import Dict, TypeGuard

import dearpygui.dearpygui as dpg

logger = logging.getLogger(__name__)


class ViewportResizeManager:
    _callback_dict: Dict[
        str,
        Callable[[tuple[int, int, int, int]], None] | Callable[[], None],
    ] = {}

    @classmethod
    def init(cls) -> None:
        dpg.set_viewport_resize_callback(cls._execute_callbacks)

    @classmethod
    def add_callback(
        cls,
        key: str,
        callback: Callable[[tuple[int, int, int, int]], None] | Callable[[], None],
    ) -> None:
        cls._callback_dict[key] = callback
        cls.invoke()

    @classmethod
    def remove_callback(cls, key: str) -> None:
        if key in cls._callback_dict:
            del cls._callback_dict[key]

    @classmethod
    def invoke(cls) -> None:
        cls._execute_callbacks()

    @classmethod
    def _execute_callbacks(cls) -> None:
        app_data = (
            dpg.get_viewport_width(),
            dpg.get_viewport_height(),
            dpg.get_viewport_client_width(),
            dpg.get_viewport_client_height(),
        )

        for key, callback in cls._callback_dict.items():
            try:
                if cls._is_callback_arg_0(callback):
                    callback()
                else:
                    callback(app_data)  # type: ignore

            except Exception as e:
                logger.error(f"Error in callback '{key}': {e}")

    @staticmethod
    def _is_callback_arg_0(callback: Callable) -> TypeGuard[Callable[[], None]]:
        return callback.__code__.co_argcount == 0
