"use client";
import { useState } from "react";
import { DayPicker, DateRange } from "react-day-picker";
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
  const selected: DateRange | undefined =
    start ? { from: new Date(start), to: end ? new Date(end) : undefined } : undefined;
  return (
    <div className="relative">
      <button
        type="button"
        className="border rounded px-2 py-1"
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
                return;
              }
              onChangeStart(range.from?.toISOString().slice(0, 10) ?? "");
              onChangeEnd(range.to?.toISOString().slice(0, 10) ?? "");
            }}
          />
          <div className="text-right mt-2">
            <button
              type="button"
              className="text-sm text-blue-600 underline"
              onClick={() => {
                onChangeStart("");
                onChangeEnd("");
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
