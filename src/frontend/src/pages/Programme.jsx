const FRIDAY = [
  ["10 am", "Opening of the local market"],
  ["10 am – 7 pm", "The authentic Sonkajärvi local market: vendors, crafts, local food, the Robber Ronkainen camp and a kids' obstacle course"],
  ["4 pm", "Market devotional"],
  ["7 pm", "Wife Carrying Sprint at the Wife Carrying Arena"],
  ["8 pm – 2 am", "Evening party at the sports hall (18+)"],
];
const SATURDAY = [
  ["10 am – 5 pm", "The authentic Sonkajärvi local market"],
  ["10 am", "Tonkkumi World Championships at the school field"],
  ["1 pm", "Team race, Wife Carrying Arena"],
  ["2.45 pm", "Parade, Wife Carrying Arena"],
  ["2.50 pm", "Opening, Wife Carrying Arena"],
  ["3 pm", "Wife Carrying World Championships, Wife Carrying Arena"],
  ["5.30 pm", "Prize-giving at the sports hall"],
  ["8 pm – 2 am", "Evening party at the sports hall (adults only)"],
];

function Day({ title, items }) {
  return (
    <section className="section">
      <h2>{title}</h2>
      <div className="table-wrap">
        <table><tbody>
          {items.map(([t, what]) => <tr key={t + what}><td style={{ whiteSpace: "nowrap", width: "9rem" }}><strong>{t}</strong></td><td>{what}</td></tr>)}
        </tbody></table>
      </div>
    </section>
  );
}

export default function Programme() {
  return (
    <>
      <h1>Programme 2027</h1>
      <p className="lead">The programme is preliminary and will be updated.</p>
      <div className="grid-2">
        <Day title="Friday 2 July 2027" items={FRIDAY} />
        <Day title="Saturday 3 July 2027" items={SATURDAY} />
      </div>
    </>
  );
}
