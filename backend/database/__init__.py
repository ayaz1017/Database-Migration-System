"""
Robust SQLite session management for the Fluxline migration tracking database.

Provides a context-manager-based session that enforces strict transaction
boundaries: commit-on-success, rollback-on-failure. This prevents data
corruption from partially applied writes when errors occur mid-transaction.
"""

import sqlite3
from contextlib import contextmanager

import os

# Re-use the same DB_FILE configuration
DB_FILE = os.environ.get("DB_PATH", "migrations.db")


@contextmanager
def get_db(row_factory=False):
    """
    Context manager that yields a (conn, cursor) tuple with strict
    transaction boundaries.

    Usage:
        with get_db() as (conn, cursor):
            cursor.execute("INSERT INTO ...", (...))
            # Auto-commits on success, auto-rolls-back on exception.

    Args:
        row_factory: If True, sets conn.row_factory = sqlite3.Row for
                     dict-style row access.
    """
    conn = sqlite3.connect(DB_FILE)
    if row_factory:
        conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    try:
        yield conn, cursor
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()
