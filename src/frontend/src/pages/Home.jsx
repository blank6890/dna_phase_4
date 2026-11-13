import { Link } from "react-router-dom";
import { DataTable, SqlPanel, seriesName, useQuery } from "../components/ui.jsx";
import { formatTime } from "../components/formatTime.js";

const SERIES_INFO = [
  ["World Championship", "Saturday 3 July, 3 pm", "253.5 m, one water and two dry obstacles. One category: the fastest pair wins.", "55 € per pair"],
  ["Sprint", "Friday 2 July, 7 pm", "About 120 m with one water obstacle. Several pairs run at once; heat winners go to the final.", "55 € per pair"],
  ["Senior +40", "Saturday 3 July", "The main track, for carriers aged 40 or over.", "55 € per pair"],
  ["Team competition", "Saturday 3 July, 1 pm", "Three carriers share one carried person and swap after a 0.5 l wife-carrying drink.", "160 € per team"],
];

export default function Home() {
  const winners = useQuery("/api/champions", {}, []);
  const latest = winners.rows ? winners.rows.filter((r) => r.Edition_Year === winners.rows[0].Edition_Year) : null;
  return (
    <>
      <section className="hero">
        <div>
          <h1>Wife-carrying World Championship</h1>
          <p className="lead" style={{ color: "#dbe5f7" }}>
            Sonkajärvi, Finland, 2–3 July 2027. Fast races on Friday evening and Saturday afternoon,
            the traditional village market and the evening party.
          </p>
          <p>Registration for 2027 is open until Wednesday 30 June 2027 at 10 pm.</p>
          <div className="hero__actions">
            <Link className="btn" to="/register">Register for the race</Link>
            <Link className="btn btn--light" to="/programme">See the programme</Link>
          </div>
        </div>
        <dl className="track">
          <dt>Main track</dt><dd>253.5 m</dd>
          <dt>Obstacles</dt><dd>1 water, 2 dry</dd>
          <dt>Carried person</dt><dd>17+ years, 49 kg+</dd>
        </dl>
      </section>

      <section className="section">
        <h2>{latest ? `${latest[0].Edition_Year} winners` : "Latest winners"}</h2>
        <DataTable rows={latest} columns={[
          { key: "Series_Code", label: "Series", render: (r) => seriesName(r.Series_Code) },
          { key: "Display_Name", label: "Winners", render: (r) => <>{r.Team_Name && <strong>{r.Team_Name} </strong>}{r.Display_Name}</> },
          { key: "Countries", label: "Country" },
          { key: "Net_Time_s", label: "Time", num: true, render: (r) => formatTime(r.Net_Time_s) },
        ]} />
        <p style={{ marginTop: "0.75rem" }}>
          <Link to="/results">Full results</Link> or <Link to="/results/champions-and-records">all champions and world records</Link>.
        </p>
        <SqlPanel sql={winners.sql} />
      </section>

      <section className="section">
        <h2>Race series</h2>
        <div className="grid-2">
          {SERIES_INFO.map(([name, when, text, fee]) => (
            <div key={name} className="stat">
              <strong>{name}</strong>
              <span className="sub">{when}, {fee}</span>
              <p style={{ marginTop: "0.4rem" }}>{text}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="section">
        <h2>The rules in short</h2>
        <p>
          The carrier must be at least 18 and the carried person at least 17 on race day. The carried person must
          weigh 49 kg or more; anyone lighter carries a weighted backpack to make up the difference. Dropping your
          partner is not penalised, but you must pick them up before you go on. Protests are made in writing to the
          jury within 15 minutes of the last finisher, for a 150 € fee.
        </p>
        <Link to="/results/champions-and-records">See who holds the world records</Link>
      </section>
    </>
  );
}
