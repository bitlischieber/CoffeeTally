#!/usr/bin/env python3
"""
Coffee Tally - Kaffeeguthaben-Verwaltung mit Kartenleser
"""
import pygame
import serial
import mysql.connector
from mysql.connector import Error
import json
import time
import sys
import os
from enum import Enum
from threading import Thread, Lock
import queue

# Pygame initialisieren
pygame.init()

# Farben
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
DARK_BLUE = (30, 60, 90)
LIGHT_BLUE = (70, 130, 180)
GREEN = (60, 180, 75)
RED = (220, 53, 69)
ORANGE = (255, 152, 0)
GRAY = (128, 128, 128)
LIGHT_GRAY = (200, 200, 200)
DARK_GRAY = (64, 64, 64)

class AppState(Enum):
    MAIN_SCREEN = 1
    DEDUCTING = 2
    CHARGE_AMOUNT = 3
    CHARGE_WAIT_CARD = 4
    CHARGE_CONFIRMING = 5
    SHOW_CREDIT_WAIT_CARD = 6
    SHOW_CREDIT_DISPLAY = 7

class CardReader:
    """Klasse für die Kommunikation mit dem Eltatec TWN4 Kartenleser"""
    def __init__(self, port, baudrate=9600, timeout=0.1):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.serial_connection = None
        self.last_card_id = None
        self.last_read_time = 0
        self.lock = Lock()
        
    def connect(self):
        """Stellt Verbindung zum Kartenleser her"""
        try:
            # Unter Windows COM-Ports, unter Linux /dev/ttyUSB0 oder ähnlich
            if sys.platform == 'win32':
                # Windows: COM1, COM2, etc. oder nur Nummer
                if self.port.upper().startswith('COM'):
                    port = self.port.upper()
                elif self.port.isdigit():
                    port = f'COM{self.port}'
                else:
                    port = self.port
            else:
                # Linux: /dev/ttyUSB0, /dev/ttyACM0, etc.
                if self.port.startswith('/dev/'):
                    port = self.port
                else:
                    port = f'/dev/{self.port}'
            
            self.serial_connection = serial.Serial(
                port=port,
                baudrate=self.baudrate,
                timeout=self.timeout,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE
            )
            print(f"✓ Verbindung zum Kartenleser auf {port} hergestellt")
            return True
        except Exception as e:
            print(f"FEHLER: Kann keine Verbindung zum Kartenleser herstellen: {e}")
            print(f"Hinweis: Prüfen Sie den COM-Port in config.ini")
            return False
    
    def read_card(self):
        """Liest eine Karte vom Leser (Eltatec TWN4 Protokoll)
        
        Sendet Suchbefehl "050020\r" und parst die Antwort:
        - "0000" = keine Karte
        - "[00][Bool: Result][Byte: TagType][Byte: IDBitCount][Byte Array: ID]\r" = Karte gefunden
          Beispiel: "00018320047757FC83\r" für Karte mit ID 7757FC83
        """
        if not self.serial_connection or not self.serial_connection.is_open:
            return None
        
        try:
            with self.lock:
                # Sende Suchbefehl "050020\r"
                search_command = "050020\r"
                self.serial_connection.write(search_command.encode('ascii'))
                self.serial_connection.flush()
                
                # Warte kurz auf Antwort
                time.sleep(0.05)
                
                # Lese Antwort (mit Timeout)
                if self.serial_connection.in_waiting > 0:
                    response = self.serial_connection.readline()
                    if response:
                        response_str = response.decode('ascii', errors='ignore').strip()
                        
                        # Keine Karte: "0000"
                        if response_str == "0000":
                            return None
                        
                        # Karte gefunden: Format "00018320047757FC83\r"
                        # [00][Bool: Result][Byte: TagType][Byte: IDBitCount][Byte Array: ID]
                        # Mindestens 8 Zeichen für Header + ID
                        if len(response_str) >= 8:
                            # Prüfe ob Result = 1 (Karte gefunden)
                            if len(response_str) >= 4 and response_str[2:4] == "01":
                                # IDBitCount ist das 6. Byte (Index 4-5)
                                # Die ID folgt nach dem Header
                                # Format: 00 01 [TagType 2 Hex] [IDBitCount 2 Hex] [IDLength 2 Hex] [ID ...]
                                # Beispiel: 00 01 83 20 04 7757FC83
                                # TagType: Position 4-5
                                # IDBitCount: Position 6-7 (in Hex, z.B. "20" = 32 Bits)
                                # IDLength: Position 8-9 (Anzahl Bytes, z.B. "04" = 4 Bytes)
                                # ID: Ab Position 10
                                
                                try:
                                    # IDBitCount in Hex (z.B. "20" = 32 Bits)
                                    id_bit_count_hex = response_str[6:8]
                                    id_bit_count = int(id_bit_count_hex, 16)
                                    
                                    # Anzahl Bytes = Bits / 8
                                    id_bytes = id_bit_count // 8
                                    
                                    # ID beginnt nach Header (mindestens 10 Zeichen: 00 01 XX XX XX)
                                    # Prüfe ob genug Zeichen vorhanden sind
                                    min_length = 10 + (id_bytes * 2)  # 2 Hex-Zeichen pro Byte
                                    if len(response_str) >= min_length:
                                        # Extrahiere ID (Hex-String)
                                        id_start = 10  # Nach Header und IDLength
                                        id_hex = response_str[id_start:id_start + (id_bytes * 2)]
                                        
                                        if id_hex and len(id_hex) > 0:
                                            # Konvertiere zu Großbuchstaben für Konsistenz
                                            card_id = id_hex.upper()
                                            self.last_card_id = card_id
                                            self.last_read_time = time.time()
                                            return card_id
                                except (ValueError, IndexError) as e:
                                    print(f"Fehler beim Parsen der Karten-Antwort: {e}, Antwort: {response_str}")
                                    return None
                            
                return None
                
        except Exception as e:
            print(f"Fehler beim Lesen der Karte: {e}")
            return None
    
    def close(self):
        """Schließt die Verbindung"""
        if self.serial_connection and self.serial_connection.is_open:
            self.serial_connection.close()

