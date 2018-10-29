import os
import sqlite3


APP_DIR = os.environ['APPDATA'] + r'\Overload'
DATASTORE = APP_DIR + r'\datastore.db'

# DATASTORE = 'datastore.db'

# Make a connection to the SQLite DB
conn = sqlite3.connect(DATASTORE)

# Obtain a Cursor object to execute SQL statements
cur = conn.cursor()

dropFTPTable = """DROP TABLE ftps;"""
cur.execute(dropFTPTable)

createFTPTable = """
	CREATE TABLE IF NOT EXISTS ftps (
 		fid INTEGER PRIMARY KEY,
	    name VARCHAR NOT NULL,
	    host VARCHAR NOT NULL,
	    folder VARCHAR,
	    user VARCHAR,
	    password VARCHAR,
	    system VARCHAR NOT NULL,
	    UNIQUE(name, system) ON CONFLICT ROLLBACK);"""

cur.execute(createFTPTable)

# Add a new column to NYPLOrderTemplate table
addColumn = "ALTER TABLE NyplOrderTemplate ADD COLUMN raction VARCHAR;"
cur.execute(addColumn)

conn.close()
