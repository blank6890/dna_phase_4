import { useParams } from "react-router-dom";
import { Alert, Bib, DataTable, SqlPanel, seriesName, useQuery } from "../components/ui.jsx";
import { formatTime } from "../components/formatTime.js";

export default function Person() {
  const { id } = useParams();
  const data = useQuery(`/api/people/${id}`, {}, [id]);
  const p = data.extra.person;
  return (
    <>
      <Alert>{data.error}</Alert>
      {p && (
        <>
          <h1>{p.First_Name} {p.Last_Name}</h1>
          <p className="lead">{p.Citizenship || "Citizenship not recorded"}</p>
          <h2>Competition history</h2>
          <DataTable rows={data.rows} empty="No race entries recorded." columns={[
            { key: "Edition_Year", label: "Year" },
            { key: "Series_Code", label: "Series", render: (r) => seriesName(r.Series_Code) },
            { key: "Role_Name", label: "Role" },
            { key: "Bib_No", label: "Bib", render: (r) => <Bib n={r.Bib_No} /> },
            { key: "Display_Name", label: "Entry", render: (r) => <>{r.Team_Name && <strong>{r.Team_Name}<br /></strong>}{r.Display_Name}</> },
            { key: "Net_Time_s", label: "Result", num: true, render: (r) =>
                r.Registration_Status === "Cancelled" ? "Cancelled"
                  : !r.Result_Status ? "Not raced yet"
                  : r.Result_Status === "Finished" ? `${formatTime(r.Net_Time_s)}${r.Stage !== "Single" ? ` (${r.Stage})` : ""}` : r.Result_Status },
            { key: "Rank_In_Stage", label: "Rank", num: true, render: (r) => r.Rank_In_Stage ? `${r.Rank_In_Stage}.` : "" },
          ]} />
          <SqlPanel sql={data.sql} />
        </>
      )}
    </>
  );
}
