"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { useNotebook } from "./NotebookProvider";

export default function NotebookSidebar() {
  const { openFile, newNotebook, file, setFile } = useNotebook();
  const [notebooks, setNotebooks] = useState<string[]>([]);

  useEffect(() => {
    api.get("/notebook/list").then((res) => {
      if (res.data.success) {
        setNotebooks(res.data.data as string[]);
      }
    });
  }, []);

  return (
    <aside className="flex flex-col h-full bg-gray-50 border-r">
      <div className="p-2 overflow-y-auto flex-1">
        <div className="text-sm space-y-1">
            <button
              className="bg-blue-500 text-white w-full py-1 mb-2 rounded"
              onClick={async () => {
                await newNotebook();
                api.get("/notebook/list").then((res) => {
                  if (res.data.success) setNotebooks(res.data.data as string[]);
                });
              }}
            >
              New Notebook
            </button>
            <button
              className="bg-gray-200 w-full py-1 mb-2 rounded"
              onClick={() =>
                api.get("/notebook/list").then((res) => {
                  if (res.data.success) setNotebooks(res.data.data as string[]);
                })
              }
            >
              Reload List
            </button>
            <ul>
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
          </div>
        </div>
    </aside>
  );
}

