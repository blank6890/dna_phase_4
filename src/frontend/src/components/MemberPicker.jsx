import { useState } from "react";
import { get } from "../api.js";

export const emptyMember = () => ({
  mode: "new", personId: null, personLabel: "", query: "", matches: [],
  first_name: "", last_name: "", dob: "", gender: "", email: "", citizenship: "FIN",
});

/** Pick an existing person (search) or describe a new one. Value is a plain object owned by the parent. */
export function MemberPicker({ legend, value, onChange, weight, onWeight, idPrefix }) {
  const [searchError, setSearchError] = useState("");
  const set = (patch) => onChange({ ...value, ...patch });

  async function search() {
    setSearchError("");
    if (value.query.trim().length < 2) return setSearchError("Type at least two letters.");
    try {
      const b = await get("/api/search/persons", { q: value.query.trim() });
      set({ matches: b.rows });
      if (!b.rows.length) setSearchError("Nobody found. Add them as a new person instead.");
    } catch (e) {
      setSearchError(e.message);
    }
  }

  return (
    <fieldset>
      <legend>{legend}</legend>
      <div className="inline-form" role="radiogroup" aria-label={`${legend}: who`}>
        <label><input type="radio" checked={value.mode === "new"} onChange={() => set({ mode: "new" })} /> New person</label>
        <label><input type="radio" checked={value.mode === "existing"} onChange={() => set({ mode: "existing" })} /> Already in the database</label>
      </div>

      {value.mode === "existing" ? (
        <div style={{ marginTop: "0.75rem" }}>
          {value.personId ? (
            <p>Selected: <strong>{value.personLabel}</strong>{" "}
              <button type="button" className="btn btn--quiet btn--small" onClick={() => set({ personId: null, personLabel: "" })}>Change</button></p>
          ) : (
            <>
              <div className="inline-form">
                <label className="field">
                  <span>Name</span>
                  <input id={`${idPrefix}-q`} value={value.query} onChange={(e) => set({ query: e.target.value })}
                         onKeyDown={(e) => { if (e.key === "Enter") { e.preventDefault(); search(); } }} />
                </label>
                <button type="button" className="btn btn--quiet" onClick={search}>Find</button>
              </div>
              {searchError && <p className="sub">{searchError}</p>}
              <ul className="list-plain">
                {value.matches.map((m) => (
                  <li key={m.Person_ID}>
                    <button type="button" className="btn btn--quiet btn--small"
                            onClick={() => set({ personId: m.Person_ID, personLabel: `${m.First_Name} ${m.Last_Name}`, matches: [] })}>
                      Choose
                    </button>{" "}
                    {m.First_Name} {m.Last_Name} <span className="sub" style={{ display: "inline" }}>{m.Citizenship}</span>
                  </li>
                ))}
              </ul>
            </>
          )}
        </div>
      ) : (
        <div className="form-row" style={{ marginTop: "0.75rem" }}>
          <label className="field"><span>First name</span>
            <input required value={value.first_name} onChange={(e) => set({ first_name: e.target.value })} /></label>
          <label className="field"><span>Last name</span>
            <input required value={value.last_name} onChange={(e) => set({ last_name: e.target.value })} /></label>
          <label className="field"><span>Date of birth</span>
            <input required type="date" value={value.dob} onChange={(e) => set({ dob: e.target.value })} /></label>
          <label className="field"><span>Citizenship (ISO code)</span>
            <input required maxLength={3} value={value.citizenship} onChange={(e) => set({ citizenship: e.target.value.toUpperCase() })} /></label>
          <label className="field"><span>E-mail (optional)</span>
            <input type="email" value={value.email} onChange={(e) => set({ email: e.target.value })} /></label>
          <label className="field"><span>Gender (optional)</span>
            <select value={value.gender} onChange={(e) => set({ gender: e.target.value })}>
              <option value="">Not given</option><option>Female</option><option>Male</option><option>Other</option>
            </select></label>
        </div>
      )}

      {onWeight && (
        <div className="form-row" style={{ marginTop: "0.75rem" }}>
          <label className="field"><span>Measured weight (kg)</span>
            <input required type="number" step="0.1" min="1" value={weight} onChange={(e) => onWeight(e.target.value)} /></label>
          {weight && Number(weight) < 49 && (
            <p className="sub" style={{ alignSelf: "end" }}>Under 49 kg: a {(49 - Number(weight)).toFixed(1)} kg backpack is required.</p>
          )}
        </div>
      )}
    </fieldset>
  );
}

/** Convert picker state to the API member format. */
export function toApiMember(role, m, weight) {
  const base = m.mode === "existing"
    ? { role, person_id: m.personId }
    : { role, new: { first_name: m.first_name, last_name: m.last_name, dob: m.dob,
                     gender: m.gender || null, email: m.email || null, citizenship: m.citizenship } };
  return weight !== undefined ? { ...base, weight_kg: weight === "" ? null : Number(weight) } : base;
}
