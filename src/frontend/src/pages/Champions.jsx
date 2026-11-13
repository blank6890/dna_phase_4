import { useState } from "react";
import { Alert, DataTable, SERIES, SqlPanel, Tabs, seriesName, useQuery } from "../components/ui.jsx";
import { formatTime } from "../components/formatTime.js";

export default function Champions() {
  const records = useQuery("/api/records", {}, []);
  const champions = useQuery("/api/champions", {}, []);
  const [series, setSeries] = useState("MAIN");
  const list = champions.rows?.filter((r) => r.Series_Code === series);
  return (
    <>
      <h1>Champions and records</h1>
      <section className="section">
        <h2>World records</h2>
        <Alert>{records.error}</Alert>
        <div className="records">
          {records.rows?.map((r) => (
            <div className="record" key={r.Series_Code}>
              <p className="record__series">{seriesName(r.Series_Code)}</p>
              <div className="record__time">{formatTime(r.Best_Time_s)}</div>
              <p>{r.Team_Name ? <strong>{r.Team_Name}: </strong> : null}{r.Display_Name}</p>
              <p className="sub">{r.Countries}, {r.Edition_Year}</p>
            </div>
          ))}
        </div>
        <SqlPanel sql={records.sql} />
      </section>
      <section className="section">
        <h2>Gold medallists</h2>
        <p>Finnish Championships 1992–1995, World Championships from 1996. No races were held in 2020–2021.</p>
        <Tabs label="Series" value={series} onChange={setSeries}
              items={SERIES.map((s) => ({ value: s.code, label: s.name }))} />
        <DataTable rows={list} empty="No champions recorded for this series." columns={[
          { key: "Edition_Year", label: "Year", render: (r) => <>{r.Edition_Year}{r.Championship_Level === "Finnish" && <span className="sub">Finnish Ch.</span>}</> },
          { key: "Display_Name", label: "Champions", render: (r) => <>{r.Team_Name && <strong>{r.Team_Name}<br /></strong>}{r.Display_Name}</> },
          { key: "Countries", label: "Country" },
          { key: "Net_Time_s", label: "Time", num: true, render: (r) => formatTime(r.Net_Time_s) },
        ]} />
        <SqlPanel sql={champions.sql} />
      </section>
    </>
  );
}
