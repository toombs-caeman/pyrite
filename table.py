#!/usr/bin/env python
from dataclasses import dataclass, replace
from typing import get_args, get_origin
from query import query

# TODO use __table__ instead of __name__
class Q:
    """an implicit form of query"""
    def __init__(self, q=None, **kwargs):
        self._query = query(**kwargs) if q is None else replace(q, **kwargs)

    def _(self, **kwargs):
        return type(self)(self._query, **kwargs)

    def __call__(self, **kwargs):
        w = self._query.where.copy()
        w.update(kwargs)
        return self._(where=w)

    def __iter__(self):
        return iter(self._query.select())

    def get(self):
        return next(iter(self))

    def list(self):
        return list(self)

    def __getitem__(self, obj):
        return self._(limit=obj)

@dataclass
class Field[T]:
    typ: type
    key: bool = False
    nullable: bool = False

    def __set_name__(self, owner, name):
        self.owner = owner
        self.name = name

    def __get__(self, obj, objtype=None):
        if obj is None:
            return self # access on class
        return obj._fields[self.name]

    def __set__(self, obj, value):
        obj._fields[self.name] = value

    def __eq__(self, obj):
        return Q(table=self.owner, where={f'{self.name}__eq':obj})

    def __ne__(self, obj):
        return Q(table=self.owner, where={f'{self.name}__ne':obj})

    def __lt__(self, obj):
        return Q(table=self.owner, where={f'{self.name}__lt':obj})

    def __le__(self, obj):
        return Q(table=self.owner, where={f'{self.name}__le':obj})

    def __gt__(self, obj):
        return Q(table=self.owner, where={f'{self.name}__gt':obj})

    def __ge__(self, obj):
        return Q(table=self.owner, where={f'{self.name}__ge':obj})

    def __iter__(self):
        return Q(table=self.owner, columns=(self.name,))

    def __str__(self):
        return self.name

    def __repr__(self):
        return f'{self.owner.__name__}.{self}'

    def _create(self):
        typ = {
                int: "INTEGER",
                float: "REAL",
                str: "TEXT",
                bytes: "BLOB",
        }.get(self.typ, self.typ.__name__)
        pk = ' PRIMARY KEY' if self.key else ''
        null = '' if self.nullable else ' NOT NULL'
        return f'{self.name} {typ}{pk}{null}'
    def __mod__(self, obj):
        return Q(table=self.owner, where={f'{self.name}__like':obj})

class fk[T](Field):
    def _create(self):
        null = '' if self.nullable else ' NOT NULL'
        return f'{self.name} INTEGER REFERENCES {self.typ.__name__}{null}'

class pk[T](Field):
    typ = int
    key = True

class table:
    __all__ = []
    db = None
    def __init__(self, **fields):
        self._fields = fields
    @classmethod
    def row_factory(cls, cursor, row):
        return cls(**{k[0]:v for k,v in zip(cursor.description, row)})
    @classmethod
    def _(cls, **kwargs):
        return Q(table=cls, where=kwargs)
    def __repr__(self):
        return f"{self.__name__}({', '.join(f'{k}={v!r}' for k,v in self._fields.items())})"
    def __init_subclass__(cls):
        super().__init_subclass__()
        cls.__name__ = cls.__dict__.get('__name__', cls.__name__)
        table.__all__.append(cls)

        for k,v in cls.__annotations__.items():
            ftype = Field
            args = get_args(v)
            if nullable:=type(None) in args:
                v = args[0] if args[1] is type(None) else args[0]
                args = get_args(v)

            typ = get_origin(v) or v
            if issubclass(typ, Field):
                ftype = typ
                if args := get_args(v):
                    typ = args[0]
                else:
                    typ = int

            key = issubclass(ftype, pk)
            field = ftype(
                typ=typ,
                key=key,
                nullable=nullable,
            )
            field.__set_name__(cls, k)
            setattr(cls, k, field)

    @classmethod
    def _create(cls):
        fields = (
            v._create()
            for v in cls.__dict__.values()
            if isinstance(v, Field)
        )
        return f'CREATE TABLE IF NOT EXISTS {cls.__name__} ({', '.join(fields)})'

    def save(self):
        pass
    def delete(self):
        pass


###################### TESTS ######################
class artist(table):
    __name__ = 'artists'
    ArtistId = Field(int, True)
    Name = Field(str)

class genre(table):
    GenreId: pk
    Name: str

class album(table):
    __name__ = 'albums'
    AlbumId: pk
    Title: str | None
    ArtistId: fk[artist] | None

def test_field():
    # explicit style
    assert artist.ArtistId.key == True
    assert artist.ArtistId.typ == int
    assert artist.ArtistId.nullable == False

    # implicit style
    assert genre.GenreId.key == True
    assert genre.GenreId.typ == int
    assert genre.GenreId.nullable == False

def test_field_comparisons():
    assert (genre.GenreId == 3)._select == 'SELECT * FROM genre WHERE GenreId = :GenreId__eq'

def test_create():
    assert album.ArtistId._create() == 'ArtistId INTEGER REFERENCES artists'
    assert album._create() == 'CREATE TABLE IF NOT EXISTS albums (AlbumId INTEGER PRIMARY KEY NOT NULL, Title TEXT, ArtistId INTEGER REFERENCES artists)'

if __name__ == "__main__":
    import pytest
    pytest.main([__file__])
