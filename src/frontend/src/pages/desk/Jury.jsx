import { useEffect, useState } from "react";
import { get, send } from "../../api.js";
import { Alert, Bib, DataTable, SERIES, SqlPanel, Tabs, YearSelect, seriesName, useEditions, useQuery } from "../../components/ui.jsx";
import { formatGap, formatTime } from "../../components/formatTime.js";

const STAGES_HEATS = ["Heat 1", "Heat 2", "Heat 3", "Final"];

function nowLocal() {
  const d = new Date(Date.now() - new Date().getTimezoneOffset() * 60000);
  return d.toISOString().slice(0, 16);
}

/** Edit-time and add-penalty controls for one result row. */
function RowActions({ row, stage, official, act }) {
  const [mode, setMode] = useState(null);
  const [time, setTime] = useState(row.Raw_Time_s ?? "");
  const [status, setStatus] = useState(row.Status);
  const [seconds, setSeconds] = useState("15");
  const [reason, setReason] = useState("");
  if (!mode) {
    return (
      <div className="inline-form">
        <button className="btn btn--quiet btn--small" onClick={() => setMode("time")}>Edit time</button>
        <button className="btn btn--quiet btn--small" onClick={() => setMode("penalty")}>Add penalty</button>
      </div>
    );
  }
  if (mode === "time") {
    return (
      <form className="inline-form" onSubmit={(e) => {
        e.preventDefault();
        act(() => send("PATCH", `/api/results/${row.Registration_ID}/${encodeURIComponent(stage)}`,
          { raw_time_s: status === "Finished" ? Number(time) : null, status, official_id: official })).then(() => setMode(null)).catch(() => {});
      }}>
        <select value={status} onChange={(e) => setStatus(e.target.value)} aria-label="Status">
          <option>Finished</option><option>DNS</option><option>DNF</option><option>DQ</option>
        </select>
        {status === "Finished" && <input type="number" step="0.01" min="0.01" required value={time} size={7}
                                         onChange={(e) => setTime(e.target.value)} aria-label="Raw time in seconds" />}
        <button className="btn btn--small" type="submit">Save</button>
        <button className="btn btn--quiet btn--small" type="button" onClick={() => setMode(null)}>Close</button>
      </form>
    );
  }
  return (
    <form className="inline-form" onSubmit={(e) => {
      e.preventDefault();
      act(() => send("POST", "/api/penalties", { registration_id: row.Registration_ID, stage, type: "Penalty",
        seconds: Number(seconds), reason, official_id: official })).then(() => setMode(null)).catch(() => {});
    }}>
      <input type="number" step="0.5" min="0.5" required value={seconds} size={4} onChange={(e) => setSeconds(e.target.value)} aria-label="Penalty seconds" />
      <input required placeholder="Reason" value={reason} onChange={(e) => setReason(e.target.value)} aria-label="Reason" />
      <button className="btn btn--small" type="submit">Add</button>
      <button className="btn btn--quiet btn--small" type="button" onClick={() => setMode(null)}>Close</button>
    </form>
  );
}

function RecordResult({ year, series, stage, results, official, act }) {
  const regs = useQuery("/api/registrations", { year, series }, [year, series, results]);
  const done = new Set((results || []).map((r) => r.Registration_ID));
  const open = (regs.rows || []).filter((r) => r.Status === "Registered" && !done.has(r.Registration_ID));
  const [reg, setReg] = useState("");
  const [status, setStatus] = useState("Finished");
  const [time, setTime] = useState("");
  if (!open.length) return <p className="sub">Every registration in this race has a {stage} result.</p>;
  return (
    <form className="inline-form" onSubmit={(e) => {
      e.preventDefault();
      act(() => send("POST", "/api/results", { registration_id: Number(reg), stage, status,
        raw_time_s: status === "Finished" ? Number(time) : null, official_id: official })).then(() => { setReg(""); setTime(""); }).catch(() => {});
    }}>
      <label className="field"><span>Registration</span>
        <select required value={reg} onChange={(e) => setReg(e.target.value)}>
          <option value="">Choose…</option>
          {open.map((r) => <option key={r.Registration_ID} value={r.Registration_ID}>Bib {r.Bib_No}: {r.Display_Name}</option>)}
        </select></label>
      <label className="field"><span>Status</span>
        <select value={status} onChange={(e) => setStatus(e.target.value)}>
          <option>Finished</option><option>DNS</option><option>DNF</option><option>DQ</option>
        </select></label>
      {status === "Finished" && <label className="field"><span>Raw time (s)</span>
        <input type="number" step="0.01" min="0.01" required value={time} onChange={(e) => setTime(e.target.value)} /></label>}
      <button className="btn" type="submit">Record result</button>
    </form>
  );
}

