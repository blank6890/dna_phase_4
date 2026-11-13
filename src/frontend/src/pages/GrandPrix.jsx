import { Alert, SqlPanel, useQuery } from "../components/ui.jsx";

const month = (d) => new Date(d).toLocaleDateString("en-GB", { month: "long", year: "numeric" });

export default function GrandPrix() {
  const data = useQuery("/api/grand-prix", {}, []);
  const continents = [...new Set((data.rows || []).map((r) => r.Continent))];
  return (
    <>
      <h1>Official Grand Prix</h1>
      <p className="lead">Official wife-carrying events around the world. 2027 events will be announced later.</p>
      <Alert>{data.error}</Alert>
      <div className="grid-2">
        {continents.map((c) => (
          <section key={c} className="section">
            <h2>{c}</h2>
            <ul className="list-plain">
              {data.rows.filter((r) => r.Continent === c).map((r) => (
                <li key={r.GP_Event_ID}>
                  <strong>{r.Event_Name}</strong>
                  <span className="sub">{r.City}, {r.Region}, {r.Country_Name}. {month(r.Event_Month_Year)}. Organiser: {r.Organiser}</span>
                </li>
              ))}
            </ul>
          </section>
        ))}
      </div>
      <SqlPanel sql={data.sql} />
    </>
  );
}
