#!/usr/bin/env python
import pytest
from pyrite import *

@table('artists')
class artist:
    ArtistId: Key[int]
    Name: str

@table('media_type')
class media_type:
    MediaTypeId: Key[int]
    Name: str

@table('genre')
class genre:
    GenreId: Key[int]
    Name: str

@table('albums')
class album:
    AlbumId: Key[int]
    Title: str
    ArtistId: Fk[artist]

@table('tracks')
class track:
    TrackId: Key[int]
    Name: str
    AlbumId: Fk[album]|None
    MediaTypeId: Fk[media_type]
    GenreId: Fk[genre]|None
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

    @property
    def tables(self):
        return self.type == 'table'

def test_expr():
    e = Expr(artist.ArtistId, '=', 3)
    assert str(e) == 'artists.ArtistId = ?'
    assert tuple(e.__params__) == (3,)
    q = artist.ArtistId == 3
    e = q.where
    assert str(e) == 'artists.ArtistId = ?', 'this should be equivalent to the previous expression'
    assert tuple(e.__params__) == (3,)
    assert str(q) == 'SELECT * FROM artists WHERE artists.ArtistId = ?'
    assert tuple(q.__params__) == (3,)

def test_object():
    """show that we can create an object in code which"""
    name = "you've never heard of them"
    new = artist(Name=name)
    assert new.Name == name
    assert new._ == new.ArtistId == None
    new.save()
    assert new.ArtistId != None
    pk = new._
    new.delete()
    assert new.ArtistId == None

    assert get(artist.ArtistId == pk) == new

    # also allow explicitly setting the primary key
    id = 1
    name = 'AC/DC'
    ac = artist(ArtistId=id, Name=name)
    assert ac.ArtistId == id
    assert ac.Name == name



def test_update():
    a = (artist.ArtistId == 1).get()
    oldname = a.Name
    new_name = f'{oldname}-new and improved'
    a.Name = new_name
    a.save()
    assert (artist.ArtistId == 1).get().Name == new_name
    a.Name = oldname
    a.save()

def test_fk():
    a = (album.AlbumId == 1).get()
    assert a.ArtistId == artist(1, 'AC/DC')

@pytest.mark.xfail
def test_reverse_fk():
    """
    Should be able to access the reverse of a foreign key relationship.
    
    """
    q = artist.ArtistId == 1
    ac = q.get()
    res = {
        album(AlbumId=1, Title="For Those About To Rock We Salute You", ArtistId=1,),
        album(AlbumId=4, Title="Let There Be Rock", ArtistId=1,)
    }
    assert set(q._albums) == res
    assert set(ac._albums) == res

if __name__ == "__main__":
    db = DB('chinook.db', debug=True)
    pytest.main([__file__])
