"use client";
interface Props {
  output: any;
}
export default function OutputArea({ output }: Props) {
  if (!output) return null;
  return (
    <div className="bg-gray-50 p-2 whitespace-pre-wrap">
      {output.stdout && <pre>{output.stdout}</pre>}
      {output.stderr && <pre className="text-red-600">{output.stderr}</pre>}
      {output.html && (
        <div dangerouslySetInnerHTML={{ __html: output.html }} />
      )}
      {output.images &&
        output.images.map((src: string, i: number) => (
          <img key={i} src={src} alt="plot" />
        ))}
    </div>
  );
}