function DecideProtest({ protest, jury, act }) {
  const [outcome, setOutcome] = useState("Rejected");
  const [votes, setVotes] = useState({});
  const [action, setAction] = useState("");
  const raceResults = useQuery("/api/results", { year: protest.Edition_Year, series: protest.Series_Code,
    stage: protest.Series_Code === "SPR" ? "Final" : undefined }, [protest.Protest_ID]);
  const penalised = (raceResults.rows || []).filter((r) => r.Penalty_Nos);
  const vote = (id) => votes[id] || (outcome === "Upheld" ? "Uphold" : "Reject");

  function submit(e) {
    e.preventDefault();
    let act_ = undefined;
    if (outcome === "Upheld" && action) {
      const [kind, reg, stage, no] = action.split("|");
      act_ = kind === "pen" ? { remove_penalty: [Number(reg), stage, Number(no)] } : { disqualify: [Number(reg), stage] };
    }
    act(() => send("POST", `/api/protests/${protest.Protest_ID}/decide`, {
      outcome, votes: jury.map((o) => ({ official_id: o.Person_ID, vote: vote(o.Person_ID) })), action: act_ }));
  }

  return (
    <form className="card-panel" onSubmit={submit}>
      <h3>Protest {protest.Protest_ID}: {seriesName(protest.Series_Code)} {protest.Edition_Year}</h3>
      <p><strong>{protest.Team_Name || protest.Display_Name}</strong> filed at {protest.Filed_At}: “{protest.Reason}”</p>
      <div className="form-row">
        <label className="field"><span>Outcome</span>
          <select value={outcome} onChange={(e) => setOutcome(e.target.value)}><option>Rejected</option><option>Upheld</option></select></label>
        {jury.map((o) => (
          <label className="field" key={o.Person_ID}><span>{o.First_Name} {o.Last_Name} ({o.Duty_Title})</span>
            <select value={vote(o.Person_ID)} onChange={(e) => setVotes((v) => ({ ...v, [o.Person_ID]: e.target.value }))}>
              <option>Uphold</option><option>Reject</option></select></label>
        ))}
        {outcome === "Upheld" && (
          <label className="field"><span>Change to results</span>
            <select value={action} onChange={(e) => setAction(e.target.value)}>
              <option value="">No change</option>
              {penalised.flatMap((r) => r.Penalty_Nos.split(",").map((no) => (
                <option key={`p${r.Registration_ID}-${no}`} value={`pen|${r.Registration_ID}|${r.Stage}|${no}`}>
                  Remove penalty {no} of bib {r.Bib_No}
                </option>)))}
              {(raceResults.rows || []).filter((r) => r.Status === "Finished").map((r) => (
                <option key={`d${r.Registration_ID}`} value={`dq|${r.Registration_ID}|${r.Stage}`}>Disqualify bib {r.Bib_No}: {r.Display_Name}</option>
              ))}
            </select></label>
        )}
      </div>
      <div className="form-actions"><button className="btn" type="submit">Record decision</button></div>
    </form>
  );
}

function FileProtest({ year, series, act }) {
  const regs = useQuery("/api/registrations", { year, series }, [year, series]);
  const [entry, setEntry] = useState("");
  const [filedAt, setFiledAt] = useState(nowLocal());
  const [reason, setReason] = useState("");
  return (
    <form className="inline-form" onSubmit={(e) => {
      e.preventDefault();
      const reg = (regs.rows || []).find((r) => r.Entry_ID === Number(entry));
      act(() => send("POST", "/api/protests", { entry_id: Number(entry), year, race_no: reg.Race_No, reason,
        filed_at: filedAt.replace("T", " ") + ":00" })).then(() => setReason(""));
    }}>
      <label className="field"><span>Protesting entry</span>
        <select required value={entry} onChange={(e) => setEntry(e.target.value)}>
          <option value="">Choose…</option>
          {(regs.rows || []).filter((r) => r.Status === "Registered").map((r) => (
            <option key={r.Registration_ID} value={r.Entry_ID}>Bib {r.Bib_No}: {r.Team_Name || r.Display_Name}</option>))}
        </select></label>
      <label className="field"><span>Filed at</span>
        <input type="datetime-local" required value={filedAt} onChange={(e) => setFiledAt(e.target.value)} /></label>
      <label className="field" style={{ flex: 1, minWidth: "16rem" }}><span>Reason</span>
        <input required value={reason} onChange={(e) => setReason(e.target.value)} /></label>
      <button className="btn" type="submit">File protest (150 €)</button>
    </form>
  );
}

