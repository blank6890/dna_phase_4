import { useState } from "react";
import { Alert, DataTable, SqlPanel, YearSelect, useEditions, useQuery } from "../components/ui.jsx";

/** Booth table columns, shared with the Organiser desk (which adds the remove action). */
export const BOOTH_COLUMNS = [
  { key: "Business_Name", label: "Vendor" },
  { key: "Booth_Size", label: "Booth" },
  { key: "Booth_Fee_EUR", label: "Fee (€)", num: true, render: (r) => r.Booth_Fee_EUR.toFixed(2) },
  { key: "Electricity_Required", label: "Electricity", render: (r) => (r.Electricity_Required ? "Yes" : "No") },
  { key: "Paid", label: "Paid", render: (r) => (r.Paid ? "Paid" : "Unpaid") },
];

function VendorSearch() {
  const [q, setQ] = useState("");
  const [category, setCategory] = useState("");
  const [applied, setApplied] = useState({});
  const data = useQuery("/api/vendors", applied, [applied.q, applied.category]);
  return (
    <section className="section">
      <h2>Find a vendor</h2>
      <form className="toolbar" onSubmit={(e) => { e.preventDefault(); setApplied({ q: q.trim() || undefined, category: category || undefined }); }}>
        <label className="field field--inline"><span>Business name</span>
          <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="e.g. leipomo" /></label>
        <label className="field field--inline"><span>Products</span>
          <select value={category} onChange={(e) => setCategory(e.target.value)}>
            <option value="">All</option><option>Food</option><option>Handicrafts</option><option>Local specialities</option>
          </select></label>
        <button className="btn btn--quiet" type="submit">Search</button>
      </form>
      <Alert>{data.error}</Alert>
      <DataTable rows={data.rows} empty="No vendor matches. Try another name or product type." columns={[
        { key: "Business_Name", label: "Vendor" },
        { key: "Categories", label: "Products" },
        { key: "Contact_Name", label: "Contact" },
        { key: "Phone", label: "Phone" },
      ]} />
      <SqlPanel sql={data.sql} />
    </section>
  );
}

function Bookings() {
  const editions = useEditions();
  const [year, setYear] = useState(2027);
  const data = useQuery(`/api/editions/${year}/booths`, {}, [year]);
  return (
    <section className="section">
      <h2>Booth bookings</h2>
      <div className="toolbar"><YearSelect years={editions} value={year} onChange={setYear} /></div>
      <DataTable rows={data.rows} empty="No booths booked for this edition." columns={BOOTH_COLUMNS} />
      <SqlPanel sql={data.sql} />
    </section>
  );
}

export default function Market() {
  return (
    <>
      <h1>The Wife Carrying Market Place</h1>
      <p className="lead">Booths with food, handicrafts and local specialities on both days of the event.</p>
      <div className="grid-2 section">
        <div className="stat"><strong>4 × 4 m booth, 70 €</strong><span className="sub">Bigger places on request</span></div>
        <div className="stat"><strong>4 × 8 m booth, 140 €</strong><span className="sub">Food booths and electricity are priced by contract. All places are paid before the event.</span></div>
      </div>
      <VendorSearch />
      <Bookings />
    </>
  );
}
