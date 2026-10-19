---
applyTo: "db/migrations/**"
---
- Follow `docs/standards/db-migration-guide.md`: expand → switch → contract, no destructive changes, new columns must allow NULL or have a DEFAULT.
- Name the file with the next number: `NNN_description.sql`. Do not modify existing files.
- The previous release (legacy app version) must still work with the new schema.
