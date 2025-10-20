from abc import ABC, abstractmethod
import sqlite3

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



class Condition:
    def __init__(self, expr):
        self.expr = expr
    

    def __and__(self, other: 'Condition'):
        return Condition(f"{self.expr} AND {other.expr}")

    def __or__(self, other: 'Condition'):
        return Condition(f"{self.expr} OR {other.expr}")

    def __invert__(self):
        return Condition(f"NOT {self.expr}")

    def __str__(self):
        return self.expr

class Field:
    def __init__(self, name, model=None):
        self.name = name
        self.model = model  # <-- NEW: who owns this field

    def __eq__(self, value):
        return Condition(f"{self.full_name()} = {repr(value)}")

    def __ne__(self, value):
        return Condition(f"{self.full_name()} != {repr(value)}")

    def __gt__(self, value):
        return Condition(f"{self.full_name()} > {repr(value)}")

    def __lt__(self, value):
        return Condition(f"{self.full_name()} < {repr(value)}")

    def __ge__(self, value):
        return Condition(f"{self.full_name()} >= {repr(value)}")

    def __le__(self, value):
        return Condition(f"{self.full_name()} <= {repr(value)}")

    def in_(self, values):
        vals = ", ".join(repr(v) for v in values)
        return Condition(f"{self.full_name()} IN ({vals})")

    def like(self, pattern):
        return Condition(f"{self.full_name()} LIKE {repr(pattern)}")

    def full_name(self):
        if self.model:
            return f"{self.model.TableName()}.{self.name}"
        return self.name

type_map = {
    int: "INTEGER",
    str: "TEXT",
    float: "REAL",
    bool: "INTEGER"
}



class ModelMeta(type):
    def __new__(mcls, name, bases, attrs):
        cls = super().__new__(mcls, name, bases, attrs)
        if name == "BaseModel":
            return cls

        cls._foreign_keys = {}

        for field_name, field_type in getattr(cls, "__annotations__", {}).items():
            if isinstance(field_type, FOREIGNKEY):
                cls._foreign_keys[field_type.target_model] = field_name 
            setattr(cls, field_name, Field(field_name,model=cls))

        return cls
    

class BaseModel(metaclass=ModelMeta):
    DB_PATH = 'app.db'
    _connection = None

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
    def all(cls):
        with cls.connection() as conn:
            cur = conn.cursor()
            cur.execute(f"SELECT * FROM {cls.TableName()}")
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
        joins = []
        where_clause = ""

        if args and isinstance(args[0], Condition):
            where_clause = str(args[0])

            for model in BaseModel.__subclasses__():
                if model.TableName() in where_clause and model != cls:
                    joins.append(model)

        else:
            conditions = []
            for k, v in kwargs.items():
                val = f"'{v}'" if isinstance(v, str) else v
                conditions.append(f"{cls.TableName()}.{k} = {val}")
            where_clause = " AND ".join(conditions)

        sql = f"SELECT {cls.TableName()}.* FROM {cls.TableName()}"

        # Add JOINs automatically
        for j in joins:
            fk_field = cls._foreign_keys[j]

            if fk_field:
                sql += f" JOIN {j.TableName()} ON {cls.TableName()}.{fk_field} = {j.TableName()}.id"
                print(sql)

        sql += f" WHERE {where_clause}"

        print("Generated SQL:", sql)


        
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
        names = [n for n in fields ]
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
        columns = []
        for name, typ in fields.items():
            sql_type = type_map.get(typ, 'TEXT')

            if isinstance(typ, PRIMARYKEY):            
                columns.append(f'{str(name)} {str(typ)}')
            elif isinstance(typ, FOREIGNKEY):
                cls._foreign_keys[typ.target_model] = name
            else:
                columns.append(f'{str(name)} {type_map[typ]}')
        
        sql = f"CREATE TABLE IF NOT EXISTS {cls.TableName()} ({(','.join(columns))})"        
        # conn = cls.connection()
        # cur = conn.cursor()
        # cur.execute(sql)
        # conn.commit()