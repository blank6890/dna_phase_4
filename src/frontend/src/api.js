/** All data comes from the Flask JSON API; the browser never talks to the database. */
async function handle(res, path) {
  // A 401 means the staff session is missing or expired: tell the StaffProvider (not for a failed login).
  if (res.status === 401 && path !== "/api/auth/login") window.dispatchEvent(new Event("staff:unauthorized"));
  let body = null;
  try {
    body = await res.json();
  } catch {
    throw new Error(`The server answered ${res.status} without data. Is the backend running?`);
  }
  if (!res.ok) throw new Error(body.error || `Request failed (${res.status})`);
  return body;
}

export async function get(path, params = {}) {
  const query = new URLSearchParams(
    Object.entries(params).filter(([, v]) => v !== undefined && v !== null && v !== ""),
  ).toString();
  return handle(await fetch(query ? `${path}?${query}` : path), path);
}

export async function send(method, path, body) {
  return handle(
    await fetch(path, {
      method,
      headers: { "Content-Type": "application/json" },
      body: body === undefined ? undefined : JSON.stringify(body),
    }),
    path,
  );
}
