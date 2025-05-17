import argparse
import logging
import os
import platform
import re
import signal
import sys
from typing import Any, Type

from colorama import Fore, Style, init

from Code.app import App
from Code.app.app_initializer import AppInitializer
from Code.app_vars import AppConfig
from Code.game import Game
from Code.handlers import ModManager
from Code.loc import Localization as loc


def signal_handler(signum, frame):
    logging.info(f"Received signal {signum}. Starting graceful shutdown...")
    try:
        App.stop()
    except Exception as e:
        logging.error(f"Error during graceful shutdown: {e}")
    finally:
        sys.exit(0)


class ColoredFormatter(logging.Formatter):
    COLORS = {
        "DEBUG": Fore.CYAN,
        "INFO": Fore.GREEN,
        "WARNING": Fore.YELLOW,
        "ERROR": Fore.RED,
        "CRITICAL": Fore.RED + Style.BRIGHT,
    }

    def format(self, record):
        color = self.COLORS.get(record.levelname, "")
        record.levelname = f"{color}{record.levelname:<7}{Style.RESET_ALL}"
        return super().format(record)


def configure_logging(debug: bool):
    log_level = logging.DEBUG if debug else logging.INFO
    log_format = "[%(asctime)s][%(levelname)s] %(name)s: %(message)s"

    console_handler = logging.StreamHandler()
    console_formatter = ColoredFormatter(log_format)
    console_handler.setFormatter(console_formatter)

    logging.basicConfig(
        level=log_level,
        handlers=[console_handler],
        encoding="utf-8",
    )


def initialize_components(debug: bool, *components: Type[Any]) -> None:
    for component in components:
        logging.debug(f"Initializing {component.__name__}...")
        init_method = getattr(component, "init", None)
        if callable(init_method):
            init_method(
                debug
            ) if "debug" in init_method.__code__.co_varnames else init_method()
            logging.debug(f"{component.__name__} initialized successfully.")

        else:
            raise AttributeError(
                f"{component.__name__} does not have a callable 'init' method."
            )


def check_path_for_non_ascii():
    script_path = os.path.abspath(__file__)
    if re.search(r"[^\x00-\x7F]", script_path):
        raise RuntimeError(
            f"The program installation path contains non-ASCII characters.\n\nCurrent path: {script_path}"
        )


def args_no_gui(
    start_game: bool,
    auto_game_path: bool,
    auto_lua: bool,
    skip_intro: bool,
    process_btm: bool,
):
    if auto_game_path:
        game_path = AppConfig.get_game_path()
        if game_path is None:
            res = Game.search_all_games_on_all_drives()
            if res:
                AppConfig.set("barotrauma_dir", str(res[0]))
                AppConfig.set_steam_mods_path()
                ModManager.load_mods()
                ModManager.load_cslua_config()

            else:
                logging.error("Failed to set game path")
                return

    if auto_lua:
        Game.download_update_lua()

    if process_btm:
        ModManager.save_mods()

    if start_game:
        Game.run_game(skip_intro=skip_intro)


def main(debug: bool):
    logging.debug("Starting program...")
    try:
        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)
    except Exception as e:
        logging.warning(f"Failed to set up signal handlers: {e}")

    try:
        initialize_components(debug, AppConfig, loc, ModManager, AppInitializer)
        logging.debug("Initialization complete.")
        App.run()
    except Exception as e:
        logging.error(
            f"Critical error during application execution: {e}", exc_info=True
        )
    finally:
        logging.debug("Application terminated.")


if __name__ == "__main__":
    try:
        init(autoreset=True)
        check_path_for_non_ascii()

        parser = argparse.ArgumentParser()
        parser.add_argument("--debug", action="store_true", help="Enable debug mode")
        parser.add_argument("--ngui", action="store_true", help="Disable GUI startup")
        parser.add_argument(
            "--sg", action="store_true", help="Start the game automatically"
        )
        parser.add_argument(
            "--apath", action="store_true", help="Set the game path automatically"
        )
        parser.add_argument(
            "--alua", action="store_true", help="Update/install Lua automatically"
        )
        parser.add_argument(
            "--si", action="store_true", help="Skip intro (requires --sg)"
        )
        parser.add_argument("--pbmt", action="store_true", help="Process modifications")
        args = parser.parse_args()

        configure_logging(args.debug)

        platform_name = platform.system()
        if platform_name == "Windows":
            os.environ["PYTHONIOENCODING"] = "utf-8"
            os.environ["PYTHONUTF8"] = "1"

        elif platform_name == "Darwin":
            logging.warning(
                "ModLoader may have bugs on MacOS. Please report any issues to https://github.com/themanyfaceddemon/Mod_Loader/issues"
            )
        del platform_name

        if args.ngui:
            args_no_gui(args.sg, args.apath, args.alua, args.si, args.pbmt)

        else:
            main(args.debug)

    except Exception:
        logging.critical("Unhandled exception occurred.", exc_info=True)
        input()