class Database:
    """Klasse für Datenbankoperationen"""
    def __init__(self, config):
        self.config = config
        self.connection = None
        
    def connect(self):
        """Stellt Verbindung zur MySQL-Datenbank her"""
        try:
            self.connection = mysql.connector.connect(
                host=self.config['host'],
                port=int(self.config['port']),
                user=self.config['user'],
                password=self.config['password'],
                database=self.config['database']
            )
            if self.connection.is_connected():
                print("✓ Verbindung zur MySQL-Datenbank hergestellt")
                return True
        except Error as e:
            print(f"FEHLER: Kann keine Verbindung zur Datenbank herstellen: {e}")
            return False
    
    def get_user_by_card(self, card_id):
        """Sucht Benutzer anhand der Karten-ID"""
        if not self.connection or not self.connection.is_connected():
            return None
        
        try:
            cursor = self.connection.cursor(dictionary=True)
            query = "SELECT * FROM users WHERE card_id = %s"
            cursor.execute(query, (card_id,))
            result = cursor.fetchone()
            cursor.close()
            return result
        except Error as e:
            print(f"Fehler beim Abfragen der Datenbank: {e}")
            return None
    
    def deduct_credit(self, card_id):
        """Reduziert Guthaben um 1 (erlaubt negative Guthaben)"""
        if not self.connection or not self.connection.is_connected():
            return False
        
        try:
            cursor = self.connection.cursor()
            # Entfernt die Bedingung "AND credit > 0", damit negative Guthaben möglich sind
            query = "UPDATE users SET credit = credit - 1 WHERE card_id = %s"
            cursor.execute(query, (card_id,))
            self.connection.commit()
            success = cursor.rowcount > 0
            cursor.close()
            return success
        except Error as e:
            print(f"Fehler beim Abzug des Guthabens: {e}")
            self.connection.rollback()
            return False
    
    def add_credit(self, card_id, amount):
        """Fügt Guthaben hinzu"""
        if not self.connection or not self.connection.is_connected():
            return False
        
        try:
            cursor = self.connection.cursor()
            query = "UPDATE users SET credit = credit + %s WHERE card_id = %s"
            cursor.execute(query, (amount, card_id))
            self.connection.commit()
            success = cursor.rowcount > 0
            cursor.close()
            return success
        except Error as e:
            print(f"Fehler beim Aufladen des Guthabens: {e}")
            self.connection.rollback()
            return False
    
    def create_user(self, card_id, name=None, initial_credit=0):
        """Erstellt einen neuen Benutzer in der Datenbank"""
        if not self.connection or not self.connection.is_connected():
            return False
        
        # Wenn kein Name angegeben, verwende card_id als Name
        if name is None:
            name = card_id
        
        try:
            cursor = self.connection.cursor()
            query = "INSERT INTO users (card_id, name, credit) VALUES (%s, %s, %s)"
            cursor.execute(query, (card_id, name, initial_credit))
            self.connection.commit()
            success = cursor.rowcount > 0
            cursor.close()
            if success:
                print(f"Neuer Benutzer erstellt: {name} (Card ID: {card_id})")
            return success
        except Error as e:
            print(f"Fehler beim Erstellen des Benutzers: {e}")
            self.connection.rollback()
            return False
    
    def close(self):
        """Schließt die Datenbankverbindung"""
        if self.connection and self.connection.is_connected():
            self.connection.close()

