import { createContext, useCallback, useContext, useEffect, useState } from "react";
import { Navigate, useLocation } from "react-router-dom";
import { get, send } from "../api.js";

/** Who is logged in to the Staff Desk. The server's session cookie is the truth; this mirrors it. */
const StaffContext = createContext(null);

export function StaffProvider({ children }) {
  const [staff, setStaff] = useState(null);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    get("/api/auth/me")
      .then((b) => setStaff(b.official))
      .catch(() => setStaff(null))
      .finally(() => setReady(true));
    const drop = () => setStaff(null);            // any 401 from the API: the session is gone
    window.addEventListener("staff:unauthorized", drop);
    return () => window.removeEventListener("staff:unauthorized", drop);
  }, []);

  const login = useCallback(async (username, password) => {
    const b = await send("POST", "/api/auth/login", { username, password });
    setStaff(b.official);
  }, []);

  const logout = useCallback(async () => {
    try { await send("POST", "/api/auth/logout"); } finally { setStaff(null); }
  }, []);

  return <StaffContext.Provider value={{ staff, ready, login, logout }}>{children}</StaffContext.Provider>;
}

export function useStaff() {
  return useContext(StaffContext);
}

/** Only a `/desk/...` page (other than the login page) may be the target after login. */
export function safeNext(next) {
  return next && next.startsWith("/desk/") && !next.startsWith("/desk/login") ? next : "/desk/organiser";
}

export function RequireStaff({ children }) {
  const { staff, ready } = useStaff();
  const { pathname } = useLocation();
  if (!ready) return null;
  if (!staff) return <Navigate to={`/desk/login?next=${encodeURIComponent(pathname)}`} replace />;
  return children;
}
