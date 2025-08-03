import logging
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, Set

from Code.app_config import AppConfig
from Code.handlers.mod_cache import ModCache
from Code.xml_object import XMLBuilder

from .id_parser import extract_ids
from .internal_library import InternalModLibrary

logger = logging.getLogger(__name__)


class SkipLoadBuild(Exception):
    pass


@dataclass
class Identifier:
    name: str
    steam_id: Optional[str]

    @property
    def id(self) -> str:
        if self.steam_id:
            return self.steam_id
        return self.name

    def __eq__(self, value: object) -> bool:
        if isinstance(value, Identifier):
            return self.id == value.id

        elif isinstance(value, str):
            return self.id == value

        return False

    def __str__(self) -> str:
        return self.id

    def __repr__(self) -> str:
        return f"Identifier(name={self.name}, steam_id={self.steam_id})"


@dataclass
class Dependencie(Identifier):
    type: Literal["patch", "requirement", "requiredAnyOrder", "conflict"]
    attributes: Dict[str, str]
    condition: Optional[str] = None

    def __str__(self) -> str:
        additional_attributes = ", ".join(
            f"{k}={v}" for k, v in self.attributes.items()
        )
        return (
            f"Dependencie(type={self.type}, id={self.id}, "
            f"condition={self.condition}, attributes={{{additional_attributes}}})"
        )

    def __repr__(self) -> str:
        return (
            f"Dependencie(name={self.name}, steam_id={self.steam_id}, "
            f"dep_type={self.type}, condition={self.condition}, "
            f"attributes={self.attributes})"
        )

    @staticmethod
    def is_valid_type(value: str):
        return value in {
            "patch",
            "requirement",
            "requiredAnyOrder",
            "conflict",
        }


@dataclass
class Metadata:
    mod_version: str
    game_version: str

    author_name: str
    license: str

    warnings: List[str]
    errors: List[str]

    dependencies: List[Dependencie]

    @staticmethod
    def create_empty() -> "Metadata":
        return Metadata(
            "base-not-set",
            "base-not-set",
            "base-unknown",
            "base-not-specified",
            [],
            [],
            [],
        )

    def __str__(self) -> str:
        dependencies_str = ", ".join(str(dep) for dep in self.dependencies)
        warnings_str = "; ".join(self.warnings)
        errors_str = "; ".join(self.errors)
        return (
            f"Metadata(mod_version={self.mod_version}, game_version={self.game_version}, "
            f"author={self.author_name}, license={self.license}, warnings=[{warnings_str}], "
            f"errors=[{errors_str}], "
            f"dependencies=[{dependencies_str}])"
        )

    def __repr__(self) -> str:
        return (
            f"Metadata(mod_version={self.mod_version}, "
            f"game_version={self.game_version}, author_name={self.author_name}, license={self.license}, "
            f"warnings={self.warnings}, errors={self.errors}, "
            f"dependencies={self.dependencies})"
        )


