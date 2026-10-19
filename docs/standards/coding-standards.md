# Coding Standards (Python / FastAPI)

1. Routers (`app/routers`) only convert input and output; business rules live in `app/services`.
2. Do not scatter policy numbers and thresholds through the code; manage them as **a constant/setting in one place**.
3. Use **parameter binding** (`?`) for all SQL. Never build SQL by string concatenation.
4. Get the time only through `app.clock`. (It must be possible to fix the time in tests.)
5. Public functions state their intent in an English docstring or comment of at least one line.
6. Every new or changed business rule has **boundary-value tests** (for example day 30 / day 31, exactly at the threshold).
7. `ruff check .` and `ruff format .` must pass.
