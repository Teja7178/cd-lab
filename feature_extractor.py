"""Lightweight, explainable source-text features for a classroom prototype.

This module does not replace a real language parser. It uses conservative regular
expressions and line-based heuristics, so findings should be reviewed by a developer.
"""
from __future__ import annotations
import re
from collections import Counter

FEATURE_NAMES = [
    "line_count", "token_count", "loop_count", "max_loop_nesting",
    "branch_count", "function_call_count", "allocation_keyword_count",
    "repeated_line_count", "repeated_expression_count",
    "condition_count", "conversion_keyword_count", "comment_line_count",
    "costly_loop_call_count",
]

TOKEN_RE = re.compile(r"\b[A-Za-z_]\w*\b|\d+|==|!=|<=|>=|&&|\|\||[^\s]")
LOOP_RE = re.compile(r"\b(for|while|do)\b")
BRANCH_RE = re.compile(r"\b(if|else\s+if|switch|case)\b")
CALL_RE = re.compile(r"\b[A-Za-z_]\w*\s*\(")
ALLOC_RE = re.compile(r"\b(new|malloc|calloc|realloc|make_shared|make_unique)\b")
CONVERSION_RE = re.compile(r"\b(to_string|atoi|atof|stoi|stod|strtol)\s*\(")
CONDITION_RE = re.compile(r"(==|!=|<=|>=|<|>|\&\&|\|\|)")
COMMENT_RE = re.compile(r"^\s*(//|/\*|\*|#)")
COSTLY_LOOP_RE = re.compile(r"\b(for|while|do)\b[^{\n]*\{?[\s\S]{0,250}\b(strlen|pow|sqrt|to_string|stoi|stod|malloc|new|calloc)\s*\(")

def extract_features(source: str) -> dict[str, float]:
    lines = source.splitlines()
    # Strip preprocessor and comments for clean syntactic analysis
    no_includes = re.sub(r"#include\s*<[^>]+>", "", source)
    no_comments = re.sub(r"//.*", "", no_includes)
    no_comments = re.sub(r"/\*[\s\S]*?\*/", "", no_comments)

    code_lines = [ln.strip() for ln in no_comments.splitlines() if ln.strip()]
    # Ignore lines that are just braces or semicolons (e.g. '{', '}', ';')
    meaningful = [ln for ln in code_lines if len(re.sub(r"[{}\s;]", "", ln)) > 2]
    counts = Counter(meaningful)
    repeated_line_count = sum(n - 1 for n in counts.values() if n > 1)

    exprs = re.findall(r"\b[A-Za-z_]\w*(?:\s*[+\-*/]\s*[A-Za-z_]\w*|\s*\([^;]*?\))", no_comments)
    expr_counts = Counter(re.sub(r"\s+", "", e) for e in exprs)
    repeated_expression_count = sum(n - 1 for n in expr_counts.values() if n > 1)

    depth = 0
    max_depth = 0
    for ln in lines:
        if LOOP_RE.search(ln):
            depth += 1
            max_depth = max(max_depth, depth)
        if "}" in ln and depth:
            depth = max(0, depth - ln.count("}"))

    costly_in_loop = len(COSTLY_LOOP_RE.findall(no_comments))

    return {
        "line_count": float(len(lines)),
        "token_count": float(len(TOKEN_RE.findall(no_comments))),
        "loop_count": float(len(LOOP_RE.findall(no_comments))),
        "max_loop_nesting": float(max_depth),
        "branch_count": float(len(BRANCH_RE.findall(no_comments))),
        "function_call_count": float(len(CALL_RE.findall(no_comments))),
        "allocation_keyword_count": float(len(ALLOC_RE.findall(no_comments))),
        "repeated_line_count": float(repeated_line_count),
        "repeated_expression_count": float(repeated_expression_count),
        "condition_count": float(len(CONDITION_RE.findall(no_comments))),
        "conversion_keyword_count": float(len(CONVERSION_RE.findall(no_comments))),
        "comment_line_count": float(sum(1 for ln in lines if COMMENT_RE.match(ln))),
        "costly_loop_call_count": float(costly_in_loop),
    }

def heuristic_evidence(source: str) -> list[str]:
    """Return explainable warning signals. They are not definitive diagnoses."""
    evidence = []
    lines = source.splitlines()
    no_includes = re.sub(r"#include\s*<[^>]+>", "", source)
    no_comments = re.sub(r"//.*", "", no_includes)
    no_comments = re.sub(r"/\*[\s\S]*?\*/", "", no_comments)

    code_lines = [ln.strip() for ln in no_comments.splitlines() if ln.strip()]
    meaningful = [ln for ln in code_lines if len(re.sub(r"[{}\s;]", "", ln)) > 2]
    counts = Counter(meaningful)
    repeated = [line for line, count in counts.items() if count > 1]
    if repeated:
        evidence.append(f"Repeated non-empty source line(s) detected ({len(repeated)} distinct repeated line pattern(s)).")

    if COSTLY_LOOP_RE.search(no_comments):
        evidence.append("A potentially costly function/allocation/conversion appears inside or near a loop; verify if it can be hoisted outside.")
    elif LOOP_RE.search(source):
        loop_lines = [i for i, ln in enumerate(lines, 1) if LOOP_RE.search(ln)]
        if len(loop_lines) >= 3:
            evidence.append(f"Multiple loop constructs found on line(s) {', '.join(map(str, loop_lines))}; review nested time complexity.")

    if len(BRANCH_RE.findall(no_comments)) >= 4:
        evidence.append("Multiple branch constructs are present; review for duplicated or redundant conditions.")

    if re.search(r"\b(for|while|do)\b[^{\n]*\{?[\s\S]{0,250}\b(malloc|new|calloc)\b", no_comments):
        evidence.append("Heap allocation inside a loop detected; verify whether buffer reuse or pre-allocation is possible.")

    if not evidence:
        evidence.append("Code structure appears clean; no common inefficient patterns detected.")
    return evidence
