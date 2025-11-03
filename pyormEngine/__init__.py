# pyorm/__init__.py
"""
pyorm: A lightweight ORM framework built with pure Python.

This module exposes the main entry points:
    - BaseModel
    - PRIMARYKEY, FOREIGNKEY, NOTNULL, DEFAULT, CHECK, UNIQUE
    - Condition, Field
"""

from .orm import (
    BaseModel,
    Condition,
    Field,
    QueryChainer,
    MetaConstruct
)

from .attributes import (
    PRIMARYKEY,
    FOREIGNKEY,
    NOTNULL,
    DEFAULT,
    CHECK,
    Unique,
)

from .common import (
    type_map,
)

__all__ = [
    "BaseModel",
    "Condition",
    "Field",
    "QueryChainer",
    "MetaConstruct",
    "PRIMARYKEY",
    "FOREIGNKEY",
    "NOTNULL",
    "DEFAULT",
    "CHECK",
    "Unique",
    "type_map",
]

__version__ = "0.1.0"
