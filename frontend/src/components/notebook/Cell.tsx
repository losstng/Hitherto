"use client";
import CodeEditor from "./CodeEditor";
import OutputArea from "./OutputArea";
import { useNotebook } from "./NotebookProvider";

interface Props {
  id: string;
  code: string;
  output: any;
}

export default function Cell({ id, code, output }: Props) {
  const { updateCell, runCell } = useNotebook();
  return (
    <div className="border rounded mb-4">
      <CodeEditor value={code} onChange={(v) => updateCell(id, v)} />
      <div className="p-2">
        <button
          className="bg-blue-500 hover:bg-blue-600 text-white px-3 py-1 text-sm rounded"
          onClick={() => runCell(id)}
        >
          Run
        </button>
      </div>
      <OutputArea output={output} />
    </div>
  );
}

