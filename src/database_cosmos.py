"""
Database Module - Azure Cosmos DB Implementation
Handles Azure Cosmos DB operations for coffee tally system
"""
import logging
from datetime import datetime, timezone
import uuid
from azure.cosmos import CosmosClient, exceptions, PartitionKey

# Suppress verbose Azure SDK logging
logging.getLogger('azure').setLevel(logging.WARNING)
logging.getLogger('azure.core').setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

class Database_Cosmos:
    """Class for Azure Cosmos DB database operations"""
    
    def __init__(self, config):
        """
        Initialize the Cosmos DB connection
        
        Args:
            config: Dictionary with database configuration
                   {endpoint, key, database_name, container_name}
        """
        self.config = config
        self.client = None
        self.database = None
        self.container = None
        
    def connect(self):
        """
        Establish connection to the Cosmos DB database
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            self.client = CosmosClient(
                url=self.config['endpoint'],
                credential=self.config['key']
            )
            
            # Get or create database
            self.database = self.client.get_database_client(self.config['database_name'])
            
            # Get or create container
            self.container = self.database.get_container_client(self.config['container_name'])
            
            print("✓ Connected to Azure Cosmos DB database")
            return True
        except Exception as e:
            logger.exception("Cannot connect to Cosmos DB: %s", e)
            print(f"ERROR: Cannot connect to Cosmos DB: {e}")
            return False
    
    def get_user_by_card(self, card_id):
        """
        Find a user by card ID
        
        Args:
            card_id: The card ID to search for
            
        Returns:
            dict: User record with fields {id, card_id, name, credit, created_at, updated_at} or None if not found
        """
        if not self.container:
            logger.error("Database not connected")
            print("ERROR: Database not connected")
            return None
        
        try:
            # Query for user with this card_id
            query = "SELECT * FROM c WHERE c.card_id = @card_id"
            parameters = [{"name": "@card_id", "value": card_id}]
            
            items = list(self.container.query_items(
                query=query,
                parameters=parameters,
                enable_cross_partition_query=True
            ))
            
            if items:
                user = items[0]
                # Convert ISO datetime strings to datetime objects for compatibility            
                if 'updated_at' in user and isinstance(user['updated_at'], str):
                    user['updated_at'] = datetime.fromisoformat(user['updated_at'].replace('Z', '+00:00'))
                return user
            return None
        except Exception as e:
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
        if not self.container:
            logger.error("Database not connected")
            print("ERROR: Database not connected")
            return False
        
        try:
            # First, get the user document
            user = self.get_user_by_card(card_id)
            if not user:
                logger.error(f"User with card_id {card_id} not found")
                return False
            
            # Update credit and updated_at timestamp
            now = datetime.now(timezone.utc).isoformat()
            user['credit'] = new_credit
            user['updated_at'] = now
            
            # Replace the document
            self.container.replace_item(item=user['id'], body=user)
            print(f"✓ Updated credit for card {card_id} to {new_credit}")
            return True
        except Exception as e:
            logger.exception("Could not update credit: %s", e)
            print(f"ERROR: Could not update credit: {e}")
            return False
    
    def update_user(self, card_id, name=None, credit=None, username=None, password_hash=None):
        """
        Update user information
        
        Args:
            card_id: The card ID of the user
            name: The user's name (optional, only updated if provided)
            credit: The new credit amount (optional, only updated if provided)
            username: Username for login (optional, only updated if provided)
            password_hash: Password hash (optional, only updated if provided)
            
        Returns:
            bool: True if update successful, False otherwise
        """
        if not self.container:
            logger.error("Database not connected")
            print("ERROR: Database not connected")
            return False
        
        try:
            # First, get the user document
            user = self.get_user_by_card(card_id)
            if not user:
                logger.error(f"User with card_id {card_id} not found")
                return False
            
            # Update fields if provided
            if name is not None:
                user['name'] = name
            if credit is not None:
                user['credit'] = credit
            if username is not None:
                user['username'] = username
            if password_hash is not None:
                user['password_hash'] = password_hash
            
            # Always update timestamp
            user['updated_at'] = datetime.now(timezone.utc).isoformat()
            
            # Replace the document
            self.container.replace_item(item=user['id'], body=user)
            print(f"✓ Updated user {name or user['name']} with card ID {card_id}")
            return True
        except Exception as e:
            logger.exception("Could not update user: %s", e)
            print(f"ERROR: Could not update user: {e}")
            return False
    
    def add_user(self, card_id, name, initial_credit=0, username=None, password_hash=None, created_at=None):
        """
        Add a new user to the database
        
        Args:
            card_id: The card ID (will be used as document id)
            name: The user's name
            initial_credit: Initial coffee credit (default: 0)
            username: Optional username for login (default: None)
            password_hash: Optional password hash for authentication (default: None)
            created_at: Optional creation timestamp (default: current time)
            
        Returns:
            bool: True if user added successfully, False otherwise
        """
        if not self.container:
            logger.error("Database not connected")
            print("ERROR: Database not connected")
            return False
        
        try:
            # Create user document
            now = datetime.now(timezone.utc).isoformat()
            
            # Use provided created_at or current time
            if created_at is not None:
                # If created_at is a datetime object, convert to ISO format
                if isinstance(created_at, datetime):
                    created_at_str = created_at.isoformat()
                else:
                    created_at_str = created_at
            else:
                created_at_str = now
            
            user_doc = {
                'id': str(uuid.uuid4()),
                'card_id': card_id,
                'name': name,
                'credit': initial_credit,
                'created_at': created_at_str,
                'updated_at': now
            }
            
            # Add optional fields if provided
            if username is not None:
                user_doc['username'] = username
            if password_hash is not None:
                user_doc['password_hash'] = password_hash
            
            self.container.create_item(body=user_doc)
            print(f"✓ Added user {name} with card ID {card_id}")
            return True
        except exceptions.CosmosResourceExistsError:
            logger.error(f"User with card_id {card_id} already exists")
            print(f"ERROR: User with card_id {card_id} already exists")
            return False
        except Exception as e:
            logger.exception("Could not add user: %s", e)
            print(f"ERROR: Could not add user: {e}")
            return False
    
    def get_all_users(self):
        """
        Get all users from the database
        
        Returns:
            list: List of user records or empty list if error
        """
        if not self.container:
            logger.error("Database not connected")
            print("ERROR: Database not connected")
            return []
        
        try:
            query = "SELECT * FROM c ORDER BY c.name"
            items = list(self.container.query_items(
                query=query,
                enable_cross_partition_query=True
            ))
            
            # Convert datetime strings to datetime objects
            for user in items:
                if 'updated_at' in user and isinstance(user['updated_at'], str):
                    user['updated_at'] = datetime.fromisoformat(user['updated_at'].replace('Z', '+00:00'))
            
            return items
        except Exception as e:
            logger.exception("Could not query users: %s", e)
            print(f"ERROR: Could not query users: {e}")
            return []
    
    def close(self):
        """Close the database connection"""
        # Cosmos DB client doesn't need explicit closing
        self.client = None
        self.database = None
        self.container = None
        print("Cosmos DB connection closed")
