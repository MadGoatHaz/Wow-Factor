#!/usr/bin/env python3

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ui.screens.views import ViewAllScoresScreen

# Test the exact scenario from the failing test
print("Testing pagination calculation...")

# Test with 0 items
screen = ViewAllScoresScreen()
screen.total_items = 0
screen._calculate_pages()
print(f"0 items: total_pages = {screen.total_pages}, expected = 1")
assert screen.total_pages == 1

# Test with exactly one page (20 items)
screen.total_items = 20
screen._calculate_pages()
print(f"20 items: total_pages = {screen.total_pages}, expected = 1")
assert screen.total_pages == 1

# Test with multiple pages (45 items)
screen.total_items = 45  # 3 pages (20, 20, 5)
screen._calculate_pages()
print(f"45 items: total_pages = {screen.total_pages}, expected = 3")
assert screen.total_pages == 3

print("All tests passed!")