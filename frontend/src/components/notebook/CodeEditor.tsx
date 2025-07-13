"use client";
import { ReactCodeMirror } from "@uiw/react-codemirror";
import { python } from "@codemirror/lang-python";

interface Props {
  value: string;
  onChange(value: string): void;
}

export default function CodeEditor({ value, onChange }: Props) {
  return (
    <ReactCodeMirror
      value={value}
      extensions={[python()]}
      height="auto"
      theme="light"
      onChange={onChange}
    />
  );
}

