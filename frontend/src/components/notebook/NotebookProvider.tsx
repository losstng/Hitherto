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
  newNotebook(): Promise<void>;
  save(): Promise<void>;
  setFile(name: string): void;
}

const NotebookContext = createContext<NotebookCtx | null>(null);

export function NotebookProvider({ children }: { children: React.ReactNode }) {
  const [session, setSession] = useState("");
  const [file, setFile] = useState("");
  const [cells, setCells] = useState<CellData[]>([]);
  const [loaded, setLoaded] = useState(false);

  const shutdown = async () => {
    if (session) {
      try {
        await api.post(`/notebook/${session}/shutdown`);
      } catch (e) {
        // ignore network errors
      }
    }
  };

  const newNotebook = async () => {
    await shutdown();
    setLoaded(false);
    const { data } = await api.post("/notebook/new");
    if (data.success) {
      const sid = data.data.session_id as string;
      setSession(sid);
      setFileName(sid);
      const starter = [
        {
          id: `cell-${Date.now()}`,
          code:
            "import pandas as pd\nimport numpy as np\nimport matplotlib.pyplot as plt\n%matplotlib inline",
        },
      ];
      setCells(starter);
      // ensure the file exists so the sidebar list updates
      await api.post(`/notebook/${sid}/save`, { notebook: { cells: starter } });
      setLoaded(true);
    if (typeof window !== "undefined") {
      localStorage.setItem("notebookFile", sid);
    }
    }
  };

  useEffect(() => {
    async function init() {
      const storedFile =
        typeof window !== "undefined" ? localStorage.getItem("notebookFile") : null;
      const res = await api.get("/notebook/list");
      const list = res.data.success ? (res.data.data as string[]) : [];
      if (storedFile && list.includes(storedFile)) {
        openFile(storedFile);
      } else if (list.length) {
        openFile(list[0]);
      } else {
        newNotebook();
      }
    }
    init();
  }, []);

  useEffect(() => {
    if (!session || !loaded) return;
    const path = file && file !== session ? `/notebook/file/${file}/save` : `/notebook/${session}/save`;
    api.post(path, { notebook: { cells } });
  }, [cells, session, file, loaded]);

  useEffect(() => {
    return () => {
      shutdown();
    };
  }, [session]);

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
    await shutdown();
    setLoaded(false);
    const { data } = await api.post("/notebook/new");
    if (data.success) {
      const sid = data.data.session_id as string;
      setSession(sid);
      setFileName(name);
    if (typeof window !== "undefined") {
      localStorage.setItem("notebookFile", name);
    }
      const res = await api.get(`/notebook/file/${name}`);
      if (res.data.success && res.data.data) {
        setCells(res.data.data.cells as CellData[]);
        setLoaded(true);
      } else {
        setCells([]);
        setLoaded(true);
      }
    }
  };

  const saveNotebook = async () => {
    if (!session) return;
    const path =
      file && file !== session ? `/notebook/file/${file}/save` : `/notebook/${session}/save`;
    await api.post(path, { notebook: { cells } });
  };

  const setFileName = (name: string) => {
    setFile(name);
    if (typeof window !== "undefined") {
      localStorage.setItem("notebookFile", name);
    }
  };

  return (
    <NotebookContext.Provider
      value={{ session, file, cells, addCell, updateCell, runCell, openFile, newNotebook, save: saveNotebook, setFile: setFileName }}
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


