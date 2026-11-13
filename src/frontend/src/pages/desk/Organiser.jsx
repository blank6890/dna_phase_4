import { useState } from "react";
import { send } from "../../api.js";
import { Alert, Bib, DataTable, SERIES, SqlPanel, Tabs, YearSelect, useEditions, useQuery } from "../../components/ui.jsx";

function AwardForm({ reg, prizes, onDone }) {
  const [prize, setPrize] = useState("");
  return (
    <form className="inline-form" onSubmit={(e) => { e.preventDefault(); if (prize) onDone(reg, Number(prize)); }}>
      <select value={prize} onChange={(e) => setPrize(e.target.value)} aria-label={`Prize for bib ${reg.Bib_No}`}>
        <option value="">Award a prize…</option>
        {prizes.map((p) => <option key={p.Prize_ID} value={p.Prize_ID}>{p.Prize_Name}</option>)}
      </select>
      <button className="btn btn--quiet btn--small" type="submit" disabled={!prize}>Award</button>
    </form>
  );
}

export default function Organiser() {
  const editions = useEditions().filter((e) => e.Series);
  const [year, setYear] = useState(2027);
  const [series, setSeries] = useState("MAIN");
  const regs = useQuery("/api/registrations", { year, series }, [year, series]);
  const prizes = useQuery("/api/prizes", { series }, [series]);
  const persons = useQuery(`/api/editions/${year}/persons`, {}, [year]);
  const heaviest = useQuery(`/api/editions/${year}/heaviest-carried`, {}, [year]);
  const loose = useQuery("/api/entries/unregistered", {}, []);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [lastSql, setLastSql] = useState("");

  async function act(fn, confirmText) {
    if (confirmText && !window.confirm(confirmText)) return;
    setMessage(""); setError("");
    try {
      const r = await fn();
      setMessage(r.message); setLastSql(r.sql);
      regs.reload(); loose.reload(); persons.reload();
    } catch (e) { setError(e.message); }
  }

  return (
    <>
      <h1>Organiser desk</h1>
      <p className="desk-note">Staff pages for the organising office. This student project has no login: anyone running it locally acts as staff.</p>
      <div className="toolbar"><YearSelect years={editions} value={year} onChange={setYear} /></div>
      <Alert kind="success">{message}</Alert>
      <Alert>{error}</Alert>
      {lastSql && <SqlPanel sql={lastSql} />}

      <section className="section">
        <h2>Registrations for {year}</h2>
        <Tabs label="Series" value={series} onChange={setSeries} items={SERIES.map((s) => ({ value: s.code, label: s.name }))} />
        <DataTable rows={regs.rows} empty="No registrations for this race." rowClass={(r) => (r.Status === "Cancelled" ? "is-out" : undefined)} columns={[
          { key: "Registration_ID", label: "No.", num: true },
          { key: "Bib_No", label: "Bib", render: (r) => <Bib n={r.Bib_No} /> },
          { key: "Display_Name", label: "Entry", render: (r) => <>{r.Team_Name && <strong>{r.Team_Name}<br /></strong>}{r.Display_Name}<span className="sub">{r.Countries}</span></> },
          { key: "Registered_At", label: "Registered" },
          { key: "Status", label: "Status", render: (r) => r.Status === "Cancelled" ? `Cancelled, refund ${r.Refund_EUR.toFixed(2)} €` : `${r.Payment_Status}, ${r.Fee_Paid_EUR.toFixed(2)} €` },
          { key: "Required_Backpack_kg", label: "Backpack", num: true, render: (r) => r.Required_Backpack_kg > 0 ? `${r.Required_Backpack_kg} kg` : "" },
          { key: "act", label: "Actions", render: (r) => (
            <>
              {prizes.rows && <AwardForm reg={r} prizes={prizes.rows}
                onDone={(reg, prize) => act(() => send("POST", "/api/awards", { prize_id: prize, registration_id: reg.Registration_ID }))} />}
              <button className="btn btn--danger" style={{ marginTop: "0.35rem" }}
                      onClick={() => act(() => send("DELETE", `/api/registrations/${r.Registration_ID}`),
                                         `Delete registration ${r.Registration_ID}? Only registrations that never ran can be deleted.`)}>
                Delete
              </button>
            </>
          ) },
        ]} />
        <SqlPanel sql={regs.sql} />
      </section>

      <div className="grid-2">
        <section className="section">
          <h2>Heaviest carried person, {year}</h2>
          <DataTable rows={heaviest.rows} empty="No carried weights recorded for this edition." columns={[
            { key: "Last_Name", label: "Name", render: (r) => `${r.First_Name} ${r.Last_Name}` },
            { key: "Measured_Weight_kg", label: "Weight", num: true, render: (r) => `${r.Measured_Weight_kg} kg` },
            { key: "Series_Code", label: "Series" },
            { key: "Bib_No", label: "Bib", render: (r) => <Bib n={r.Bib_No} /> },
          ]} />
          <SqlPanel sql={heaviest.sql} />
        </section>
        <section className="section">
          <h2>Entries with no registrations</h2>
          <DataTable rows={loose.rows} empty="Every entry is registered for at least one race." columns={[
            { key: "Entry_ID", label: "Entry", num: true },
            { key: "Display_Name", label: "Members", render: (r) => <>{r.Team_Name && <strong>{r.Team_Name}<br /></strong>}{r.Display_Name}</> },
            { key: "act", label: "", render: (r) => (
              <button className="btn btn--danger" onClick={() => act(() => send("DELETE", `/api/entries/${r.Entry_ID}`),
                `Delete entry ${r.Entry_ID}? The people stay in the database.`)}>Delete entry</button>
            ) },
          ]} />
          <SqlPanel sql={loose.sql} />
        </section>
      </div>

      <section className="section">
        <h2>Everyone registered in {year}</h2>
        <p>First name, last name and date of birth of every person with a live registration in this edition.</p>
        <DataTable rows={persons.rows} empty="Nobody is registered for this edition yet." columns={[
          { key: "First_Name", label: "First name" },
          { key: "Last_Name", label: "Last name" },
          { key: "Date_of_Birth", label: "Date of birth", render: (r) => r.Date_of_Birth || "Not recorded" },
        ]} />
        <SqlPanel sql={persons.sql} />
      </section>
    </>
  );
}
