import ast
import os

# ------------------ PHASE 1: Deep Code Analysis ------------------
class CodeAnalyzer:
    def __init__(self, file_path):
        self.file_path = file_path
        with open(file_path, 'r') as f:
            self.code = f.read()
        self.tree = ast.parse(self.code)  
    
    def extract_functions(self):
        """Extract all functions with complexity, params, decorators"""
        functions = []
        for node in ast.walk(self.tree):
            if isinstance(node, ast.FunctionDef):
                functions.append({
                    'name': node.name,
                    "node": node,
                    'args': [arg.arg for arg in node.args.args],
                    'is_async': isinstance(node, ast.AsyncFunctionDef),
                    'decorators': [d.id if isinstance(d, ast.Name) else "" for d in node.decorator_list],
                    'complexity': self._count_branches(node),
                    'calls': self._extract_calls(node),
                    'line': node.lineno
                })
        return functions

    def _count_branches(self, node):
        count = 0
        for n in ast.walk(node):
            if isinstance(n, (ast.If, ast.For, ast.While, ast.Try, ast.With)):
                count += 1
        return count
    
    def _extract_calls(self, node):
        calls = []
        for n in ast.walk(node):
            if isinstance(n, ast.Call):
                if isinstance(n.func, ast.Name):
                    calls.append(n.func.id)
                elif isinstance(n.func, ast.Attribute):
                    calls.append(n.func.attr)
        return calls
    
    def calculate_priority(self, func):
        """Priority: complexity + 2 if async + 1 if params > 3"""
        priority = func['complexity']
        if func['is_async']:
            priority += 2
        if len(func['args']) > 3:
            priority += 1
        return priority
 
    
