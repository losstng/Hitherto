// src/components/NewsletterTable.tsx
import { NewsletterLite } from "@/lib/types";
import NewsletterRow from "./NewsletterRow";

export default function NewsletterTable({ data }: { data: NewsletterLite[] }) {
  return (
    <table className="w-full text-sm">
      <thead>
        <tr className="bg-gray-100">
          <th className="p-2 text-left">Title</th>
          <th className="p-2 text-left">Date</th>
          <th className="p-2 text-left">Actions</th>
        </tr>
      </thead>
      <tbody>{data.map((n) => <NewsletterRow key={n.message_id} n={n} />)}</tbody>
    </table>
  );
}
