from string import Template
from types import SimpleNamespace
from typing import Optional, TypeVar

T = TypeVar("T", bound=SimpleNamespace)


class _BraceOnlyStringTemplate(Template):
    idpattern = None
    braceidpattern = Template.idpattern


def file_to_string(file_path: str, var_mapping: Optional[T] = None) -> str:
    """
    Converts a file to a string.
    :param path: Path to a file.
    :param var_mapping: A mapping of variables to replace in the template.
    :return: The file content converted to a string.
    :raises: FileNotFoundError if the template file is not found.
    """
    with open(file_path, 'r') as f:
        data = f.read()
        if var_mapping is not None:
            return _BraceOnlyStringTemplate(data).safe_substitute(var_mapping.__dict__)
        return data
