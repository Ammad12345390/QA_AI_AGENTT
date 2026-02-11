"""
Main launcher for the Project Analyzer + AI Test Generation tool.

Includes:
 - ZIP extraction & project analysis
 - AST generation
 - Deep code analysis
 - LLM-based test generation  
 - Auto unittest verification
 - Direct Unittest execution
 - AI-Based Test Reporting Agent
"""

import os
import sys
from tkinter import Tk, filedialog
from dotenv import load_dotenv
from tree.astree import ASTTree
from Test_executor_agent import TestExecutorAgent
from reporting_agent import ReportingAgent
from context_enricher import (
    extract_imports_from_file,
    find_local_imported_files,
    save_generated_tests,
    gather_enriched_context,
    generate_tests_with_llm
)
from project_analyzer import find_python_entry_files, extract_zip, generate_ast_tree
from code_analyzer import CodeAnalyzer

load_dotenv()
PROJECT_PATH = os.path.dirname(__file__)

# ------------------ MAIN PIPELINE ------------------
def main():
    print("\n🤖 Automated Test Generation & Execution Pipeline Started")

    # Step 1: Select ZIP file
    Tk().withdraw()
    zip_path = filedialog.askopenfilename(
        title="Select a Python Project ZIP file",
        filetypes=[("ZIP files", "*.zip")],
    )

    if not zip_path:
        print(" No file selected. Exiting.")
        return

    print(f"\n Selected file: {zip_path}")

    # Step 2: Extract ZIP
    folder = extract_zip(zip_path)
    print(f" Extracted to: {folder}")

    # Step 3: Ensure package structure
    for sub in ["", "src", "generated_tests"]:
        init_path = os.path.join(folder, sub, "__init__.py")
        os.makedirs(os.path.dirname(init_path), exist_ok=True)
        if not os.path.exists(init_path):
            open(init_path, "w").close()

    print("Initialized package structure.")

    # Step 4: Find Python entry files
    entry_files = find_python_entry_files(folder)
    print(f" Entry Python files detected: {entry_files}")

    # Step 4a: Analyze imports
    for py_file in entry_files:
        imports = extract_imports_from_file(py_file)
        local_files = find_local_imported_files(imports, folder)

        print(f"\n File: {py_file}")
        print(f"    Imports: {imports}")
        print(f"    Local Files: {local_files}")

    # Step 5: Select target Python file
    target_file = input("\nEnter the target Python file for test generation: ").strip()
    if not os.path.exists(target_file):
        print("❌ Invalid target file path. Exiting.")
        return

    print(f"🎯 Target file: {target_file}")

    # ----------------- Step 5a: Generate AST Tree -----------------
    print("\n🌳 Generating AST Tree...")
    try:
        ast_tree_path = generate_ast_tree(target_file)
        print(f"🌲 AST Tree generated at: {ast_tree_path}")
    except Exception as e:
        print(f"⚠️ AST generation failed: {e}")
        return

    # ----------------- Step 5b: Deep Code Analysis -----------------
    print("\n🔍 Running Deep Code Analyzer...")
    analyzer = CodeAnalyzer(target_file)
    functions = analyzer.extract_functions()
    for func in functions:
        func["priority"] = analyzer.calculate_priority(func)

    ranked_functions = sorted(functions, key=lambda x: x["priority"], reverse=True)

    print("\n📌 Functions Found (sorted by priority):")
    for idx, fn in enumerate(ranked_functions, start=1):
        print(
            f"{idx}. {fn['name']} "
            f"(Priority: {fn['priority']}, "
            f"Complexity: {fn['complexity']}, "
            f"Args: {fn['args']})"
        )

    # ----------------- Step 6: Gather Enriched Context -----------------
    print("\n Gathering enriched LLM execution context...")
    context = gather_enriched_context(target_file, folder)

    # ----------------- Step 7: Generate Tests via LLM -----------------
    print("\n Generating tests using LLM...")
    test_code = generate_tests_with_llm(context)

    # ----------------- Step 8: Save Generated Tests -----------------
    print("\n Saving generated tests...")
    test_path = save_generated_tests(
        save_dir=os.path.join(folder, "generated_tests"),
        target_file=target_file,
        test_code=test_code,
    )
    print(f" Test file saved at: {test_path}")

    # ----------------- Step 9: Prepare Environment -----------------
    abs_folder = os.path.abspath(folder)
    if abs_folder not in sys.path:
        sys.path.insert(0, abs_folder)

    # ----------------- Step 10: Execute Tests -----------------
    print("\n Executing generated tests...\n")
    executor = TestExecutorAgent(project_path=PROJECT_PATH)
    test_results = executor.execute_tests()

    print("\n Test Execution Summary:")
    print(test_results)

    # ----------------- Step 11: AI Reporting Agent -----------------
    print("\n Generating AI Test Report...")

    log_path = test_results.get("log_report")
    if not log_path or not os.path.exists(log_path):
        print(" Test log not found. Skipping report generation.")
        return

    # Initialize Reporting Agent
    reporter = ReportingAgent(log_path)

    # Step 1: Parse logs
    summary = reporter.parse_unittest_log()

    # Step 2: Optional AI analysis
    ai_analysis = reporter.analyze_with_llm(summary)

    # Step 3: Generate Markdown report
    markdown_report = reporter.generate_markdown_report(summary, ai_analysis)
    md_path = reporter.save_markdown_report(markdown_report)
    print(f"\n Markdown report saved at: {md_path.resolve()}")

    # Step 4: Generate PDF report
    pdf_path = os.path.join(folder, "ai_test_report.pdf")
    reporter.generate_pdf_report(pdf_path)
    print(f"\n PDF report saved at: {os.path.abspath(pdf_path)}")


if __name__ == "__main__":
    main()