@dataclass
class ModUnit(Identifier):
    local: bool

    corepackage: bool

    has_toggle_content: bool

    load_order: Optional[int]
    path: Path

    metadata: Metadata

    use_lua: bool
    use_cs: bool

    settings: Dict[str, Any]

    add_id: Set[str]
    override_id: Set[str]

    def __hash__(self) -> int:
        return hash(self.id)

    def __eq__(self, other):
        return isinstance(other, ModUnit) and self.id == other.id

    def __getstate__(self):
        state = self.__dict__.copy()
        state["path"] = str(self.path) if self.path else None
        return state

    def __setstate__(self, state):
        state["path"] = Path(state["path"]) if state["path"] else None
        self.__dict__.update(state)

    @staticmethod
    def create_empty() -> "ModUnit":
        return ModUnit(
            "base-not-set",
            None,
            False,
            False,
            False,
            None,
            Path(),
            Metadata.create_empty(),
            False,
            False,
            {},
            set(),
            set(),
        )

    def get_str_path(self) -> str:
        if not self.local:
            return str(self.path)

        else:
            return f"LocalMods/{self.path.parts[-1]}"

    def get_bool_settigs(self, key: str) -> Optional[bool]:
        if key not in self.settings:
            return None

        value = self.settings[key]

        if isinstance(value, bool):
            return value

        elif isinstance(value, str):
            return value.lower() == "true"

        elif isinstance(value, (int | float)):
            return value > 0

        return False

    @staticmethod
    def build(path: (Path | str)) -> Optional["ModUnit"]:
        try:
            path = Path(path)

            mod_hash = ModCache.calculate_mod_hash(path)

            filelist_path = path / "filelist.xml"
            if filelist_path.exists():
                filelist = XMLBuilder.load(filelist_path)
                if filelist:
                    mod_name = filelist.attributes.get("name")
                    if mod_name and mod_name != "Something went rong":
                        cached_mod = ModCache.load_cached_mod(mod_name, mod_hash)
                        if cached_mod:
                            cached_mod.path = path
                            return cached_mod

            obj = ModUnit.create_empty()

            if "LocalMods" in path.parts:
                obj.local = True

            ModUnit.parse_filelist(obj, path)

            if obj.corepackage:
                logging.warning(
                    f"The program does not support core packages!\n|Mod details: '{obj.name}' | Steam ID: '{obj.steam_id}'"
                )
                return None

            obj.path = path
            obj.use_lua = ModUnit.has_file(path, ".lua")
            obj.use_cs = ModUnit.has_file(path, ".cs") or ModUnit.has_file(path, ".dll")

            ModUnit.parse_files(obj, path)
            ModUnit.parse_metadata(obj, path)

            if obj.name != "base-not-set":
                ModCache.save_mod_cache(obj.name, mod_hash, obj)

            return obj

        except SkipLoadBuild:
            return None

    @staticmethod
    def has_file(path: Path, extension: str) -> bool:
        return next(path.rglob(f"*{extension}"), None) is not None

    @staticmethod
    def parse_filelist(obj: "ModUnit", path: Path) -> None:
        file_list_path = path / "filelist.xml"
        if not file_list_path.exists():
            raise ValueError(f"{file_list_path} don't exsist")

        xml_obj = XMLBuilder.load(file_list_path)
        if xml_obj is None:
            raise ValueError(f"{file_list_path} invalid xml struct")

        obj.name = xml_obj.attributes.get("name", "Something went rong")
        obj.corepackage = (
            xml_obj.attributes.get("corepackage", "false").lower() == "true"
        )

        obj.steam_id = xml_obj.attributes.get("steamworkshopid")
        obj.metadata.game_version = xml_obj.attributes.get(
            "gameversion", "base-not-specified"
        )
        obj.metadata.mod_version = xml_obj.attributes.get(
            "modversion", "base-not-specified"
        )

    @staticmethod
    def parse_files(obj: "ModUnit", path: Path) -> None:
        xml_files_paths = path.rglob("*.xml")

        with ThreadPoolExecutor() as executor:
            for xml_file_path in xml_files_paths:
                executor.submit(ModUnit._process_xml_file, xml_file_path, obj)

    @staticmethod
    def _process_xml_file(xml_file_path: Path, obj: "ModUnit"):
        try:
            if xml_file_path.name.lower() == "modparts.xml":
                obj.has_toggle_content = True
                return

            if xml_file_path.name.lower() in AppConfig.xml_system_dirs:
                return

            xml_obj = XMLBuilder.load(xml_file_path)
            if xml_obj is None:
                logger.warning(f"File {xml_file_path} is empty")
                return

            id_parser_unit = extract_ids(xml_obj)
            obj.add_id.update(id_parser_unit.add_id)
            obj.override_id.update(id_parser_unit.override_id)

            if not obj.has_toggle_content:
                for elem in xml_obj.find_only_comments("BTM:*"):
                    obj.has_toggle_content = True

        except Exception as err:
            logger.error(str(err) + f"\n|Mod: {obj!r}")

    @staticmethod
    def parse_metadata(obj: "ModUnit", path: Path) -> None:
        metadata_path = path / "metadata.xml"

        if not metadata_path.exists():
            if InternalModLibrary.has_mod(obj.id):
                ModUnit._parse_metadata_viva_internal_mod_library(obj)

            return

        xml_obj = XMLBuilder.load(metadata_path)
        if xml_obj is None:
            raise ValueError(f"Empty metadata.xml for {obj.id}!")

        for element in xml_obj.iter_non_comment_childrens():
            element_name_lower = element.tag.lower()

            if element_name_lower == "settings":
                for ch in element.iter_non_comment_childrens():
                    setting_name = ch.attributes.get("name")
                    if setting_name:
                        obj.settings[setting_name] = ch.attributes.get("value")

            if element_name_lower == "meta":
                for ch in element.iter_non_comment_childrens():
                    ch_name_lower = ch.tag.lower()
                    if ch_name_lower == "author":
                        obj.metadata.author_name = ch.content
                    elif ch_name_lower == "license":
                        obj.metadata.license = ch.content
                    elif ch_name_lower == "warning":
                        obj.metadata.warnings.extend(ch.content.strip().splitlines())
                    elif ch_name_lower == "error":
                        obj.metadata.errors.extend(ch.content.strip().splitlines())

            if element_name_lower == "dependencies":
                dependencies = []
                for ch in element.iter_non_comment_childrens():
                    dep_type = ch.tag

                    if not Dependencie.is_valid_type(dep_type):
                        logger.warning(
                            f"Ignoring unsupported dependency type '{dep_type}' in {ch}"
                        )
                        continue

                    name = ch.attributes.get("name")
                    steam_id = ch.attributes.get("steamID")
                    condition = ch.attributes.get("condition")

                    if not name and not steam_id:
                        logger.error(
                            f"Dependency element missing 'name' or 'steamID' attribute in element {ch}"
                        )
                        continue

                    add_attributes = ch.attributes.copy()
                    add_attributes.pop("name", None)
                    add_attributes.pop("steamID", None)
                    add_attributes.pop("condition", None)

                    dependency = Dependencie(
                        name=name or "",
                        steam_id=steam_id,
                        type=dep_type,  # type: ignore
                        attributes=add_attributes,
                        condition=condition,
                    )
                    dependencies.append(dependency)

                obj.metadata.dependencies.extend(dependencies)

    @staticmethod
    def _parse_metadata_viva_internal_mod_library(obj: "ModUnit") -> None:
        settings = InternalModLibrary.get_mod_settings(obj.id)
        meta = InternalModLibrary.get_mod_meta(obj.id)
        deps = InternalModLibrary.get_mod_dependencies(obj.id)

        if settings:
            obj.settings.update(settings)

        if meta:
            if author := meta.get("author"):
                obj.metadata.author_name = author
            if license_ := meta.get("license"):
                obj.metadata.license = license_

            if warning_str := meta.get("warning"):
                obj.metadata.warnings.extend(warning_str.strip().splitlines())
            if error_str := meta.get("error"):
                obj.metadata.errors.extend(error_str.strip().splitlines())

        if deps:
            for dep_type, items in deps.items():
                if not Dependencie.is_valid_type(dep_type):
                    logger.warning(
                        f"Ignoring unsupported dependency type '{dep_type}' in DB for mod {obj.id}"
                    )
                    continue

                for item in items:
                    name = item.get("name", "")
                    steam_id = item.get("steamID")
                    condition = item.get("condition")

                    attrs = {
                        k: v
                        for k, v in item.items()
                        if k not in ("name", "steamID", "condition")
                    }

                    dependency = Dependencie(
                        name=name,
                        steam_id=steam_id,
                        type=dep_type,  # type: ignore
                        attributes=attrs,
                        condition=condition,
                    )
                    obj.metadata.dependencies.append(dependency)

    def update_meta_errors(self) -> None:
        metadata_path = self.path / "metadata.xml"

        if not metadata_path.exists():
            if InternalModLibrary.has_mod(self.id):
                self._update_meta_errors_viva_internal_mod_library()

            return

        xml_obj = XMLBuilder.load(metadata_path)
        if xml_obj is None:
            raise ValueError(f"Empty metadata.xml for {self.id}!")

        self.metadata.errors.clear()
        self.metadata.warnings.clear()

        for element in xml_obj.find_only_elements("meta"):
            for ch in element.iter_non_comment_childrens():
                ch_name_lower = ch.tag.lower()
                if ch_name_lower == "warning":
                    self.metadata.warnings.extend(ch.content.strip().splitlines())

                elif ch_name_lower == "error":
                    self.metadata.errors.extend(ch.content.strip().splitlines())

    def _update_meta_errors_viva_internal_mod_library(self) -> None:
        meta = InternalModLibrary.get_mod_meta(self.id)
        if not meta:
            return

        self.metadata.errors.clear()
        self.metadata.warnings.clear()

        if "warning" in meta:
            self.metadata.warnings.extend(meta["warning"].strip().splitlines())

        if "error" in meta:
            self.metadata.errors.extend(meta["error"].strip().splitlines())
