import { useState } from "react";
import { Alert, Bib, DataTable, SERIES, SqlPanel, Tabs, YearSelect, useEditions, useQuery } from "../components/ui.jsx";

function Entries() {
  const editions = useEditions().filter((e) => e.Series);
  const [year, setYear] = useState(2027);
  const [series, setSeries] = useState("MAIN");
  const [country, setCountry] = useState("");
  const [applied, setApplied] = useState("");
  const data = useQuery("/api/entries", { year, series, country: applied || undefined }, [year, series, applied]);
  return (
    <>
      <form className="toolbar" onSubmit={(e) => { e.preventDefault(); setApplied(country.trim().toUpperCase()); }}>
        <YearSelect years={editions} value={year} onChange={setYear} />
        <label className="field field--inline">
          <span>Country code</span>
          <input value={country} onChange={(e) => setCountry(e.target.value)} placeholder="e.g. FIN" maxLength={3} size={6} />
        </label>
        <button className="btn btn--quiet" type="submit">Filter</button>
        {applied && <button className="btn btn--quiet" type="button" onClick={() => { setCountry(""); setApplied(""); }}>Show all countries</button>}
      </form>
      <Tabs label="Series" value={series} onChange={setSeries} items={SERIES.map((s) => ({ value: s.code, label: s.name }))} />
      <Alert>{data.error}</Alert>
      {data.rows && <p className="sub">{data.rows.length} registered{applied ? ` from ${applied}` : ""}</p>}
      <DataTable rows={data.rows} empty="No confirmed registrations match these filters yet." columns={[
        { key: "Bib_No", label: "Bib", render: (r) => <Bib n={r.Bib_No} /> },
        ...(series === "TEAM" ? [{ key: "Team_Name", label: "Team" }] : []),
        { key: "Carriers", label: series === "TEAM" ? "Carriers" : "Carrier" },
        { key: "Carried", label: "Carried" },
        { key: "Countries", label: "Country" },
      ]} />
      <SqlPanel sql={data.sql} />
    </>
  );
}

function Teams() {
  const data = useQuery("/api/teams", {}, []);
  return (
    <>
      <p>Every team that has entered the team competition, with the organisation it represents.</p>
      <DataTable rows={data.rows} columns={[
        { key: "Team_Name", label: "Team" },
        { key: "Represented_Organisation", label: "Represents", render: (r) => r.Represented_Organisation || "–" },
      ]} />
      <SqlPanel sql={data.sql} />
    </>
  );
}

export default function Competitors() {
  const [tab, setTab] = useState("entries");
  return (
    <>
      <h1>Registered competitors</h1>
      <p className="lead">Pairs and teams by series. The list updates as soon as a registration is confirmed.</p>
      <Tabs label="View" value={tab} onChange={setTab}
            items={[{ value: "entries", label: "Competitors by series" }, { value: "teams", label: "Teams" }]} />
      {tab === "entries" ? <Entries /> : <Teams />}
    </>
  );
}
