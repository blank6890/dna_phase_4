import { useEffect, useState } from "react";
import { get } from "../api.js";

export const SERIES = [
  { code: "MAIN", name: "World Championship" },
  { code: "WOMEN", name: "Women" },
  { code: "M40", name: "Senior +40" },
  { code: "TEAM", name: "Team" },
  { code: "SPR", name: "Sprint" },
];
export const seriesName = (code) => SERIES.find((s) => s.code === code)?.name ?? code;

/** A race bib: the one decorative element of the site. */
export function Bib({ n }) {
  if (n === null || n === undefined) return <span className="bib bib--none">–</span>;
  return <span className="bib" aria-label={`Bib ${n}`}>{n}</span>;
}

export function Alert({ kind = "error", children }) {
  if (!children) return null;
  return (
    <div className={`alert alert--${kind}`} role={kind === "error" ? "alert" : "status"}>
      {children}
    </div>
  );
}

/** The exact SQL the backend ran for this view, collapsed by default. */
export function SqlPanel({ sql }) {
  if (!sql) return null;
  return (
    <details className="sql">
      <summary>Show SQL</summary>
      <pre>{sql}</pre>
    </details>
  );
}

/** rowKey: stable id per row, so per-row state (open forms, inputs) follows its row when rows re-sort. */
export function DataTable({ columns, rows, empty = "Nothing to show.", rowClass, rowKey }) {
  if (!rows) return null;
  if (rows.length === 0) return <p className="empty">{empty}</p>;
  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>{columns.map((c) => <th key={c.key} className={c.num ? "num" : undefined}>{c.label}</th>)}</tr>
        </thead>
        <tbody>
          {rows.map((r, i) => (
            <tr key={rowKey ? rowKey(r) : i} className={rowClass ? rowClass(r) : undefined}>
              {columns.map((c) => (
                <td key={c.key} className={c.num ? "num" : undefined}>
                  {c.render ? c.render(r) : r[c.key] ?? ""}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function Tabs({ items, value, onChange, label }) {
  return (
    <div className="tabs" role="tablist" aria-label={label}>
      {items.map((it) => (
        <button key={it.value} role="tab" aria-selected={it.value === value}
                className={it.value === value ? "tab tab--on" : "tab"} onClick={() => onChange(it.value)}>
          {it.label}
        </button>
      ))}
    </div>
  );
}

/** Edition years from the database (newest first), optionally only years with a given series. */
export function useEditions() {
  const [years, setYears] = useState([]);
  useEffect(() => {
    get("/api/editions").then((b) => setYears(b.rows)).catch(() => setYears([]));
  }, []);
  return years;
}

export function YearSelect({ value, onChange, years, label = "Edition" }) {
  return (
    <label className="field field--inline">
      <span>{label}</span>
      <select value={value} onChange={(e) => onChange(Number(e.target.value))}>
        {years.map((y) => <option key={y.Edition_Year} value={y.Edition_Year}>{y.Edition_Year}</option>)}
      </select>
    </label>
  );
}

/** Load {rows, sql} from an endpoint whenever `deps` change. Data is tagged with the query it
    answers, so a render never pairs new columns with rows from the previous query. */
export function useQuery(path, params, deps) {
  const key = JSON.stringify([path, ...deps]);
  const [state, setState] = useState({ key: null, rows: null, sql: "", error: "", extra: {} });
  const [tick, setTick] = useState(0);
  useEffect(() => {
    if (!path) return;
    let live = true;
    get(path, params)
      .then((b) => live && setState({ key, rows: b.rows, sql: b.sql, error: "", extra: b }))
      .catch((e) => live && setState({ key, rows: null, sql: "", error: e.message, extra: {} }));
    return () => { live = false; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [key, tick]);
  const current = state.key === key;
  return {
    rows: current ? state.rows : null,
    sql: current ? state.sql : "",
    error: current ? state.error : "",
    extra: current ? state.extra : {},
    loading: !current,
    reload: () => setTick((t) => t + 1),
  };
}
