-- migrate:up

-- `date` was a timestamptz used purely as a calendar day (always inserted via
-- CURRENT_DATE), which made day comparisons depend on session timezone. A plain
-- date column is unambiguous and matches how the app actually uses it.
ALTER TABLE balance
    ALTER COLUMN date TYPE date USING date::date,
    ALTER COLUMN date SET DEFAULT CURRENT_DATE;

-- `rate` was stored as rate*10000 (an integer) to avoid floats; numeric stores
-- the real exchange rate directly and removes the *10000 math from the app.
ALTER TABLE balance
    ALTER COLUMN rate TYPE numeric USING (rate / 10000.0);

-- migrate:down

ALTER TABLE balance
    ALTER COLUMN rate TYPE integer USING ROUND(rate * 10000)::integer;

ALTER TABLE balance
    ALTER COLUMN date TYPE timestamp with time zone USING date::timestamp with time zone,
    ALTER COLUMN date SET DEFAULT CURRENT_TIMESTAMP;
