import React, { createContext, useContext, useState } from "react";
import type { DashboardState } from "../types/dashboard";

const DEFAULT_STATE: DashboardState = {
  status: "idle",
  upload: {
    progress: 0,
    activeTaskId: null,
    isUploading: false,
  },
  analysis: {
    stats: null,
    detect: null,
    derivedData: {},
    lastUpdated: null,
  },
  metadata: {
    filename: null,
    fileSize: null,
    startedAt: null,
    completedAt: null,
    processingDurationMs: null,
  },
  ui: {
    activeTab: "file",
    selectedFormat: "auto",
    logText: "",
    error: null,
  },
};

interface DashboardContextProps {
  state: DashboardState;
  setState: React.Dispatch<React.SetStateAction<DashboardState>>;
}

const DashboardContext = createContext<DashboardContextProps | undefined>(undefined);

export const DashboardProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [state, setState] = useState<DashboardState>(DEFAULT_STATE);

  return (
    <DashboardContext.Provider value={{ state, setState }}>
      {children}
    </DashboardContext.Provider>
  );
};

DashboardProvider.displayName = "DashboardProvider";

// eslint-disable-next-line react-refresh/only-export-components
export const useDashboardContext = (): DashboardContextProps => {
  const context = useContext(DashboardContext);
  if (!context) {
    throw new Error("useDashboardContext must be used within a DashboardProvider");
  }
  return context;
};
