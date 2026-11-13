import { Link, Route, Routes } from "react-router-dom";
import Layout from "./components/Layout.jsx";
import Champions from "./pages/Champions.jsx";
import Jury from "./pages/desk/Jury.jsx";
import Organiser from "./pages/desk/Organiser.jsx";
import Reports from "./pages/desk/Reports.jsx";
import Competitors from "./pages/Competitors.jsx";
import GrandPrix from "./pages/GrandPrix.jsx";
import Home from "./pages/Home.jsx";
import Market from "./pages/Market.jsx";
import MyRegistration from "./pages/MyRegistration.jsx";
import Person from "./pages/Person.jsx";
import Programme from "./pages/Programme.jsx";
import Register from "./pages/Register.jsx";
import Results from "./pages/Results.jsx";
import Search from "./pages/Search.jsx";

function NotFound() {
  return (
    <section className="section">
      <h1>Page not found</h1>
      <p>That address does not exist. Try the <Link to="/results">results</Link> or the <Link to="/">front page</Link>.</p>
    </section>
  );
}

export default function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/results" element={<Results />} />
        <Route path="/results/champions-and-records" element={<Champions />} />
        <Route path="/competitors" element={<Competitors />} />
        <Route path="/register" element={<Register />} />
        <Route path="/my-registration" element={<MyRegistration />} />
        <Route path="/search" element={<Search />} />
        <Route path="/people/:id" element={<Person />} />
        <Route path="/grand-prix" element={<GrandPrix />} />
        <Route path="/market" element={<Market />} />
        <Route path="/programme" element={<Programme />} />
        <Route path="/desk/organiser" element={<Organiser />} />
        <Route path="/desk/jury" element={<Jury />} />
        <Route path="/desk/reports" element={<Reports />} />
        <Route path="*" element={<NotFound />} />
      </Routes>
    </Layout>
  );
}
