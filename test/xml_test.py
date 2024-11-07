import re
from pathlib import Path
from typing import Dict, List, Optional, Union


class XMLParserException(Exception):
    def __init__(
        self,
        message: str,
        tag: Optional[str] = None,
        position: Optional[int] = None,
        line: Optional[int] = None,
    ):
        super().__init__(message)
        self.tag = tag
        self.position = position
        self.line = line

    def __str__(self):
        return (
            f"{self.args[0]} "
            f"(Tag: {self.tag}, Position: {self.position}, Line: {self.line})"
        )


class XMLComment:
    def __init__(self, text: str):
        self.text = text

    def dump(
        self,
        indent: int = 0,
        indent_char: str = " ",
        single_line: bool = False,
        inline_content: bool = False,
    ) -> str:
        indent_str = "" if single_line else indent_char * indent
        return f"{indent_str}<!-- {self.text} -->"

    def to_element(self) -> "XMLElement":
        xml_obj = XMLElement.build_element(self.text)
        if not xml_obj:
            raise XMLParserException(
                "Unable to convert comment to element: Empty content."
            )
        return xml_obj

    def __repr__(self):
        return f"XMLComment(text={repr(self.text)})"


class XMLElement:
    def __init__(self, name: str, attributes: Optional[Dict[str, str]] = None):
        self.name = name
        self.attributes: Dict[str, str] = attributes if attributes is not None else {}
        self.children: List[Union["XMLElement", XMLComment]] = []
        self.content: str = ""

    def add_child(self, child: Union["XMLElement", XMLComment]):
        self.children.append(child)

    def dump(
        self,
        indent: int = 0,
        indent_char: str = " ",
        single_line: bool = False,
        inline_content: bool = False,
    ) -> str:
        indent_str = "" if single_line else indent_char * indent
        attrs = " ".join(f'{key}="{value}"' for key, value in self.attributes.items())
        opening_tag = f"<{self.name}{(' ' + attrs) if attrs else ''}>"

        if not self.children and not self.content:
            return f"{indent_str}<{self.name}{(' ' + attrs) if attrs else ''} />"

        if not self.children and inline_content and self.content:
            return f"{indent_str}{opening_tag}{self.content}</{self.name}>"

        result = f"{indent_str}{opening_tag}"
        if not single_line:
            result += "\n"

        if self.content:
            content_str = f"{self.content}"
            if not single_line:
                content_str = indent_char * (indent + 4) + content_str + "\n"
            result += content_str

        for child in self.children:
            child_str = child.dump(indent + 4, indent_char, single_line, inline_content)
            if not single_line:
                child_str += "\n"
            result += child_str

        closing_tag = f"</{self.name}>"
        if not single_line:
            result += indent_char * indent
        result += closing_tag

        return result

    def to_comment(self) -> XMLComment:
        element_str = self.dump(single_line=True, inline_content=True)
        return XMLComment(element_str)

    @staticmethod
    def build_element(content: str) -> Optional["XMLElement"]:
        stack: List[XMLElement] = []
        root = None

        content = content.strip()
        i = 0

        if content.startswith("<?xml"):
            i = content.find(">")

        if i == -1:
            raise XMLParserException("Invalid <?xml>", line=1, position=0)

        while i < len(content):
            if content[i : i + 4] == "<!--":
                end_comment = content.find("-->", i + 4)
                if end_comment == -1:
                    raise XMLParserException("Unclosed comment", position=i)
                comment_text = content[i + 4 : end_comment].strip()
                comment = XMLComment(comment_text)
                if stack:
                    stack[-1].add_child(comment)
                else:
                    pass  # TODO
                i = end_comment + 3

            elif content[i] == "<":
                if content.startswith("</", i):
                    # Closing tag
                    tag_start = i + 2
                    tag_end = content.find(">", tag_start)
                    if tag_end == -1:
                        raise XMLParserException("Malformed closing tag", position=i)

                    tag_name = content[tag_start:tag_end].strip()
                    if not stack or stack[-1].name != tag_name:
                        raise XMLParserException(
                            "Unexpected closing tag", tag=tag_name, position=i
                        )
                    closed_element = stack.pop()
                    if not stack:
                        root = closed_element

                    else:
                        stack[-1].add_child(closed_element)
                    i = tag_end + 1
                else:
                    # Opening tag or self-closing tag
                    tag_start = i + 1
                    tag_end = content.find(">", tag_start)
                    if tag_end == -1:
                        raise XMLParserException("Malformed tag", position=i)

                    is_self_closing = content[tag_end - 1] == "/"
                    tag_content = content[tag_start:tag_end].strip()
                    if is_self_closing:
                        tag_content = tag_content[:-1].strip()

                    # Parse tag name and attributes
                    parts = re.split(r"\s+", tag_content, maxsplit=1)
                    tag_name = parts[0]
                    attributes = {}
                    if len(parts) > 1:
                        attr_str = parts[1]
                        attr_regex = re.compile(r'(\w[\w-]*)\s*=\s*(".*?"|\'.*?\'|\S+)')
                        for match in attr_regex.finditer(attr_str):
                            key, value = match.groups()
                            if value[0] in "\"'":
                                value = value[1:-1]
                            attributes[key] = value

                    element = XMLElement(tag_name, attributes)
                    if is_self_closing:
                        if stack:
                            stack[-1].add_child(element)
                        else:
                            root = element
                    else:
                        stack.append(element)
                    i = tag_end + 1

            else:
                # Handle text content
                text_start = i
                next_tag_pos = content.find("<", i)
                if next_tag_pos == -1:
                    next_tag_pos = len(content)
                text_content = content[text_start:next_tag_pos]
                if stack and text_content.strip():
                    stack[-1].content += text_content.strip()
                i = next_tag_pos

        if stack:
            raise XMLParserException(
                "Unclosed tags remain", tag=stack[-1].name, position=i
            )

        return root

    def find(self, pattern: str) -> List[Union["XMLElement", XMLComment]]:
        compiled_pattern = re.compile(pattern)
        result = []

        def match_element(element: XMLElement):
            if compiled_pattern.search(element.name):
                result.append(element)
            elif any(
                compiled_pattern.search(value) for value in element.attributes.values()
            ):
                result.append(element)
            for child in element.children:
                if isinstance(child, XMLElement):
                    match_element(child)
                elif isinstance(child, XMLComment):
                    if compiled_pattern.search(child.text):
                        result.append(child)

        match_element(self)
        return result

    def __repr__(self):
        return (
            f"XMLElement(name={repr(self.name)}, attributes={self.attributes}, "
            f"children={self.children}, content={repr(self.content)})"
        )


