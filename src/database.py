"""
Database Module
Handles MySQL database operations for coffee tally system
"""
import logging
import mysql.connector
from mysql.connector import Error

logger = logging.getLogger(__name__)


class Database:
    """Class for database operations"""
    
    def __init__(self, config):
        """
        Initialize the database connection
        
        Args:
            config: Dictionary with database configuration
                   {host, port, user, password, database, table}
        """
        self.config = config
        self.connection = None
        
    def connect(self):
        """
        Establish connection to the MySQL database
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            self.connection = mysql.connector.connect(
                host=self.config['host'],
                port=int(self.config['port']),
                user=self.config['user'],
                password=self.config['password'],
                database=self.config['database'],
            )
            if self.connection.is_connected():
                print("✓ Connected to MySQL database")
                return True
            return False
        except Error as e:
            logger.exception("Cannot connect to database: %s", e)
            print(f"ERROR: Cannot connect to database: {e}")
            return False
    
    def get_user_by_card(self, card_id):
        """
        Find a user by card ID
        
        Args:
            card_id: The card ID to search for
            
        Returns:
            dict: User record with fields {id, card_id, name, credit} or None if not found
        """
        if not self.connection or not self.connection.is_connected():
            logger.error("Database not connected")
            print("ERROR: Database not connected")
            return None
        
        try:
            cursor = self.connection.cursor(dictionary=True)
            query = f"SELECT * FROM {self.config['table']} WHERE card_id = %s"
            cursor.execute(query, (card_id,))
            result = cursor.fetchone()
            cursor.close()
            return result
        except Error as e:
            logger.exception("Could not query user: %s", e)
            print(f"ERROR: Could not query user: {e}")
            return None
    
    def update_credit(self, card_id, new_credit):
        """
        Update the coffee credit for a user
        
        Args:
            card_id: The card ID of the user
            new_credit: The new credit amount
            
        Returns:
            bool: True if update successful, False otherwise
        """
        if not self.connection or not self.connection.is_connected():
            logger.error("Database not connected")
            print("ERROR: Database not connected")
            return False
        
        try:
            cursor = self.connection.cursor()
            query = f"UPDATE {self.config['table']} SET credit = %s WHERE card_id = %s"
            cursor.execute(query, (new_credit, card_id))
            self.connection.commit()
            cursor.close()
            print(f"✓ Updated credit for card {card_id} to {new_credit}")
            return True
        except Error as e:
            logger.exception("Could not update credit: %s", e)
            print(f"ERROR: Could not update credit: {e}")
            return False
    
    def add_user(self, card_id, name, initial_credit=0):
        """
        Add a new user to the database
        
        Args:
            card_id: The card ID
            name: The user's name
            initial_credit: Initial coffee credit (default: 0)
            
        Returns:
            bool: True if user added successfully, False otherwise
        """
        if not self.connection or not self.connection.is_connected():
            logger.error("Database not connected")
            print("ERROR: Database not connected")
            return False
        
        try:
            cursor = self.connection.cursor()
            query = f"INSERT INTO {self.config['table']} (card_id, name, credit) VALUES (%s, %s, %s)"
            cursor.execute(query, (card_id, name, initial_credit))
            self.connection.commit()
            cursor.close()
            print(f"✓ Added user {name} with card ID {card_id}")
            return True
        except Error as e:
            logger.exception("Could not add user: %s", e)
            print(f"ERROR: Could not add user: {e}")
            return False
    
    def get_all_users(self):
        """
        Get all users from the database
        
        Returns:
            list: List of user records or empty list if error
        """
        if not self.connection or not self.connection.is_connected():
            logger.error("Database not connected")
            print("ERROR: Database not connected")
            return []
        
        try:
            cursor = self.connection.cursor(dictionary=True)
            query = f"SELECT * FROM {self.config['table']} ORDER BY name"
            cursor.execute(query)
            results = cursor.fetchall()
            cursor.close()
            return results
        except Error as e:
            logger.exception("Could not query users: %s", e)
            print(f"ERROR: Could not query users: {e}")
            return []
    
    def close(self):
        """Close the database connection"""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            print("Database connection closed")
