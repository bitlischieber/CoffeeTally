#!/usr/bin/env python3
"""
Script to set up the MySQL database for Coffee Tally
"""
import mysql.connector
from mysql.connector import Error
import json
import sys
import os

def read_config():
    """Read the configuration file"""
    if not os.path.exists('config.json'):
        print("ERROR: config.json not found!")
        print("Please create config.json with the database connection details.")
        sys.exit(1)

    with open('config.json', 'r', encoding='utf-8') as f:
        config = json.load(f)

    return config['database']

def create_database(connection):
    """Create the database if it does not exist"""
    cursor = connection.cursor()
    db_name = read_config()['database']

    try:
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_name}")
        print(f"Database '{db_name}' created or already exists.")
    except Error as e:
        print(f"Error creating database: {e}")
        sys.exit(1)
    finally:
        cursor.close()

def create_tables(connection):
    """Create required tables"""
    cursor = connection.cursor()
    db_name = read_config()['database']
    table_name = read_config()['table']

    try:
        # Use the database
        cursor.execute(f"USE {db_name}")

        # Users and credit table
        create_users_table = f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            id INT AUTO_INCREMENT PRIMARY KEY,
            card_id VARCHAR(50) UNIQUE NOT NULL,
            name VARCHAR(100) NOT NULL,
            credit INT DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            username VARCHAR(10),
            password_hash VARCHAR(100)
        )
        """

        cursor.execute(create_users_table)
        print(f"Table '{table_name}' created or already exists.")

        connection.commit()
        print("\n[OK] Database setup completed successfully!")
        print(f"\nYou can add test users like:")
        print(f"  INSERT INTO {db_name}.{table_name} (card_id, name, credit) VALUES ('CARD123', 'Test User', 10);")

    except Error as e:
        print(f"Error creating tables: {e}")
        sys.exit(1)
    finally:
        cursor.close()

def main():
    """Main function"""
    print("=== Coffee Tally Database Setup ===\n")

    # Read configuration
    db_config = read_config()

    # Connect to MySQL (without database name to allow creating the DB)
    connection = None
    try:
        connection = mysql.connector.connect(
            host=db_config['host'],
            port=int(db_config['port']),
            user=db_config['user'],
            password=db_config['password']
        )

        if connection.is_connected():
            print(f"[OK] Connected to MySQL server")

            # Create database
            create_database(connection)

            # Close and reconnect with the database
            connection.close()
            connection = mysql.connector.connect(
                host=db_config['host'],
                port=int(db_config['port']),
                user=db_config['user'],
                password=db_config['password'],
                database=db_config['database']
            )

            # Create tables
            create_tables(connection)

    except Error as e:
        print(f"Error connecting to the database: {e}")
        print("\nPlease check config.json for correct connection details.")
        sys.exit(1)
    finally:
        if connection and connection.is_connected():
            connection.close()
            print("\nMySQL connection closed.")

if __name__ == "__main__":
    main()
