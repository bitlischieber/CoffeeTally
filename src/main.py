#!/usr/bin/env python3
"""
Coffee Tally - Kivy Version
Coffee credit management with card reader
"""
from datetime import datetime, timezone

from kivy.lang import Builder
from kivy.factory import Factory
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.properties import StringProperty, NumericProperty

from kivymd.app import MDApp
from kivymd.uix.button import MDRaisedButton, MDFlatButton
from kivymd.uix.dialog import MDDialog

import json
import logging
import os
import sys
import time
from threading import Thread, Lock
from enum import Enum
from kivy.clock import mainthread

from card_reader import CardReader
from database import Database
from error_logging import setup_error_logging


class CardMode(Enum):
    IDLE = "idle"
    CHARGE = "charge"
    SHOW_CREDIT = "show_credit"


class CoffeeTallyApp(MDApp):
    """Main application class"""
    
    # Properties for UI binding
    main_text = StringProperty("Show card to deduct coffee credit.")
    charge_amount = NumericProperty(1)
    wait_prompt_text = StringProperty("")
    error_text = StringProperty("")
    version_text = StringProperty("v0.1.2.1")
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.config_data = None
        self.card_reader = None
        self.last_card_id = None
        self.database = None
        self.current_dialog = None
        self.display_timer = None
        self.card_poll_event = None
        self.lock = Lock()
        self.reading_card = False  # Thread guard to prevent multiple simultaneous card reads
        self.waiting_for_card = False
        self.card_mode = CardMode.IDLE
        self.version_tap_count = 0
        self.version_tap_start = None
        
    def build(self):
        """Build the application UI"""
        kv_path = os.path.join(os.path.dirname(__file__), "main.kv")
        Builder.load_file(kv_path)

        # Configure window based on platform
        # Windows: Fixed size window (1280x720)
        # Linux/Raspberry Pi: Fullscreen (1280x720)
        if sys.platform == 'win32':
            # Windows: Fixed size window
            Window.size = (1280, 720)
            Window.fullscreen = False
        else:
            # Linux/Raspberry Pi: Fullscreen
            Window.size = (1280, 720)
            Window.fullscreen = True
        
        # Set theme
        self.theme_cls.primary_palette = "Blue"
        self.theme_cls.primary_hue = "700"
        self.theme_cls.theme_style = "Light"
        
        # Load configuration
        if not self.load_config():
            self.show_error_dialog(
                "Configuration Error",
                "Could not load config.json. Please check the file exists and is valid."
            )
            self.error_text = "Application Error\nPlease check configuration and restart"
            return Factory.ErrorLayout()
        
        # Initialize card reader
        self.card_reader = CardReader(
            port=self.config_data['card_reader']['port'],
            baudrate=self.config_data['card_reader']['baudrate'],
            timeout=self.config_data['card_reader']['timeout']
        )
        
        if not self.card_reader.connect():
            self.show_error_dialog("Card Reader Error", 
                                   "Could not connect to card reader. Check COM port in config.json")
        
        # Initialize database
        self.database = Database(self.config_data['database'])
        if not self.database.connect():
            self.show_error_dialog("Database Error", 
                                   "Could not connect to database. Check settings in config.json")
        
        # Start card polling
        self.card_poll_event = Clock.schedule_interval(self.poll_card_reader, 0.75)
        
        return Factory.RootLayout()
    
    def load_config(self):
        """Load configuration from config.json"""
        config_path = os.path.join(os.path.dirname(__file__), 'config.json')
        if not os.path.exists(config_path):
            print(f"ERROR: config.json not found at {config_path}")
            return False
        
        try:
            with open(config_path, 'r') as f:
                self.config_data = json.load(f)
            return True
        except Exception as e:
            logging.exception("Could not load config.json: %s", e)
            return False

    
    def poll_card_reader(self, dt):
        """Poll the card reader for cards"""
        if not self.card_reader or not self.card_reader.serial_connection:
            return
        
        # Read card in background thread to avoid blocking UI
        # Only start a new thread if no read operation is currently in progress
        if not self.reading_card:
            Thread(target=self._read_card_thread, daemon=True).start()
    
    def _read_card_thread(self):
        """Read card in background thread"""
        # Double-check to prevent race conditions
        if self.reading_card:
            logging.debug("Card read already in progress, skipping")
            return
        
        self.reading_card = True
        try:
            logging.debug("Card read thread started")
            card_id = self.card_reader.read_card()
            logging.debug(f"Card read result: {card_id}")
            
            if card_id and card_id != self.last_card_id:
                self.last_card_id = card_id
                # Schedule UI update on main thread
                Clock.schedule_once(lambda dt: self.on_card_detected(card_id), 0)
            if card_id is None:
                self.last_card_id = None  # Reset last card ID when no card is present
        except Exception as e:
            logging.exception(f"Error reading card: {e}")
        finally:
            self.reading_card = False
            logging.debug("Card read thread finished")
                
    @mainthread
    def on_card_detected(self, card_id):
        """Handle card detection"""
        print(f"Card detected: {card_id}")

        if self.current_dialog and self.card_mode == CardMode.IDLE:
            # Ignore card scans while a non-action dialog is open.
            return
        
        self.card_reader.beep()        
        if self.card_mode == CardMode.CHARGE:
            # Charging credit
            self.process_charge_card(card_id)
        elif self.card_mode == CardMode.SHOW_CREDIT:
            # Showing credit
            self.process_show_credit_card(card_id)
        else:
            # Normal deduction
            self.process_deduct_coffee(card_id)
    
    def process_deduct_coffee(self, card_id):
        """Process coffee deduction"""
        user = self.database.get_user_by_card(card_id)
        
        if user:
            # Deduct one coffee
            new_credit = user['credit'] - 1
            self.database.update_credit(card_id, new_credit)
            
            # Show user info
            self.display_user_info(user['name'], new_credit)
        else:
            # Card not found
            if self.database.add_user(card_id, card_id, initial_credit=0):
                # Deduct one coffee from the initial 0 credit
                new_credit = -1
                self.database.update_credit(card_id, new_credit)
                self.display_user_info(card_id, new_credit)
            else:
                self.show_info_dialog(
                    "Card Not Found",
                    "Card not registered in system."
                )
    
    def process_charge_card(self, card_id):
        """Process charging credit to card"""
        user = self.database.get_user_by_card(card_id)
        
        if user:
            # Add credit
            new_credit = user['credit'] + self.charge_amount
            self.database.update_credit(card_id, new_credit)
            
            # Close any open dialogs
            if self.current_dialog:
                self.current_dialog.dismiss()
                self.current_dialog = None
            
            # Reset mode
            self.card_mode = CardMode.IDLE
            
            # Show user info
            self.display_user_info(user['name'], new_credit)
        else:
            # Card not found
            if self.current_dialog:
                self.current_dialog.dismiss()
            self.card_mode = CardMode.IDLE
            self.show_info_dialog("Card Not Found", 
                                  "Card not registered in system.")
    
    def process_show_credit_card(self, card_id):
        """Process showing credit for card"""
        user = self.database.get_user_by_card(card_id)
        
        if user:            
            # Close any open dialogs
            if self.current_dialog:
                self.current_dialog.dismiss()
                self.current_dialog = None
            
            # Reset mode
            self.card_mode = CardMode.IDLE
            
            # Show user info
            self.display_user_info(user['name'], user['credit'], user['updated_at'], True)
        else:
            # Card not found
            if self.current_dialog:
                self.current_dialog.dismiss()
            self.card_mode = CardMode.IDLE
            self.show_info_dialog("Card Not Found", 
                                  "Card not registered in system.")
            
    def display_user_info(self, name, credit, last_update_date_time : datetime = None, accent_color=False):
        """Display user information for 5 seconds"""
        # Cancel any existing timer
        if self.display_timer:
            self.display_timer.cancel()
        
        # Update and show user info
        if last_update_date_time:
            # Convert UTC to local time
            local_time = last_update_date_time.replace(tzinfo=timezone.utc).astimezone()
            self.root.ids.user_info_label.text = f"{name}\nCredit: {credit} coffees\nLast credit update: {local_time.strftime('%Y-%m-%d %H:%M')}"
        else:
            self.root.ids.user_info_label.text = f"{name}\nCredit: {credit} coffees"
        self.root.ids.user_info_card.opacity = 1
        self.root.ids.main_label.opacity = 0
        
        if accent_color:
            self.root.ids.user_info_card.md_bg_color = self.theme_cls.accent_color
        else:
            self.root.ids.user_info_card.md_bg_color = self.theme_cls.primary_color
            
        # Schedule hide after 5 seconds
        self.display_timer = Clock.schedule_once(self.hide_user_info, 5.0)
    
    def hide_user_info(self, dt):
        """Hide user info and return to main screen"""
        self.root.ids.user_info_card.opacity = 0
        self.root.ids.main_label.opacity = 1

    def on_version_tap(self, widget, touch):
        """Quit the app after 5 taps within 10 seconds on the version label."""
        if not widget.collide_point(*touch.pos):
            return False

        now = time.monotonic()
        if self.version_tap_start is None or (now - self.version_tap_start) > 10:
            self.version_tap_start = now
            self.version_tap_count = 1
        else:
            self.version_tap_count += 1

        if self.version_tap_count >= 5:
            self.stop()
        return True
    
    def show_charge_dialog(self, instance):
        """Show dialog to set charge amount"""
        self.charge_amount = 1  # Reset to default charge amount---
        content = Factory.ChargeDialogContent()
        self.current_dialog = MDDialog(
            title="Charge Credit",
            type="custom",            
            content_cls=content,
            buttons=[
                MDFlatButton(
                    text="CANCEL",
                    font_size=20,
                    on_release=lambda x: self.dismiss_dialog()
                ),
                MDRaisedButton(
                    text="OK",
                    font_size=20,
                    on_release=lambda x: self.show_charge_card_prompt()
                ),
            ],
        )
        self.current_dialog.open()
    
    def change_charge_amount(self, delta):
        """Change the charge amount"""
        if delta == 10 and self.charge_amount == 1:
            self.charge_amount = 10
            return
        self.charge_amount = max(1, self.charge_amount + delta)
    
    def show_charge_card_prompt(self):
        """Show dialog prompting user to present card for charging"""
        if self.current_dialog:
            self.current_dialog.dismiss()
        
        self.wait_prompt_text = "Present card to charge"
        content = Factory.WaitCardDialogContent()
        
        self.current_dialog = MDDialog(
            title="Waiting for Card",
            type="custom",
            content_cls=content,
            buttons=[
                MDFlatButton(
                    text="CANCEL",
                    font_size=20,
                    on_release=lambda x: self.cancel_charge()
                ),
            ],
        )
        self.current_dialog.open()
        self.card_mode = CardMode.CHARGE
    
    def cancel_charge(self):
        """Cancel charging operation"""
        self.card_mode = CardMode.IDLE
        self.dismiss_dialog()
    
    def show_credit_dialog(self, instance):
        """Show dialog prompting user to present card to show credit"""
        self.wait_prompt_text = "Present card to show credit"
        content = Factory.WaitCardDialogContent()
        
        self.current_dialog = MDDialog(
            title="Show Credit",
            type="custom",
            content_cls=content,
            buttons=[
                MDFlatButton(
                    text="CANCEL",
                    font_size=20,
                    on_release=lambda x: self.cancel_show_credit()
                ),
            ],
        )
        self.current_dialog.open()
        self.card_mode = CardMode.SHOW_CREDIT
    
    def cancel_show_credit(self):
        """Cancel show credit operation"""
        self.card_mode = CardMode.IDLE
        self.dismiss_dialog()
    
    def dismiss_dialog(self):
        """Dismiss the current dialog"""
        if self.current_dialog:
            self.current_dialog.dismiss()
            self.current_dialog = None
    
    def show_error_dialog(self, title, message):
        """Show an error dialog"""
        dialog = MDDialog(
            title=title,
            text=message,
            buttons=[
                MDFlatButton(
                    text="OK",
                    on_release=lambda x: dialog.dismiss()
                ),
            ],
        )
        dialog.open()
    
    def show_info_dialog(self, title, message):
        """Show an info dialog"""
        dialog = MDDialog(
            title=title,
            text=message,
            buttons=[
                MDFlatButton(
                    text="OK",
                    on_release=lambda x: dialog.dismiss()
                ),
            ],
        )
        dialog.open()
    
    def on_stop(self):
        """Clean up when app closes"""
        if self.card_poll_event:
            self.card_poll_event.cancel()
        
        if self.card_reader:
            self.card_reader.close()
        
        if self.database:
            self.database.close()


if __name__ == '__main__':
    setup_error_logging()
    CoffeeTallyApp().run()