class CoffeeTallyApp:
    """Hauptklasse der Anwendung"""
    def __init__(self):
        # Lese Konfiguration
        if not os.path.exists('config.json'):
            print("FEHLER: config.json nicht gefunden!")
            sys.exit(1)
        
        with open('config.json', 'r', encoding='utf-8') as f:
            self.config = json.load(f)
        
        # Bildschirm einrichten
        # Auf Windows: Fenstermodus, auf Linux/Raspberry Pi: Vollbild
        if sys.platform == 'win32':
            # Windows: Fenster mit 1280x720 (kann angepasst werden)
            self.width = 1280
            self.height = 720
            self.screen = pygame.display.set_mode((self.width, self.height), pygame.RESIZABLE)
            pygame.display.set_caption("Coffee Tally")
        else:
            # Linux/Raspberry Pi: Vollbild (Kiosk-Modus)
            self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
            self.width, self.height = self.screen.get_size()
            pygame.display.set_caption("Coffee Tally")
        
        # Initialisiere Komponenten
        self.card_reader = CardReader(
            port=self.config['card_reader']['port'],
            baudrate=int(self.config['card_reader']['baudrate']),
            timeout=float(self.config['card_reader']['timeout'])
        )
        
        self.database = Database(self.config['database'])
        
        # Verbindungen herstellen
        if not self.card_reader.connect():
            print("WARNUNG: Kartenleser konnte nicht verbunden werden. App läuft im Testmodus.")
        
        if not self.database.connect():
            print("FEHLER: Datenbankverbindung fehlgeschlagen!")
            sys.exit(1)
        
        # App-Status
        self.state = AppState.MAIN_SCREEN
        self.clock = pygame.time.Clock()
        self.running = True
        
        # Kartenleser-Thread
        self.card_poll_interval = 1.0  # Sekunden
        self.last_poll_time = 0
        self.current_card_id = None
        self.last_card_id = None
        
        # Guthaben-Aufladen
        self.charge_amount = 1
        
        # Display-Informationen
        self.display_message = None
        self.display_user_name = None
        self.display_credit = None
        self.display_start_time = None
        self.display_duration = 5.0  # Sekunden
        
        # Fonts - Verwende System-Fonts für Unicode-Unterstützung
        # Fallback zu Standard-Font wenn kein System-Font verfügbar
        try:
            self.title_font = pygame.font.SysFont('arial', 72, bold=True)
            self.subtitle_font = pygame.font.SysFont('arial', 48)
            self.button_font = pygame.font.SysFont('arial', 40)
            self.display_font = pygame.font.SysFont('arial', 64, bold=True)
            self.small_font = pygame.font.SysFont('arial', 32)
        except:
            # Fallback zu Standard-Font
            self.title_font = pygame.font.Font(None, 72)
            self.subtitle_font = pygame.font.Font(None, 48)
            self.button_font = pygame.font.Font(None, 40)
            self.display_font = pygame.font.Font(None, 64)
            self.small_font = pygame.font.Font(None, 32)
        
        # Button-Positionen - dynamisch basierend auf Bildschirmgröße
        self.button_height = 80
        self.button_width = 400
        self.button_spacing = 30
        # Buttons weiter nach unten verschieben, um Platz für Text zu schaffen
        self.button_y = self.height // 2 + 180
        
    def poll_card_reader(self):
        """Pollt den Kartenleser"""
        current_time = time.time()
        if current_time - self.last_poll_time >= self.card_poll_interval:
            card_id = self.card_reader.read_card()
            self.last_poll_time = current_time
            
            if card_id and card_id != self.current_card_id:
                self.current_card_id = card_id
                return card_id
            elif not card_id and self.current_card_id:
                # Karte entfernt
                self.current_card_id = None
                self.last_card_id = None
        
        return self.current_card_id
    
    def handle_card_detected(self, card_id):
        """Behandelt erkannte Karte je nach Status"""
        if not card_id:
            return
        
        if self.state == AppState.MAIN_SCREEN:
            # Guthaben abziehen
            self.process_deduction(card_id)
        elif self.state == AppState.CHARGE_WAIT_CARD:
            # Guthaben aufladen
            self.process_charge(card_id)
        elif self.state == AppState.SHOW_CREDIT_WAIT_CARD:
            # Guthaben anzeigen
            self.process_show_credit(card_id)
        elif self.state in [AppState.DEDUCTING, AppState.CHARGE_CONFIRMING, AppState.SHOW_CREDIT_DISPLAY]:
            # Während der Anzeige neue Karte erkannt - abbrechen und neu verarbeiten
            if card_id != self.last_card_id:
                self.process_deduction(card_id)
    
    def process_deduction(self, card_id):
        """Verarbeitet Guthaben-Abzug (erlaubt negative Guthaben)"""
        user = self.database.get_user_by_card(card_id)
        if not user:
            # Karte nicht gefunden - automatisch hinzufügen
            if self.database.create_user(card_id, name=card_id, initial_credit=0):
                # Lade den neu erstellten Benutzer
                user = self.database.get_user_by_card(card_id)
            else:
                self.show_user_info("Fehler", 0, "Konnte Benutzer nicht erstellen!")
                self.state = AppState.DEDUCTING
                self.last_card_id = card_id
                return
        
        if user:
            if self.database.deduct_credit(card_id):
                # Aktualisiere Benutzerdaten
                user['credit'] -= 1
                # Bestimme Nachricht basierend auf Guthabenstand
                if user['credit'] < 0:
                    message = f"Guthaben abgebucht! Schulden: {abs(user['credit'])}"
                elif user['credit'] == 0:
                    message = "Guthaben abgebucht! Guthaben: 0"
                else:
                    message = "Guthaben abgebucht!"
                self.show_user_info(user['name'], user['credit'], message)
                self.state = AppState.DEDUCTING
            else:
                self.show_user_info(user['name'], user['credit'], "Fehler beim Abzug!")
                self.state = AppState.DEDUCTING
        
        self.last_card_id = card_id
    
    def process_charge(self, card_id):
        """Verarbeitet Guthaben-Aufladung"""
        user = self.database.get_user_by_card(card_id)
        if not user:
            # Karte nicht gefunden - automatisch hinzufügen
            if self.database.create_user(card_id, name=card_id, initial_credit=0):
                # Lade den neu erstellten Benutzer
                user = self.database.get_user_by_card(card_id)
            else:
                self.show_user_info("Fehler", 0, "Konnte Benutzer nicht erstellen!")
                self.state = AppState.CHARGE_CONFIRMING
                self.last_card_id = card_id
                return
        
        if user:
            if self.database.add_credit(card_id, self.charge_amount):
                # Aktualisiere Benutzerdaten
                user['credit'] += self.charge_amount
                self.show_user_info(user['name'], user['credit'], f"+{self.charge_amount} aufgeladen!")
                self.state = AppState.CHARGE_CONFIRMING
                # Schließe Modals
                self.charge_amount = 1
            else:
                self.show_user_info(user['name'], user['credit'], "Fehler beim Aufladen!")
                self.state = AppState.CHARGE_CONFIRMING
        
        self.last_card_id = card_id
    
    def process_show_credit(self, card_id):
        """Verarbeitet Guthaben-Anzeige"""
        user = self.database.get_user_by_card(card_id)
        if not user:
            # Karte nicht gefunden - automatisch hinzufügen
            if self.database.create_user(card_id, name=card_id, initial_credit=0):
                # Lade den neu erstellten Benutzer
                user = self.database.get_user_by_card(card_id)
            else:
                self.show_user_info("Fehler", 0, "Konnte Benutzer nicht erstellen!")
                self.state = AppState.SHOW_CREDIT_DISPLAY
                self.last_card_id = card_id
                return
        
        if user:
            self.show_user_info(user['name'], user['credit'], "Aktuelles Guthaben")
            self.state = AppState.SHOW_CREDIT_DISPLAY
        
        self.last_card_id = card_id
    
    def show_user_info(self, name, credit, message=""):
        """Zeigt Benutzerinformationen an"""
        self.display_user_name = name
        self.display_credit = credit
        self.display_message = message
        self.display_start_time = time.time()
    
    def check_display_timeout(self):
        """Prüft ob Display-Timeout erreicht wurde"""
        if self.display_start_time:
            elapsed = time.time() - self.display_start_time
            if elapsed >= self.display_duration:
                self.display_message = None
                self.display_user_name = None
                self.display_credit = None
                self.display_start_time = None
                if self.state != AppState.MAIN_SCREEN:
                    self.state = AppState.MAIN_SCREEN
    
    def draw_button(self, surface, x, y, width, height, text, color, hover_color=None, hover=False):
        """Zeichnet einen Button"""
        current_color = hover_color if hover and hover_color else color
        pygame.draw.rect(surface, current_color, (x, y, width, height), border_radius=15)
        pygame.draw.rect(surface, WHITE, (x, y, width, height), width=3, border_radius=15)
        
        text_surface = self.button_font.render(text, True, WHITE)
        text_rect = text_surface.get_rect(center=(x + width // 2, y + height // 2))
        surface.blit(text_surface, text_rect)
        
        return pygame.Rect(x, y, width, height)
    
    def draw_modal(self, surface, title, subtitle=""):
        """Zeichnet ein Modal-Fenster"""
        modal_width = 800
        modal_height = 500
        modal_x = (self.width - modal_width) // 2
        modal_y = (self.height - modal_height) // 2
        
        # Hintergrund mit Transparenz-Simulation (dunkler Overlay)
        overlay = pygame.Surface((self.width, self.height))
        overlay.set_alpha(200)
        overlay.fill(BLACK)
        surface.blit(overlay, (0, 0))
        
        # Modal-Fenster
        pygame.draw.rect(surface, DARK_BLUE, (modal_x, modal_y, modal_width, modal_height), border_radius=20)
        pygame.draw.rect(surface, LIGHT_BLUE, (modal_x, modal_y, modal_width, modal_height), width=4, border_radius=20)
        
        # Titel
        title_surface = self.display_font.render(title, True, WHITE)
        title_rect = title_surface.get_rect(center=(modal_x + modal_width // 2, modal_y + 100))
        surface.blit(title_surface, title_rect)
        
        # Untertitel
        if subtitle:
            subtitle_surface = self.subtitle_font.render(subtitle, True, LIGHT_GRAY)
            subtitle_rect = subtitle_surface.get_rect(center=(modal_x + modal_width // 2, modal_y + 180))
            surface.blit(subtitle_surface, subtitle_rect)
        
        return modal_x, modal_y, modal_width, modal_height
    
    def draw_charge_amount_modal(self, surface, mouse_pos):
        """Zeichnet Modal für Guthaben-Betrag"""
        modal_x, modal_y, modal_width, modal_height = self.draw_modal(
            surface, "Guthaben aufladen", "Charge credit"
        )
        
        # Up/Down Control
        control_width = 200
        control_height = 80
        control_x = modal_x + (modal_width - control_width) // 2
        control_y = modal_y + 250
        
        # Zahl anzeigen
        amount_text = str(self.charge_amount)
        amount_surface = self.display_font.render(amount_text, True, WHITE)
        amount_rect = amount_surface.get_rect(center=(control_x + control_width // 2, control_y + control_height // 2))
        pygame.draw.rect(surface, DARK_GRAY, (control_x, control_y, control_width, control_height), border_radius=10)
        surface.blit(amount_surface, amount_rect)
        
        # Up/Down Buttons (+1 / -1 und +10 / -10)
        button_size = 60
        button_spacing_horizontal = 10
        
        # +1 Button (links)
        up_rect = self.draw_button(
            surface, control_x + control_width + 20, control_y,
            button_size, button_size, "+1", GREEN, hover_color=(80, 200, 100),
            hover=self.is_point_in_rect(mouse_pos, (control_x + control_width + 20, control_y, button_size, button_size))
        )
        
        # +10 Button (rechts von +1)
        up_10_x = control_x + control_width + 20 + button_size + button_spacing_horizontal
        up_10_rect = self.draw_button(
            surface, up_10_x, control_y,
            button_size, button_size, "+10", GREEN, hover_color=(80, 200, 100),
            hover=self.is_point_in_rect(mouse_pos, (up_10_x, control_y, button_size, button_size))
        )
        
        # -10 Button (links von -1)
        down_10_x = control_x - button_size - 20 - button_size - button_spacing_horizontal
        down_10_rect = self.draw_button(
            surface, down_10_x, control_y,
            button_size, button_size, "-10", RED, hover_color=(240, 80, 90),
            hover=self.is_point_in_rect(mouse_pos, (down_10_x, control_y, button_size, button_size))
        )
        
        # -1 Button (rechts)
        down_rect = self.draw_button(
            surface, control_x - button_size - 20, control_y,
            button_size, button_size, "-1", RED, hover_color=(240, 80, 90),
            hover=self.is_point_in_rect(mouse_pos, (control_x - button_size - 20, control_y, button_size, button_size))
        )
        
        # OK und Cancel Buttons
        button_width = 150
        button_height = 60
        button_spacing = 30
        total_width = button_width * 2 + button_spacing
        start_x = modal_x + (modal_width - total_width) // 2
        
        ok_rect = self.draw_button(
            surface, start_x, modal_y + modal_height - 100,
            button_width, button_height, "OK", GREEN, hover_color=(80, 200, 100),
            hover=self.is_point_in_rect(mouse_pos, (start_x, modal_y + modal_height - 100, button_width, button_height))
        )
        
        cancel_rect = self.draw_button(
            surface, start_x + button_width + button_spacing, modal_y + modal_height - 100,
            button_width, button_height, "Abbrechen", RED, hover_color=(240, 80, 90),
            hover=self.is_point_in_rect(mouse_pos, (start_x + button_width + button_spacing, modal_y + modal_height - 100, button_width, button_height))
        )
        
        return {'up': up_rect, 'down': down_rect, 'up_10': up_10_rect, 'down_10': down_10_rect, 'ok': ok_rect, 'cancel': cancel_rect}
    
    def draw_wait_card_modal(self, surface, text, mouse_pos):
        """Zeichnet Modal zum Warten auf Karte"""
        modal_x, modal_y, modal_width, modal_height = self.draw_modal(surface, text)
        
        # Cancel Button
        button_width = 150
        button_height = 60
        cancel_x = modal_x + (modal_width - button_width) // 2
        cancel_rect = self.draw_button(
            surface, cancel_x, modal_y + modal_height - 100,
            button_width, button_height, "Abbrechen", RED, hover_color=(240, 80, 90),
            hover=self.is_point_in_rect(mouse_pos, (cancel_x, modal_y + modal_height - 100, button_width, button_height))
        )
        
        return {'cancel': cancel_rect}
    
    def is_point_in_rect(self, point, rect):
        """Prüft ob Punkt in Rechteck"""
        return rect[0] <= point[0] <= rect[0] + rect[2] and rect[1] <= point[1] <= rect[1] + rect[3]
    
    def draw_main_screen(self, surface, mouse_pos):
        """Zeichnet Hauptbildschirm"""
        # Hintergrund-Gradient
        for y in range(self.height):
            ratio = y / self.height
            r = int(DARK_BLUE[0] * (1 - ratio) + BLACK[0] * ratio)
            g = int(DARK_BLUE[1] * (1 - ratio) + BLACK[1] * ratio)
            b = int(DARK_BLUE[2] * (1 - ratio) + BLACK[2] * ratio)
            pygame.draw.line(surface, (r, g, b), (0, y), (self.width, y))
        
        # Haupttext - mit mehr Abstand zwischen englisch und deutsch
        title_en = "Show card to deduct coffee credit."
        title_de = "Karte vorhalten um Kaffeeguthaben abzubuchen"
        
        # Englischer Text weiter oben
        title_surface = self.title_font.render(title_en, True, WHITE)
        title_rect = title_surface.get_rect(center=(self.width // 2, self.height // 2 - 200))
        surface.blit(title_surface, title_rect)
        
        # Deutscher Text mit mehr Abstand zum englischen Text
        subtitle_surface = self.subtitle_font.render(title_de, True, LIGHT_GRAY)
        subtitle_rect = subtitle_surface.get_rect(center=(self.width // 2, self.height // 2 - 120))
        surface.blit(subtitle_surface, subtitle_rect)
        
        # Buttons
        button_x1 = self.width // 2 - self.button_width - self.button_spacing // 2
        button_x2 = self.width // 2 + self.button_spacing // 2
        
        charge_rect = self.draw_button(
            surface, button_x1, self.button_y,
            self.button_width, self.button_height,
            "Charge credit, Guthaben laden", LIGHT_BLUE, hover_color=(90, 150, 200),
            hover=self.is_point_in_rect(mouse_pos, (button_x1, self.button_y, self.button_width, self.button_height))
        )
        
        show_rect = self.draw_button(
            surface, button_x2, self.button_y,
            self.button_width, self.button_height,
            "Show credit / Guthaben anzeigen", ORANGE, hover_color=(255, 180, 50),
            hover=self.is_point_in_rect(mouse_pos, (button_x2, self.button_y, self.button_width, self.button_height))
        )
        
        return {'charge': charge_rect, 'show': show_rect}
    
    def draw_user_display(self, surface):
        """Zeichnet Benutzerinformationen"""
        if not self.display_user_name:
            return
        
        # Overlay
        overlay = pygame.Surface((self.width, self.height))
        overlay.set_alpha(180)
        overlay.fill(BLACK)
        surface.blit(overlay, (0, 0))
        
        # Info-Box
        box_width = 1000
        box_height = 400
        box_x = (self.width - box_width) // 2
        box_y = (self.height - box_height) // 2
        
        pygame.draw.rect(surface, DARK_BLUE, (box_x, box_y, box_width, box_height), border_radius=25)
        pygame.draw.rect(surface, LIGHT_BLUE, (box_x, box_y, box_width, box_height), width=5, border_radius=25)
        
        # Name
        name_surface = self.display_font.render(self.display_user_name, True, WHITE)
        name_rect = name_surface.get_rect(center=(box_x + box_width // 2, box_y + 120))
        surface.blit(name_surface, name_rect)
        
        # Guthaben - zeige negatives Guthaben als Schulden an
        if self.display_credit < 0:
            credit_text = f"Schulden: {abs(self.display_credit)}"
            credit_color = RED
        elif self.display_credit == 0:
            credit_text = "Guthaben: 0"
            credit_color = ORANGE
        else:
            credit_text = f"Guthaben: {self.display_credit}"
            credit_color = GREEN
        
        credit_surface = self.title_font.render(credit_text, True, credit_color)
        credit_rect = credit_surface.get_rect(center=(box_x + box_width // 2, box_y + 220))
        surface.blit(credit_surface, credit_rect)
        
        # Nachricht
        if self.display_message:
            msg_surface = self.subtitle_font.render(self.display_message, True, LIGHT_GRAY)
            msg_rect = msg_surface.get_rect(center=(box_x + box_width // 2, box_y + 300))
            surface.blit(msg_surface, msg_rect)
    
    def handle_events(self):
        """Behandelt Pygame-Events"""
        mouse_pos = pygame.mouse.get_pos()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if self.state in [AppState.CHARGE_AMOUNT, AppState.CHARGE_WAIT_CARD, AppState.SHOW_CREDIT_WAIT_CARD]:
                        self.state = AppState.MAIN_SCREEN
                        self.charge_amount = 1
                    else:
                        self.running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Linksklick
                    self.handle_click(mouse_pos)
    
    def handle_click(self, pos):
        """Behandelt Mausklicks"""
        if self.state == AppState.MAIN_SCREEN and not self.current_card_id:
            buttons = self.draw_main_screen(self.screen, pos)
            if buttons['charge'].collidepoint(pos):
                self.state = AppState.CHARGE_AMOUNT
                self.charge_amount = 1
            elif buttons['show'].collidepoint(pos):
                self.state = AppState.SHOW_CREDIT_WAIT_CARD
        
        elif self.state == AppState.CHARGE_AMOUNT:
            buttons = self.draw_charge_amount_modal(self.screen, pos)
            if buttons['up'].collidepoint(pos):
                # +1 Button
                self.charge_amount = min(self.charge_amount + 1, 100)
            elif buttons['down'].collidepoint(pos):
                # -1 Button
                self.charge_amount = max(self.charge_amount - 1, 1)
            elif buttons['up_10'].collidepoint(pos):
                # +10 Button: Springt zum nächsten Vielfachen von 10 (1->10, 10->20, 20->30, etc.)
                # Wenn bereits bei einem Vielfachen, springe zum nächsten
                next_multiple = ((self.charge_amount // 10) + 1) * 10
                self.charge_amount = min(next_multiple, 100)
            elif buttons['down_10'].collidepoint(pos):
                # -10 Button: Springt zum vorherigen Vielfachen von 10 (20->10, 10->0->1, etc.)
                prev_multiple = (self.charge_amount // 10) * 10
                if prev_multiple == self.charge_amount:
                    # Wenn bereits ein Vielfaches von 10, gehe zum vorherigen
                    prev_multiple = max(prev_multiple - 10, 0)
                if prev_multiple <= 0:
                    prev_multiple = 1
                self.charge_amount = max(prev_multiple, 1)
            elif buttons['ok'].collidepoint(pos):
                self.state = AppState.CHARGE_WAIT_CARD
            elif buttons['cancel'].collidepoint(pos):
                self.state = AppState.MAIN_SCREEN
                self.charge_amount = 1
        
        elif self.state == AppState.CHARGE_WAIT_CARD:
            buttons = self.draw_wait_card_modal(
                self.screen, "Present card to charge\nKarte vorhalten um aufzuladen", pos
            )
            if buttons['cancel'].collidepoint(pos):
                self.state = AppState.CHARGE_AMOUNT
        
        elif self.state == AppState.SHOW_CREDIT_WAIT_CARD:
            buttons = self.draw_wait_card_modal(
                self.screen, "Present card to show credit\nKarte vorhalten guthaben anzuzeigen", pos
            )
            if buttons['cancel'].collidepoint(pos):
                self.state = AppState.MAIN_SCREEN
    
    def run(self):
        """Hauptschleife der Anwendung"""
        while self.running:
            self.handle_events()
            
            # Poll Kartenleser
            card_id = self.poll_card_reader()
            if card_id:
                self.handle_card_detected(card_id)
            
            # Prüfe Display-Timeout
            self.check_display_timeout()
            
            # Zeichne Bildschirm
            self.screen.fill(BLACK)
            mouse_pos = pygame.mouse.get_pos()
            
            if self.state == AppState.MAIN_SCREEN:
                if self.display_user_name:
                    self.draw_user_display(self.screen)
                else:
                    self.draw_main_screen(self.screen, mouse_pos)
            elif self.state == AppState.CHARGE_AMOUNT:
                self.draw_main_screen(self.screen, mouse_pos)
                self.draw_charge_amount_modal(self.screen, mouse_pos)
            elif self.state == AppState.CHARGE_WAIT_CARD:
                self.draw_main_screen(self.screen, mouse_pos)
                self.draw_wait_card_modal(
                    self.screen, "Present card to charge\nKarte vorhalten um aufzuladen", mouse_pos
                )
            elif self.state == AppState.CHARGE_CONFIRMING:
                self.draw_user_display(self.screen)
            elif self.state == AppState.SHOW_CREDIT_WAIT_CARD:
                self.draw_main_screen(self.screen, mouse_pos)
                self.draw_wait_card_modal(
                    self.screen, "Present card to show credit\nKarte vorhalten guthaben anzuzeigen", mouse_pos
                )
            elif self.state in [AppState.DEDUCTING, AppState.SHOW_CREDIT_DISPLAY]:
                self.draw_user_display(self.screen)
            
            pygame.display.flip()
            self.clock.tick(60)
        
        # Cleanup
        self.card_reader.close()
        self.database.close()
        pygame.quit()

if __name__ == "__main__":
    app = CoffeeTallyApp()
    app.run()
