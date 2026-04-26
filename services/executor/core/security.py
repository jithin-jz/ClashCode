import ast
import logging
from typing import List, Tuple

logger = logging.getLogger(__name__)

# Standard blocked modules for a coding challenge environment
BLOCKED_MODULES = {
    "os",
    "subprocess",
    "socket",
    "shutil",
    "pathlib",
    "ctypes",
    "multiprocessing",
    "threading",
    "asyncio",
    "http",
    "urllib",
    "requests",
    "ftplib",
    "telnetlib",
    "ssl",
    "sys",
    "platform",
}

# Dangerous functions that allow code execution or environment escape
BLOCKED_FUNCTIONS = {
    "eval",
    "exec",
    "compile",
    "open",
    "getattr",
    "setattr",
    "delattr",
    "help",
    "globals",
    "locals",
    "vars",
    "breakpoint",
}


class CodeSecurityValidator(ast.NodeVisitor):
    def __init__(self):
        self.errors = []

    def visit_Import(self, node):
        for alias in node.names:
            if alias.name.split(".")[0] in BLOCKED_MODULES:
                self.errors.append(f"Import of module '{alias.name}' is blocked.")
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        if node.module and node.module.split(".")[0] in BLOCKED_MODULES:
            self.errors.append(f"Import from module '{node.module}' is blocked.")
        self.generic_visit(node)

    def visit_Call(self, node):
        # Block dangerous function calls
        if isinstance(node.func, ast.Name):
            if node.func.id in BLOCKED_FUNCTIONS:
                self.errors.append(f"Call to function '{node.func.id}' is blocked.")

        # Block dynamic imports via __import__
        elif isinstance(node.func, ast.Attribute):
            if node.func.attr == "__import__":
                self.errors.append("Dynamic imports via __import__ are blocked.")

        self.generic_visit(node)

    def visit_Attribute(self, node):
        # Block common jailbreak attributes
        if node.attr in ("__subclasses__", "__globals__", "__builtins__", "__mro__"):
            self.errors.append(f"Access to attribute '{node.attr}' is blocked.")
        self.generic_visit(node)


def validate_code_safety(code: str) -> Tuple[bool, List[str]]:
    """
    Performs Abstract Syntax Tree analysis to detect dangerous patterns.
    Returns (is_safe, error_messages)
    """
    try:
        tree = ast.parse(code)
        validator = CodeSecurityValidator()
        validator.visit(tree)

        if validator.errors:
            return False, validator.errors
        return True, []
    except SyntaxError as e:
        return False, [f"Syntax Error: {e.msg} at line {e.lineno}"]
    except Exception as e:
        logger.error(f"AST Analysis failed: {e}")
        return False, ["Failed to analyze code security."]
