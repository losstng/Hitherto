// src/components/CategorySelect.tsx
"use client";
import { useCategories } from "@/hooks/useIngest";
export default function CategorySelect({
  value,
  onChange,
}: {
  value: string;
  onChange: (c: string) => void;
}) {
  const { data: categories } = useCategories();
  return (
    <select
      value={value}
      onChange={(e) => onChange(e.target.value)}
      className="border rounded px-2 py-1"
    >
      <option value="">All categories</option>
      {categories?.map((c) => (
        <option key={c} value={c}>
          {c}
        </option>
      ))}
    </select>
  );
}
