import { describe, expect, test } from "vitest";
import { formatGap, formatTime } from "./formatTime.js";

describe("formatTime", () => {
  test("missing time shows a dash", () => expect(formatTime(null)).toBe("–"));
  test("under a minute keeps hundredths", () => expect(formatTime(33.77)).toBe("33.77"));
  test("under a minute recorded in tenths", () => expect(formatTime(56.9)).toBe("56.9"));
  test("a minute or more is m:ss.d", () => {
    expect(formatTime(64.4)).toBe("1:04.4");
    expect(formatTime(154.9)).toBe("2:34.9");
    expect(formatTime(73.49)).toBe("1:13.49");   // hundredths kept when recorded (records page)
    expect(formatTime(99.51)).toBe("1:39.51");
  });
  test("exact minutes pad seconds", () => expect(formatTime(120)).toBe("2:00.0"));
});

describe("formatGap", () => {
  test("leader has no gap", () => expect(formatGap(0)).toBe(""));
  test("tenths by default, hundredths on request", () => {
    expect(formatGap(1.8)).toBe("+1.8");
    expect(formatGap(0.61, 2)).toBe("+0.61");
  });
  test("a minute or more", () => expect(formatGap(66.2)).toBe("+1:06.2"));
});
