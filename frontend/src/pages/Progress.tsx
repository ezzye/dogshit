import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';

export default function Progress() {
  const { jobId } = useParams();
  const navigate = useNavigate();

  const [status, setStatus] = useState<string>('uploaded');

  useEffect(() => {
    const interval = setInterval(async () => {
      const res = await fetch(`/status/${jobId}`);
      const data = await res.json();
      setStatus(data.status);
      if (data.status === 'completed') {
        clearInterval(interval);
        navigate(`/results/${jobId}`);
      }
      if (data.status === 'failed') {
        clearInterval(interval);
      }
    }, 1000);
    return () => clearInterval(interval);
  }, [jobId, navigate]);

  return (
    <main className="p-4" aria-busy={status !== 'failed' && status !== 'completed'}>
      <h1 className="text-2xl font-bold">Processing...</h1>
      {status === 'failed' ? (
        <p role="alert">Processing failed. Please try again.</p>
      ) : (
        <p role="status">Current status: {status}</p>
      )}
      {jobId && (
        <p>
          Job ID: <span>{jobId}</span>
        </p>
      )}
    </main>
  );
}
