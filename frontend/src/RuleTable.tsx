import React, { useState } from 'react';

export interface Rule {
  id?: number;
  label: string;
  pattern: string;
}

interface Props {
  rules: Rule[];
  onChange: (rules: Rule[]) => void;
  onSave: (rule: Rule) => void;
}

export default function RuleTable({ rules, onChange, onSave }: Props) {
  const [newRule, setNewRule] = useState<Rule>({ label: '', pattern: '' });

  const handleDelete = (idx: number) => {
    const updated = [...rules];
    updated.splice(idx, 1);
    onChange(updated);
  };

  const handleInput = (idx: number, field: keyof Rule, value: string) => {
    const updated = rules.map((r, i) => (i === idx ? { ...r, [field]: value } : r));
    onChange(updated);
  };

  const handleAdd = () => {
    if (!newRule.label || !newRule.pattern) return;
    onSave({ ...newRule });
    setNewRule({ label: '', pattern: '' });
  };

  const handleSaveRow = (rule: Rule) => {
    onSave(rule);
  };

  const handleImport = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = () => {
      const text = reader.result as string;
      const lines = text.trim().split(/\r?\n/);
      const imported = lines.map(line => {
        const [label, pattern] = line.split(',');
        return { label, pattern };
      });
      onChange([...rules, ...imported]);
    };
    reader.readAsText(file);
  };

  const handleExport = () => {
    const csv = rules.map(r => `${r.label},${r.pattern}`).join('\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'heuristics.csv';
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div>
      <div className="mb-2 space-x-2">
        <input type="file" onChange={handleImport} />
        <button onClick={handleExport}>Export CSV</button>
      </div>
      <table className="border-collapse w-full">
        <thead>
          <tr>
            <th className="border p-2">Label</th>
            <th className="border p-2">Pattern</th>
            <th className="border p-2">Actions</th>
          </tr>
        </thead>
        <tbody>
          {rules.map((rule, idx) => (
            <tr key={idx}>
              <td className="border p-2">
                <input
                  value={rule.label}
                  onChange={e => handleInput(idx, 'label', e.target.value)}
                />
              </td>
              <td className="border p-2">
                <input
                  value={rule.pattern}
                  onChange={e => handleInput(idx, 'pattern', e.target.value)}
                />
              </td>
              <td className="border p-2 space-x-2">
                <button onClick={() => handleSaveRow(rule)}>Save</button>
                <button onClick={() => handleDelete(idx)}>Delete</button>
              </td>
            </tr>
          ))}
          <tr>
            <td className="border p-2">
              <input
                placeholder="Label"
                value={newRule.label}
                onChange={e => setNewRule({ ...newRule, label: e.target.value })}
              />
            </td>
            <td className="border p-2">
              <input
                placeholder="Pattern"
                value={newRule.pattern}
                onChange={e => setNewRule({ ...newRule, pattern: e.target.value })}
              />
            </td>
            <td className="border p-2">
              <button onClick={handleAdd}>Add</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  );
}
