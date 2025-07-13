"use client";
import { useNotebook } from "./NotebookProvider";
import Cell from "./Cell";

export default function Notebook() {
  const { cells, addCell } = useNotebook();
  return (
    <div className="p-4 space-y-4">
      {cells.map((c) => (
        <Cell key={c.id} id={c.id} code={c.code} output={c.output} />
      ))}
      <button
        className="py-1 px-3 bg-green-500 text-white rounded"
        onClick={addCell}
      >
        Add Cell
      </button>
    </div>
  );
}

