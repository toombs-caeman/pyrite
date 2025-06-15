#!/usr/bin/env python
from pyrite import *

@table
class artists:
    ArtistId: Key[int]
    Name: str

@table
class media_types:
    MediaTypeId: Key[int]
    Name: str

@table
class genres:
    GenreId: Key[int]
    Name: str

@table
class albums:
    AlbumId: Key[int]
    Title: str
    ArtistId: Fk[artists]

@table
class tracks:
    TrackId: Key[int]
    Name: str
    AlbumId: Fk[albums]|None
    MediaTypeId: Fk[media_types]
    GenreId: Fk[genres]|None
    Composer: str
    Milliseconds: int
    Bytes: int
    UnitPrice: float

@table
class sqlite_master:
    type: str|None
    name: str|None
    tbl_name: str|None
    rootpage: str|None
    sql: str|None

DB('chinook.db', debug=True)


def test_expr():
    e = Expr(artists.ArtistId, '=', 3)
    assert str(e) == 'artists.ArtistId = ?'
    assert tuple(e.__params__) == (3,)
    q = artists.ArtistId == 3
    e = q.where
    assert str(e) == 'artists.ArtistId = ?', 'this should be equivalent to the previous expression'
    assert tuple(e.__params__) == (3,)
    assert str(q) == 'SELECT * FROM artists WHERE artists.ArtistId = ?'
    assert tuple(q.__params__) == (3,)

def test_special():
    anno = artists.__annotations__['ArtistId']
    assert anno.__origin__ == Key
    assert anno.__args__[0] == int

    anno = albums.__annotations__['ArtistId']
    assert anno.__origin__ == Fk
    assert anno.__args__[0] == artists


    assert isinstance(albums.Title, Field)
    assert isinstance(albums.ArtistId, Fk)

    assert isinstance(albums.ArtistId == 1, Query)
    assert str(albums.ArtistId == 1) == 'SELECT * FROM albums WHERE albums.ArtistId = ?'

    #assert artists._ == ('artists.ArtistId',), 'primary key'
    #tables = {t.name:t.sql for t in sqlite_master.type == 'table'}

def test_crud():
    ac = artists(1, 'AC/DC')
    assert ac == (artists.ArtistId == 1).get()

if __name__ == "__main__":
    import pytest
    pytest.main([__file__])
