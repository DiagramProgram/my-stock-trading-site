----
-- phpLiteAdmin database dump (http://www.phpliteadmin.org/)
-- phpLiteAdmin version: 1.9.7.1
-- Exported: 1:33am on December 30, 2020 (UTC)
-- database file: /home/ubuntu/yy/finance/finance.db
----
BEGIN TRANSACTION;

----
-- Table structure for users
----
CREATE TABLE 'users' ('id' INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, 'username' TEXT NOT NULL, 'hash' TEXT NOT NULL, 'cash' NUMERIC NOT NULL DEFAULT 10000.00 );

----
-- structure for index username on table users
----
CREATE UNIQUE INDEX 'username' ON "users" ("username");
COMMIT;