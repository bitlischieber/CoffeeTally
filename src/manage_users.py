#!/usr/bin/env python3
"""
User Management Utility
Allows adding, removing, and listing users in the coffee tally system
"""
import json
import os
import sys
from database import Database


def load_config():
    """Load configuration from config.json"""
    config_path = os.path.join(os.path.dirname(__file__), 'config.json')
    if not os.path.exists(config_path):
        print("ERROR: config.json not found")
        print("Please copy config.json.template to config.json and configure it")
        return None
    
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"ERROR: Could not load config.json: {e}")
        return None


def print_menu():
    """Print the main menu"""
    print("\n" + "="*50)
    print("Coffee Tally - User Management")
    print("="*50)
    print("1. List all users")
    print("2. Add new user")
    print("3. Update user credit")
    print("4. Delete user")
    print("5. Exit")
    print("="*50)


def list_users(db):
    """List all users"""
    users = db.get_all_users()
    if not users:
        print("\nNo users found in database")
        return
    
    print("\n" + "="*80)
    print(f"{'ID':<5} {'Card ID':<20} {'Name':<25} {'Credit':<10}")
    print("="*80)
    for user in users:
        print(f"{user['id']:<5} {user['card_id']:<20} {user['name']:<25} {user['credit']:<10}")
    print("="*80)
    print(f"Total users: {len(users)}")


def add_user(db):
    """Add a new user"""
    print("\n--- Add New User ---")
    card_id = input("Enter card ID (scan card or enter manually): ").strip()
    if not card_id:
        print("ERROR: Card ID cannot be empty")
        return
    
    name = input("Enter user name: ").strip()
    if not name:
        print("ERROR: Name cannot be empty")
        return
    
    credit_input = input("Enter initial credit (default: 0): ").strip()
    credit = int(credit_input) if credit_input.isdigit() else 0
    
    if db.add_user(card_id, name, credit):
        print(f"\n✓ User '{name}' added successfully with {credit} credits")
    else:
        print(f"\n✗ Failed to add user (card ID may already exist)")


def update_credit(db):
    """Update user credit"""
    print("\n--- Update User Credit ---")
    card_id = input("Enter card ID: ").strip()
    if not card_id:
        print("ERROR: Card ID cannot be empty")
        return
    
    user = db.get_user_by_card(card_id)
    if not user:
        print(f"ERROR: User with card ID '{card_id}' not found")
        return
    
    print(f"\nCurrent user: {user['name']}")
    print(f"Current credit: {user['credit']}")
    
    new_credit_input = input("Enter new credit amount: ").strip()
    if not new_credit_input.isdigit():
        print("ERROR: Invalid credit amount")
        return
    
    new_credit = int(new_credit_input)
    if db.update_credit(card_id, new_credit):
        print(f"\n✓ Credit updated successfully to {new_credit}")
    else:
        print(f"\n✗ Failed to update credit")


def delete_user(db):
    """Delete a user"""
    print("\n--- Delete User ---")
    card_id = input("Enter card ID to delete: ").strip()
    if not card_id:
        print("ERROR: Card ID cannot be empty")
        return
    
    user = db.get_user_by_card(card_id)
    if not user:
        print(f"ERROR: User with card ID '{card_id}' not found")
        return
    
    print(f"\nUser to delete:")
    print(f"  Name: {user['name']}")
    print(f"  Card ID: {user['card_id']}")
    print(f"  Credit: {user['credit']}")
    
    confirm = input("\nAre you sure you want to delete this user? (yes/no): ").strip().lower()
    if confirm != 'yes':
        print("Deletion cancelled")
        return
    
    try:
        if db.connection and db.connection.is_connected():
            cursor = db.connection.cursor()
            query = f"DELETE FROM {db.config['table']} WHERE card_id = %s"
            cursor.execute(query, (card_id,))
            db.connection.commit()
            cursor.close()
            print(f"\n✓ User '{user['name']}' deleted successfully")
        else:
            print("ERROR: Database not connected")
    except Exception as e:
        print(f"\n✗ Failed to delete user: {e}")


def main():
    """Main function"""
    # Load configuration
    config = load_config()
    if not config:
        sys.exit(1)
    
    # Connect to database
    db = Database(config['database'])
    if not db.connect():
        print("ERROR: Could not connect to database")
        print("Please check your config.json settings")
        sys.exit(1)
    
    print("\n✓ Connected to database successfully")
    
    # Main loop
    while True:
        print_menu()
        choice = input("\nEnter your choice (1-5): ").strip()
        
        if choice == '1':
            list_users(db)
        elif choice == '2':
            add_user(db)
        elif choice == '3':
            update_credit(db)
        elif choice == '4':
            delete_user(db)
        elif choice == '5':
            print("\nGoodbye!")
            break
        else:
            print("\nInvalid choice. Please enter 1-5")
    
    # Close database connection
    db.close()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(0)
