A second attempt at a python-sqlite ORM in <1000 lines
[previous attempt here](https://github.com/toombs-caeman/microlite)

This time trying to be more deliberate about the design, rather than fumbling towards something that works (which is how the last one worked).

# Restrictions and Goals
I think I want to aim for something tighter this time, maybe <500 lines.
Rather than trying to make it the "best" and stuffing as many features in as I can under the limit, I want this version to be readable and basic, both in terms of code and usage. I want to use this for future small experiments.

As before, code lines are counted with `cloc`, and tests don't count.

# Concept
For small experiments, I can write the table create statements by hand, or use an existing example db.
# What are databases
In isolation, databases can be thought of as durable (transactional) storage that also provides a strong query interface (SQL).
However, from the point of view of many programs, databases can be seen as a way to grant persistence to data. Marshalling data into and out of the database is incidental.


# Concept
Focus on getting the query interface right, so start with chinook and ignore migrations for now.

Tables are classes, and instances are rows.

[X] initalize DB connection
    [ ] guard initialization if the tables and classes don't match
[X] model definitions should look like dataclasses
    [X] type annotations correspond to fields
    [X] type | None makes field nullable
    [ ] values correspond to default values
    [ ] lambda values correspond to generated columns
    [X] create table statement from class definition
[ ] single row CRUD
    [ ] row.save() - create/update
    [ ] row.delete() - delete
    [X] (table.id == 123).get() - read
[ ] debug mode
    [X] str(query) get query as string
    [ ] all queries logged/printed
[ ] optimized iteration
    [ ] query.first()
    [ ] query.last()
    [X] query.all() aka list(iter(query))
    [ ] query.page(order, offset, limit)
    [ ] query.only()
[ ] foreign keys
    [ ] autofetch foreign key fields on access
    [ ] pre-fetch foreign key fields when requested
[ ] where slices
[ ] model mixins (SoftDelete, TimestampedCreation)
[ ] LSP must be happy with typing

# probably not features
[ ] migration
    [ ] create table if not exists
    [ ] update table definition
[ ] upsert statements
[ ] transactions
