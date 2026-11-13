import { useEffect, useState } from "react";
import { Link, NavLink, useLocation, useNavigate } from "react-router-dom";
import { useStaff } from "./staff.jsx";

const MENU = [
  { label: "The Event", items: [["Programme 2027", "/programme"], ["Market Place", "/market"]] },
  {
    label: "Competitors",
    items: [
      ["Register", "/register"],
      ["Registered Competitors", "/competitors"],
      ["Results", "/results"],
      ["Champions and Records", "/results/champions-and-records"],
      ["Official Grand Prix", "/grand-prix"],
      ["Manage my registration", "/my-registration"],
    ],
  },
];

const DESK = [["Organiser", "/desk/organiser"], ["Jury", "/desk/jury"], ["Committee reports", "/desk/reports"]];

const PARTNERS = [
  ["Olvi", "http://www.olvi.fi/"],
  ["DNA", "https://www.dna.fi/"],
  ["Ylä-Savon Jätehuolto", "https://www.ylasavonjatehuolto.fi/"],
  ["IPA", "https://ipa.fi"],
  ["Rebekan hoitokoti", "https://rebekanhoitokoti.fi/"],
  ["Sonkajärven kunta", null],
];

function SearchBox({ onDone }) {
  const [q, setQ] = useState("");
  const navigate = useNavigate();
  return (
    <form className="search" role="search" onSubmit={(e) => {
      e.preventDefault();
      if (q.trim().length >= 2) { navigate(`/search?q=${encodeURIComponent(q.trim())}`); onDone?.(); }
    }}>
      <label htmlFor="site-search" className="visually-hidden">Search competitors and teams</label>
      <input id="site-search" type="search" placeholder="Search names or teams" value={q}
             onChange={(e) => setQ(e.target.value)} minLength={2} />
      <button type="submit">Search</button>
    </form>
  );
}

/** Staff Desk menu group: a login link when logged out; the desk pages and log out when logged in. */
function StaffMenu() {
  const { staff, logout } = useStaff();
  const navigate = useNavigate();
  return (
    <div className="nav__group">
      <span className="nav__label">Staff Desk</span>
      <ul>
        {staff ? (
          <>
            {DESK.map(([text, to]) => <li key={to}><NavLink to={to} end>{text}</NavLink></li>)}
            <li>
              <a href="/" onClick={(e) => { e.preventDefault(); logout().finally(() => navigate("/")); }}>
                Log out ({staff.First_Name} {staff.Last_Name})
              </a>
            </li>
          </>
        ) : (
          <li><NavLink to="/desk/login" end>Staff login</NavLink></li>
        )}
      </ul>
    </div>
  );
}

export default function Layout({ children }) {
  const [open, setOpen] = useState(false);
  const location = useLocation();
  useEffect(() => setOpen(false), [location.pathname]);

  return (
    <>
      <a className="skip" href="#main">Skip to content</a>
      <header className="masthead">
        <div className="masthead__inner">
          <Link to="/" className="brand">
            <span className="brand__mark" aria-hidden="true" />
            <span className="brand__text">Wife Carrying<br />World Championships</span>
          </Link>
          <button className="menu-toggle" aria-expanded={open} aria-controls="primary-nav"
                  onClick={() => setOpen((o) => !o)}>
            {open ? "Close" : "Menu"}
          </button>
          <nav id="primary-nav" className={open ? "nav nav--open" : "nav"} aria-label="Main">
            {MENU.map((group) => (
              <div className="nav__group" key={group.label}>
                <span className="nav__label">{group.label}</span>
                <ul>
                  {group.items.map(([text, to]) => (
                    <li key={to}><NavLink to={to} end>{text}</NavLink></li>
                  ))}
                </ul>
              </div>
            ))}
            <StaffMenu />
            <NavLink to="/register" className="nav__cta">Register for 2027</NavLink>
            <SearchBox onDone={() => setOpen(false)} />
          </nav>
        </div>
      </header>

      <main id="main" className="page">{children}</main>

      <footer className="footer">
        <div className="footer__inner">
          <div>
            <h2 className="footer__title">In cooperation with</h2>
            <ul className="partners">
              {PARTNERS.map(([name, url]) => (
                <li key={name}>{url ? <a href={url} target="_blank" rel="noreferrer">{name}</a> : name}</li>
              ))}
            </ul>
          </div>
          <address>
            Sonkajärven Eukonkanto Oy<br />Lyseotie 1, 74300 Sonkajärvi, Finland
          </address>
          <p className="footer__note">
            Student project (Data and Applications, Phase 4) modelled on eukonkanto.fi.
            Data from the official site; rows marked as generated in the database are illustrative.
          </p>
        </div>
      </footer>
    </>
  );
}
