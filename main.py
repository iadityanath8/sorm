from abc import ABC, abstractmethod
import sqlite3


class NOTNULL:
    def __str__(self):
        return "NOT NULL"

class PRIMARYKEY:
    def __str__(self):
        return "PRIMARY KEY AUTOINCREMENT"

class UNIQUE:
    def __str__(self):
        return "UNIQUE"

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



class Condition:
    def __init__(self, expr):
        self.expr = expr
    

    def __and__(self, other: 'Condition'):
        print("Meow","AA")
        return Condition(f"{self.expr} AND {other.expr}")

    def __or__(self, other: 'Condition'):
        return Condition(f"{self.expr} OR {other.expr}")

    def __invert__(self):
        return Condition(f"NOT {self.expr}")

    def __str__(self):
        return self.expr

class Field:
    def __init__(self, name):
        self.name = name

    def __eq__(self, value):
        return Condition(f"{self.name} = {repr(value)}")

    def __ne__(self, value):
        return Condition(f"{self.name} != {repr(value)}")

    def __gt__(self, value):
        return Condition(f"{self.name} > {repr(value)}")

    def __lt__(self, value):
        return Condition(f"{self.name} < {repr(value)}")

    def __ge__(self, value):
        return Condition(f"{self.name} >= {repr(value)}")

    def __le__(self, value):
        return Condition(f"{self.name} <= {repr(value)}")

    def in_(self, values):
        vals = ", ".join(repr(v) for v in values)
        return Condition(f"{self.name} IN ({vals})")

    def like(self, pattern):
        return Condition(f"{self.name} LIKE {repr(pattern)}")


type_map = {
    int: "INTEGER",
    str: "TEXT",
    float: "REAL",
    bool: "INTEGER"
}



class ModelMeta(type):
    def __new__(mcls,name,bases,attrs):
        cls = super().__new__(mcls,name,bases,attrs)

        if name == "BaseModel":
            return cls 
        
        for field_name in getattr(cls, "__annotations__", {}):
            setattr(cls,field_name,Field(field_name))

        return cls 
    

class BaseModel(metaclass=ModelMeta):
    DB_PATH = 'app.db'
    _connection = None 
    _cloumns  = []

    def __init__(self, **kwargs):
        for name in self.fields():
            setattr(self, name, kwargs.get(name))

        def __init_subclass__(cls):
            super().__init_subclass__()
            for field_name in cls.fields().keys():
                setattr(cls, field_name, Field(field_name))

    @classmethod 
    def connection(cls):
        if cls._connection is None:
            cls._connection = sqlite3.connect(cls.DB_PATH)
        return cls._connection

    @classmethod
    def constraint(cls):
        return cls.CONSTRAINT

    @classmethod
    def name(cls) -> str:
        return cls.__name__

    @classmethod
    def all(cls):
        with cls.connection() as conn:
            cur = conn.cursor()
            cur.execute(f"SELECT * FROM {cls.name()}")
            rows = cur.fetchall()
        
        field_name = list(cls.fields().keys())
        objects = []
        for row in rows:
            data = {name: value for name, value in zip(field_name, row)}
            obj = cls(**data)
            objects.append(obj)
        return objects

    @classmethod
    def filter(cls, *args, **kwargs):
        field_map = cls.fields()

        if args and isinstance(args[0], Condition):
            where_clause = str(args[0])
        else:
            conditions = []
            for k, v in kwargs.items():
                if k not in field_map:
                    raise RuntimeError(f"Invalid field '{k}' for {cls.name()}")
                val = f"'{v}'" if isinstance(v, str) else v
                conditions.append(f"{k} = {val}")
            where_clause = " AND ".join(conditions)

        sql = f"SELECT * FROM {cls.TableName()} WHERE {where_clause}"
        
        print("Executing: ", sql)
        with cls.connection() as conn:
            cur = conn.cursor()
            cur.execute(sql)
            rows = cur.fetchall()

        field_names = list(cls.fields().keys())
        return [cls(**dict(zip(field_names, row))) for row in rows]

        
    @classmethod
    def primary_key(cls) -> str:
        return getattr(cls,"PK", "id")

    @classmethod    
    @abstractmethod
    def TableName(cls) -> str:
        return cls.__name__.lower()


    @classmethod
    def fields(cls) -> dict[str,type]:
        return getattr(cls,"__annotations__", {})

    @classmethod
    def describe(cls):
        print(f"Table: {cls.TableName()}")

        for field, typ in cls.fields().items():
            print(f" {field}: {typ.__name__}")

    def save(self):
        '''
            INSERT INTO {table_name} (columns)
        '''

        fields = self.__class__.fields()
        pk = self.primary_key()
        names = [n for n in fields if n != pk]
        values = [getattr(self,n, None) for n in names]
        placeholders = ", ".join("?" for _ in names)
        sql = f"INSERT INTO {self.__class__.TableName()} ({', '.join(names)}) VALUES ({placeholders})"
        
        conn = self.__class__.connection()
        cur = conn.cursor()
        cur.execute(sql, values)
        conn.commit()

    @classmethod
    def create_table(cls):
        fields = cls.fields()

        '''
            create table {table_name} (
                {name} {type} 
            )
        '''
        constraints = cls.constraint()
        columns = []
        for name, typ in fields.items():
            sql_type = type_map.get(typ, 'TEXT')
            col_constraint = []
            
            
            c = constraints.get(name)
            if c:
                if isinstance(c, list):
                    col_constraint.extend(str(x) for x in c)
                else:
                    col_constraint.append(str(c))
            
            column_def = f"{name} {sql_type} {' '.join(col_constraint)}".strip()
            columns.append(column_def)
        sql = f"CREATE TABLE IF NOT EXISTS {cls.TableName()} ({', '.join(columns)});"
        
        with cls.connection() as conn: 
            conn.execute(sql)


class User(BaseModel):
    a: int 
    b: str 
    c: int

    CONSTRAINT = {
        "a": PRIMARYKEY(),
        "b": NOTNULL(),
        "c" : [DEFAULT(0), CHECK("c < 9")]
    }

    def __repr__(self):
        return f"User Model value {self.a} {self.b} {self.c}"
    
    @classmethod
    def TableName(cls):
        return super().TableName()



if __name__ == '__main__':
    u = User(b = "Bhow",c = 2)
    print(User.filter((User.a == 1) | (User.a == 2)))