#!/usr/bin/env python
import pytest
from pyrite import *

class artist(table):
    __name__ = 'artists'
    ArtistId: pk
    Name: str

class media_type(table):
    MediaTypeId: pk
    Name: str

class genre(table):
    GenreId: pk
    Name: str

class album(table):
    __name__ ='albums'
    AlbumId: pk
    Title: str
    ArtistId: fk[artist]

class track(table):
    __name__ = 'tracks'
    TrackId: pk
    Name: str
    AlbumId: fk[album]|None
    MediaTypeId: fk[media_type]
    GenreId: fk[genre]|None
    Composer: str
    Milliseconds: int
    Bytes: int
    UnitPrice: float

class sqlite_master(table):
    type: str|None
    name: str|None
    tbl_name: str|None
    rootpage: str|None
    sql: str|None

    @property
    def tables(self):
        return self.type == 'table'

init_db('chinook.db')


def test_object():
    """show that we can create an object in code which"""
    name = "you've never heard of them"
    new = artist(Name=name)
    assert new.Name == name
    assert new.ArtistId == None
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
