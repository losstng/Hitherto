// src/components/CategorySelect.tsx
"use client";
import { useCategories } from "@/hooks/useIngest";
import { useChatContext } from "./ChatProvider";
export default function CategorySelect({
  value,
  onChange,
}: {
  value: string;
  onChange: (c: string) => void;
}) {
  const { data: categories } = useCategories();
  const { setFilters } = useChatContext();
  const sorted = categories?.slice().sort((a, b) => a.localeCompare(b));
  return (
    <select
      value={value}
      onChange={(e) => {
        onChange(e.target.value);
        setFilters({ category: e.target.value });
      }}
      className="border rounded px-2 py-1"
    >
      <option value="">All categories</option>
      {sorted?.map((c) => (
        <option key={c} value={c}>
          {c}
        </option>
      ))}
    </select>
  );
}
