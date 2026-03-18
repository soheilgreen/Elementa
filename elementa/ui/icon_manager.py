import os
from PyQt6.QtGui import QIcon

# Assuming this file is in ui/
# Assets are in ../assets/ relative to this file
ASSETS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'assets')

def get_icon(name: str) -> QIcon:
    """
    Loads an icon from the assets directory.
    If the icon is not found, returns a default QIcon.
    
    Args:
        name (str): The name of the icon file (e.g., 'icon_geometry.png').
    """
    path = os.path.join(ASSETS_DIR, name)
    if os.path.exists(path):
        return QIcon(path)
    return QIcon.fromTheme("image-missing") # Fallback
