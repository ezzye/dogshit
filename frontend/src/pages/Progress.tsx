import { useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';

export default function Progress() {
  const { jobId } = useParams();
  const navigate = useNavigate();

  useEffect(() => {
    const interval = setInterval(async () => {
      const res = await fetch(`/status/${jobId}`);
      const data = await res.json();
      if (data.status === 'completed') {
        clearInterval(interval);
        navigate(`/results/${jobId}`);
      }
    }, 1000);
    return () => clearInterval(interval);
  }, [jobId, navigate]);

  return (
    <main className="p-4" aria-busy="true">
      <h1 className="text-2xl font-bold">Processing...</h1>
      <p role="status">We are processing your file. This may take a moment.</p>
      {jobId && (
        <p>
          Job ID: <span>{jobId}</span>
        </p>
      )}
    </main>
  );
}
