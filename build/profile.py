from pathlib import Path
from tkinter import Tk, Canvas, Button, PhotoImage, Frame, Label, Entry, messagebox
import mysql.connector
from utils import UtilityFunctions
import sys
import os

OUTPUT_PATH = Path(__file__).parent

def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    
    return os.path.join(base_path, relative_path)

def relative_to_assets(path: str) -> Path:
    return Path(resource_path(f"resources/assets/frame8/{path}"))  # Adjust frame number as needed

class ProfileWindow:
    def __init__(self, parent, user_data, back_callback, get_db_connection):
        self.parent = parent
        self.user_data = user_data
        self.back_callback = back_callback
        self.get_db_connection = get_db_connection
        
        self.setup_ui()

    # ... rest of your profile.py code