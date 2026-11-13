import { Route, Routes, Link } from "react-router-dom";
import Layout from "./components/Layout.jsx";

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
        <Route path="*" element={<NotFound />} />
      </Routes>
    </Layout>
  );
}
