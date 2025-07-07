// src/components/CategorySelect.tsx
"use client";
export default function CategorySelect({
  value,
  onChange,
}: {
  value: string;
  onChange: (c: string) => void;
}) {
  return (
    <select
      value={value}
      onChange={(e) => onChange(e.target.value)}
      className="border rounded px-2 py-1"
    >
      <option value="">All categories</option>
      <option value="economics_daily">economics_daily</option>
      <option value="supply_lines">supply_lines</option>
      {/* add more */}
    </select>
  );
}
