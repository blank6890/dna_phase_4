import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { get, send } from "../api.js";
import { Alert, Bib, DataTable, SqlPanel, seriesName } from "../components/ui.jsx";
import { MemberPicker, emptyMember, toApiMember } from "../components/MemberPicker.jsx";

export default function MyRegistration() {
  const [params, setParams] = useSearchParams();
  const [id, setId] = useState(params.get("id") || "");
  const [data, setData] = useState(null);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [lastSql, setLastSql] = useState("");
  const [replacing, setReplacing] = useState(null);
  const [replacement, setReplacement] = useState(emptyMember());
  const [weight, setWeight] = useState("");

  async function load(regId) {
    setError("");
    try {
      setData(await get(`/api/registrations/${regId}`));
    } catch (e) {
      setData(null); setError(e.message);
    }
  }
  useEffect(() => { if (params.get("id")) load(params.get("id")); }, [params]);

  const reg = data?.registration;

  async function cancel() {
    if (!window.confirm("Cancel this registration? Cancelling 30 or more days before the race refunds the fee minus 10 €.")) return;
    setError(""); setMessage("");
    try {
      const r = await send("POST", `/api/registrations/${reg.Registration_ID}/cancel`);
      setMessage(r.message); setLastSql(r.sql); load(reg.Registration_ID);
    } catch (e) { setError(e.message); }
  }

  async function replace(e) {
    e.preventDefault();
    setError(""); setMessage("");
    try {
      const member = toApiMember(replacing, replacement, replacing === "CARRIED" ? weight : undefined);
      const r = await send("PATCH", `/api/entries/${reg.Entry_ID}/roles/${replacing}`, member);
      setMessage(r.message); setLastSql(r.sql); setReplacing(null); setReplacement(emptyMember()); setWeight("");
      load(reg.Registration_ID);
    } catch (err) { setError(err.message); }
  }

  return (
    <>
      <h1>Manage my registration</h1>
      <form className="toolbar" onSubmit={(e) => { e.preventDefault(); if (id) setParams({ id }); }}>
        <label className="field field--inline"><span>Registration number</span>
          <input value={id} onChange={(e) => setId(e.target.value.replace(/\D/g, ""))} inputMode="numeric" required /></label>
        <button className="btn" type="submit">Look up</button>
      </form>
      <Alert>{error}</Alert>
      <Alert kind="success">{message}</Alert>

      {reg && (
        <section className="section">
          <h2>{reg.Team_Name ? `${reg.Team_Name}: ` : ""}{reg.Display_Name}</h2>
          <div className="grid-2" style={{ marginBottom: "1rem" }}>
            <div className="stat"><strong>{seriesName(reg.Series_Code)} {reg.Edition_Year}</strong><span className="sub">Race starts {reg.Race_Start}</span></div>
            <div className="stat"><strong>{reg.Status}</strong>
              <span className="sub">Bib <Bib n={reg.Bib_No} />, fee {reg.Fee_Paid_EUR.toFixed(2)} € ({reg.Payment_Status.toLowerCase()})
                {reg.Status === "Cancelled" && `, refund ${reg.Refund_EUR.toFixed(2)} €`}</span></div>
          </div>
          <DataTable rows={data.rows} columns={[
            { key: "Role_Name", label: "Role" },
            { key: "Last_Name", label: "Name", render: (m) => `${m.First_Name} ${m.Last_Name}` },
            { key: "Measured_Weight_kg", label: "Weight (kg)", num: true, render: (m) => m.Measured_Weight_kg ?? "" },
            { key: "act", label: "", render: (m) => reg.Status === "Registered" && !reg.Has_Results ? (
              <button className="btn btn--quiet btn--small" onClick={() => { setReplacing(m.Role_Code); setReplacement(emptyMember()); }}>Replace</button>
            ) : null },
          ]} />
          {replacing && (
            <form onSubmit={replace} style={{ marginTop: "1rem" }}>
              <MemberPicker idPrefix="replace" legend={`New ${data.rows.find((m) => m.Role_Code === replacing)?.Role_Name.toLowerCase()}`}
                            value={replacement} onChange={setReplacement}
                            weight={replacing === "CARRIED" ? weight : undefined}
                            onWeight={replacing === "CARRIED" ? setWeight : undefined} />
              <div className="form-actions">
                <button className="btn" type="submit">Replace member</button>
                <button className="btn btn--quiet" type="button" onClick={() => setReplacing(null)}>Keep current member</button>
              </div>
            </form>
          )}
          {reg.Status === "Registered" && (
            <div className="form-actions">
              <button className="btn btn--danger" onClick={cancel}>Cancel registration</button>
              <span className="sub">{reg.Has_Results ? "This registration already has results and cannot be cancelled." : "Up to 30 days before the race the fee is refunded minus 10 €; later cancellations are not refunded."}</span>
            </div>
          )}
          <SqlPanel sql={lastSql || data.sql} />
        </section>
      )}
    </>
  );
}
