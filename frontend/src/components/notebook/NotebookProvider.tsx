"use client";
import { createContext, useContext, useEffect, useState } from "react";
import { api } from "@/lib/api";

export interface CellData {
  id: string;
  code: string;
  output?: any;
}

interface NotebookCtx {
  session: string;
  file: string;
  cells: CellData[];
  addCell(): void;
  updateCell(id: string, code: string): void;
  runCell(id: string): Promise<void>;
  openFile(name: string): Promise<void>;
  setFile(name: string): void;
}

const NotebookContext = createContext<NotebookCtx | null>(null);

export function NotebookProvider({ children }: { children: React.ReactNode }) {
  const [session, setSession] = useState("");
  const [file, setFile] = useState("");
  const [cells, setCells] = useState<CellData[]>([]);

  useEffect(() => {
    async function init() {
      const { data } = await api.post("/notebook/new");
      if (data.success) {
        const sid = data.data.session_id as string;
        setSession(sid);
        setFile(sid);
        const res = await api.get(`/notebook/${sid}/load`);
        if (res.data.success && res.data.data) {
          setCells(res.data.data.cells as CellData[]);
        } else {
          setCells([
            {
              id: `cell-${Date.now()}`,
              code: "import pandas as pd\nimport numpy as np\nimport matplotlib.pyplot as plt\n%matplotlib inline",
            },
          ]);
        }
      }
    }
    init();
  }, []);

  useEffect(() => {
    if (!session) return;
    api.post(`/notebook/${session}/save`, { notebook: { cells } });
  }, [cells, session]);

  const addCell = () =>
    setCells((c) => [...c, { id: `cell-${Date.now()}`, code: "" }]);

  const updateCell = (id: string, code: string) =>
    setCells((c) => c.map((cell) => (cell.id === id ? { ...cell, code } : cell)));

  const runCell = async (id: string) => {
    const cell = cells.find((c) => c.id === id);
    if (!cell) return;
    const { data } = await api.post(`/notebook/${session}/execute`, {
      cellId: id,
      code: cell.code,
    });
    if (data.success) {
      setCells((cs) =>
        cs.map((c) => (c.id === id ? { ...c, output: data.data } : c))
      );
    }
  };

  const openFile = async (name: string) => {
    const { data } = await api.post("/notebook/new");
    if (data.success) {
      const sid = data.data.session_id as string;
      setSession(sid);
      setFile(name);
      const res = await api.get(`/notebook/file/${name}`);
      if (res.data.success && res.data.data) {
        setCells(res.data.data.cells as CellData[]);
      } else {
        setCells([]);
      }
    }
  };

  return (
    <NotebookContext.Provider
      value={{ session, file, cells, addCell, updateCell, runCell, openFile, setFile }}
    >
      {children}
    </NotebookContext.Provider>
  );
}

export const useNotebook = () => {
  const ctx = useContext(NotebookContext);
  if (!ctx) throw new Error("Notebook context missing");
  return ctx;
};


