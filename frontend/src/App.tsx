import React, { useEffect, useState } from 'react';
import RuleTable, { Rule } from './RuleTable';

export default function App() {
  const [rules, setRules] = useState<Rule[]>([]);
  const [message, setMessage] = useState<string>('');

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const text = await file.text();
    const lines = text.trim().split(/\r?\n/);
    const txs = lines.map(line => JSON.parse(line));
    setMessage('Uploading...');
    try {
      const resp = await fetch('/upload?token=dummy', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(txs)
      });
      if (resp.ok) {
        const data = await resp.json();
        setMessage(`Uploaded ${data.count} transactions`);
      } else {
        setMessage('Upload failed');
      }
    } catch {
      setMessage('Upload failed');
    }
    setTimeout(() => setMessage(''), 1000);
  };

  // load heuristics on mount
  useEffect(() => {
    fetch('/heuristics?token=dummy')
      .then(r => r.json())
      .then(setRules)
      .catch(() => setRules([]));
  }, []);

  const handleChange = (updated: Rule[]) => {
    setRules(updated);
  };

  const handleSave = async (rule: Rule) => {
    const idx = rules.findIndex(r => r.id === rule.id);
    const newRules = [...rules];
    if (idx >= 0) newRules[idx] = rule; else newRules.push(rule);
    setRules(newRules);
    setMessage('Saving...');
    await fetch('/heuristics?token=dummy', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(rule)
    });
    setMessage('Saved');
    setTimeout(() => setMessage(''), 1000);
  };

  return (
    <div className="p-4">
      <h1 className="text-xl font-bold mb-4">Heuristic Editor</h1>
      <input type="file" accept=".jsonl" onChange={handleUpload} className="mb-2" />
      {message && <div role="alert">{message}</div>}
      <RuleTable rules={rules} onChange={handleChange} onSave={handleSave} />
    </div>
  );
}
