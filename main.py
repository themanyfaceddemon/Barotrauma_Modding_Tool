import argparse
import logging
import os
import platform

from colorama import Fore, Style, init

from Code.app_config import AppConfig
from Code.game import Finder, Game, Updater
from Code.gui.app import App
from Code.handlers import ModManager


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
            res = Finder.search()
            if res:
                AppConfig.set("barotrauma_dir", str(res[0]))
                AppConfig.set_steam_mods_path()
                ModManager.load_mods()
                ModManager.load_cslua_config()

            else:
                logging.error("Failed to set game path")
                return

    if auto_lua:
        Updater.download()

    if process_btm:
        ModManager.save_mods()

    if start_game:
        Game.run(skip_intro=skip_intro)


def main(debug: bool):
    try:
        App.run(debug)

    except Exception as e:
        logging.error(
            f"Critical error during application execution: {e}", exc_info=True
        )

    finally:
        logging.info("Application terminated.")


if __name__ == "__main__":
    try:
        init(autoreset=True)

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

        if platform.system() == "Windows":
            os.environ["PYTHONIOENCODING"] = "utf-8"
            os.environ["PYTHONUTF8"] = "1"

        elif platform.system() == "Darwin":
            logging.warning(
                f"{AppConfig.app_name} may have bugs on MacOS. Please report any issues to {AppConfig.app_github}/issues"
            )

        if args.ngui:
            args_no_gui(args.sg, args.apath, args.alua, args.si, args.pbmt)

        else:
            main(args.debug)

    except Exception:
        logging.critical("Unhandled exception occurred.", exc_info=True)
        input()
