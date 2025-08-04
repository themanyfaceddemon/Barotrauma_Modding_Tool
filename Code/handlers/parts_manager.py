import logging
import re
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Set

from Code.app_config import AppConfig
from Code.package import ModUnit
from Code.xml_object import XMLBuilder, XMLComment, XMLElement

from .condition_manager import process_condition

logger = logging.getLogger(__name__)


# TODO: Это бы рефакторнуть разок
class PartsManager:
    # BTM: conditions="", setState="on/off": start
    # BTM: end
    @staticmethod
    def do_chenges(mod: ModUnit, active_mod_ids: Set[str]):
        PartsManager._corrupt_xml_by_config(mod.path, active_mod_ids)

        for xml_path in mod.path.rglob("*.xml"):
            if xml_path.name.lower() in AppConfig.xml_system_dirs:
                continue

            with ThreadPoolExecutor() as executor:
                executor.submit(
                    PartsManager._corrupt_xml_by_commits, xml_path, active_mod_ids
                )

    @staticmethod
    def rollback_chenges(mod: ModUnit):
        PartsManager._fix_xml_by_config(mod.path)

        for xml_path in mod.path.rglob("*.xml"):
            if xml_path.name.lower() in AppConfig.xml_system_dirs:
                continue

            with ThreadPoolExecutor() as executor:
                executor.submit(PartsManager._fix_xml_by_commits, xml_path)

    @staticmethod
    def rollback_changes_no_thread(mod: ModUnit):
        PartsManager._fix_xml_by_config(mod.path)

        for xml_path in mod.path.rglob("*.xml"):
            if xml_path.name.lower() in AppConfig.xml_system_dirs:
                continue

            PartsManager._fix_xml_by_commits(xml_path)

    @staticmethod
    def _corrupt_xml_by_commits(file_path: Path, active_mod_ids: Set[str]):
        PartsManager._by_xml(file_path, active_mod_ids)

    @staticmethod
    def _corrupt_xml_by_config(mod_path: Path, active_mod_ids: Set[str]):
        PartsManager._by_config(mod_path, active_mod_ids)

    @staticmethod
    def _fix_xml_by_commits(file_path: Path):
        PartsManager._by_xml(file_path, is_fix=True)

    @staticmethod
    def _fix_xml_by_config(mod_path: Path):
        PartsManager._by_config(mod_path, is_fix=True)

    @staticmethod
    def _by_xml(
        file_path: Path, active_mod_ids: Set[str] = set(), is_fix: bool = False
    ):
        xml_obj = XMLBuilder.load(file_path)
        if xml_obj is None:
            return

        for com_start, objs, com_end in xml_obj.find_between_comments(
            "BTM:.*start", "BTM:.*end"
        ):
            if not is_fix:
                match = re.search(r'conditions="(.*?)"', com_start.content)
                if match:
                    condition_value = match.group(1)
                else:
                    logger.error(
                        f"Error in searching for switching conditions value\n|Path: {file_path}"
                    )
                    continue

            match = re.search(r'setState="(.*?)"', com_start.content)
            if match:
                set_to = (
                    not is_fix
                    if match.group(1).lower() in ["on", "1", "true"]
                    else is_fix
                )
            else:
                logger.error(
                    f"Error in searching for set state value\n|Path: {file_path}"
                )
                continue

            if not is_fix:
                if not process_condition(  # ERROR
                    condition_value,  # type: ignore
                    active_mod_ids=active_mod_ids,
                ):
                    continue

            for obj in objs:
                if obj.index is None:
                    continue

                if set_to:
                    if isinstance(obj, XMLElement):
                        continue

                else:
                    if isinstance(obj, XMLComment):
                        continue

                try:
                    if isinstance(obj, XMLComment):
                        xml_obj.replace(obj.index, obj.to_element())
                    else:
                        xml_obj.replace(obj.index, obj.to_comment())

                except Exception:
                    continue

        XMLBuilder.save(xml_obj, file_path)

    @staticmethod
    def _by_config(
        mod_path: Path, active_mod_ids: Set[str] = set(), is_fix: bool = False
    ):
        xml_obj = XMLBuilder.load((mod_path / "modparts.xml"))
        xml_file_list = XMLBuilder.load((mod_path / "filelist.xml"))

        if not all((xml_obj, xml_file_list)):
            return

        for action in xml_obj.iter_non_comment_childrens():  # type: ignore
            if not is_fix:
                if not process_condition(
                    action.get_attribute_ignore_case("conditions"),
                    active_mod_ids=active_mod_ids,
                ):
                    continue

            path_to_file = action.get_attribute_ignore_case("file")
            cond_type = action.get_attribute_ignore_case("type")
            set_to = action.get_attribute_ignore_case("setState")

            if not all((path_to_file, cond_type, set_to)):
                continue

            set_to = not is_fix if set_to in ["on", "1", "true"] else is_fix

            for item in xml_file_list.childrens:  # type: ignore # TODO Think about optimization
                if isinstance(item, XMLComment):
                    try:
                        tmp_item = item.to_element()

                    except Exception:
                        continue

                else:
                    tmp_item = item

                tag_item = tmp_item.tag
                item_file = tmp_item.get_attribute_ignore_case("file")
                if not all((tag_item, item_file)):
                    continue

                if set_to:
                    if isinstance(item, XMLElement):
                        continue

                else:
                    if isinstance(item, XMLComment):
                        continue

                if tag_item == cond_type and item_file == path_to_file:
                    try:
                        if isinstance(item, XMLComment):
                            xml_file_list.replace(item.index, item.to_element())  # type: ignore
                            path_to_file.replace(  # type: ignore
                                "%ModDir%",
                                AppConfig.get_steam_mod_path(),  # type: ignore
                            )
                            path_to_file.replace(  # type: ignore
                                "LocalMods",
                                AppConfig.get_local_mod_path(),  # type: ignore
                            )
                            path_xml = Path(path_to_file)  # type: ignore
                            if path_xml.exists():
                                path_xml.rename(path_xml.stem + "xml_off")

                        else:
                            xml_file_list.replace(item.index, item.to_comment())  # type: ignore
                            path_to_file.replace(  # type: ignore
                                "%ModDir%",
                                AppConfig.get_steam_mod_path(),  # type: ignore
                            )
                            path_to_file.replace(  # type: ignore
                                "LocalMods",
                                AppConfig.get_local_mod_path(),  # type: ignore
                            )
                            path_xml = Path(path_to_file)  # type: ignore
                            if path_xml.exists():
                                path_xml.rename(path_xml.stem + "xml")

                    except Exception:
                        continue

        XMLBuilder.save(xml_file_list, (mod_path / "filelist.xml"))  # type: ignore
