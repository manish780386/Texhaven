import { parsePhoneNumberFromString, type CountryCode } from "libphonenumber-js";
import { useId, useMemo, useState } from "react";
import { buildCountries, guessCountry } from "../lib/countries";

interface Props {
  onChange: (e164: string | null) => void;
  blocked?: string[];
}

export default function PhoneField({ onChange, blocked = [] }: Props) {
  const id = useId();
  const countries = useMemo(buildCountries, []);
  const [country, setCountry] = useState<CountryCode>(guessCountry);
  const [raw, setRaw] = useState("");
  const [touched, setTouched] = useState(false);

  const parsed = raw ? parsePhoneNumberFromString(raw, raw.startsWith("+") ? undefined : country) : undefined;
  const valid = !!parsed?.isValid();
  const isBlocked = !!parsed?.country && blocked.includes(parsed.country);

  function update(nextRaw: string, nextCountry: CountryCode) {
    setRaw(nextRaw);
    setCountry(nextCountry);
    const p = nextRaw ? parsePhoneNumberFromString(nextRaw, nextRaw.startsWith("+") ? undefined : nextCountry) : undefined;
    if (p?.country && nextRaw.startsWith("+")) setCountry(p.country);
    onChange(p?.isValid() && !(p.country && blocked.includes(p.country)) ? p.number : null);
  }

  const dial = countries.find((c) => c.code === country)?.dial ?? "";
  const showError = touched && raw !== "" && (!valid || isBlocked);

  return (
    <div>
      <label htmlFor={id} className="label">Recipient's mobile number</label>
      <div className="flex gap-2">
        <select
          aria-label="Country"
          className="field !w-[9.5rem] shrink-0 !px-2"
          value={country}
          onChange={(e) => update(raw.startsWith("+") ? "" : raw, e.target.value as CountryCode)}
        >
          {countries.map((c) => (
            <option key={c.code} value={c.code}>{c.flag} {c.code} {c.dial}</option>
          ))}
        </select>
        <input
          id={id}
          type="tel"
          inputMode="tel"
          autoComplete="off"
          className="field"
          placeholder={`${dial} ...`}
          value={raw}
          onChange={(e) => update(e.target.value, country)}
          onBlur={() => setTouched(true)}
          aria-invalid={showError}
          aria-describedby={`${id}-hint`}
        />
      </div>
      <p id={`${id}-hint`} className={`mt-1.5 text-sm ${showError ? "text-buoy" : "text-muted"}`} role={showError ? "alert" : undefined}>
        {showError
          ? isBlocked ? "Texhaven cannot send to this country yet." : "That number does not look valid for this country."
          : valid && parsed ? `Will send to ${parsed.formatInternational()}` : "Pick a country, or paste the full number starting with +."}
      </p>
    </div>
  );
}
