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


type_map = {
    int: "INTEGER",
    str: "TEXT",
    float: "REAL",
    bool: "INTEGER"
}

class BaseModel(ABC):
    DB_PATH = 'app.db'
    _connection = None 
    _cloumns  = []

    def __init__(self, **kwargs):
        for name in self.fields():
            setattr(self, name, kwargs.get(name))

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
        pk = cls.primary_key()

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
            
            
            if name == pk:
                col_constraint.append(str(PRIMARYKEY()))
            
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

    PK = "a"

    CONSTRAINT = {
        "b": NOTNULL(),
        "c" : [DEFAULT(0), CHECK("c < 9")]
    }

    @classmethod
    def TableName(cls):
        return super().TableName()



if __name__ == '__main__':
    u = User()
    User.create_table()
