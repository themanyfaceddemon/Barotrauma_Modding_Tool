import json
import sqlite3
from pathlib import Path
from typing import Any

from Code.app_config import AppConfig
from Code.xml_object import XMLBuilder


class InternalModLibrary:
    _path_to_db: Path = AppConfig.get_data_root_path() / "InternalModLibrary.db"

    @classmethod
    def create_tabel(cls) -> None:
        if cls._path_to_db.exists():
            return

        with sqlite3.connect(cls._path_to_db) as con:
            con.executescript("""
            CREATE TABLE IF NOT EXISTS mod_metadata (
                mod_id INTEGER PRIMARY KEY,
                settings TEXT,
                meta TEXT,
                dependencies TEXT
            )
            """)

    @staticmethod
    def is_valid_int(value: int | str | None) -> int | None:
        if value is None:
            return None

        if isinstance(value, str):
            try:
                value = int(value)
            except (ValueError, TypeError):
                return None

        return value

    @classmethod
    def has_mod(cls, mod_id: int | str | None) -> bool:
        mod_id = cls.is_valid_int(mod_id)
        if mod_id is None:
            return False

        with sqlite3.connect(cls._path_to_db) as con:
            cursor = con.execute(
                "SELECT 1 FROM mod_metadata WHERE mod_id = ?", (mod_id,)
            )
            return cursor.fetchone() is not None

    @classmethod
    def _get_json_column(cls, mod_id: int | str | None, column: str):
        mod_id = cls.is_valid_int(mod_id)
        if mod_id is None:
            return None

        with sqlite3.connect(cls._path_to_db) as con:
            cursor = con.execute(
                f"SELECT {column} FROM mod_metadata WHERE mod_id = ?", (mod_id,)
            )
            row = cursor.fetchone()
            if row is None or row[0] is None:
                return None

            return json.loads(row[0])

    @classmethod
    def get_mod_settings(cls, mod_id: int | str | None) -> dict[str, str] | None:
        return cls._get_json_column(mod_id, "settings")

    @classmethod
    def get_mod_meta(cls, mod_id: int | str | None) -> dict[str, str] | None:
        return cls._get_json_column(mod_id, "meta")

    @classmethod
    def get_mod_dependencies(
        cls, mod_id: int | str | None
    ) -> dict[str, list[dict[str, Any]]] | None:
        return cls._get_json_column(mod_id, "dependencies")

    @classmethod
    def _build_and_drop(cls) -> None:
        """внутренний метод. Вызывал руками чтобы перенести всё в db"""
        with sqlite3.connect(cls._path_to_db) as con:
            cursor = con.cursor()

            for path in (AppConfig.get_data_root_path() / "InternalLibrary").rglob(
                "*.xml"
            ):
                print(path.stem)
                xml_obj = XMLBuilder.load(path)
                if xml_obj is None:
                    continue

                settings_dict: dict[str, str] = {}
                meta_dict: dict[str, str] = {}
                dependencies_dict: dict[str, list[str]] = {}

                for children in xml_obj.iter_non_comment_childrens():
                    match children.tag:
                        case "settings":
                            for sub_children in children.iter_non_comment_childrens():
                                settings_dict[sub_children.attributes.get("name")] = (  # type: ignore
                                    sub_children.attributes.get("value")
                                )

                        case "meta":
                            for sub_children in children.iter_non_comment_childrens():
                                meta_dict[sub_children.tag] = sub_children.content

                        case "dependencies":
                            for sub_children in children.iter_non_comment_childrens():
                                tag = sub_children.tag
                                dependencies_dict.setdefault(tag, []).append(
                                    {
                                        "name": sub_children.attributes.get("name", ""),
                                        "steamID": sub_children.attributes.get(
                                            "steamID", ""
                                        ),
                                        "condition": sub_children.attributes.get(
                                            "condition", "None"
                                        )
                                        if tag in ("patch", "requirement")
                                        else None,
                                        "message": sub_children.attributes.get(
                                            "message", "Conflict detected"
                                        )
                                        if tag == "conflict"
                                        else None,
                                        "level": sub_children.attributes.get(
                                            "level", "error"
                                        )
                                        if tag == "conflict"
                                        else None,
                                    }  # type: ignore
                                )

                        case _:
                            continue

                cursor.execute(
                    """
                INSERT OR REPLACE INTO mod_metadata (mod_id, settings, meta, dependencies)
                VALUES (?, ?, ?, ?)
                """,
                    (
                        int(path.stem),
                        json.dumps(settings_dict),
                        json.dumps(meta_dict),
                        json.dumps(dependencies_dict),
                    ),
                )
                con.commit()
