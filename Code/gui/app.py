import logging
import signal
import sys
from typing import Any

import dearpygui.dearpygui as dpg

from Code.app_config import AppConfig
from Code.dpg_tools import FontManager, ThemesManager, ViewportResizeManager
from Code.game import Game
from Code.gui.windows import MainWindow, ModManagerWindow, SettingsWindow
from Code.handlers import ModManager
from Code.loc import Localization

logger = logging.getLogger(__name__)


class App:
    _LIST_OF_COMPONENTS: list[Any] = [
        AppConfig,
        Localization,
        ModManager,
        ThemesManager,
        ViewportResizeManager,
    ]
    _DEBUG: bool = False

    @classmethod
    def _signal_callback(cls, signum, frame) -> None:
        logger.info(f"Received signal {signum}. Starting graceful shutdown...")
        try:
            cls.stop()
        except Exception as e:
            logger.error(f"Error during graceful shutdown: {e}")

        finally:
            sys.exit(0)

    @classmethod
    def _setup_signals(cls) -> None:
        try:
            signal.signal(signal.SIGTERM, cls._signal_callback)
            signal.signal(signal.SIGINT, cls._signal_callback)
            logger.info("Signal handlers set up.")

        except Exception as e:
            logger.warning(f"Failed to set up signal handlers: {e}")

    @classmethod
    def _init_components(cls) -> None:
        logger.info("Initialization components start.")

        for component in cls._LIST_OF_COMPONENTS:
            logger.info(f"Initializing {component.__name__}...")
            init_method = getattr(component, "init", None)
            if callable(init_method):
                if "debug" in init_method.__code__.co_varnames:
                    init_method(cls._DEBUG)
                else:
                    init_method()

                logger.info(f"{component.__name__} initialized successfully.")

            else:
                logger.warning(
                    f"{component.__name__} does not have a callable 'init' method."
                )

        logger.info("Initialization components complete.")

    @staticmethod
    def _global_exception_handler(exctype, value, traceback_obj):
        logging.error("Exception occurred", exc_info=(exctype, value, traceback_obj))

    @classmethod
    def _init_viewport(cls):
        size = AppConfig.get("last_viewport_size", "600 400")
        if size is None:
            size = "600 400"
        width, height = size.split(" ")
        dpg.create_viewport(
            title=Localization.get_string("viewport_name"),
            width=int(width),
            min_width=600,
            height=int(height),
            min_height=400,
        )

    @classmethod
    def _load_img(cls) -> None:
        with dpg.texture_registry():
            for lang_code in Localization.get_all_lang_code():
                width, height, _, data = dpg.load_image(
                    str(
                        AppConfig.get_data_root_path()
                        / f"img/lang_btn_img/{lang_code}.png"
                    )
                )

                dpg.add_static_texture(
                    width=width,
                    height=height,
                    default_value=data,
                    tag=lang_code + "_btn_img",
                )

    @classmethod
    def run(cls, debug: bool = False) -> None:
        logger.info("Starting GUI program...")

        cls._DEBUG = debug

        cls._setup_signals()
        sys.excepthook = cls._global_exception_handler

        dpg.create_context()
        dpg.setup_dearpygui()
        FontManager.load_fonts()

        cls._init_components()
        cls._load_img()
        cls._init_viewport()

        MainWindow.create()
        MainWindow.add_button(
            "open_mod_manager_btn",
            ModManagerWindow.create,
        )
        MainWindow.add_button(
            "open_settings_btn",
            SettingsWindow.create,
        )
        MainWindow.add_button(
            "run_game_btn",
            Game.run,
            Game.is_valid_exec,
        )

        dpg.show_viewport()
        ViewportResizeManager.invoke()
        dpg.start_dearpygui()
        dpg.destroy_context()

    @classmethod
    def stop(cls) -> None:
        logger.info("Stopping application...")
        dpg.stop_dearpygui()
