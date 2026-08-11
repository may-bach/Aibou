import os
import ast
import math
import datetime
from pathlib import Path
from langchain_core.tools import tool

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent

@tool
def web_search(query: str) -> str:
    """Search the web for up-to-date facts, current news, live external information, or documentation.
    CRITICAL: Use this ONLY when the user explicitly asks for current events, live information, or specific research.
    DO NOT use this tool for greetings, casual conversation, common knowledge, or standard questions."""
    try:
        from ddgs import DDGS
        ddgs = DDGS()
        results = list(ddgs.text(query, max_results=5))
        if not results:
            return f"No search results found for query: '{query}'."
        
        formatted = []
        for i, item in enumerate(results, 1):
            title = item.get("title", "No Title")
            snippet = item.get("body", item.get("snippet", ""))
            link = item.get("href", item.get("link", ""))
            formatted.append(f"[{i}] {title}\nSummary: {snippet}\nSource: {link}")
        
        return "\n\n".join(formatted)
    except Exception as e:
        return f"Web search encountered an issue: {str(e)}"


SAFE_MATH_NAMES = {
    'abs': abs,
    'round': round,
    'min': min,
    'max': max,
    'sum': sum,
    'pow': pow,
    'sqrt': math.sqrt,
    'sin': math.sin,
    'cos': math.cos,
    'tan': math.tan,
    'log': math.log,
    'log10': math.log10,
    'exp': math.exp,
    'pi': math.pi,
    'e': math.e,
}

def _eval_ast_math(node):
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    elif isinstance(node, ast.UnaryOp):
        operand = _eval_ast_math(node.operand)
        if isinstance(node.op, ast.UAdd):
            return +operand
        elif isinstance(node.op, ast.USub):
            return -operand
    elif isinstance(node, ast.BinOp):
        left = _eval_ast_math(node.left)
        right = _eval_ast_math(node.right)
        if isinstance(node.op, ast.Add):
            return left + right
        elif isinstance(node.op, ast.Sub):
            return left - right
        elif isinstance(node.op, ast.Mult):
            return left * right
        elif isinstance(node.op, ast.Div):
            return left / right
        elif isinstance(node.op, ast.FloorDiv):
            return left // right
        elif isinstance(node.op, ast.Mod):
            return left % right
        elif isinstance(node.op, ast.Pow):
            return left ** right
    elif isinstance(node, ast.Call):
        if isinstance(node.func, ast.Name) and node.func.id in SAFE_MATH_NAMES:
            func = SAFE_MATH_NAMES[node.func.id]
            args = [_eval_ast_math(arg) for arg in node.args]
            return func(*args)
    elif isinstance(node, ast.Name) and node.id in SAFE_MATH_NAMES:
        return SAFE_MATH_NAMES[node.id]
    raise ValueError(f"Unsupported math syntax or function: {ast.dump(node)}")

@tool
def calculate(expression: str) -> str:
    """Safely evaluate mathematical calculations, equations, percentages, and arithmetic.
    Use ONLY when explicit math calculation or numeric formula evaluation is needed. DO NOT use for general text."""
    try:
        cleaned_expr = expression.replace("^", "**").replace("×", "*").replace("÷", "/")
        parsed = ast.parse(cleaned_expr, mode='eval')
        result = _eval_ast_math(parsed.body)
        return f"Result: {result}"
    except Exception as e:
        return f"Calculation error for '{expression}': {str(e)}"


@tool
def get_current_time(timezone: str = "local") -> str:
    """Get the current date, exact local time, day of the week, and year.
    Use ONLY when the user explicitly asks for current date, today's day of the week, or the present time."""
    now = datetime.datetime.now()
    return (
        f"Current Time: {now.strftime('%A, %B %d, %Y at %I:%M:%S %p')} (Local)\n"
        f"Date: {now.strftime('%Y-%m-%d')}\n"
        f"Year: {now.year}"
    )


@tool
def read_local_file(filepath: str) -> str:
    """Read the contents of a local file in the project workspace.
    Use ONLY when the user explicitly requests reading a file or asks about project codebase contents."""
    try:
        target_path = (WORKSPACE_ROOT / filepath).resolve()
        
        # Guard against directory traversal outside the workspace
        if not str(target_path).startswith(str(WORKSPACE_ROOT)):
            return "Error: Cannot access files outside the workspace root."
        
        if not target_path.exists():
            return f"Error: File '{filepath}' does not exist."
            
        if not target_path.is_file():
            return f"Error: '{filepath}' is not a regular file."
            
        with open(target_path, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read(30000) # Cap at 30KB
            if len(content) == 30000:
                content += "\n... [Content truncated to first 30KB] ..."
            return content
    except Exception as e:
        return f"Error reading file '{filepath}': {str(e)}"


# Tools exposed to model
aibou_tools = [web_search, calculate, get_current_time, read_local_file]
tool_map = {t.name: t for t in aibou_tools}


