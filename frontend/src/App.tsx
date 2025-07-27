import React, { useEffect, useState } from 'react';
import RuleTable, { Rule } from './RuleTable';

export default function App() {
  const [rules, setRules] = useState<Rule[]>([]);
  const [message, setMessage] = useState<string>('');

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
      {message && <div role="alert">{message}</div>}
      <RuleTable rules={rules} onChange={handleChange} onSave={handleSave} />
    </div>
  );
}
