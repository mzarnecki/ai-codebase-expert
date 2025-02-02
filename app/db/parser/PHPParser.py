import re

class PHPParser:
    def __init__(self):
        pass

    def parse_code(self, code):
        if not code or not code.startswith('<?php'):
            return {
                "class_name": None,
                "parent_class": None,
                "methods": None,
                "dependencies": None,
            }
        result = {
            "class_name": self.extract_class_name(code),
            "parent_class": self.extract_parent_class(code),
            "methods": self.extract_methods(code),
            "dependencies": self.extract_dependencies(code),
        }
        return result

    def extract_class_name(self, code)->str|None:
        match = re.search(r'class\s+(\w+)', code)
        return match.group(1) if match else None

    def extract_parent_class(self, code)->str|None:
        match = re.search(r'extends\s+([^\s{]+)', code)
        return match.group(1).strip() if match else None

    def extract_methods(self, code)->list:
        matches = re.findall(r'(?:public|protected|private|static)?\s*function\s+(\w+)\s*\(', code)
        return matches if matches else []

    def extract_dependencies(self, code)->str|None:
        dependencies = []
        use_statements = re.findall(r'use\s+([^;]+?)(?:\s+as\s+\w+)?\s*;', code)
        for use_stmt in use_statements:
            parts = use_stmt.strip().split('\\')
            if len(parts) >= 2:
                dep = '/'.join(parts[-2:])
            else:
                dep = parts[-1]
            dependencies.append(dep)
        return dependencies