class XMLObject:
    def __init__(self) -> None:
        self.root: Optional[XMLElement] = None

    def find(self, pattern: str) -> List[Union[XMLElement, XMLComment]]:
        if self.root:
            return self.root.find(pattern)
        return []

    def replace_element_with_comment(self, element_name: str) -> None:
        if self.root:
            self._replace_element_with_comment(self.root, element_name)

    def _replace_element_with_comment(
        self, element: XMLElement, element_name: str
    ) -> None:
        for i, child in enumerate(element.children):
            if isinstance(child, XMLElement):
                if child.name == element_name:
                    element.children[i] = child.to_comment()
                else:
                    self._replace_element_with_comment(child, element_name)

    def replace_comment_with_element(self, comment_text: str) -> None:
        if self.root:
            self._replace_comment_with_element(self.root, comment_text)

    def _replace_comment_with_element(
        self, element: XMLElement, comment_text: str
    ) -> None:
        for i, child in enumerate(element.children):
            if isinstance(child, XMLComment):
                if comment_text in child.text:
                    element.children[i] = child.to_element()
            elif isinstance(child, XMLElement):
                self._replace_comment_with_element(child, comment_text)

    def dump(
        self,
        indent_char: str = " ",
        single_line: bool = False,
        inline_content: bool = True,
    ) -> str:
        if self.root:
            return self.root.dump(0, indent_char, single_line, inline_content)
        return ""

    @staticmethod
    def load_file(path: Union[Path, str], encoding: str = "utf-8") -> "XMLObject":
        path = Path(path)
        with open(path, "r", encoding=encoding) as file:
            content = file.read()
        obj = XMLObject()
        obj.root = XMLElement.build_element(content)
        return obj


def main():
    try:
        test = XMLObject.load_file(Path("Data/InternalLibrary/3247838390.xml"))
        print(test.dump())
        print("---")

        test.replace_element_with_comment("dependencies")
        print(test.dump())
        print("---")

        test.replace_comment_with_element("dependencies")
        print(test.dump())

    except XMLParserException as e:
        print(f"XML Error: {e}")


if __name__ == "__main__":
    main()
