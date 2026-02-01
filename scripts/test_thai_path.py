# -*- coding: utf-8 -*-
from pathlib import Path
import os

# Test Thai path
path_str = r"G:\ไดรฟ์ของฉัน\Library"
print(f"Testing path: {path_str}")

# Method 1: pathlib
p = Path(path_str)
print(f"Path object: {p}")
print(f"Exists (pathlib): {p.exists()}")

# Method 2: os.path
print(f"Exists (os.path): {os.path.exists(path_str)}")
print(f"Is dir (os.path): {os.path.isdir(path_str)}")

# Method 3: Try listing
if p.exists():
    files = list(p.glob("*.pdf"))
    print(f"PDF files found: {len(files)}")
