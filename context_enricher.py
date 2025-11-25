import ast
import os
import re
import tiktoken
from openai import OpenAI

# =========================
# Load API Key
# =========================
import os
from openai import OpenAI


api_key = os.getenv("OPENAI_API_KEY")


if not api_key:
    raise ValueError("❌ OPENAI_API_KEY is missing. Please set it as an environment variable.")

# Initialize OpenAI client
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
    print(f"\nGathering context for {target_file} ...")
    imports = extract_imports_from_file(target_file)
    print(f"Found imports: {imports}")

    local_files = find_local_imported_files(imports, project_root)
    print(f"Local imported files: {local_files}")

    enriched_context = f"# Target File: {target_file}\n\n" + get_file_content(target_file)

    for lf in local_files:
        enriched_context += f"\n\n# Context from imported module: {lf}\n\n"
        enriched_context += get_file_content(lf)


# =========================
# Clean LLM Output
# =========================
def clean_test_code(raw_code):
    code_block = re.search(r"```python(.*?)```", raw_code, re.DOTALL)
    if code_block:
        return code_block.group(1).strip()
    cleaned = re.sub(r"(?i)^.*?(import unittest)", r"\1", raw_code, flags=re.DOTALL)
    return cleaned.strip()


# =========================
# Generate Tests
# =========================
def generate_tests_with_llm(enriched_context):
    print("\n🧠 Sending context to LLM for test generation...")

    prompt = f"""
You are an expert Python test engineer.

Task:
- Generate runnable **unittest** test code for this project.
- Focus on testing all **functions and classes** in the provided context.
- Cover **normal behavior, edge cases, and error handling** where applicable.
- Ensure correct **import paths** relative to the project.
- Capture **stdout** output if the function prints anything.
- Each test case must have a **descriptive name** and docstring.
- Output **only Python code**, no explanations or markdown.

<<<<<<< HEAD
import unittest
from io import StringIO
import sys
import importlib
from extracted.src import app

class TestAppModule(unittest.TestCase):
    def test_app_prints_message_on_import(self):
        captured_output = StringIO()
        sys.stdout = captured_output
        importlib.reload(app)  # Reload to capture print output again
        sys.stdout = sys.__stdout__
        self.assertIn('App module running', captured_output.getvalue())

if __name__ == "__main__":
    unittest.main()
    
=======
# Project Context:
----------------
{enriched_context}
"""

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "system", "content": "You are a senior Python QA engineer."},
            {"role": "user", "content": prompt},
        ]
    )

    test_code = response.choices[0].message.content
    print("\n✅ Test code generated successfully.")
    return clean_test_code(test_code)



def save_generated_tests(save_dir, target_file, test_code):
    import os
    os.makedirs(save_dir, exist_ok=True)
    test_filename = f"test_{os.path.basename(target_file)}"
    test_file_path = os.path.join(save_dir, test_filename)

    with open(test_file_path, "w", encoding="utf-8") as f:
        f.write(test_code.strip())

    print(f"\n💾 Saved generated tests to: {test_file_path}")
    return test_file_path


