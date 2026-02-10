#!/usr/bin/env python3
"""
Database backup script for Coffee Tally
Creates INSERT statements for all database entries
"""
import mysql.connector
from mysql.connector import Error
import json
import sys
import os
from datetime import datetime

def read_config():
    """Read the configuration file"""
    if not os.path.exists('config.json'):
        print("ERROR: config.json not found!")
        print("Please create config.json with the database connection details.")
        sys.exit(1)

    with open('config.json', 'r', encoding='utf-8') as f:
        config = json.load(f)

    return config['database']

def escape_sql_value(value):
    """Escape value for SQL INSERT statement"""
    if value is None:
        return 'NULL'
    elif isinstance(value, str):
        # Escape single quotes by doubling them
        return f"'{value.replace(chr(39), chr(39)*2)}'"
    elif isinstance(value, datetime):
        # Format datetime as string
        return f"'{value.strftime('%Y-%m-%d %H:%M:%S')}'"
    else:
        return str(value)

def create_backup():
    """Create database backup with INSERT statements"""
    print("=== Coffee Tally Database Backup ===\n")

    # Read configuration
    db_config = read_config()

    # Connect to MySQL
    connection = None
    cursor = None
    try:
        connection = mysql.connector.connect(
            host=db_config['host'],
            port=int(db_config['port']),
            user=db_config['user'],
            password=db_config['password'],
            database=db_config['database']
        )

        if connection.is_connected():
            print(f"[OK] Connected to MySQL database '{db_config['database']}'")

            cursor = connection.cursor()

            # Get table name
            table_name = db_config['table']

            # Select all data from the table
            query = f"SELECT * FROM {table_name}"
            cursor.execute(query)

            # Get column names
            column_names = [desc[0] for desc in cursor.description]

            # Fetch all rows
            rows = cursor.fetchall()

            if not rows:
                print(f"No data found in table '{table_name}'")
                return

            print(f"Found {len(rows)} records in table '{table_name}'")

            # Create timestamp for filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"db_back_{timestamp}.sql"

            # Write backup file
            with open(filename, 'w', encoding='utf-8') as f:
                # Write header
                f.write(f"-- Coffee Tally Database Backup\n")
                f.write(f"-- Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"-- Database: {db_config['database']}\n")
                f.write(f"-- Table: {table_name}\n")
                f.write(f"-- Records: {len(rows)}\n\n")

                # Write USE statement
                f.write(f"USE {db_config['database']};\n\n")

                # Write INSERT statements
                for row in rows:
                    values = [escape_sql_value(value) for value in row]
                    values_str = ', '.join(values)
                    columns_str = ', '.join(column_names)

                    insert_stmt = f"INSERT INTO {table_name} ({columns_str}) VALUES ({values_str});\n"
                    f.write(insert_stmt)

            print(f"\n[OK] Backup created successfully: {filename}")
            print(f"File location: {os.path.abspath(filename)}")

    except Error as e:
        print(f"Error during backup: {e}")
        sys.exit(1)
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()
            print("\nMySQL connection closed.")

if __name__ == "__main__":
    create_backup()