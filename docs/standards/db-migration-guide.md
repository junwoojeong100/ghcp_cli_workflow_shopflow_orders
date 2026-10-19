# DB Migration Guide (zero downtime · backward compatible)

1. File names are `NNN_description.sql` (3-digit number, ascending). A file that has already been applied is **never modified.**
2. Follow the three steps **expand → switch → contract**. Never drop, rename or change the type of a column in a single step.
3. When you add a column to an existing table, make it **nullable or give it a DEFAULT value**. (Never add a column that is only `NOT NULL`.)
4. If you change existing data, write the way to undo it (rollback SQL or a backup procedure) in the design document.
5. The legacy application version (the previous release) must still work on the new schema.
