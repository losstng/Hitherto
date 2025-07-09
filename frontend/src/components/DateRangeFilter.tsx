"use client";

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
  return (
    <div className="flex items-center gap-2">
      <input
        type="date"
        value={start}
        onChange={(e) => onChangeStart(e.target.value)}
        className="border rounded px-2 py-1"
      />
      <span>to</span>
      <input
        type="date"
        value={end}
        onChange={(e) => onChangeEnd(e.target.value)}
        className="border rounded px-2 py-1"
      />
    </div>
  );
}
