"""Test configuration for pytest."""

import os
import sys

# Add the parent directory to sys.path to allow importing the package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))