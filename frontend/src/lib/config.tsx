import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import type { AppConfig } from "../types";
import { api } from "./api";

interface ConfigState {
  config: AppConfig | null;
  error: string | null;
}
const Ctx = createContext<ConfigState>({ config: null, error: null });

export function ConfigProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<ConfigState>({ config: null, error: null });
  useEffect(() => {
    api.config().then(
      (config) => setState({ config, error: null }),
      (e: Error) => setState({ config: null, error: e.message }),
    );
  }, []);
  return <Ctx.Provider value={state}>{children}</Ctx.Provider>;
}

export const useConfig = () => useContext(Ctx);
