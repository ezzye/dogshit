import { useEffect, useState } from 'react';
import type { UserRule } from '../lib/types';
import { Button } from '../components/ui/button';

export default function Rules() {
  const [rules, setRules] = useState<UserRule[]>([]);
  const [suggestions, setSuggestions] = useState<Record<number, string>>({});
  const [errors, setErrors] = useState<Record<number, string>>({});
  const [submitted, setSubmitted] = useState<Record<number, boolean>>({});

  useEffect(() => {
    fetch('/rules')
      .then((r) => r.json())
      .then(setRules)
      .catch(() => setRules([]));
  }, []);

  const handleSubmit = async (
    e: React.FormEvent<HTMLFormElement>,
    rule: UserRule,
  ) => {
    e.preventDefault();
    const id = rule.id ?? 0;
    const suggestion = suggestions[id]?.trim() ?? '';
    if (!suggestion) {
      setErrors((prev) => ({ ...prev, [id]: 'Suggestion is required' }));
      return;
    }
    setErrors((prev) => ({ ...prev, [id]: '' }));
    await fetch('/feedback', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ rule_id: rule.id, suggestion }),
    });
    setSubmitted((prev) => ({ ...prev, [id]: true }));
    setSuggestions((prev) => ({ ...prev, [id]: '' }));
  };

  return (
    <main className="p-4 space-y-4">
      <h1 className="text-2xl font-bold">Rules</h1>
      <ul className="space-y-4">
        {rules.map((rule) => (
          <li key={rule.id ?? rule.pattern} className="space-y-2">
            <p>{`${rule.pattern} → ${rule.label}`}</p>
            <form
              onSubmit={(e) => handleSubmit(e, rule)}
              className="space-y-2"
              aria-label={`Suggest correction for rule ${rule.pattern}`}
            >
              <div>
                <label
                  htmlFor={`suggestion-${rule.id}`}
                  className="block font-medium"
                >
                  Suggestion
                </label>
                <input
                  id={`suggestion-${rule.id}`}
                  type="text"
                  value={suggestions[rule.id ?? 0] ?? ''}
                  onChange={(e) =>
                    setSuggestions((prev) => ({
                      ...prev,
                      [rule.id ?? 0]: e.target.value,
                    }))
                  }
                  className="mt-1 block w-full rounded border p-2 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500"
                  aria-label="Suggestion"
                />
              </div>
              {errors[rule.id ?? 0] && (
                <p role="alert" className="text-red-600">
                  {errors[rule.id ?? 0]}
                </p>
              )}
              <Button type="submit">Suggest correction</Button>
              {submitted[rule.id ?? 0] && (
                <p role="status" className="text-green-600">
                  Thanks for your feedback!
                </p>
              )}
            </form>
          </li>
        ))}
      </ul>
    </main>
  );
}
