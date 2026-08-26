/* @ds-bundle: {"format":4,"namespace":"OtherwhereCapitalDesignSystem_101f00","components":[{"name":"GridCell","sourcePath":"components/controls/GridCell.jsx"},{"name":"SliderControl","sourcePath":"components/controls/SliderControl.jsx"},{"name":"BridgeRow","sourcePath":"components/data/BridgeRow.jsx"},{"name":"NavBar","sourcePath":"components/navigation/NavBar.jsx"}],"sourceHashes":{"components/controls/GridCell.jsx":"fdbcfcb8a98e","components/controls/SliderControl.jsx":"551b44c9af2d","components/data/BridgeRow.jsx":"09901ae03089","components/navigation/NavBar.jsx":"3bd1ad763c9b"},"inlinedExternals":[],"unexposedExports":[]} */

(() => {

const __ds_ns = (window.OtherwhereCapitalDesignSystem_101f00 = window.OtherwhereCapitalDesignSystem_101f00 || {});

const __ds_scope = {};

(__ds_ns.__errors = __ds_ns.__errors || []);

// components/controls/GridCell.jsx
try { (() => {
/**
 * GridCell — compact cell for cross-segment grid inputs.
 * Stacks a formatted value above a range slider, centered.
 * Set `isStatic` for read-only display cells (WACC output rows, derived values).
 */
function GridCell({
  value,
  min = 0,
  max = 1,
  step = 0.01,
  unit = '',
  onChange,
  isStatic = false,
  caption
}) {
  function fmt(v) {
    if (unit === '%') return `${(v * 100).toFixed(2)}%`;
    if (unit === '%-raw') return `${Number(v).toFixed(2)}%`;
    if (unit === 'x') return `${Number(v).toFixed(2)}×`;
    if (Number.isInteger(Number(v))) return String(v);
    return `${Number(v).toFixed(2)}`;
  }
  return /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      gap: '2px',
      padding: '0 6px'
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      fontFamily: 'var(--font-mono)',
      fontSize: isStatic ? '13px' : '12px',
      fontWeight: isStatic ? '500' : '400',
      color: isStatic ? 'var(--navy)' : 'var(--navy)',
      fontVariantNumeric: 'tabular-nums'
    }
  }, fmt(value)), caption && /*#__PURE__*/React.createElement("span", {
    style: {
      fontFamily: 'var(--font-mono)',
      fontSize: '8px',
      color: 'var(--cat-label)',
      whiteSpace: 'nowrap'
    }
  }, caption), !isStatic && /*#__PURE__*/React.createElement("input", {
    type: "range",
    min: min,
    max: max,
    step: step,
    value: value,
    onChange: e => onChange && onChange(Number(e.target.value)),
    style: {
      width: '100%'
    }
  }));
}
Object.assign(__ds_scope, { GridCell });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/controls/GridCell.jsx", error: String((e && e.message) || e) }); }

// components/controls/SliderControl.jsx
try { (() => {
/**
 * SliderControl — range input with label and live formatted value.
 * Renders a label row (text left, formatted value right) above a
 * styled range input. Matches the App.css `.slider-control` pattern.
 */
function SliderControl({
  label,
  value,
  min = 0,
  max = 100,
  step = 1,
  unit = '',
  onChange,
  formatValue
}) {
  function fmt(v) {
    if (formatValue) return formatValue(v);
    if (unit === '%') return `${(v * 100).toFixed(1)}%`;
    if (unit === '%-raw') return `${v.toFixed(1)}%`;
    if (unit === '$') return `$${Number(v).toLocaleString('en-US')}`;
    if (unit === '$M') return `$${Math.round(v).toLocaleString('en-US')}M`;
    if (unit === 'x') return `${Number(v).toFixed(2)}×`;
    if (unit === 'yr') return `${Number(v).toFixed(1)} yr`;
    if (Number.isInteger(v)) return String(v);
    return `${Number(v).toFixed(2)}`;
  }
  return /*#__PURE__*/React.createElement("label", {
    style: {
      display: 'block',
      cursor: 'pointer'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      justifyContent: 'space-between',
      marginBottom: '2px'
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: '11px',
      color: 'var(--navy-mid)',
      lineHeight: '1.2',
      fontFamily: 'var(--font-sans)'
    }
  }, label), /*#__PURE__*/React.createElement("span", {
    style: {
      fontFamily: 'var(--font-mono)',
      fontSize: '11px',
      color: 'var(--navy)',
      whiteSpace: 'nowrap',
      fontVariantNumeric: 'tabular-nums'
    }
  }, fmt(value))), /*#__PURE__*/React.createElement("input", {
    type: "range",
    min: min,
    max: max,
    step: step,
    value: value,
    onChange: e => onChange && onChange(Number(e.target.value))
  }));
}
Object.assign(__ds_scope, { SliderControl });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/controls/SliderControl.jsx", error: String((e && e.message) || e) }); }

// components/data/BridgeRow.jsx
try { (() => {
/**
 * BridgeRow — financial summary row with label/value pair.
 * Used in capital structure bridge tables, share count bridges,
 * net cash bridges, and unlock schedule output columns.
 *
 * variant:
 *   'default'   — standard row, navy-mid label, mono value
 *   'total'     — subtotal separator, semibold, slightly larger value
 *   'highlight' — bg-subtle background, main KPI row (per-share price, net cash)
 *   'muted'     — label and value in navy-light (reference-only rows)
 *   'negative'  — value rendered in var(--neg) red-orange
 */
function BridgeRow({
  label,
  value,
  variant = 'default'
}) {
  const isTotal = variant === 'total';
  const isHighlight = variant === 'highlight';
  const isMuted = variant === 'muted';
  const isNegative = variant === 'negative';
  return /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center',
      padding: isHighlight ? '8px 6px' : '6px 0',
      borderBottom: isHighlight ? 'none' : '1px solid var(--border)',
      background: isHighlight ? 'var(--bg-subtle)' : 'transparent',
      margin: isHighlight ? '6px -6px 0' : '0',
      fontSize: '11px',
      fontFamily: 'var(--font-sans)',
      fontWeight: isTotal || isHighlight ? '600' : '400',
      color: isMuted ? 'var(--navy-light)' : 'var(--navy-mid)'
    }
  }, /*#__PURE__*/React.createElement("span", null, label), /*#__PURE__*/React.createElement("strong", {
    style: {
      fontFamily: 'var(--font-mono)',
      fontWeight: isHighlight ? '500' : '400',
      fontSize: isHighlight ? '15px' : isTotal ? '12px' : '11px',
      color: isNegative ? 'var(--neg)' : isMuted ? 'var(--navy-light)' : 'var(--navy)',
      fontVariantNumeric: 'tabular-nums'
    }
  }, value));
}
Object.assign(__ds_scope, { BridgeRow });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/data/BridgeRow.jsx", error: String((e && e.message) || e) }); }

// components/navigation/NavBar.jsx
try { (() => {
/**
 * NavBar — application top navigation.
 * Renders the 3px gold topbar stripe + the 52px nav row.
 * Brand: ticker mark | divider | company subtitle (left).
 * Actions: section label + optional action buttons/links (right).
 */
function NavBar({
  ticker = 'SPCX',
  company,
  section,
  actions = []
}) {
  return /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("div", {
    style: {
      height: '3px',
      background: 'var(--gold)'
    }
  }), /*#__PURE__*/React.createElement("nav", {
    style: {
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      padding: '0 40px',
      height: '52px',
      borderBottom: '1px solid var(--border)'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      alignItems: 'center',
      gap: '16px'
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      fontFamily: 'var(--font-mono)',
      fontSize: '13px',
      fontWeight: '500',
      letterSpacing: '0.14em',
      color: 'var(--navy)'
    }
  }, ticker), company && /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("span", {
    style: {
      width: '1px',
      height: '14px',
      background: 'var(--border-mid)'
    }
  }), /*#__PURE__*/React.createElement("span", {
    style: {
      fontFamily: 'var(--font-sans)',
      fontSize: '11px',
      letterSpacing: '0.07em',
      textTransform: 'uppercase',
      color: 'var(--navy-light)'
    }
  }, company))), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      alignItems: 'center',
      gap: '20px'
    }
  }, section && /*#__PURE__*/React.createElement("span", {
    style: {
      fontFamily: 'var(--font-mono)',
      fontSize: '10px',
      letterSpacing: '0.12em',
      textTransform: 'uppercase',
      color: 'var(--navy-light)'
    }
  }, section), actions.map((action, i) => action.href ? /*#__PURE__*/React.createElement("a", {
    key: i,
    href: action.href,
    target: action.external ? '_blank' : undefined,
    rel: action.external ? 'noreferrer' : undefined,
    style: {
      fontFamily: 'var(--font-sans)',
      fontSize: '11px',
      color: 'var(--navy-mid)',
      textDecoration: 'none',
      borderBottom: '1px solid var(--border-mid)',
      paddingBottom: '1px',
      letterSpacing: '0.03em'
    }
  }, action.label, action.external ? ' ↗' : '') : /*#__PURE__*/React.createElement("button", {
    key: i,
    onClick: action.onClick,
    style: {
      fontFamily: 'var(--font-mono)',
      fontSize: '9px',
      fontWeight: '500',
      letterSpacing: '0.14em',
      textTransform: 'uppercase',
      color: 'var(--navy-light)',
      background: 'none',
      border: '1px solid var(--border-mid)',
      padding: '4px 10px',
      cursor: 'pointer'
    }
  }, action.label)))));
}
Object.assign(__ds_scope, { NavBar });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/navigation/NavBar.jsx", error: String((e && e.message) || e) }); }

__ds_ns.GridCell = __ds_scope.GridCell;

__ds_ns.SliderControl = __ds_scope.SliderControl;

__ds_ns.BridgeRow = __ds_scope.BridgeRow;

__ds_ns.NavBar = __ds_scope.NavBar;

})();
