import re

def safe_filename(text):
    """Create a filesystem-safe filename from text"""
    return re.sub(r'[^a-zA-Z0-9_-]', '_', text)
