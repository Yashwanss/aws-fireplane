import sys
import os

# Ensure src directory is in Python path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))

from main import main

if __name__ == "__main__":
    main()
