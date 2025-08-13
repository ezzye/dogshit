import { useEffect, useState } from 'react';
import { Button } from '../components/ui/button';
import { waitForJobStatus } from '../lib/utils';

export default function Upload() {
  const [file, setFile] = useState<File | null>(null);
  const [rules, setRules] = useState<string[]>([]);
  const [jobId, setJobId] = useState<string | null>(null);

  useEffect(() => {
    fetch('/rules')
      .then((r) => r.json())
      .then(setRules)
      .catch(() => setRules([]));
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) return;
    const typedFile = new File([file], file.name, {
      type: 'application/x-ndjson',
    });
    const formData = new FormData();
    formData.append('file', typedFile);
    const res = await fetch('/upload', { method: 'POST', body: formData });
    const data = await res.json();
    setJobId(data.job_id);
    await waitForJobStatus(data.job_id);
    await fetch('/classify', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ job_id: data.job_id }),
    });
    window.location.href = `/progress/${data.job_id}`;
  };

  return (
    <main className="p-4 space-y-4">
      <h1 className="text-2xl font-bold">Upload Bank Statement</h1>
      <form onSubmit={handleSubmit} className="space-y-4" aria-label="Upload form">
        <div>
          <label htmlFor="file" className="block font-medium">
            Select file
          </label>
          <input
            id="file"
            type="file"
            accept=".jsonl"
            onChange={(e) => setFile(e.target.files?.[0] ?? null)}
            className="mt-1 block w-full rounded border p-2 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500"
            aria-label="Bank statement file"
          />
        </div>
        <Button type="submit" disabled={!file} aria-disabled={!file}>
          Upload
        </Button>
      </form>
      {jobId && (
        <p>
          Job ID: <span>{jobId}</span>
        </p>
      )}
      <section aria-labelledby="rules-heading" className="space-y-2">
        <h2 id="rules-heading" className="text-xl font-semibold">
          Rules
        </h2>
        <ul className="list-disc pl-4">
          {rules.map((r) => (
            <li key={r}>{r}</li>
          ))}
        </ul>
      </section>
    </main>
  );
}
