/** Seconds -> the site's notation: "33.77" under a minute, "1:04.4" (or "1:13.49") from a minute up, "–" when missing. */
export function formatTime(seconds) {
  if (seconds === null || seconds === undefined) return "–";
  const hundredths = Math.round(seconds * 100);
  const digits = hundredths % 10 === 0 ? 1 : 2;          // keep hundredths only when they were recorded
  if (seconds < 60) return (hundredths / 100).toFixed(digits);
  const minutes = Math.floor(hundredths / 6000);
  const rest = ((hundredths - minutes * 6000) / 100).toFixed(digits).padStart(digits + 3, "0");
  return `${minutes}:${rest}`;
}

/** Gap to the leader: "+4.4" (or "+0.61" with digits=2), "+1:06.2" from a minute up; "" for the leader. */
export function formatGap(seconds, digits = 1) {
  if (!seconds) return "";
  return seconds < 60 ? `+${seconds.toFixed(digits)}` : `+${formatTime(seconds)}`;
}
