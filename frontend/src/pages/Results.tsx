import { useParams } from 'react-router-dom';

export default function Results() {
  const { jobId } = useParams();
  return (
    <main className="p-4 space-y-4">
      <h1 className="text-2xl font-bold">Results</h1>
      <div className="flex gap-4">
        <a
          href={`/download/${jobId}/summary`}
          className="rounded-md bg-blue-600 px-4 py-2 text-white focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-blue-500"
          download
        >
          Download Summary
        </a>
        <a
          href={`/download/${jobId}/details`}
          className="rounded-md bg-blue-600 px-4 py-2 text-white focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-blue-500"
          download
        >
          Download Details
        </a>
      </div>
    </main>
  );
}
