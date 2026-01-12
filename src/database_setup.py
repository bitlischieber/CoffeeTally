#!/usr/bin/env python3
"""
Skript zum Einrichten der MySQL-Datenbank für Coffee Tally
"""
import mysql.connector
from mysql.connector import Error
import json
import sys
import os

def read_config():
    """Liest die Konfigurationsdatei"""
    if not os.path.exists('config.json'):
        print("FEHLER: config.json nicht gefunden!")
        print("Bitte erstelle die config.json Datei mit den Datenbankverbindungsdetails.")
        sys.exit(1)
    
    with open('config.json', 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    return config['database']

def create_database(connection):
    """Erstellt die Datenbank falls sie nicht existiert"""
    cursor = connection.cursor()
    db_name = read_config()['database']
    
    try:
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_name}")
        print(f"Datenbank '{db_name}' wurde erfolgreich erstellt oder existiert bereits.")
    except Error as e:
        print(f"Fehler beim Erstellen der Datenbank: {e}")
        sys.exit(1)
    finally:
        cursor.close()

def create_tables(connection):
    """Erstellt die notwendigen Tabellen"""
    cursor = connection.cursor()
    db_name = read_config()['database']
    
    try:
        # Verwende die Datenbank
        cursor.execute(f"USE {db_name}")
        
        # Tabelle für Benutzer und Guthaben
        create_users_table = """
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            card_id VARCHAR(50) UNIQUE NOT NULL,
            name VARCHAR(100) NOT NULL,
            credit INT DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        )
        """
        
        cursor.execute(create_users_table)
        print("Tabelle 'users' wurde erfolgreich erstellt oder existiert bereits.")
        
        connection.commit()
        print("\n[OK] Datenbank-Setup erfolgreich abgeschlossen!")
        print(f"\nSie können nun Testbenutzer hinzufügen mit:")
        print(f"  INSERT INTO {db_name}.users (card_id, name, credit) VALUES ('CARD123', 'Test User', 10);")
        
    except Error as e:
        print(f"Fehler beim Erstellen der Tabellen: {e}")
        sys.exit(1)
    finally:
        cursor.close()

def main():
    """Hauptfunktion"""
    print("=== Coffee Tally Datenbank-Setup ===\n")
    
    # Lese Konfiguration
    db_config = read_config()
    
    # Verbindung zur MySQL (ohne Datenbankname, um die DB erstellen zu können)
    connection = None
    try:
        connection = mysql.connector.connect(
            host=db_config['host'],
            port=int(db_config['port']),
            user=db_config['user'],
            password=db_config['password']
        )
        
        if connection.is_connected():
            print(f"[OK] Verbindung zu MySQL-Server erfolgreich")
            
            # Erstelle Datenbank
            create_database(connection)
            
            # Schließe Verbindung und verbinde erneut mit der Datenbank
            connection.close()
            connection = mysql.connector.connect(
                host=db_config['host'],
                port=int(db_config['port']),
                user=db_config['user'],
                password=db_config['password'],
                database=db_config['database']
            )
            
            # Erstelle Tabellen
            create_tables(connection)
            
    except Error as e:
        print(f"Fehler bei der Datenbankverbindung: {e}")
        print("\nBitte überprüfen Sie die config.json Datei mit den korrekten Verbindungsdaten.")
        sys.exit(1)
    finally:
        if connection and connection.is_connected():
            connection.close()
            print("\nMySQL-Verbindung geschlossen.")

if __name__ == "__main__":
    main()
