/** Seconds -> the site's notation: "33.77" under a minute, "1:04.4" from a minute up, "–" when missing. */
export function formatTime(seconds) {
  if (seconds === null || seconds === undefined) return "–";
  if (seconds < 60) return seconds.toFixed(2);
  const tenths = Math.round(seconds * 10) / 10;
  const minutes = Math.floor(tenths / 60);
  const rest = (tenths - minutes * 60).toFixed(1).padStart(4, "0");
  return `${minutes}:${rest}`;
}

/** Gap to the leader: "+4.4" (or "+0.61" with digits=2), "+1:06.2" from a minute up; "" for the leader. */
export function formatGap(seconds, digits = 1) {
  if (!seconds) return "";
  return seconds < 60 ? `+${seconds.toFixed(digits)}` : `+${formatTime(seconds)}`;
}
