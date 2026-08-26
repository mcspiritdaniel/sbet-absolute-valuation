#!/usr/bin/env python3
"""Cross-file invariant checks for the SBET Absolute Valuation app.

Kept deliberately separate from the model workbook's own regression harness
(see README "Audit"): those validate the model; this validates that the two
`.dc.html` files stayed in sync with each other, with the model snapshot
that fed `build.py`, and with their own declared statics. A failure here is
a packaging/drift bug, not a model bug, and conflating the two muddies what
a failure means.

Assertions:
  1. SNAP and ASOF (ASOF/ASOF_SHORT/ASOF_LONG) are byte-identical across
     both files.
  2. SRC is a subset relationship (print's keys/values subset of main's),
     not equality.
  3. TARGETS matches the model snapshot's checks{}, key-for-key through the
     same explicit mapping build.py uses (imported from build.py, not
     re-derived, so the two can never silently diverge).
  4. No money-shaped ($1,234.56) or share-count-shaped (217,031,714) numeric
     literal appears outside SNAP, SRC, TARGETS, WARRANTS, NORMCDF_COEF, or
     OPTIONALITY_NOTE (print-only, build-time-generated — see build.py) —
     across the WHOLE FILE, not just the logic class. This is deliberately
     wider on two axes than an earlier "3+ decimal places, logic-class-only"
     version of this check: a 2-decimal price ($2,266.79) has too few
     decimals for that rule, and it lived in the HTML template, not the
     logic class — exactly where that version could never have looked. See
     "A stale price is the whole argument" below.

  Bonus, preserved from the previous version of this script (not one of the
  four above, but real protection with a real incident behind it — see
  README "Audit" point 4):
  5. Every `Component.X` reference resolves to a declared static in the
     same file.

Exits non-zero if any assertion fails.
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
MAIN_FILE = ROOT / "SBET Absolute Valuation.dc.html"
PRINT_FILE = ROOT / "SBET Absolute Valuation-print.dc.html"

# TARGETS_MAP and load_model are imported, not redefined — the model
# snapshot -> checks{} -> TARGETS key mapping must never exist in two
# places that can drift from each other. See build.py's own docstring and
# README "TARGETS key mapping — do not infer this".
sys.path.insert(0, str(ROOT))
from build import TARGETS_MAP, load_model, DEFAULT_MODEL  # noqa: E402

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
# Print-only, build-time-generated (see build.py:derive_optionality_note).
OPTIONALITY_NOTE_BLOCK_RE = re.compile(r"static OPTIONALITY_NOTE = '[^']*';")

# money-shaped: a dollar sign followed by digits, optional thousands commas,
# optional decimals — $4.80, $2,266.79, $8,000, $000 (the last is a unit
# suffix, not an amount, and is excluded explicitly below).
MONEY_LITERAL_RE = re.compile(r'\$\d[\d,]*(?:\.\d+)?')
# share-count-shaped: a comma-grouped integer (4+ digits), with or without a
# trailing decimal, not already part of a $-prefixed money literal (the
# negative lookbehind keeps "$8,000" a single money hit rather than also
# reporting "8,000" as a second, redundant share-count hit).
SHARE_COUNT_LITERAL_RE = re.compile(r'(?<![\d.$])\d{1,3}(?:,\d{3})+(?:\.\d+)?')


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
# TARGETS vs the model snapshot's checks{}, through build.py's own mapping.

def check_targets_match_checks(main_text, model_path):
    problems = []
    if not model_path.exists():
        return [
            f"Model snapshot not found: {model_path}. Pass the current week's "
            f"snapshot explicitly: python3 audit_app.py <snapshot.json>"
        ]
    model = load_model(model_path)
    checks = model.get('checks', {})

    targets_m = extract_one(main_text, TARGETS_BLOCK_RE, "TARGETS", MAIN_FILE.name)
    targets = parse_object_literal(targets_m.group(0))

    for target_key, checks_key in TARGETS_MAP:
        if checks_key not in checks:
            problems.append(
                f"Model snapshot ({model_path.name}) checks{{}} is missing key "
                f"'{checks_key}' needed for TARGETS.{target_key}"
            )
            continue
        expected = checks[checks_key]  # string, full source precision (parse_float=str)
        raw_actual = targets.get(target_key)
        if raw_actual is None:
            problems.append(f"TARGETS.{target_key} not found in {MAIN_FILE.name}")
            continue
        actual = raw_actual[1:-1] if raw_actual.startswith("'") else raw_actual
        if actual != expected:
            problems.append(
                f"TARGETS.{target_key} = '{actual}' in {MAIN_FILE.name}, but "
                f"checks{{}}.{checks_key} = '{expected}' in {model_path.name} "
                f"(asOf={model.get('asOf')!r}). Re-run build.py against the "
                f"current snapshot."
            )
    return problems


# ------------------------------------------------------------ assertion 4 --
# No money-shaped or share-count-shaped literal outside the named data
# blocks, scanned across the WHOLE FILE.
#
# "A stale price is the whole argument." The bug this check exists to catch
# (a hardcoded $2,266.79 ETH price, three weeks and a deploy stale) lived in
# a <p> tag in the HTML template, not in the Component logic class — a
# narrower, logic-class-only, 3+-decimal version of this check could not
# have found it on either axis: wrong scope, wrong threshold. This version
# fixes both: full-file scope, and money/share shape instead of a decimal
# count (a 2-decimal dollar amount is exactly the risk).
#
# That widening surfaces a lot of genuinely fine prose — historical capital-
# allocation narrative, chart axis ticks, a quarter-pinned GAAP figure, the
# "per 1,000 shares" unit convention itself. Each is allow-listed below by
# name and reason, the same discipline as the narrower check this replaces:
# do not loosen the rule to make the noise go away, name the exception.

ALLOWLIST = [
    # NOTE: '$000' (the thousands-of-dollars unit suffix, e.g. 'Cash · $000')
    # is exempted by an exact-token skip in check_money_share_literals, not
    # a line predicate here — it is never an amount, so there is nothing to
    # allow-list per occurrence.
    (
        "June 2026 close explicitly retained, not seeded",
        "'The $4.69 that previously seeded the June date ... is retained "
        "where it belongs' — the sentence's own subject is that this "
        "figure is a fixed historical anchor, deliberately not tracking "
        "the live seed. Listed ahead of the '1,000 shares' entry below "
        "because this line also matches that predicate, and this is the "
        "reason that actually explains the $4.69 on it.",
        lambda line: 'previously seeded the June date' in line,
    ),
    (
        "'per 1,000 shares' display convention",
        "The app's fixed ETH-concentration unit ('ETH per 1,000 shares'). "
        "Not a share count — 1,000 never changes.",
        lambda line: 'per 1,000' in line or 'each 1,000' in line,
    ),
    (
        "chart axis tick labels ($750 / $8,000)",
        "Fixed chart-scale boundaries for the ETH-price axis (Chart 2 in "
        "both files), co-located with the f.sx() scaling call. Not model "
        "data — the axis range does not move with the weekly refresh.",
        lambda line: 'f.sx(' in line,
    ),
    (
        "scenario grid is explicitly the fixed workbook grid",
        "'the workbook grid: fixed ETH rows from $2,000 to $10,000' — the "
        "sentence's own point is that this grid does NOT move with the "
        "seeded ETH price. A pinned grid boundary, not model output.",
        lambda line: 'workbook grid' in line,
    ),
    (
        "Marginal Action fixed test size ($50m)",
        "The section's illustrative issuance size. Not sourced from the "
        "model snapshot — there is no SNAP field for a hypothetical "
        "issuance amount — so it cannot drift against one.",
        lambda line: 'Marginal action' in line,
    ),
    (
        "ETH concentration timing-gap caveat ($200m raise)",
        "Refers to a specific, dated, completed raise ('timing gaps "
        "between share issuance and ETH deployment') cited as a historical "
        "caveat on the concentration chart. Permanently fixed by the date "
        "it describes.",
        lambda line: 'timing gaps between share issuance' in line,
    ),
    (
        "capital allocation scorecard narrative",
        "The scorecard's 3-of-6-measured deals and their prices are a "
        "permanently fixed historical record (FY2025/2026 transactions), "
        "not weekly-refreshed model output. Matches the same figures in "
        "the model workbook's own Historicals tab.",
        lambda line: '3 of 6 deals' in line or 'was clearly accretive' in line
        or 'was roughly a wash' in line,
    ),
    (
        "October 2025 raise — premium-to-market detail",
        "Describes the same dated, completed October 2025 raise as the "
        "scorecard entry above, in more detail (main file only).",
        lambda line: '12% premium' in line,
    ),
    (
        "warrant/option structure narrative (basic mNAV)",
        "Restates the same tranche struck at $8.15 that is already in the "
        "exempted WARRANTS block, in prose describing what basic mNAV "
        "misses. Tied to that block's own review, not weekly data.",
        lambda line: 'warrants struck at $8.15 and the stock reaches $20' in line,
    ),
    (
        "warrant/option structure narrative (fully diluted mNAV)",
        "Restates the option count/strike (3,146 @ $122.88) and the "
        "$8.15 warrant exercise proceeds already in SNAP.options and the "
        "exempted WARRANTS block, in prose. Same review boundary as above.",
        lambda line: 'warrants are exercised the company receives roughly $81.6m' in line,
    ),
    (
        "dilution-vs-price sensitivity ('where it bites')",
        "A fixed illustrative sensitivity table (company-method overstatement "
        "at $5 vs $30) transcribed from the model workbook's own "
        "Cap_Structure sensitivity section, independent of the current "
        "seeded price.",
        lambda line: 'opposite of the intuition' in line,
    ),
    (
        "seeded-price provenance note ($4.80 historical close)",
        "The other seeded SBET close (30 June 2026) is a permanently fixed "
        "historical fact, cited alongside the live seed for provenance, "
        "not a value that refreshes.",
        lambda line: 'official NASDAQ closes' in line,
    ),
    (
        "GAAP reconciliation — carrying value ($369.1m)",
        "Quarter-pinned 10-Q figure (LsETH/weETH carrying value at 30 June "
        "2026). Refreshes on the next 10-Q, not on the weekly SNAP cycle — "
        "same category as the model workbook's own GAAP reconciliation "
        "memo, which is explicitly not part of the weekly refresh.",
        lambda line: 'cost less impairment' in line,
    ),
    (
        "GAAP reconciliation — quarterly impairment ($87.8m)",
        "Same quarter-pinned category as the carrying-value entry above.",
        lambda line: 'impairments in the June quarter' in line,
    ),
]


def exempt_spans(text):
    spans = []
    for pattern in (SNAP_BLOCK_RE, SRC_BLOCK_RE, TARGETS_BLOCK_RE,
                     WARRANTS_BLOCK_RE, NORMCDF_COEF_BLOCK_RE, OPTIONALITY_NOTE_BLOCK_RE):
        for m in pattern.finditer(text):
            spans.append((m.start(), m.end()))
    return spans


def in_span(pos, spans):
    return any(start <= pos < end for start, end in spans)


def check_money_share_literals(text, file_name):
    """Assertion 4, scanning the WHOLE file (template and logic class
    alike) — see the module comment above for why scope, not just pattern,
    had to widen."""
    violations = []
    allowed = []

    spans = exempt_spans(text)
    lines = text.split('\n')

    for pattern in (MONEY_LITERAL_RE, SHARE_COUNT_LITERAL_RE):
        for m in pattern.finditer(text):
            if in_span(m.start(), spans):
                continue
            if m.group(0) == '$000':
                continue  # unit suffix, not an amount — see ALLOWLIST entry
            line_no = text.count('\n', 0, m.start()) + 1
            line_text = lines[line_no - 1].strip()

            matched_allow = None
            for label, reason, predicate in ALLOWLIST:
                if predicate(line_text):
                    matched_allow = (label, reason)
                    break
            if matched_allow:
                allowed.append((file_name, line_no, m.group(0), line_text, matched_allow[0]))
            else:
                violations.append((file_name, line_no, m.group(0), line_text))
    return violations, allowed


# ------------------------------------------------------------ assertion 5 --
# (bonus — preserved from the previous version of this script)

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

def main(argv):
    model_path = Path(argv[1]) if len(argv) > 1 else DEFAULT_MODEL
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

    print(f"\n== Assertion 3: TARGETS matches checks{{}} ({model_path.name}) ==")
    try:
        problems = check_targets_match_checks(main_text, model_path)
    except Exception as e:
        problems = [f"Could not evaluate: {e}"]
    if problems:
        failures.extend(problems)
        for p in problems:
            print(f"  FAIL: {p}")
    else:
        print("  OK")

    print("\n== Assertion 4: no money/share-count-shaped literal outside SNAP/SRC/TARGETS ==")
    all_violations = []
    for file_name, text in ((MAIN_FILE.name, main_text), (PRINT_FILE.name, print_text)):
        violations, allowed = check_money_share_literals(text, file_name)
        all_violations.extend(violations)
        for fn, ln, lit, line_text, label in allowed:
            print(f"  allow-listed [{label}]: {fn}:{ln} `{lit}`  {line_text[:100]}")
    if all_violations:
        for fn, ln, lit, line_text in all_violations:
            print(f"  FAIL: {fn}:{ln} `{lit}`  {line_text[:100]}")
        failures.append(f"{len(all_violations)} un-allow-listed money/share-shaped literal(s) — see above")
    else:
        print("  OK (no un-allow-listed violations)")

    print("\n== Assertion 5 (bonus): every Component.X reference resolves to a declared static ==")
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
        main(sys.argv)
    except AuditFailure as e:
        print(f"audit_app.py: {e}", file=sys.stderr)
        sys.exit(1)
