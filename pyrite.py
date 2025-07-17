from typing import Callable
import datetime
import sqlite3

def registerType[P](
    type:type[P],
    to_sql: Callable[[P],int|float|str|bytes],
    from_sql:Callable[[bytes],P]
):
    """Define how to pickle a scalar type."""
    sqlite3.register_adapter(type, to_sql)
    sqlite3.register_converter(type.__name__, from_sql)

registerType(
    datetime.date,
    datetime.date.isoformat,
    lambda d: datetime.date.fromisoformat(d.decode()),
)
registerType(
    datetime.datetime,
    datetime.datetime.isoformat,
    lambda dt: datetime.datetime.fromisoformat(dt.decode()),
)
registerType(
    datetime.timedelta,
    datetime.timedelta.total_seconds,
    lambda td: datetime.timedelta(seconds=int(td)),
)

def DB(db="file::memory:?cache=shared"):
    for t in table.__all__:
        c = sqlite3.Connection(
            database=db,
            detect_types=sqlite3.PARSE_DECLTYPES,
            uri=True,
        )
        c.execute("PRAGMA FOREIGN_KEY=1")
        c.row_factory = t.row_factory
        t.db = c

# re-exports
from table import table, query, Field, fk, pk
__all__ = [
    'registerType',
    'DB',
    'query',
    'table',
    'Field',
    'fk',
    'pk'
]
