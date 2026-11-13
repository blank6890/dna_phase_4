import { useEffect, useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { Alert, Bib, DataTable, SERIES, SqlPanel, Tabs, YearSelect, useEditions, useQuery } from "../components/ui.jsx";
import { formatGap, formatTime } from "../components/formatTime.js";

const STAGES = ["Heat 1", "Heat 2", "Heat 3", "Final"];

export function resultColumns(series) {
  const digits = series === "SPR" ? 2 : 1;
  return [
    { key: "Rank_In_Stage", label: "Rank", render: (r) => r.Rank_In_Stage ? <span className="rank">{r.Rank_In_Stage}.</span> : r.Status },
    { key: "Bib_No", label: "Bib", render: (r) => <Bib n={r.Bib_No} /> },
    { key: "Display_Name", label: series === "TEAM" ? "Carriers / carried" : "Carrier / carried", render: (r) => (
      <>
        {r.Team_Name && <strong>{r.Team_Name}<br /></strong>}
        {r.Display_Name}
        {r.Adjustments && <span className="penalty">{r.Adjustments}</span>}
      </>
    ) },
    { key: "Countries", label: "Country" },
    { key: "Net_Time_s", label: "Result", num: true, render: (r) => r.Status === "Finished" ? formatTime(r.Net_Time_s) : r.Status },
    { key: "Gap_To_Leader_s", label: "Diff", num: true, render: (r) => formatGap(r.Gap_To_Leader_s, digits) },
  ];
}

export default function Results() {
  const [params, setParams] = useSearchParams();
  const editions = useEditions().filter((e) => e.Series);
  const year = Number(params.get("year")) || 2026;
  const edition = editions.find((e) => e.Edition_Year === year);
  const available = useMemo(() => SERIES.filter((s) => edition?.Series.split(",").includes(s.code)), [edition]);
  const series = params.get("series") || "MAIN";
  const [stage, setStage] = useState("Final");

  useEffect(() => {
    if (available.length && !available.some((s) => s.code === series)) {
      setParams({ year: String(year), series: available[0].code });
    }
  }, [available, series, year, setParams]);

  const data = useQuery("/api/results", { year, series, stage: series === "SPR" ? stage : undefined }, [year, series, stage]);
  const finished = data.rows?.filter((r) => r.Status === "Finished").length ?? 0;

  return (
    <>
      <h1>Results</h1>
      <p className="lead">Every result is ranked by net time: the raw time plus any time penalties from the jury.</p>
      <div className="toolbar">
        <YearSelect years={editions} value={year} onChange={(y) => setParams({ year: String(y), series })} />
      </div>
      <Tabs label="Series" value={series} onChange={(s) => setParams({ year: String(year), series: s })}
            items={available.map((s) => ({ value: s.code, label: s.name }))} />
      {series === "SPR" && (
        <Tabs label="Stage" value={stage} onChange={setStage} items={STAGES.map((s) => ({ value: s, label: s }))} />
      )}
      <Alert>{data.error}</Alert>
      {data.rows && (
        <p className="sub" style={{ marginBottom: "0.5rem" }}>
          {data.rows.length} {data.rows.length === 1 ? "entry" : "entries"}, {finished} finished
        </p>
      )}
      <DataTable rows={data.rows} columns={resultColumns(series)} empty="No results recorded for this race yet."
                 rowClass={(r) => (r.Rank_In_Stage === 1 ? "is-first" : r.Status !== "Finished" ? "is-out" : undefined)} />
      <SqlPanel sql={data.sql} />
    </>
  );
}
