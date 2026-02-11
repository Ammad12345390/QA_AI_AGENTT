import ast
import os
import re
from openai import OpenAI

# =========================
# Load API Key (SAFE)
# =========================
api_key = os.getenv("OPENAI_API_KEY")

client = None
if not api_key:
    print("OPENAI_API_KEY not found. LLM features disabled.")
else:
    client = OpenAI(api_key=api_key)

# =========================
# Extract Imports
# =========================
def extract_imports_from_file(file_path):
    imports = []
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read(), filename=file_path)

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.append(node.module.split(".")[0])
    except Exception as e:
        print(f"Error parsing imports in {file_path}: {e}")

    return imports


def find_local_imported_files(imports, project_root):
    local_files = []
    for root, _, files in os.walk(project_root):
        for file in files:
            if file.endswith(".py") and os.path.splitext(file)[0] in imports:
                local_files.append(os.path.join(root, file))
    return local_files


def get_file_content(filepath):
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        print(f"Error reading file {filepath}: {e}")
        return ""


def gather_enriched_context(target_file, project_root):
    print(f"\n Gathering context for {target_file} ...")

    imports = extract_imports_from_file(target_file)
    print(f"Found imports: {imports}")

    local_files = find_local_imported_files(imports, project_root)
    print(f"Local imported files: {local_files}")

    enriched_context = f"# Target File: {target_file}\n\n"
    enriched_context += get_file_content(target_file)

    for lf in local_files:
        enriched_context += f"\n\n# Context from imported module: {lf}\n\n"
        enriched_context += get_file_content(lf)

    return enriched_context   


def gather_all_project_context(project_root):
    """
    Recursively scans the project root and gathers content from relevant files
    to form a complete project context for the chatbot.
    """
    print(f"\n Gathering FULL project context from: {project_root}")
    
    context = ""
    
    # Directories to ignore
    ignore_dirs = {
        "__pycache__", ".git", ".venv", "env", "venv", "node_modules", 
        "extracted", "uploaded_projects", "tests", "generated_tests", "report"
    }
    
    # Extensions to include
    valid_extensions = {".py", ".md", ".txt", ".json", ".html", ".css", ".js"}

    for root, dirs, files in os.walk(project_root):
        # Remove ignored directories from traversal
        dirs[:] = [d for d in dirs if d not in ignore_dirs]
        
        for file in files:
            ext = os.path.splitext(file)[1].lower()
            if ext in valid_extensions:
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, project_root)
                
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        file_content = f.read()
                        
                    context += f"\n\n# File: {rel_path}\n"
                    context += "=" * 40 + "\n"
                    context += file_content + "\n"
                except Exception as e:
                    print(f"Skipping file {rel_path} due to error: {e}")
                    
    return context


# =========================
# Clean LLM Output
# =========================
def clean_test_code(raw_code):
    code_block = re.search(r"```python(.*?)```", raw_code, re.DOTALL)
    if code_block:
        return code_block.group(1).strip()

    cleaned = re.sub(
        r"(?i)^.*?(import unittest)",
        r"\1",
        raw_code,
        flags=re.DOTALL
    )
    return cleaned.strip()


# =========================
# Generate Tests (SAFE)
# =========================
def generate_tests_with_llm(enriched_context):
    if client is None:
        print(" LLM disabled. Skipping test generation.")
        return ""

    print("\n Sending context to LLM for test generation...")

    prompt = f"""
You are an expert Python test engineer. Generate a SINGLE, COMPLETE, and RUNNABLE Python unittest module with exactly 3 test cases.

STRICT REQUIREMENTS:
- Output ONLY valid Python code. Do NOT include explanations or markdown.
- The code MUST be syntactically correct and runnable using `python -m unittest`.
- Use ONLY spaces for indentation (4 spaces per level). No tabs.
- Start the file with necessary imports only.
- Each test class MUST inherit from unittest.TestCase.
- Use proper setUp() and tearDown() methods inside each class.
- Ensure all class and method indentations are correct.

TESTING REQUIREMENTS:
- Include all necessary imports.
- Cover normal cases, edge cases, and error scenarios.
- Mock external dependencies (like file I/O, sys.exit, APIs, or pygame) using unittest.mock.
- Capture stdout/stderr when testing print statements.
- Use clear and descriptive test method names.
- Skip tests gracefully if optional dependencies are unavailable.
- Dynamically locate modules using importlib, pathlib, or sys.path modification.
- Do NOT use hard-coded absolute paths.
- Ensure tests run in isolation without manual setup.

FINAL CHECK:
- Verify there are no indentation errors, missing imports, undefined variables, or syntax errors.
- Ensure the module can be executed directly with `python -m unittest` without failing due to ModuleNotFoundError.

Requirements for test coverage:
- Test normal functionality of the module.
- Test at least one edge case.
- Test at least one error scenario or exception handling.

Output ONLY the final Python code, fully runnable.

some sample are 

=======
PROJECT CONTEXT:
{enriched_context}
"""

    response = client.chat.completions.create(
        model="gpt-5-nano",
        messages=[
            {"role": "system", "content": "You are a senior Python QA engineer."},
            {"role": "user", "content": prompt},
        ],
    )

    test_code = response.choices[0].message.content
    print(" Test code generated successfully.")
    return clean_test_code(test_code)


def save_generated_tests(save_dir, target_file, test_code):
    if not test_code.strip():
        print(" No test code to save.")
        return None

    os.makedirs(save_dir, exist_ok=True)

    test_filename = f"test_{os.path.basename(target_file)}"
    test_file_path = os.path.join(save_dir, test_filename)

    with open(test_file_path, "w", encoding="utf-8") as f:
        f.write(test_code.strip())

    print(f" generated tests to: {test_file_path}")
    return test_file_path
