-- Adminer 4.7.6 PostgreSQL dump

DROP TABLE IF EXISTS "users";
CREATE TABLE "public"."users" (
    "id" SERIAL PRIMARY KEY,
    "username" text,
    "hash" text,
    "cash" numeric DEFAULT '10000.00',
    CONSTRAINT "idx_23208741_username" UNIQUE ("username")
) WITH (oids = false);

-- 2021-01-01 00:32:29.995538+00