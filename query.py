#!/usr/bin/env python
import sqlite3
from functools import cached_property
from dataclasses import dataclass, field, replace
import typing

@dataclass(frozen=True)
class query:
    """underlying explicit syntax for queries"""
    table: type = sqlite3.Row
    @cached_property
    def _table(self):
        return self.table.__name__

    columns: tuple = ()
    @cached_property
    def _columns(self):
        return ', '.join(self.columns) if self.columns else '*'

    where: dict[str,typing.Any] = field(default_factory=dict)
    @cached_property
    def _where(self):
        if not self.where:
            return ''
        wtr = {
            'like': 'LIKE',
            'ne': '!=',
            'eq': '=',
            'lt': '<',
            'le': '<=',
            'gt': '>',
            'ge': '>=',
        }
        clauses = []
        for k in self.where:
            field, *tr = k.split('__')
            if not tr:
                tr = 'eq',
                k += '__eq'
            clauses.append(f'{field} {wtr[tr[0]]} :{k}')
        return f' WHERE {' AND '.join(clauses)}'

    order: tuple = ()
    @cached_property
    def _order(self):
        if not self.order:
            return ''
        return f' ORDER BY {', '.join(self.order)}'

    distinct: bool = False
    @cached_property
    def _distinct(self):
        return ' DISTINCT' if self.distinct else ''

    limit: int|slice = slice(None)
    @cached_property
    def _limit(self):
        if self.limit == slice(None):
            return ''
        if isinstance(self.limit, int):
            # this is pretty bad practice
            return f' LIMIT 1 OFFSET {self.limit}'

        offset = self.limit.start or 0
        limit = self.limit.stop - offset if self.limit.stop else - 1
        return f' LIMIT {limit} OFFSET {offset}'

    params: dict[str, typing.Any] = field(default_factory=dict)
    @cached_property
    def _params(self):
        p = {
            (k if '__' in k else f'{k}__eq'):v
            for k, v in self.where.items()
        }
        p.update(self.params)
        return p

    @cached_property
    def _db(self):
        return self.table.db

    @cached_property
    def _select(self):
        return f"SELECT{self._distinct} {self._columns} FROM {self._table}{self._where}{self._order}{self._limit}"


    @cached_property
    def _save(self):
        # TODO instead of keys use self.columns?
        sql = f"INSERT INTO {self._table} ({', '.join(self.params)}) VALUES ({', '.join(f':{k}' for k in self.params)})"
        # allow upsert if keys set
        if self.columns:
            sql += f' ON CONFLICT UPDATE ({self._columns}) UPDATE SET {', '.join(f'{k} = :{k}' for k in self.params)}'
        return sql

    @cached_property
    def _delete(self):
        return f'DELETE FROM {self._table}{self._where}{self._limit}'


    def save(self):
        return self._db.execute(self._save, self._params)
    def delete(self):
        return self._db.execute(self._delete, self._params)
    def select(self):
        return self._db.execute(self._select, self._params)


    
def test_table():
    class newRow(sqlite3.Row):
        x: str
    db = query()
    # manually create the table for now
    db._db.execute('create table newRow (x text);')

    q = query(
        table=newRow,
        params={'x':'ok'},
        order=('x',),
    )
    assert q._select == 'SELECT * FROM newRow ORDER BY x'
    assert q._save   == 'INSERT INTO newRow (x) VALUES (:x)'
    assert q._delete == 'DELETE FROM newRow'

    q.save()
    results = list(q.select())
    assert len(results) == 1
    row = results[0]
    assert isinstance(row, newRow)
    assert row['x'] == 'ok'

    q.delete()
    results = list(q.select())
    assert len(results) == 0

def test_where():
    q = query(
        params={'x':'ok'},
        where={'field__ne':3, 'f2':4}
    )
    assert q._select == 'SELECT * FROM Row WHERE field != :field__ne AND f2 = :f2__eq'
    assert q._save == 'INSERT INTO Row (x) VALUES (:x)'
    assert q._delete == 'DELETE FROM Row WHERE field != :field__ne AND f2 = :f2__eq'

def test_column_distinct():
    q = query(
        distinct=True,
        columns=('a','b'),
    )
    assert q._select == 'SELECT DISTINCT a, b FROM Row'

def test_params():
    q = query(params={'x':'ok'}, where={'field__ne':3, 'f2':4})
    assert q._params == {'x':'ok', 'field__ne':3, 'f2__eq':4}

def test_limit():
    class ql(query):
        def __getitem__(self, obj):
            return replace(self, limit=obj)
    q = ql()
    assert q[4]  ._select == 'SELECT * FROM Row LIMIT 1 OFFSET 4'
    assert q[:4] ._select == 'SELECT * FROM Row LIMIT 4 OFFSET 0'
    assert q[3:] ._select == 'SELECT * FROM Row LIMIT -1 OFFSET 3'
    assert q[3:4]._select == 'SELECT * FROM Row LIMIT 1 OFFSET 3'

def test_order():
    q = query(order=('a','b'))
    assert q._select == 'SELECT * FROM Row ORDER BY a, b'

def test_foreign_key():
    assert False

if __name__ == "__main__":
    import pytest
    pytest.main([__file__])
