import { describe, expect, it } from "vitest";
import { smsInfo } from "./sms";

describe("smsInfo (must match the Django implementation)", () => {
  it("counts GSM-7 segments", () => {
    expect(smsInfo("a".repeat(160)).segments).toBe(1);
    expect(smsInfo("a".repeat(161)).segments).toBe(2);
    expect(smsInfo("a".repeat(306)).segments).toBe(2);
    expect(smsInfo("a".repeat(307)).segments).toBe(3);
  });
  it("counts extension characters twice", () => {
    expect(smsInfo("{".repeat(80)).units).toBe(160);
    expect(smsInfo("{".repeat(81)).segments).toBe(2);
  });
  it("switches to UCS-2 for non-GSM text", () => {
    expect(smsInfo("नमस्ते").encoding).toBe("ucs2");
    expect(smsInfo("😀".repeat(35)).segments).toBe(1);
    expect(smsInfo("😀".repeat(36)).segments).toBe(2);
  });
  it("returns zero segments for empty text", () => {
    expect(smsInfo("").segments).toBe(0);
  });
});
