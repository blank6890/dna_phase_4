import { useState } from "react";
import { Alert, DataTable, SqlPanel, Tabs, YearSelect, seriesName, useEditions, useQuery } from "../../components/ui.jsx";
import { formatTime } from "../../components/formatTime.js";

const eur = (v) => `${v.toFixed(2)} €`;
const t = (key) => (r) => formatTime(r[key]);

const REPORTS = {
  "avg-times": { label: "Average times", text: "Average net time of the finishers in each series and edition (Sprint: the final).",
    columns: [{ key: "Edition_Year", label: "Year" }, { key: "Series_Code", label: "Series", render: (r) => seriesName(r.Series_Code) },
              { key: "Avg_Net_Time_s", label: "Average", num: true, render: t("Avg_Net_Time_s") }, { key: "Finishers", label: "Finishers", num: true }] },
  fees: { label: "Fees", text: "Total registration fees paid per edition.",
    columns: [{ key: "Edition_Year", label: "Year" }, { key: "Registrations", label: "Registrations", num: true },
              { key: "Total_Fees_EUR", label: "Fees paid", num: true, render: (r) => eur(r.Total_Fees_EUR) }] },
  "registrations-by-country": { label: "By country", year: true, text: "Number of live registrations per country represented in the edition.",
    columns: [{ key: "Country_Name", label: "Country" }, { key: "ISO_Code", label: "Code" }, { key: "Registrations", label: "Registrations", num: true }] },
  medals: { label: "Medal table", text: "First, second and third places in the World Championship main series, all editions, by country.",
    columns: [{ key: "Country_Name", label: "Country" }, { key: "Gold", label: "Gold", num: true }, { key: "Silver", label: "Silver", num: true }, { key: "Bronze", label: "Bronze", num: true }] },
  backpacks: { label: "Backpacks", text: "Carried people under the 49 kg minimum and the backpack weight each must carry.",
    columns: [{ key: "Edition_Year", label: "Year" }, { key: "Series_Code", label: "Series", render: (r) => seriesName(r.Series_Code) },
              { key: "Last_Name", label: "Carried person", render: (r) => `${r.First_Name} ${r.Last_Name}` },
              { key: "Carried_Weight_kg", label: "Weight", num: true, render: (r) => `${r.Carried_Weight_kg} kg` },
              { key: "Required_Backpack_kg", label: "Backpack", num: true, render: (r) => `${r.Required_Backpack_kg} kg` }] },
  "multi-series": { label: "Multi-series", year: true, text: "People who raced in more than one series in the same edition, with their role and result in each.",
    columns: [{ key: "Last_Name", label: "Person", render: (r) => `${r.First_Name} ${r.Last_Name}` },
              { key: "Series_Code", label: "Series", render: (r) => seriesName(r.Series_Code) }, { key: "Role_Name", label: "Role" },
              { key: "Net_Time_s", label: "Result", num: true, render: (r) => r.Status === "Finished" ? `${formatTime(r.Net_Time_s)}${r.Stage !== "Single" ? ` (${r.Stage})` : ""}` : r.Status || "Not raced" }] },
  income: { label: "Income", text: "Per edition: registration fees net of refunds, protest fees (150 € each) and paid booth fees.",
    columns: [{ key: "Edition_Year", label: "Year" },
              { key: "Registration_Fees_Net_EUR", label: "Registration fees", num: true, render: (r) => eur(r.Registration_Fees_Net_EUR) },
              { key: "Protest_Fees_EUR", label: "Protest fees", num: true, render: (r) => eur(r.Protest_Fees_EUR) },
              { key: "Booth_Fees_EUR", label: "Booth fees", num: true, render: (r) => eur(r.Booth_Fees_EUR) }] },
  protests: { label: "Protests", text: "Protests filed and upheld per race, and the officials who voted.",
    columns: [{ key: "Edition_Year", label: "Year" }, { key: "Series_Code", label: "Race", render: (r) => seriesName(r.Series_Code) },
              { key: "Filed", label: "Filed", num: true }, { key: "Upheld", label: "Upheld", num: true }, { key: "Pending", label: "Pending", num: true },
              { key: "Voters", label: "Voted", render: (r) => r.Voters || "No votes yet" }] },
  "above-average": { label: "Faster than average", year: true, text: "Countries whose average main-series time beat the average of all finishers in the edition.",
    columns: [{ key: "Country_Name", label: "Country" }, { key: "Country_Avg_s", label: "Country average", num: true, render: t("Country_Avg_s") },
              { key: "Edition_Avg_s", label: "Edition average", num: true, render: t("Edition_Avg_s") }, { key: "Finishers", label: "Finishers", num: true }] },
};

export default function Reports() {
  const editions = useEditions().filter((e) => e.Series);
  const [name, setName] = useState("medals");
  const [year, setYear] = useState(2026);
  const report = REPORTS[name];
  const data = useQuery(`/api/reports/${name}`, report.year ? { year } : {}, [name, year]);
  return (
    <>
      <h1>Committee reports</h1>
      <Tabs label="Report" value={name} onChange={setName}
            items={Object.entries(REPORTS).map(([value, r]) => ({ value, label: r.label }))} />
      <p>{report.text}</p>
      {report.year && <div className="toolbar"><YearSelect years={editions} value={year} onChange={setYear} /></div>}
      <Alert>{data.error}</Alert>
      <DataTable rows={data.rows} columns={report.columns} empty="This report has no rows for the chosen edition." />
      <SqlPanel sql={data.sql} />
    </>
  );
}
