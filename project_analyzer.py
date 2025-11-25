"""
Project Analyzer — Extracts a Python project ZIP,
shows its directory tree, detects entry Python files,
and generates an Abstract Syntax Tree (AST) for analysis.
"""

import os
import shutil
import zipfile
import ast
from tkinter import Tk, filedialog


def extract_zip(zip_path, extract_to="extracted"):
    """
    Extracts the given ZIP file to a clean folder.
    If an old extracted folder exists, it will be deleted first.
    """
    if os.path.exists(extract_to):
        shutil.rmtree(extract_to)

    os.makedirs(extract_to, exist_ok=True)

    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_to)

    print(f"\n Extracted successfully to: {os.path.abspath(extract_to)}")
    return extract_to


def find_python_entry_files(folder):
    """
    Searches for main Python entry files like main.py, app.py, etc.
    Returns a list of found entry file paths.
    """
    
    entry_candidates = [
        "main.py", "app.py", "run.py", "manage.py", "index.py", "__main__.py"
    ]
    found_entries = []

    for root, _, files in os.walk(folder):
        for file in files:
            if file.lower() in entry_candidates:
                full_path = os.path.join(root, file)
                found_entries.append(full_path)

    if found_entries:
        print("\n Possible Python entry files found:")
        for f in found_entries:
            print(f"   • {f}")
    else:
        print("\n No common Python entry file found.")

    return found_entries

def generate_ast_tree(file_path):
    """
    Parses a Python file and prints a simplified AST (Abstract Syntax Tree).
    """
    print(f"\n🧠 Generating AST for: {file_path}")
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            source = f.read()

        tree = ast.parse(source, filename=file_path)

        print("\n📜 Abstract Syntax Tree:")
        print(ast.dump(tree, indent=4))  # Pretty print with indentation

    except SyntaxError as e:
        print(f"❌ Syntax error in {file_path}: {e}")
    except Exception as e:
        print(f"❌ Error generating AST: {e}")