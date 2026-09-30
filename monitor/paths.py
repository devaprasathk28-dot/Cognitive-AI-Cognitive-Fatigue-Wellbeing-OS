import os
import sys

BASE_DIR = getattr(sys, "_MEIPASS", os.path.dirname(os.path.dirname(__file__)))

def get_data_path(filename):
    return os.path.join(BASE_DIR, "data", filename)