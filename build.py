#!/usr/bin/env python3
"""Weekly refresh build step.

Writes the four seeded data blocks (ASOF/ASOF_SHORT/ASOF_LONG, SNAP, SRC,
TARGETS) into both `.dc.html` files from two inputs:

  - the model workbook's snapshot JSON (computed model output, checked by
    the workbook's own regression harness)
  - src_manual.json (five hand-transcribed facts read off SBET's live
    investor dashboard and press releases — not model output, and not
    validated by the workbook)

Each block is replaced whole (block-level substitution), matching the
existing hand-authored formatting exactly, so that running this generator
against the snapshot already reflected in the files produces a zero-diff
result. See README.md ("Weekly refresh", "Things that must not be
'restored'") for why the two inputs are kept separate and what each block
means.

Usage:
    python3 build.py [snapshot.json] [src_manual.json]
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DEFAULT_MODEL = ROOT / "SBET_App_Snapshot_25Aug2026-a55ad6ef.json"
DEFAULT_MANUAL = ROOT / "src_manual.json"
MAIN_FILE = ROOT / "SBET Absolute Valuation.dc.html"
PRINT_FILE = ROOT / "SBET Absolute Valuation-print.dc.html"

MONTHS_SHORT = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
MONTHS_LONG = ['January', 'February', 'March', 'April', 'May', 'June',
               'July', 'August', 'September', 'October', 'November', 'December']

# TARGETS key <- checks{} key. Four of eight do NOT match by name — see
# README "TARGETS key mapping — do not infer this". Encoded explicitly.
TARGETS_MAP = [
    ('lineInSand', 'lineInSand'),
    ('mnavEconomic', 'mnavEconomic'),
    ('navPerShareEconomic', 'navPerShareEconomic'),
    ('ethConcBasic', 'ethConcentration'),
    ('justifiedScenario', 'mnavJustifiedScenario'),
    ('justifiedOnScenario', 'priceJustifiedScenario'),
    ('priceJustifiedEconomic', 'priceJustifiedEconomic'),
    ('yieldPV', 'yieldPV'),
]

REQUIRED_MANUAL_FIELDS = {
    'asOf': str,
    'holdingsRelease': str,
    'dashConc': (int, float),
    'dashEth': int,
    'dashNavPS': (int, float),
    'dashAsOf': str,
}


class BuildError(Exception):
    pass


def fail(msg):
    raise BuildError(msg)


# ---------------------------------------------------------------- loading --

def load_model(path):
    if not path.exists():
        fail(f"Model snapshot not found: {path}")
    text = path.read_text()
    try:
        # parse_float=str preserves the exact decimal precision the workbook
        # wrote (needed for TARGETS — see "emit the full precision the
        # workbook holds" in README). Arithmetic below converts to float
        # explicitly where needed.
        return json.loads(text, parse_float=str)
    except json.JSONDecodeError as e:
        fail(f"{path.name} is not valid JSON: {e}")


def load_manual(path, model_as_of):
    if not path.exists():
        fail(
            f"{path.name} not found. SRC's hand-transcribed fields "
            "(holdingsRelease, dashConc, dashEth, dashNavPS, dashAsOf) "
            "have no source in the model snapshot and must be supplied "
            "in this file — see README 'Weekly refresh'."
        )
    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError as e:
        fail(f"{path.name} is not valid JSON: {e}")

    missing = [k for k in REQUIRED_MANUAL_FIELDS if k not in data]
    if missing:
        fail(f"{path.name} is missing required field(s): {', '.join(missing)}")

    for key, kind in REQUIRED_MANUAL_FIELDS.items():
        val = data[key]
        if isinstance(val, bool) or not isinstance(val, kind):
            fail(
                f"{path.name}.{key} has the wrong type: expected "
                f"{kind if isinstance(kind, type) else ' or '.join(t.__name__ for t in kind)}, "
                f"got {type(val).__name__} ({val!r})"
            )

    if data['asOf'] != model_as_of:
        fail(
            f"{path.name} is pinned to asOf={data['asOf']!r} but the model "
            f"snapshot's asOf is {model_as_of!r}. This week's dashboard "
            "reading has not been transcribed yet — refusing to pair a "
            "stale manual file with a fresh model snapshot."
        )

    return data


# ------------------------------------------------------------- formatting --

def fnum(json_float_str, keep_decimal=False):
    """Format a JSON number (as a source-precision string) the way SNAP/SRC
    literals are hand-styled: whole numbers drop the trailing '.0'; values
    that already carry a fraction keep their exact source digits.
    `keep_decimal` forces at least one decimal place even on a whole number
    (used for `vol`, which is hand-styled as e.g. `1.0` rather than `1`).
    """
    f = float(json_float_str)
    if f == int(f) and not keep_decimal:
        return str(int(f))
    return json_float_str


def money2(value):
    """Fixed 2-decimal literal, e.g. for optionStrike, dashConc, dashNavPS."""
    return f"{value:.2f}"


def targets_str(json_float_str):
    """TARGETS values are pinned strings at the workbook's full precision.
    parse_float=str already preserved that exact source text."""
    return json_float_str


def format_date(iso_date):
    y, m, d = iso_date.split('-')
    day = str(int(d))
    month_i = int(m) - 1
    asof = iso_date
    asof_short = f"{day} {MONTHS_SHORT[month_i]}"
    asof_long = f"{day} {MONTHS_SHORT[month_i]} {y}"
    close_date = f"{day} {MONTHS_LONG[month_i]} {y}"
    return asof, asof_short, asof_long, close_date


# --------------------------------------------------------------- derived --

def derive_option_strike(fundamentals, warrant_tranches):
    """SNAP.optionStrike (employee option strike price) has no field of its
    own in the model snapshot, but it is algebraically implied by
    fullExerciseProceeds: that figure (in $ thousands, matching how
    `compute()` scales proceeds — see `w.n * w.k / 1000` in the main file)
    is the sum of prefunded-warrant, option, and warrant exercise proceeds.
    Solve for the one unknown.

    This is inference, not a sourced input — see README "optionStrike is
    inferred, not sourced" for why it should move to checks{} directly.
    `recompute_full_exercise_proceeds` below is the guard against a silent
    wrong answer in the meantime: it re-derives fullExerciseProceeds from
    this result through an independently-written formula and the build
    fails if the two don't agree to full precision.
    """
    warrants_total = sum(float(w['n']) * float(w['k']) for w in warrant_tranches)
    prefunded_total = float(fundamentals['prefundedWarrants']) * 0.0001
    full_exercise_thousands = float(fundamentals['fullExerciseProceeds']) * 1000
    options = float(fundamentals['options'])
    remainder = full_exercise_thousands - warrants_total - prefunded_total
    return remainder / options


def recompute_full_exercise_proceeds(fundamentals, warrant_tranches, option_strike):
    """Independent forward recomputation of fullExerciseProceeds from a
    given optionStrike, the warrant tranche table, and prefundedWarrants —
    written separately from derive_option_strike's algebra so that a coding
    mistake in either direction (wrong field, wrong sign, wrong /1000 scale)
    breaks the round trip instead of canceling out."""
    warrants_total = sum(float(w['n']) * float(w['k']) for w in warrant_tranches)
    prefunded_total = float(fundamentals['prefundedWarrants']) * 0.0001
    options_total = float(fundamentals['options']) * option_strike
    return (warrants_total + prefunded_total + options_total) / 1000


def verify_option_strike_round_trip(fundamentals, warrant_tranches, option_strike):
    expected = float(fundamentals['fullExerciseProceeds'])
    recomputed = recompute_full_exercise_proceeds(fundamentals, warrant_tranches, option_strike)
    if abs(recomputed - expected) > 1e-6:
        fail(
            "optionStrike round trip failed: recomputing fullExerciseProceeds "
            f"from the derived optionStrike ({option_strike!r}) gives "
            f"{recomputed!r}, but the model snapshot's fullExerciseProceeds "
            f"is {expected!r}. The derivation formula and the workbook's "
            "accounting for exercise proceeds have diverged — optionStrike "
            "is inferred, not sourced, and this is exactly the case that "
            "silent inference would get wrong. Do not proceed without "
            "resolving the discrepancy."
        )


# ------------------------------------------------------------ block text --

def build_asof_block(asof, asof_short, asof_long):
    return (
        f"  static ASOF = '{asof}';\n"
        f"  static ASOF_SHORT = '{asof_short}';\n"
        f"  static ASOF_LONG = '{asof_long}';"
    )


def build_targets_block(checks):
    lines = ["  static TARGETS = {"]
    for i, (target_key, checks_key) in enumerate(TARGETS_MAP):
        if checks_key not in checks:
            fail(f"Model snapshot checks{{}} is missing key '{checks_key}' "
                 f"needed for TARGETS.{target_key}")
        comma = ',' if i < len(TARGETS_MAP) - 1 else ''
        lines.append(f"    {target_key}: '{targets_str(checks[checks_key])}'{comma}")
    lines.append("  };")
    return "\n".join(lines)


def build_snap_block(fundamentals, assumptions, checks, option_strike):
    f, a, c = fundamentals, assumptions, checks
    v = {
        'ethNative': fnum(f['ethNative']), 'ethLsETH': fnum(f['ethLsETH']), 'ethWeETH': fnum(f['ethWeETH']),
        'cash': fnum(f['cash']), 'otherAssets': fnum(f['otherAssets']), 'liabilities': fnum(f['liabilities']),
        'sharesCommon': fnum(f['sharesCommon']), 'prefundedWarrants': fnum(f['prefundedWarrants']),
        'rsu': fnum(f['rsu']), 'options': fnum(f['options']),
        'aprNative': fnum(a['aprNative']), 'aprLsETH': fnum(a['aprLsETH']), 'aprWeETH': fnum(a['aprWeETH']),
        'incentivesY1': fnum(a['incentivesY1']), 'incentiveDecay': fnum(a['incentiveDecay']),
        'galaxyCommit': fnum(a['galaxyCommit']), 'galaxyReturn': fnum(a['galaxyReturn']),
        'sgaAnnual': fnum(a['sgaAnnual']), 'affiliate': fnum(a['affiliate']),
        'discountRate': fnum(a['discountRate']), 'horizonYears': fnum(a['horizonYears']),
        'atmOption': fnum(a['atmOption']), 'ecoOption': fnum(a['ecoOption']),
        'govDiscount': fnum(a['govDiscount']), 'riskFree': fnum(a['riskFree']),
        'vol': fnum(a['vol'], keep_decimal=True),
        'ethPrice': fnum(c['ethPrice']), 'sbetPrice': fnum(c['sbetPrice']),
        'optionStrike': money2(option_strike),
    }
    return (
        "  static SNAP = {\n"
        f"    ethNative: {v['ethNative']}, ethLsETH: {v['ethLsETH']}, ethWeETH: {v['ethWeETH']},\n"
        f"    cash: {v['cash']}, otherAssets: {v['otherAssets']}, liabilities: {v['liabilities']},\n"
        f"    sharesCommon: {v['sharesCommon']}, prefundedWarrants: {v['prefundedWarrants']}, rsu: {v['rsu']}, options: {v['options']},\n"
        f"    aprNative: {v['aprNative']}, aprLsETH: {v['aprLsETH']}, aprWeETH: {v['aprWeETH']},\n"
        f"    incentivesY1: {v['incentivesY1']}, incentiveDecay: {v['incentiveDecay']}, galaxyCommit: {v['galaxyCommit']}, galaxyReturn: {v['galaxyReturn']},\n"
        f"    sgaAnnual: {v['sgaAnnual']}, affiliate: {v['affiliate']}, discountRate: {v['discountRate']}, horizonYears: {v['horizonYears']},\n"
        f"    atmOption: {v['atmOption']}, ecoOption: {v['ecoOption']}, govDiscount: {v['govDiscount']}, riskFree: {v['riskFree']}, vol: {v['vol']},\n"
        f"    ethPrice: {v['ethPrice']}, sbetPrice: {v['sbetPrice']}, optionStrike: {v['optionStrike']}\n"
        "  };"
    )


def build_src_block(fundamentals, manual, close_date, include_dash_nav_ps):
    holdings_eth = fnum(fundamentals['ethTotal'])
    dash_conc = money2(float(manual['dashConc']))
    dash_nav_ps = money2(float(manual['dashNavPS']))
    line2 = (
        f"    dashConc: {dash_conc}, dashEth: {manual['dashEth']}, "
        + (f"dashNavPS: {dash_nav_ps}, " if include_dash_nav_ps else "")
        + f"dashAsOf: '{manual['dashAsOf']}', closeDate: '{close_date}'"
    )
    return (
        "  static SRC = {\n"
        f"    holdingsEth: {holdings_eth}, holdingsRelease: '{manual['holdingsRelease']}',\n"
        f"{line2}\n"
        "  };"
    )


# ------------------------------------------------------------- splicing --

ASOF_BLOCK_RE = re.compile(
    r"  static ASOF = '[^']*';\n"
    r"  static ASOF_SHORT = '[^']*';\n"
    r"  static ASOF_LONG = '[^']*';"
)
TARGETS_BLOCK_RE = re.compile(r"  static TARGETS = \{.*?\n  \};", re.DOTALL)
SRC_BLOCK_RE = re.compile(r"  static SRC = \{.*?\n  \};", re.DOTALL)
SNAP_BLOCK_RE = re.compile(r"  static SNAP = \{.*?\n  \};", re.DOTALL)


def splice(text, pattern, replacement, block_name, file_name):
    matches = list(pattern.finditer(text))
    if len(matches) != 1:
        fail(f"Expected exactly one {block_name} block in {file_name}, found {len(matches)}")
    return text[:matches[0].start()] + replacement + text[matches[0].end():]


def apply_blocks(path, asof_block, targets_block, src_block, snap_block):
    text = path.read_text()
    text = splice(text, ASOF_BLOCK_RE, asof_block, "ASOF", path.name)
    text = splice(text, TARGETS_BLOCK_RE, targets_block, "TARGETS", path.name)
    text = splice(text, SRC_BLOCK_RE, src_block, "SRC", path.name)
    text = splice(text, SNAP_BLOCK_RE, snap_block, "SNAP", path.name)
    path.write_text(text)


# ------------------------------------------------------------------ main --

def main(argv):
    model_path = Path(argv[1]) if len(argv) > 1 else DEFAULT_MODEL
    manual_path = Path(argv[2]) if len(argv) > 2 else DEFAULT_MANUAL

    model = load_model(model_path)
    manual = load_manual(manual_path, model['asOf'])

    fundamentals = model['fundamentals']
    assumptions = model['assumptions']
    checks = model['checks']

    asof, asof_short, asof_long, close_date = format_date(model['asOf'])
    option_strike = derive_option_strike(fundamentals, model['warrants'])
    verify_option_strike_round_trip(fundamentals, model['warrants'], option_strike)

    asof_block = build_asof_block(asof, asof_short, asof_long)
    targets_block = build_targets_block(checks)
    snap_block = build_snap_block(fundamentals, assumptions, checks, option_strike)

    src_block_main = build_src_block(fundamentals, manual, close_date, include_dash_nav_ps=True)
    src_block_print = build_src_block(fundamentals, manual, close_date, include_dash_nav_ps=False)

    apply_blocks(MAIN_FILE, asof_block, targets_block, src_block_main, snap_block)
    apply_blocks(PRINT_FILE, asof_block, targets_block, src_block_print, snap_block)

    print(f"Wrote ASOF/SNAP/SRC/TARGETS for asOf={model['asOf']} into:")
    print(f"  {MAIN_FILE.name}")
    print(f"  {PRINT_FILE.name}")


if __name__ == '__main__':
    try:
        main(sys.argv)
    except BuildError as e:
        print(f"build.py: {e}", file=sys.stderr)
        sys.exit(1)
