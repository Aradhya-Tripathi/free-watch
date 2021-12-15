import json
import os
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Optional

from rich.console import Console

import fire_watch

from .errorfactory import ConfigFileNotFound


class Flags(SimpleNamespace):
    """Class for application wide flags prints,
    to `stderr` in case of attribute error.
    """

    def __getattribute__(self, name: str) -> Any:
        try:
            return super().__getattribute__(name)
        except AttributeError:
            fire_watch.print(f"[blod red]{name} flag does not exist")
            return


class Conf(dict):
    """dict like class allows accessing attributes"""

    def __getattr__(self, __name):
        return self.get(__name)


def get_config(base_path):
    """
    Search for config file in `fire_watch.config` name space
    if found return unsanitized config file as a dictionary.
    else raise `ConfigFileNotFound` error.
    """
    path = os.path.join(base_path, "config/config.json")
    if not os.path.exists(path):
        raise ConfigFileNotFound(path=path)

    with open(path) as f:
        return Conf(json.loads(f.read()))


def sanitized_configs(base_path: Path):
    """Sanitize config file if found by `get_config`"""
    conf = get_config(base_path)
    # TODO: sanitize config file
    return conf


def init_flags():
    fire_watch.flags = Flags()


def set_debug_flags():
    fire_watch.flags.send_email = False


def set_db_name(conf):
    fire_watch.flags.db_name = (
        os.getenv("TESTDB") if conf.developer or os.getenv("CI") else os.getenv("DB")
    )


def init_print_utils(
    file: Optional[str] = None,
):
    console = Console(file=file)
    fire_watch.print = console.print
    fire_watch.print_json = console.print_json
    fire_watch.print_exception = console.print_exception
