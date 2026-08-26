#!/usr/bin/env python3
"""Cross-file invariant checks for the SBET Absolute Valuation app.

Kept deliberately separate from the model workbook's own 18-check
regression harness (see README "Audit"): those validate the model: this
validates that the two `.dc.html` files stayed in sync with each other and
with their own declared statics. A failure here is a packaging/drift bug,
not a model bug, and conflating the two muddies what a failure means.

Assertions:
  1. SNAP and ASOF (ASOF/ASOF_SHORT/ASOF_LONG) are byte-identical across
     both files.
  2. SRC is a subset relationship (print's keys/values subset of main's),
     not equality.
  3. No numeric literal with three or more decimal places appears outside
     SNAP, SRC, TARGETS (or an explicit, commented allow-list entry).
  4. Every `Component.X` reference resolves to a declared static in the
     same file.

Exits non-zero if any assertion fails.
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
MAIN_FILE = ROOT / "SBET Absolute Valuation.dc.html"
PRINT_FILE = ROOT / "SBET Absolute Valuation-print.dc.html"

SCRIPT_BLOCK_RE = re.compile(
    r'<script type="text/x-dc" data-dc-script[^>]*>(.*?)</script>', re.DOTALL
)
ASOF_BLOCK_RE = re.compile(
    r"static ASOF = '[^']*';\n"
    r"\s*static ASOF_SHORT = '[^']*';\n"
    r"\s*static ASOF_LONG = '[^']*';"
)
TARGETS_BLOCK_RE = re.compile(r"static TARGETS = \{.*?\n\s*\};", re.DOTALL)
SRC_BLOCK_RE = re.compile(r"static SRC = \{.*?\n\s*\};", re.DOTALL)
SNAP_BLOCK_RE = re.compile(r"static SNAP = \{.*?\n\s*\};", re.DOTALL)
WARRANTS_BLOCK_RE = re.compile(r"static WARRANTS = \[.*?\n\s*\];", re.DOTALL)
NORMCDF_COEF_BLOCK_RE = re.compile(r"static NORMCDF_COEF = \{.*?\};", re.DOTALL)

DECIMAL_LITERAL_RE = re.compile(r"\d+\.\d{3,}")
# Belt-and-suspenders: a decimal literal immediately followed by a CSS unit
# is a style value, never model data, even if it somehow ends up inside the
# logic class scan region below. Excluded by construction, not enumeration.
CSS_UNIT_SUFFIX_RE = re.compile(r"\d+\.\d{3,}(px|em|rem|%|vh|vw|deg|s|ms)\b")

# --- Assertion 3 scope ---------------------------------------------------
# Scanned region is the <script data-dc-script> body (the Component class)
# only — never the HTML template. Markup/style literals (letter-spacing,
# font-size, etc.) are therefore out of scope structurally; they can never
# need an allow-list entry no matter how many headings get added.
#
# Within that scope, whole named-static blocks are exempt (SNAP/SRC/TARGETS
# are the generated data blocks; WARRANTS and NORMCDF_COEF are their own
# reviewed, named sources of truth — see README). Everything else is an
# individual literal, allow-listed one at a time with a reason.

# --- Assertion 3 allow-list -------------------------------------------
# Explicit, reviewed exceptions to "no 3+ decimal literal outside
# SNAP/SRC/TARGETS(/WARRANTS/NORMCDF_COEF)". Do NOT loosen the regex/
# threshold instead of adding an entry here — a narrow rule with named
# exceptions still catches drift; a loosened one doesn't.
#
# Each entry is (label, reason, predicate(file_name, line_text) -> bool).
ALLOWLIST = [
    (
        "prefunded warrant strike (0.0001)",
        "Pre-funded warrants are effectively free to exercise; 0.0001 is "
        "the actual $/share strike, confirmed genuine by design review.",
        lambda fn, line: "0.0001" in line and "prefundedStrike" in line,
    ),
    (
        "warrant tranche table region",
        "static WARRANTS carries per-tranche strikes/tenors sourced from "
        "the model; a future tranche's strike or tenor may legitimately "
        "need 3+ decimals. Confirmed genuine by design review.",
        None,  # handled as a block-span exemption, not a line predicate
    ),
    (
        "normal-CDF approximation coefficients",
        "static NORMCDF_COEF is a named, sourced mathematical constant "
        "(Abramowitz & Stegun 26.2.17), not model data.",
        None,  # handled as a block-span exemption, not a line predicate
    ),
    (
        "chart level-label offset (0.0004)",
        "Controls: pixel/value separation nudge so two warrant-strike "
        "level labels on the chart don't overlap when their strikes are "
        "close together. A display-layout constant, not a model input.",
        lambda fn, line: "0.0004" in line and "levels.push" in line,
    ),
    (
        "near-zero per-share display threshold (0.005)",
        "Controls: below half a cent, a per-share dollar amount is "
        "treated as effectively zero for display rather than shown as a "
        "misleadingly precise fraction of a cent.",
        lambda fn, line: "perShare < 0.005" in line,
    ),
    (
        "wash-threshold epsilon (0.00005)",
        "Controls: the floating-point-zero tolerance for framing net "
        "optionality as 'an actual wash' rather than a signed non-zero "
        "drag/addition.",
        lambda fn, line: "0.00005" in line and "actual wash" in line,
    ),
]


class AuditFailure(Exception):
    pass


def read(path):
    if not path.exists():
        raise AuditFailure(f"File not found: {path}")
    return path.read_text()


def extract_one(text, pattern, name, file_name):
    matches = list(pattern.finditer(text))
    if len(matches) != 1:
        raise AuditFailure(
            f"Expected exactly one {name} block in {file_name}, found {len(matches)}"
        )
    return matches[0]


# ------------------------------------------------------------ assertion 1 --

def check_snap_asof_identical(main_text, print_text):
    problems = []
    for name, pattern in (("SNAP", SNAP_BLOCK_RE), ("ASOF", ASOF_BLOCK_RE)):
        main_m = extract_one(main_text, pattern, name, MAIN_FILE.name)
        print_m = extract_one(print_text, pattern, name, PRINT_FILE.name)
        if main_m.group(0) != print_m.group(0):
            problems.append(
                f"{name} block differs between {MAIN_FILE.name} and {PRINT_FILE.name}:\n"
                f"  --- {MAIN_FILE.name} ---\n{main_m.group(0)}\n"
                f"  --- {PRINT_FILE.name} ---\n{print_m.group(0)}"
            )
    return problems


# ------------------------------------------------------------ assertion 2 --

KV_RE = re.compile(r"(\w+):\s*('(?:[^'\\]|\\.)*'|-?\d+(?:\.\d+)?)")


def parse_object_literal(block_text):
    inner = block_text.split('{', 1)[1].rsplit('}', 1)[0]
    return dict(KV_RE.findall(inner))


def check_src_subset(main_text, print_text):
    problems = []
    main_src = parse_object_literal(extract_one(main_text, SRC_BLOCK_RE, "SRC", MAIN_FILE.name).group(0))
    print_src = parse_object_literal(extract_one(print_text, SRC_BLOCK_RE, "SRC", PRINT_FILE.name).group(0))

    extra_keys = set(print_src) - set(main_src)
    if extra_keys:
        problems.append(
            f"{PRINT_FILE.name}'s SRC has key(s) not present in {MAIN_FILE.name}'s SRC: "
            f"{', '.join(sorted(extra_keys))}"
        )
    for key in set(print_src) & set(main_src):
        if print_src[key] != main_src[key]:
            problems.append(
                f"SRC.{key} differs: {MAIN_FILE.name}={main_src[key]!r} "
                f"vs {PRINT_FILE.name}={print_src[key]!r}"
            )
    return problems


# ------------------------------------------------------------ assertion 3 --

def exempt_spans(text):
    """Named-static-block spans exempt from the decimal-literal scan,
    relative to `text` (the full file — callers translate into the scan
    region's own offsets)."""
    spans = []
    for pattern in (SNAP_BLOCK_RE, SRC_BLOCK_RE, TARGETS_BLOCK_RE,
                     WARRANTS_BLOCK_RE, NORMCDF_COEF_BLOCK_RE):
        for m in pattern.finditer(text):
            spans.append((m.start(), m.end()))
    return spans


def in_span(pos, spans):
    return any(start <= pos < end for start, end in spans)


def check_decimal_literals(text, file_name):
    """Assertion 3, scoped to the Component logic class only (the
    <script data-dc-script> body) — HTML/CSS literals are out of scope by
    construction, not by enumeration, since style values are never model
    data. See module-level comment above ALLOWLIST."""
    violations = []
    allowed = []

    script_match = SCRIPT_BLOCK_RE.search(text)
    if script_match is None:
        raise AuditFailure(f"No <script data-dc-script> block found in {file_name}")
    scan_start, scan_end = script_match.span(1)

    spans = exempt_spans(text)
    lines = text.split('\n')
    line_starts = []
    offset = 0
    for line in lines:
        line_starts.append(offset)
        offset += len(line) + 1

    for m in DECIMAL_LITERAL_RE.finditer(text, scan_start, scan_end):
        if in_span(m.start(), spans):
            continue
        # Defense in depth: a literal immediately followed by a CSS unit
        # is a style value even if found inside the logic class.
        if CSS_UNIT_SUFFIX_RE.match(text, m.start()):
            continue
        line_no = next(i for i in range(len(line_starts) - 1, -1, -1) if line_starts[i] <= m.start()) + 1
        line_text = lines[line_no - 1].strip()

        matched_allow = None
        for label, reason, predicate in ALLOWLIST:
            if predicate is not None and predicate(file_name, line_text):
                matched_allow = (label, reason)
                break
        if matched_allow:
            allowed.append((file_name, line_no, m.group(0), line_text, matched_allow[0]))
        else:
            violations.append((file_name, line_no, m.group(0), line_text))
    return violations, allowed


# ------------------------------------------------------------ assertion 4 --

STATIC_DECL_RE = re.compile(r"static\s+(\w+)\s*[=(]")
COMPONENT_REF_RE = re.compile(r"Component\.(\w+)")


def check_component_refs(text, file_name):
    declared = set(STATIC_DECL_RE.findall(text))
    problems = []
    for m in COMPONENT_REF_RE.finditer(text):
        name = m.group(1)
        if name not in declared:
            line_no = text.count('\n', 0, m.start()) + 1
            problems.append(
                f"{file_name}:{line_no} — Component.{name} does not resolve to any "
                f"declared static in this file"
            )
    return problems


# ------------------------------------------------------------------ main --

def main():
    failures = []

    main_text = read(MAIN_FILE)
    print_text = read(PRINT_FILE)

    print("== Assertion 1: SNAP and ASOF byte-identical across both files ==")
    problems = check_snap_asof_identical(main_text, print_text)
    if problems:
        failures.extend(problems)
        for p in problems:
            print(f"  FAIL: {p}")
    else:
        print("  OK")

    print("\n== Assertion 2: SRC is a subset relationship ==")
    problems = check_src_subset(main_text, print_text)
    if problems:
        failures.extend(problems)
        for p in problems:
            print(f"  FAIL: {p}")
    else:
        print("  OK")

    print("\n== Assertion 3: no 3+ decimal literal outside SNAP/SRC/TARGETS ==")
    all_violations = []
    for file_name, text in ((MAIN_FILE.name, main_text), (PRINT_FILE.name, print_text)):
        violations, allowed = check_decimal_literals(text, file_name)
        all_violations.extend(violations)
        for fn, ln, lit, line_text, label in allowed:
            print(f"  allow-listed [{label}]: {fn}:{ln} `{lit}`  {line_text[:100]}")
    if all_violations:
        for fn, ln, lit, line_text in all_violations:
            print(f"  FAIL: {fn}:{ln} `{lit}`  {line_text[:100]}")
        failures.append(f"{len(all_violations)} un-allow-listed 3+ decimal literal(s) — see above")
    else:
        print("  OK (no un-allow-listed violations)")

    print("\n== Assertion 4: every Component.X reference resolves to a declared static ==")
    problems = []
    for file_name, text in ((MAIN_FILE.name, main_text), (PRINT_FILE.name, print_text)):
        problems.extend(check_component_refs(text, file_name))
    if problems:
        failures.extend(problems)
        for p in problems:
            print(f"  FAIL: {p}")
    else:
        print("  OK")

    print()
    if failures:
        print(f"audit_app.py: FAILED ({len(failures)} problem(s))")
        sys.exit(1)
    print("audit_app.py: all assertions passed")


if __name__ == '__main__':
    try:
        main()
    except AuditFailure as e:
        print(f"audit_app.py: {e}", file=sys.stderr)
        sys.exit(1)
