from .common import type_map 

class NOTNULL:
    def __class_getitem__(cls, item):
        obj = cls()
        obj.base_type = item
        return obj

    def __str__(self):
        return f"{type_map.get(self.base_type, 'TEXT')} NOT NULL"


class PRIMARYKEY:
    def __class_getitem__(cls, item):
        obj = cls()
        obj.base_type = item
        return obj

    def __str__(self):
        return f"{type_map[self.base_type]} PRIMARY KEY AUTOINCREMENT"

class FOREIGNKEY:
    def __class_getitem__(cls, target_model):
        # target_model is the *actual* class (like PlayList)
        obj = cls()
        obj.target_model = target_model     # store the model class
        return obj

    def __str__(self):
        # This is used during table creation
        table_name = self.target_model.TableName()
        return f"INTEGER REFERENCES {table_name}(id)"

class Unique:
    def __class_getitem__(cls, item):
        obj = cls()
        obj.base_type = item
        return obj

    def __str__(self):
        return f"{type_map[self.base_type]} UNIQUE"
    

class DEFAULT:
    def __init__(self, value):
        self.value = value

    def __str__(self):
        if isinstance(self.value, str):
            return f"DEFAULT '{self.value}'"
        return f"DEFAULT {self.value}"

class CHECK:
    def __init__(self, expr):
        self.expr = expr

    def __str__(self):
        return f"CHECK({self.expr})"

