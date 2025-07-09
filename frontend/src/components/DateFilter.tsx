"use client";
export default function DateFilter({
  value,
  onChange,
}: {
  value: string;
  onChange: (d: string) => void;
}) {
  return (
    <input
      type="date"
      value={value}
      onChange={(e) => onChange(e.target.value)}
      className="border rounded px-2 py-1"
    />
  );
}
