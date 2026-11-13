import { describe, expect, it } from "vitest";
import { safeNext } from "./staff.jsx";

describe("safeNext", () => {
  it("follows desk pages", () => {
    expect(safeNext("/desk/jury")).toBe("/desk/jury");
  });
  it("ignores off-site, login and empty targets", () => {
    for (const bad of ["https://evil.example", "//evil", "/desk/login", "/results", "", null]) {
      expect(safeNext(bad)).toBe("/desk/organiser");
    }
  });
});
