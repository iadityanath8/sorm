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
    def update(cls, where: dict = None, **kwargs):
        """
        UPDATE {table_name}
        SET k = v {from kwargs}
        WHERE {conditions from where dict}
        """

        if not kwargs:
            raise ValueError("No fields to update")

        set_clause = ", ".join([f"{k} = ?" for k in kwargs.keys()])
        set_values = list(kwargs.values())

        where_clause = ""
        where_values = []
        if where:
            where_clause = " AND ".join([f"{k} = ?" for k in where.keys()])
            where_values = list(where.values())

        sql = f"UPDATE {cls.TableName()} SET {set_clause}"
        if where_clause:
            sql += f" WHERE {where_clause}"


        conn = cls.connection()
        cur = conn.cursor()
        cur.execute(sql,set_values + where_values)
        conn.commit()



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
                
        sql += f" WHERE {where_clause}"

        conn = cls.connection()
        cur = conn.cursor()
        cur.execute(sql)
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
        names = [n for n in fields ]
        values = [getattr(self,n, None) for n in names]
        placeholders = ", ".join("?" for _ in names)
        sql = f"INSERT INTO {self.__class__.TableName()} ({', '.join(names)}) VALUES ({placeholders})"


        conn = self.__class__.connection()
        cur = conn.cursor()
        cur.execute(sql, values)
        conn.commit()


    @classmethod
    def query(self):
        return QueryChainer(self)

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
                columns.append(f'{str(name)} {str(typ)}')
            else:
                columns.append(f'{str(name)} {type_map[typ]}')
        
        sql = f"CREATE TABLE IF NOT EXISTS {cls.TableName()} ({(','.join(columns))})"        
    
        conn = cls.connection()
        cur = conn.cursor()
        cur.execute(sql)
        conn.commit()



# YET TO implement to complex set of queries in here 
class QueryChainer:
    def __init__(self, model: BaseModel):
        self.model = model
        self._conditions = [] 
        self._kwargs = {}
        self._selected_fields = []
        self._order_by = []
        self._limit = None
        self._count = False


    def order_by(self, *fields):
        self._order_by = fields
        return self


    def count(self):
        self._count = True
        return self

    def limit(self, n):
        self._limit = n
        return self

    def select(self, *fields):
        """
        Accept Field objects like User.id, User.name
        """
        self._selected_fields = fields
        return self

    def filter(self,*args, **kwargs):
        
        for cond in args:
            if isinstance(cond, Condition):
                self._conditions.append(cond)
        

        for k, v in self._kwargs:
            self._kwargs[k] = v

        return self

    def _build_where_and_joins(self):
        joins = []
        clauses = []

        if self._conditions:
            if len(self._conditions) == 1:
                combined = self._conditions[0]
            else:
                combined = self._conditions[0]
                for cond in self._conditions[1:]:
                    combined = cond & combined

            where_clause = str(combined)


            for model in BaseModel.__subclasses__():
                if model.TableName() in where_clause and model != self.model:
                    joins.append(model)

            clauses.append(where_clause)

         # Process kwargs as normal
        for k, v in self._kwargs.items():
            val = f"'{v}'" if isinstance(v, str) else v
            clauses.append(f"{self.model.TableName()}.{k} = {val}")

        final_where = " AND ".join(clauses) if clauses else ""
        return final_where, joins


    def all(self):
        if self._count:
            field_list = "COUNT(*)"
        elif self._selected_fields:
            field_name = []
            for f in self._selected_fields:
                if f.model is not self.model:
                    raise ValueError("Invalid model in select class")

                field_name.append(f.full_name())
            
            field_list = ', '.join(field_name)
        else:
            field_list = f"{self.model.TableName()}.*"
        
        where_clause, joins = self._build_where_and_joins()
        sql = f"SELECT {field_list} FROM {self.model.TableName()}"

        for j in joins:
            fk_field = self.model._foreign_keys[j]
            sql += f" JOIN {j.TableName()} ON {self.model.TableName()}.{fk_field} = {j.TableName()}.id"

        if where_clause:
            sql += f" WHERE {where_clause}"

        if self._order_by:
            order_clause = ", ".join([f.full_name() for f in self._order_by])
            sql += f" ORDER BY {order_clause}"       

        if self._limit is not None:
            sql += f" LIMIT {self._limit}"


        print(sql)
        conn = self.model.connection()
        cur = conn.cursor()
        cur.execute(sql)
        rows = cur.fetchall()

        field_names = [f.name for f in self._selected_fields] if self._selected_fields else list(self.model.fields().keys())
        return [self.model(**dict(zip(field_names, row))) for row in rows]
    
    def first(self):
        results = self.all()
        return results[0] if results else None