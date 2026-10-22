import { getCountries, getCountryCallingCode, type CountryCode } from "libphonenumber-js";

export interface CountryOption {
  code: CountryCode;
  name: string;
  dial: string;
  flag: string;
}

const flag = (code: string) =>
  String.fromCodePoint(...code.toUpperCase().split("").map((c) => 0x1f1a5 + c.charCodeAt(0)));

export function buildCountries(): CountryOption[] {
  const names = new Intl.DisplayNames(["en"], { type: "region" });
  return getCountries()
    .map((code) => ({ code, name: names.of(code) ?? code, dial: "+" + getCountryCallingCode(code), flag: flag(code) }))
    .sort((a, b) => a.name.localeCompare(b.name));
}

export function guessCountry(): CountryCode {
  const region = (navigator.language || "en-US").split("-")[1]?.toUpperCase();
  return (getCountries() as string[]).includes(region ?? "") ? (region as CountryCode) : "US";
}
