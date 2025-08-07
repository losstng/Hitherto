"use client";
import { useState } from "react";
import { DayPicker, DateRange } from "react-day-picker";
import { format, parseISO } from "date-fns";
import { useChatContext } from ".";
import "@/styles/daypicker.css";

export default function DateRangeFilter({
  start,
  end,
  onChangeStart,
  onChangeEnd,
}: {
  start: string;
  end: string;
  onChangeStart: (d: string) => void;
  onChangeEnd: (d: string) => void;
}) {
  const [open, setOpen] = useState(false);
  const { setFilters } = useChatContext();
  const selected: DateRange | undefined = start
    ? { from: parseISO(start), to: end ? parseISO(end) : undefined }
    : undefined;
  return (
    <div className="relative">
      <button
        type="button"
        className="border rounded px-2 py-1 flex-shrink-0"
        onClick={() => setOpen(!open)}
      >
        {selected?.from
          ? `${selected.from.toLocaleDateString()}${selected.to ? ` – ${selected.to.toLocaleDateString()}` : ""}`
          : "Select date"}
      </button>
      {open && (
        <div className="absolute z-10 bg-white shadow p-2">
          <DayPicker
            mode="range"
            selected={selected}
            onSelect={(range) => {
              if (!range) {
                onChangeStart("");
                onChangeEnd("");
                setFilters({ start: "", end: "" });
                return;
              }
              const from = range.from ? format(range.from, "yyyy-MM-dd") : "";
              const to = range.to ? format(range.to, "yyyy-MM-dd") : "";
              onChangeStart(from);
              onChangeEnd(to);
              setFilters({ start: from, end: to });
            }}
          />
          <div className="text-right mt-2">
            <button
              type="button"
              className="text-sm text-blue-600 underline"
              onClick={() => {
                onChangeStart("");
                onChangeEnd("");
                setFilters({ start: "", end: "" });
                setOpen(false);
              }}
            >
              Reset
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
