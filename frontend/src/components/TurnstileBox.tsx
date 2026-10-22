import { Turnstile, type TurnstileInstance } from "@marsidev/react-turnstile";
import { forwardRef, useEffect, useImperativeHandle, useRef } from "react";
import { useConfig } from "../lib/config";

export interface TurnstileHandle {
  reset: () => void;
}

/** Cloudflare Turnstile. With no site key (local dev) it reports a placeholder the dev backend accepts. */
const TurnstileBox = forwardRef<TurnstileHandle, { onToken: (t: string) => void }>(({ onToken }, ref) => {
  const { config } = useConfig();
  const inst = useRef<TurnstileInstance>(null);
  const siteKey = config?.turnstile_site_key;

  useImperativeHandle(ref, () => ({
    reset: () => {
      onToken("");
      if (siteKey) inst.current?.reset();
      else onToken("dev-bypass");
    },
  }));

  useEffect(() => {
    if (config && !siteKey) onToken("dev-bypass");
  }, [config, siteKey, onToken]);

  if (!siteKey) return null;
  return (
    <Turnstile
      ref={inst}
      siteKey={siteKey}
      onSuccess={onToken}
      onExpire={() => onToken("")}
      onError={() => onToken("")}
      options={{ theme: "light" }}
    />
  );
});

export default TurnstileBox;
