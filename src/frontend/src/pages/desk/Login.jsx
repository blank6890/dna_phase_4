import { useState } from "react";
import { Navigate, useNavigate, useSearchParams } from "react-router-dom";
import { Alert } from "../../components/ui.jsx";
import { safeNext, useStaff } from "../../components/staff.jsx";

export default function Login() {
  const { staff, ready, login } = useStaff();
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const next = safeNext(params.get("next"));
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  if (ready && staff) return <Navigate to={next} replace />;

  async function submit(e) {
    e.preventDefault();
    setError(""); setBusy(true);
    try {
      await login(username, password);
      navigate(next, { replace: true });
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="section" style={{ maxWidth: "26rem" }}>
      <h1>Staff login</h1>
      <p className="lead">The Staff Desk is for championship officials. Log in with your own account.</p>
      <form className="card-panel" onSubmit={submit}>
        <div className="form-row" style={{ gridTemplateColumns: "1fr" }}>
          <label className="field"><span>Username</span>
            <input name="username" autoComplete="username" required autoFocus
                   value={username} onChange={(e) => setUsername(e.target.value)} /></label>
          <label className="field"><span>Password</span>
            <input name="password" type="password" autoComplete="current-password" required
                   value={password} onChange={(e) => setPassword(e.target.value)} /></label>
        </div>
        <Alert>{error}</Alert>
        <div className="form-actions"><button className="btn" type="submit" disabled={busy}>Log in</button></div>
      </form>
    </section>
  );
}
