import types
import typing
import sqlite3
import datetime
from dataclasses import dataclass

# TODO 
#   https://docs.sqlalchemy.org/en/13/orm/extensions/hybrid.html#module-sqlalchemy.ext.hybrid

def registerType[P](type:type[P],to_sql: typing.Callable[[P],int|float|str|bytes], from_sql:typing.Callable[[bytes],P]):
    """Define how to pickle a scalar type."""
    sqlite3.register_adapter(type, to_sql)
    sqlite3.register_converter(type.__name__, from_sql)

registerType(datetime.date, datetime.date.isoformat, lambda d: datetime.date.fromisoformat(d.decode()),)
registerType(datetime.datetime, datetime.datetime.isoformat, lambda dt: datetime.datetime.fromisoformat(dt.decode()),)
registerType(datetime.timedelta, datetime.timedelta.total_seconds, lambda td: datetime.timedelta(seconds=int(td)),)

# https://stackoverflow.com/questions/28237955/same-name-for-classmethod-and-instancemethod
@dataclass
class hybridmethod:
    fclass: type
    finstance: types.MethodDescriptorType|None = None

    def classmethod(self, fclass):
        return type(self)(fclass, self.finstance)

    def instancemethod(self, finstance):
        return type(self)(self.fclass, finstance)

    def __get__(self, instance, cls):
        if instance is None or self.finstance is None:
              # either bound to the class, or no instance method available
            return self.fclass.__get__(cls, None)
        return self.finstance.__get__(instance, cls)

@dataclass
class Expr:
    """Represent an arbitrary SQL expression."""
    left: typing.Any
    op: str
    right: typing.Any
    def __str__(self):
        return ' '.join((
            str(self.left) if isinstance(self.left, (Field, Expr))else'?',
            self.op,
            str(self.right) if isinstance(self.right, (Field, Expr))else'?',
        ))
    @property
    def __params__(self):
        for v in (self.left, self.right):
            if isinstance(v, Expr):
                yield from v.__params__
            elif isinstance(v, Field):
                pass
            else:
                yield v

@dataclass
class Query:
    """Represents a SQL query."""
    table: type
    where: Expr|None = None
    limit: slice|None = None
    order: tuple = ()
    distinct: bool = False
    # TODO comparison operators "=" "<" ">" "<=" "<>" ">=" "IN" 'AND' 'OR'

    def __and__(self, value):
        pass # TODO
    def __eq__(self, _):
        raise NotImplementedError # TODO
    def __where(self):
        return f" WHERE {self.where}" if self.where else ''
    def __group(self):
        # TODO
        return ''
    def __distinct(self):
        return ' DISTINCT' if self.distinct else ''
    def __order(self):
        return f" ORDER BY {','.join(self.order)}" if self.order else ''
    def __limit(self):
        if self.limit is None:
            return ''
        l = self.limit.stop
        o = self.limit.start
        if o is None:
            return f" LIMIT {l}"
        if l is None:
            return f" LIMIT {o}, -1"
        return f" LIMIT {o}, {l}"

    def __str__(self):
        """produce sql from query structure"""
        return f"SELECT{self.__distinct()} * FROM {self.table.__name__}{self.__where()}{self.__group()}{self.__order()}{self.__limit()}"

    def get(self):
        return next(iter(self))
    def __iter__(self):
        params = tuple(self.where.__params__) if self.where else ()
        return (self.table(*row) for row in self._.execute(str(self), params))
    def all(self):
        return list(self)
    @property
    def __params__(self):
        if self.where:
            yield from self.where.__params__

@dataclass
class Field[T](Query):
    """a descriptor that handles weirdness around columns"""
    name: str = ''

    def __str__(self):
        return f"{self.table.__name__}.{self.name}"

    def __eq__(self, value):
        return Query(table=self.table, where=Expr(self, '=', value))


class Key[T](Field):
    """a field that is a primary key"""

class Fk[T](Field):
    def __get__(self, obj, t=None):
        if obj is None:
            return self  # called on type
        # fetch object along foreign key
        foreign = typing.get_args(type(self))[0]
        if not isinstance(self.value, foreign):
            # the primary key of the foreign table
            self.value = (foreign._ == self.value).first()
        return self.value

def table(cls, name=None):
    """class decorator to mark as a table"""
    # handle partial application, and when table_name != class_name
    if isinstance(cls, str):
        return lambda kls: table(kls, name=cls)
    if name is None:
        name = cls.__name__

    cls = dataclass(cls)
    # construct create table statement
    create = [f'CREATE TABLE IF NOT EXISTS "{name}" (']
    for k,v in cls.__annotations__.items():
        typ = typing.get_origin(v) or v
        args = typing.get_args(v)
        nullable = typ is types.UnionType and types.NoneType in args
        if nullable:
            v = v.__args__[0]
            args = tuple(filter(lambda x:x is not types.NoneType, args))
            typ = args[0]
        # primary key
        pk = typ is Key
        if pk:
            # save primary keys.
            # TODO consider managing these centrally, along with the list of all tables
            cls._pk = k
            typ = args[0]
            args = typing.get_args(typ)
        # foreign key
        fk = typ is Fk
        if fk:
            foreign_table = args[0]
            fk = f"{foreign_table.__name__}({foreign_table._pk})"
            typ = int # TODO handle non-integer keys, multikeys
            args = ()

        sql_type = {
                int: "INTEGER",
                float: "REAL",
                str: "TEXT",
                bytes: "BLOB",
        }.get(typ, typ.__name__)
        # report
        create.append(f"[{k}] {sql_type}")
        if pk:
            create.append(' PRIMARY KEY')
        if fk:
            create.append(f' REFERENCES {fk}')
        if not nullable:
            create.append(' NOT NULL')
        setattr(cls, k, Field(table=cls, name=k))
        create.append(',')
    create.append(');')
    cls.__sql__ = ''.join(create)
    return cls

def DB(
    database="file::memory:?cache=shared",
    debug=False,
    **options,
):
    options = { "database": database,
        "detect_types": sqlite3.PARSE_DECLTYPES,
        "uri": True,
        **options,
    }
    c = sqlite3.connect(**options)
    c.execute("PRAGMA FOREIGN_KEY=1")
    if debug:
        c.set_trace_callback(lambda msg: print(f"sql: {msg!r}"))
    Query._ = c
    return c