export default function Jury() {
  const editions = useEditions().filter((e) => e.Series);
  const [officials, setOfficials] = useState([]);
  const [official, setOfficial] = useState("");
  const [year, setYear] = useState(2026);
  const [series, setSeries] = useState("MAIN");
  const [stage, setStage] = useState("Final");
  const effectiveStage = series === "SPR" ? stage : "Single";
  const results = useQuery("/api/results", { year, series, stage: series === "SPR" ? stage : undefined }, [year, series, stage]);
  const pending = useQuery("/api/protests", { status: "Pending" }, []);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [lastSql, setLastSql] = useState("");

  useEffect(() => { get("/api/officials").then((b) => setOfficials(b.rows)).catch((e) => setError(e.message)); }, []);
  const jury = officials.filter((o) => ["Chief Judge", "Jury Member"].includes(o.Duty_Title));

  async function act(fn) {
    setMessage(""); setError("");
    if (!official) { setError("Choose the acting official first."); throw new Error("no official"); }
    try {
      const r = await fn();
      setMessage(r.message); setLastSql(r.sql);
      results.reload(); pending.reload();
      return r;
    } catch (e) { setError(e.message); throw e; }
  }
  const safeAct = (fn) => act(fn).catch(() => {});

  return (
    <>
      <h1>Jury desk</h1>
      <p className="desk-note">Record and correct results, add time penalties and decide protests. Every change is stored with the acting official.</p>
      <div className="toolbar">
        <label className="field field--inline"><span>Acting official</span>
          <select value={official} onChange={(e) => setOfficial(Number(e.target.value) || "")}>
            <option value="">Choose…</option>
            {officials.map((o) => <option key={o.Person_ID} value={o.Person_ID}>{o.First_Name} {o.Last_Name}, {o.Duty_Title}</option>)}
          </select></label>
        <YearSelect years={editions} value={year} onChange={setYear} />
      </div>
      <Alert kind="success">{message}</Alert>
      <Alert>{error}</Alert>
      {lastSql && <SqlPanel sql={lastSql} />}

      <section className="section">
        <h2>Race results</h2>
        <Tabs label="Series" value={series} onChange={setSeries} items={SERIES.map((s) => ({ value: s.code, label: s.name }))} />
        {series === "SPR" && <Tabs label="Stage" value={stage} onChange={setStage} items={STAGES_HEATS.map((s) => ({ value: s, label: s }))} />}
        <DataTable rows={results.rows} empty="No results recorded for this race yet." rowClass={(r) => (r.Rank_In_Stage === 1 ? "is-first" : undefined)} columns={[
          { key: "Rank_In_Stage", label: "Rank", render: (r) => r.Rank_In_Stage ? <span className="rank">{r.Rank_In_Stage}.</span> : r.Status },
          { key: "Bib_No", label: "Bib", render: (r) => <Bib n={r.Bib_No} /> },
          { key: "Display_Name", label: "Entry", render: (r) => <>{r.Team_Name && <strong>{r.Team_Name}<br /></strong>}{r.Display_Name}{r.Adjustments && <span className="penalty">{r.Adjustments}</span>}</> },
          { key: "Raw_Time_s", label: "Raw", num: true, render: (r) => formatTime(r.Raw_Time_s) },
          { key: "Net_Time_s", label: "Net", num: true, render: (r) => r.Status === "Finished" ? formatTime(r.Net_Time_s) : r.Status },
          { key: "Gap_To_Leader_s", label: "Diff", num: true, render: (r) => formatGap(r.Gap_To_Leader_s, series === "SPR" ? 2 : 1) },
          { key: "act", label: "", render: (r) => <RowActions row={r} stage={effectiveStage} official={official} act={act} /> },
        ]} />
        <SqlPanel sql={results.sql} />
        <h3 style={{ marginTop: "1.5rem" }}>Record a result</h3>
        <RecordResult year={year} series={series} stage={effectiveStage} results={results.rows} official={official} act={act} />
      </section>

      <section className="section">
        <h2>Pending protests</h2>
        <DataTable rows={pending.rows} empty="No protests are waiting for a decision." columns={[
          { key: "Protest_ID", label: "No.", num: true },
          { key: "Edition_Year", label: "Race", render: (r) => `${seriesName(r.Series_Code)} ${r.Edition_Year}` },
          { key: "Display_Name", label: "Filed by", render: (r) => r.Team_Name || r.Display_Name },
          { key: "Filed_At", label: "Filed at" },
          { key: "Reason", label: "Reason" },
        ]} />
        <SqlPanel sql={pending.sql} />
        {(pending.rows || []).map((p) => <DecideProtest key={p.Protest_ID} protest={p} jury={jury} act={safeAct} />)}
      </section>

      <section className="section">
        <h2>File a protest</h2>
        <p>Written protests reach the jury within 15 minutes of the last finisher; the fee is 150 €. Uses the race chosen above.</p>
        <FileProtest year={year} series={series} act={safeAct} />
      </section>
    </>
  );
}
