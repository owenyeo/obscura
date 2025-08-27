import sys
from pathlib import Path

# Add the backend folder to sys.path so "src.*" imports work
sys.path.append(str(Path(__file__).resolve().parents[1]))