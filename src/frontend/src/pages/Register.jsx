import { useState } from "react";
import { Link } from "react-router-dom";
import { send } from "../api.js";
import { Alert, Bib, SqlPanel } from "../components/ui.jsx";
import { MemberPicker, emptyMember, toApiMember } from "../components/MemberPicker.jsx";

const YEAR = 2027;
const OPTIONS = [
  ["MAIN", "World Championship, main series (55 € per pair)"],
  ["WOMEN", "Women's main series (55 € per pair)"],
  ["M40", "+40 series, carrier aged 40 or over (55 € per pair)"],
  ["SPR", "Sprint (55 € per pair)"],
  ["TEAM", "Team series: three carriers, one carried (160 € per team)"],
];

export default function Register() {
  const [series, setSeries] = useState("MAIN");
  const team = series === "TEAM";
  const [members, setMembers] = useState({ CARRIER_1: emptyMember(), CARRIER_2: emptyMember(), CARRIER_3: emptyMember(), CARRIED: emptyMember() });
  const [weight, setWeight] = useState("");
  const [teamName, setTeamName] = useState("");
  const [organisation, setOrganisation] = useState("");
  const [countries, setCountries] = useState("FIN");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [done, setDone] = useState(null);

  const roles = team ? ["CARRIER_1", "CARRIER_2", "CARRIER_3", "CARRIED"] : ["CARRIER_1", "CARRIED"];
  const label = { CARRIER_1: team ? "Carrier 1" : "Carrier", CARRIER_2: "Carrier 2", CARRIER_3: "Carrier 3", CARRIED: "Carried person" };

  async function submit(e) {
    e.preventDefault();
    setError(""); setDone(null); setBusy(true);
    try {
      const payload = {
        year: YEAR, series, entry_type: team ? "Team" : "Pair",
        team_name: team ? teamName : null, organisation: team ? organisation || null : null,
        countries: countries.split(/[\s,/]+/).filter(Boolean).map((c) => c.toUpperCase()),
        members: roles.map((r) => toApiMember(r, members[r], r === "CARRIED" ? weight : undefined)),
      };
      for (const m of payload.members) {
        if (m.person_id === null) throw new Error("Choose a person for every role, or switch to “New person”.");
      }
      setDone(await send("POST", "/api/registrations", payload));
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      <h1>Register for the 2027 championships</h1>
      <p className="lead">Registration is open from 1 November 2026 until Wednesday 30 June 2027 at 10 pm (Finnish time).</p>
      <p>
        Each series is a separate registration. The carrier must be at least 18 (40 in the +40 series) and the carried
        person at least 17 on race day. A registration can be cancelled up to 30 days before the race for a 10 € fee.
      </p>

      {done ? (
        <div className="card-panel">
          <Alert kind="success">Registered. Your registration number is {done.registration_id}.</Alert>
          <p>Bib number <Bib n={done.bib_no} />, participation fee {done.fee.toFixed(2)} € paid.</p>
          <p>Keep the registration number: you need it to <Link to={`/my-registration?id=${done.registration_id}`}>manage or cancel your registration</Link>.</p>
          <button className="btn btn--quiet" onClick={() => setDone(null)}>Register another pair or team</button>
          <SqlPanel sql={done.sql} />
        </div>
      ) : (
        <form onSubmit={submit}>
          <fieldset>
            <legend>Series</legend>
            <div className="form-row">
              <label className="field"><span>Series</span>
                <select value={series} onChange={(e) => setSeries(e.target.value)}>
                  {OPTIONS.map(([v, t]) => <option key={v} value={v}>{t}</option>)}
                </select></label>
              <label className="field"><span>Countries represented (ISO codes)</span>
                <input required value={countries} onChange={(e) => setCountries(e.target.value)} placeholder="FIN or USA/LTU" /></label>
              {team && <>
                <label className="field"><span>Team name</span>
                  <input required value={teamName} onChange={(e) => setTeamName(e.target.value)} /></label>
                <label className="field"><span>Organisation represented (optional)</span>
                  <input value={organisation} onChange={(e) => setOrganisation(e.target.value)} /></label>
              </>}
            </div>
          </fieldset>
          {roles.map((r) => (
            <MemberPicker key={r} idPrefix={r} legend={label[r]} value={members[r]}
                          onChange={(v) => setMembers((m) => ({ ...m, [r]: v }))}
                          weight={r === "CARRIED" ? weight : undefined}
                          onWeight={r === "CARRIED" ? setWeight : undefined} />
          ))}
          <Alert>{error}</Alert>
          <div className="form-actions">
            <button className="btn" type="submit" disabled={busy}>{busy ? "Registering…" : "Register and pay"}</button>
            <span className="sub">The fee is taken from the race; payment is recorded as paid.</span>
          </div>
        </form>
      )}
    </>
  );
}
