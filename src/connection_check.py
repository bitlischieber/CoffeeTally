"""
Connection check helpers.
"""
import socket
from mysql.connector import Error
from database import Database


class ConnectionChecker:
    """Check database reachability and internet connectivity."""

    def __init__(self, db_config, timeout_seconds=2.0):
        self.db_config = db_config
        self.timeout_seconds = timeout_seconds

    def check_database(self, database: Database):
        """Return True if the database is reachable."""
        try:
            is_ok = database.connection.is_connected()
            return is_ok
        except Error:
            return False

    def check_internet(self):
        """Return True if a simple external socket connection succeeds."""
        try:
            socket.create_connection(("8.8.8.8", 53), self.timeout_seconds).close()
            return True
        except OSError:
            return False

    def check(self, database: Database):
        """Return tuple (db_ok, internet_ok)."""
        db_ok = self.check_database(database)
        if db_ok:
            return True, True
        return False, self.check_internet()
