import { Link, useSearchParams } from "react-router-dom";
import { Alert, DataTable, SqlPanel, useQuery } from "../components/ui.jsx";

export default function Search() {
  const [params] = useSearchParams();
  const q = params.get("q") || "";
  const persons = useQuery(q.length >= 2 ? "/api/search/persons" : null, { q }, [q]);
  const teams = useQuery(q.length >= 2 ? "/api/search/teams" : null, { q }, [q]);
  if (q.length < 2) {
    return <><h1>Search</h1><p>Type at least two letters of a name, team or organisation in the search box above.</p></>;
  }
  return (
    <>
      <h1>Search results for “{q}”</h1>
      <section className="section">
        <h2>People</h2>
        <Alert>{persons.error}</Alert>
        <DataTable rows={persons.rows} empty={`No competitor or official has a name containing “${q}”.`} columns={[
          { key: "Last_Name", label: "Name", render: (r) => <Link to={`/people/${r.Person_ID}`}>{r.First_Name} {r.Last_Name}</Link> },
          { key: "Citizenship", label: "Citizenship" },
          { key: "Registrations", label: "Races entered", num: true },
          { key: "Is_Official", label: "", render: (r) => (r.Is_Official ? "Official" : "") },
        ]} />
        <SqlPanel sql={persons.sql} />
      </section>
      <section className="section">
        <h2>Teams and organisations</h2>
        <Alert>{teams.error}</Alert>
        <DataTable rows={teams.rows} empty={`No team or organisation matches “${q}”.`} columns={[
          { key: "Team_Name", label: "Team" },
          { key: "Represented_Organisation", label: "Represents", render: (r) => r.Represented_Organisation || "–" },
          { key: "Display_Name", label: "Members (carriers / carried)" },
          { key: "Years", label: "Years" },
        ]} />
        <SqlPanel sql={teams.sql} />
      </section>
    </>
  );
}
