from pathlib import Path
from typing import Dict, Optional

from Code.app_vars import AppConfig

"""
Пример .loc
main-app-name={form-apple} {sex-apple} # комментарий
    .form1-apple=яблоко
    .form2-apple=яблока
    .form5-apple=яблок
    .male-apple=Он
    .female-apple=Она
    .neuter-apple=Оно
"""


class Localization:
    _translations: Dict[str, str] = {}

    @classmethod
    def init(cls) -> None:
        localization_path = (
            AppConfig.get_data_root_path()
            / "localization"
            / AppConfig.get("lang", "eng")  # type: ignore
        )
        cls.load_translations(localization_path)

    @classmethod
    def clear_load_translation(cls) -> None:
        cls._translations.clear()

    @classmethod
    def reload_translation(cls, lang: str) -> None:
        cls._translations.clear()

        loc_path = AppConfig.get_data_root_path() / "localization" / lang
        if loc_path.exists():
            cls.load_translations(loc_path)

    @classmethod
    def load_translations(cls, folder_path: str | Path) -> None:
        """Рекурсивно загружает все файлы локализации (.loc) из указанной папки.

        Args:
            folder_path (str | Path): Путь к папке, содержащей файлы локализации.
        """
        folder = Path(folder_path)
        for file_path in folder.rglob("*.loc"):
            cls._load_file(file_path)

    @classmethod
    def _load_file(cls, file_path: Path) -> None:
        """Загружает и парсит файл локализации, добавляя переводы в словарь.

        Args:
            file_path (Path): Путь к файлу локализации (.loc).
        """
        with file_path.open("r", encoding="utf-8") as file:
            current_key: Optional[str] = None
            for line in file:
                line = line.strip()

                if "#" in line:
                    line = cls._remove_comment(line)

                if "=" in line and not line.startswith("."):
                    current_key, value = line.split("=", 1)
                    cls._translations[current_key.strip()] = value.strip()

                elif line.startswith(".") and current_key:
                    sub_key, sub_value = line.split("=", 1)
                    cls._translations[sub_key.strip()] = sub_value.strip()

    @staticmethod
    def _remove_comment(line: str) -> str:
        """Удаляет комментарий из строки, если # не экранирован.

        Args:
            line (str): Строка с возможным комментарием.

        Returns:
            str: Строка без комментария.
        """
        if r"\#" in line:
            line = line.replace(r"\#", "__TEMP_HASH__")

        line = line.split("#", 1)[0].strip()

        return line.replace("__TEMP_HASH__", "#")

    @staticmethod
    def _select_form(count: int, base_key: str) -> str:
        """Определяет форму слова на основе числа.

        Args:
            count (int): Количество, определяющее форму слова.
            base_key (str): Базовый ключ слова, для которого выбирается форма.

        Returns:
            str: Ключ формы слова ('form1', 'form2', 'form5').
        """
        if count % 10 == 1 and count % 100 != 11:
            return f"form1-{base_key}"

        elif 2 <= count % 10 <= 4 and not 12 <= count % 100 <= 14:
            return f"form2-{base_key}"

        else:
            return f"form5-{base_key}"

    @classmethod
    def has_string(cls, key: str) -> bool:
        text = cls._translations.get(key)
        if text:
            return True
        return False

    @classmethod
    def get_string(cls, key: str, **kwargs) -> str:
        """Возвращает строку перевода с подстановкой форм слов или других строк.

        Args:
            key (str): Ключ основной строки локализации.
            **kwargs: Дополнительные параметры для подстановки форм, рода или строк.

        Returns:
            str: Строка с подставленными формами, родом или строками, или сообщение об отсутствии ключа.

        Examples::

            result = Localization.get_string(
                'main-app-name',
                key1={'count': 3, 'gender': 'female'},
                key2='custom string'
            )
        """
        text: str = cls._translations.get(key, f"[Missing key: {key}]")

        for sub_key, value in kwargs.items():
            if isinstance(value, dict):
                count: Optional[int] = value.get("count", None)
                if count is not None:
                    form_key: str = Localization._select_form(count, sub_key)
                    form_value: str = cls._translations.get(
                        form_key, f"[Missing form: {form_key}]"
                    )
                    text = text.replace(f"{{form-{sub_key}}}", form_value)

                gender: Optional[str] = value.get("gender", None)
                if gender is not None:
                    gender_key: str = f"{gender}-{sub_key}"
                    gender_value: str = cls._translations.get(
                        gender_key, f"[Missing gender: {gender_key}]"
                    )
                    text = text.replace(f"{{sex-{sub_key}}}", gender_value)

            else:
                text = text.replace(f"{{{sub_key}}}", str(value))

        return text

    @classmethod
    def change_language(cls, new_lang: str) -> None:
        AppConfig.set("lang", new_lang)
        cls.reload_translation(new_lang)
