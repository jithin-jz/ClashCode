"""
Static pre-check for learner code.

This is an early, friendly rejection of obviously dangerous code. It is NOT the
security boundary: Python cannot be sandboxed by inspecting source. Isolation
comes from the sandbox process (clean env, rlimits, no network) and the pod/
container it runs in. Keep this list conservative so valid solutions still pass.
"""

import ast
import logging

logger = logging.getLogger(__name__)

# Modules that give access to the OS, the interpreter internals, or the network.
BLOCKED_MODULES = {
    "asyncio",
    "builtins",
    "code",
    "codeop",
    "concurrent",
    "ctypes",
    "fcntl",
    "ftplib",
    "gc",
    "glob",
    "http",
    "importlib",
    "inspect",
    "io",
    "marshal",
    "mmap",
    "multiprocessing",
    "os",
    "pathlib",
    "pickle",
    "platform",
    "pty",
    "requests",
    "resource",
    "runpy",
    "select",
    "selectors",
    "shutil",
    "signal",
    "socket",
    "ssl",
    "subprocess",
    "sys",
    "telnetlib",
    "tempfile",
    "threading",
    "urllib",
    "zipimport",
}

# Builtins that allow dynamic code execution, file access or introspection.
BLOCKED_FUNCTIONS = {
    "__import__",
    "breakpoint",
    "compile",
    "delattr",
    "eval",
    "exec",
    "exit",
    "getattr",
    "globals",
    "help",
    "locals",
    "open",
    "quit",
    "setattr",
    "vars",
}

# Names that expose the builtins/import machinery directly.
BLOCKED_NAMES = {"__builtins__", "__import__", "__loader__", "__spec__"}

# Attributes used to escape to object internals or walk interpreter frames.
BLOCKED_ATTRIBUTES = {
    "__base__",
    "__bases__",
    "__builtins__",
    "__class__",
    "__closure__",
    "__code__",
    "__dict__",
    "__globals__",
    "__import__",
    "__mro__",
    "__subclasses__",
    "cr_frame",
    "f_back",
    "f_builtins",
    "f_globals",
    "f_locals",
    "gi_frame",
    "tb_frame",
    "tb_next",
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
        if isinstance(node.func, ast.Name) and node.func.id in BLOCKED_FUNCTIONS:
            self.errors.append(f"Call to function '{node.func.id}' is blocked.")
        self.generic_visit(node)

    def visit_Name(self, node):
        if node.id in BLOCKED_NAMES:
            self.errors.append(f"Use of '{node.id}' is blocked.")
        self.generic_visit(node)

    def visit_Attribute(self, node):
        if node.attr in BLOCKED_ATTRIBUTES:
            self.errors.append(f"Access to attribute '{node.attr}' is blocked.")
        self.generic_visit(node)


def validate_code_safety(code: str) -> tuple[bool, list[str]]:
    """
    Performs Abstract Syntax Tree analysis to detect dangerous patterns.
    Returns (is_safe, error_messages)
    """
    try:
        tree = ast.parse(code)
        validator = CodeSecurityValidator()
        validator.visit(tree)

        if validator.errors:
            # De-duplicate while keeping order so the message stays readable.
            return False, list(dict.fromkeys(validator.errors))
        return True, []
    except SyntaxError as e:
        return False, [f"Syntax Error: {e.msg} at line {e.lineno}"]
    except Exception as e:
        logger.error(f"AST Analysis failed: {e}")
        return False, ["Failed to analyze code security."]
