"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { useNotebook } from "./NotebookProvider";

export default function NotebookSidebar() {
  const { session, cells, openFile, file, setFile } = useNotebook();
  const [tab, setTab] = useState<"notebooks" | "variables">("notebooks");
  const [notebooks, setNotebooks] = useState<string[]>([]);
  const [variables, setVariables] = useState<Record<string, string>>({});

  useEffect(() => {
    if (tab === "notebooks") {
      api.get("/notebook/list").then((res) => {
        if (res.data.success) {
          setNotebooks(res.data.data as string[]);
        }
      });
    }
  }, [tab]);

  useEffect(() => {
    if (tab === "variables" && session) {
      api.get(`/notebook/${session}/variables`).then((res) => {
        if (res.data.success) {
          setVariables(res.data.data as Record<string, string>);
        }
      });
    }
  }, [tab, session, cells]);

  return (
    <aside className="flex flex-col h-full bg-gray-50 border-r">
      <div className="flex">
        <button
          className={`flex-1 p-2 text-sm ${tab === "notebooks" ? "bg-white" : ""}`}
          onClick={() => setTab("notebooks")}
        >
          Notebooks
        </button>
        <button
          className={`flex-1 p-2 text-sm ${tab === "variables" ? "bg-white" : ""}`}
          onClick={() => setTab("variables")}
        >
          Variables
        </button>
      </div>
      <div className="p-2 overflow-y-auto flex-1">
        {tab === "notebooks" ? (
          <ul className="text-sm space-y-1">
            {notebooks.map((n) => (
              <li key={n} className="flex items-center justify-between">
                <button
                  className="text-left flex-1 hover:underline"
                  onClick={() => openFile(n)}
                >
                  {n === file ? <strong>{n}</strong> : n}
                </button>
                <button
                  className="text-xs px-1"
                  onClick={async () => {
                    const name = prompt("Rename", n);
                    if (name && name !== n) {
                      await api.post(`/notebook/file/${n}/rename`, { new_name: name });
                      if (file === n) setFile(name);
                      api.get("/notebook/list").then((res) => {
                        if (res.data.success) setNotebooks(res.data.data as string[]);
                      });
                    }
                  }}
                >
                  Rename
                </button>
                <button
                  className="text-xs px-1"
                  onClick={async () => {
                    if (confirm(`Delete ${n}?`)) {
                      await api.post(`/notebook/file/${n}/delete`);
                      if (file === n) setFile("");
                      api.get("/notebook/list").then((res) => {
                        if (res.data.success) setNotebooks(res.data.data as string[]);
                      });
                    }
                  }}
                >
                  Delete
                </button>
              </li>
            ))}
            {notebooks.length === 0 && (
              <li className="text-gray-500">No notebooks</li>
            )}
          </ul>
        ) : (
          <ul className="text-sm space-y-1">
            {Object.entries(variables).map(([k, v]) => (
              <li key={k}>
                <span className="font-mono">{k}</span>: {v}
              </li>
            ))}
            {Object.keys(variables).length === 0 && (
              <li className="text-gray-500">No variables</li>
            )}
          </ul>
        )}
      </div>
    </aside>
  );
}
