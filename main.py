"""
Main launcher for the Project Analyzer + AI Test Generation tool.
Includes:
 - ZIP extraction & project analysis
 - LLM-based test generation
 - Auto unittest verification
 - Direct Unittest execution (AI Test Executor Agent)
"""

import os
import sys
from tkinter import Tk, filedialog
from dotenv import load_dotenv
from tree.astree import ASTTree
from openai import OpenAI
from Test_executor_agent import TestExecutorAgent
from context_enricher import (
    extract_imports_from_file,
    find_local_imported_files,
    save_generated_tests,
    gather_enriched_context,
    generate_tests_with_llm,
)
from project_analyzer import find_python_entry_files, extract_zip, generate_ast_tree


load_dotenv()

PROJECT_PATH = os.path.dirname(__file__)

# =========================
# MAIN PIPELINE
# =========================
def main():
    print("\n🤖 Automated Test Generation & Execution Pipeline Started")

    # Step 1: Select ZIP file
    Tk().withdraw()
    zip_path = filedialog.askopenfilename(
        title="Select a Python Project ZIP file",
        filetypes=[("ZIP files", "*.zip")],
    )
    if not zip_path:
        print("❌ No file selected. Exiting.")
        return

    print(f"\n📁 Selected file: {zip_path}")

    # Step 2: Extract ZIP
    folder = extract_zip(zip_path)
    print(f"📂 Extracted to: {folder}")

    # Step 3: Ensure package structure
    for sub in ["", "src", "generated_tests"]:
        init_path = os.path.join(folder, sub, "__init__.py")
        os.makedirs(os.path.dirname(init_path), exist_ok=True)
        if not os.path.exists(init_path):
            open(init_path, "w").close()
    print("📦 Initialized package structure.")

    # Step 4: Analyze Python files
    entry_files = find_python_entry_files(folder)
    print(f"📝 Entry Python files: {entry_files}")

    # Optional: Analyze imports
    for py_file in entry_files:
        imports = extract_imports_from_file(py_file)
        local_files = find_local_imported_files(imports, folder)
        print(f"\nFile: {py_file}\nImports: {imports}\nLocal Files: {local_files}")

    # Step 5: Select target file for test generation
    target_file = input("\nEnter the target Python file for test generation: ").strip()
    print(f"🎯 Target file: {target_file}")
    if not os.path.exists(target_file):
        print("❌ Invalid target file path.")
        return

    # Step 5a: Generate AST for the target file
    print("\n🔍 Generating AST for the target file...")
    generate_ast_tree(target_file)

    # Step 6: Gather enriched context for LLM
    context = gather_enriched_context(target_file, folder)

    # Step 7: Generate tests using LLM
    test_code = generate_tests_with_llm(context)
    
    
    test_path = save_generated_tests(save_dir=os.path.join(folder, "generated_tests"), target_file=target_file,
    test_code=test_code)

    print("\n🧪 Generated Test Code:\n")


    print(f"✅ Tests saved at: {test_path}")

    # Step 10: Prepare environment
    abs_folder = os.path.abspath(folder)
    if abs_folder not in sys.path:
        sys.path.insert(0, abs_folder)
     
    # === Step 4: Execute tests ===
    print("\n🤖 Executing generated tests...\n")

    executor = TestExecutorAgent(project_path=PROJECT_PATH)
    result = executor.execute_tests()
    print("\nFinal Summary:", result)

if __name__ == "__main__":
    main()
