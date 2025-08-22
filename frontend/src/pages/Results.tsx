import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';

interface Totals {
  income: number;
  expenses: number;
  net: number;
}

interface CategoryBreakdown {
  name: string;
  total: number;
  count: number;
}

interface RecurringCharge {
  merchant: string;
  cadence: string;
  avg_amount: number;
  count: number;
}

interface Summary {
  totals: Totals;
  categories: CategoryBreakdown[];
  recurring?: RecurringCharge[];
}

export interface Transaction {
  date: string;
  description: string;
  amount: number;
  type: string;
  category?: string;
  label?: string;
}

export default function Results() {
  const { jobId } = useParams();
  const [summary, setSummary] = useState<Summary | null>(null);
  const [transactions, setTransactions] = useState<Transaction[]>([]);

  useEffect(() => {
    async function loadData() {
      const [summaryRes, txRes] = await Promise.all([
        fetch(`/summary/${jobId}`),
        fetch(`/transactions/${jobId}`),
      ]);

      if (summaryRes.ok) {
        setSummary(await summaryRes.json());
      }
      if (txRes.ok) {
        setTransactions(await txRes.json());
      }
    }
    if (jobId) {
      loadData();
    }
  }, [jobId]);

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
          href={`/download/${jobId}/report`}
          className="rounded-md bg-blue-600 px-4 py-2 text-white focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-blue-500"
          download
        >
          Download Report
        </a>
      </div>

      {summary && (
        <section className="space-y-4">
          <h2 className="text-xl font-semibold">Summary</h2>
          <table className="min-w-full text-left">
            <tbody>
              <tr>
                <td className="pr-4">Income</td>
                <td>{summary.totals.income}</td>
              </tr>
              <tr>
                <td className="pr-4">Expenses</td>
                <td>{summary.totals.expenses}</td>
              </tr>
              <tr>
                <td className="pr-4">Net</td>
                <td>{summary.totals.net}</td>
              </tr>
            </tbody>
          </table>

          <h3 className="text-lg font-semibold">Categories</h3>
          <table className="min-w-full text-left">
            <thead>
              <tr>
                <th className="pr-4">Name</th>
                <th className="pr-4">Total</th>
                <th>Count</th>
              </tr>
            </thead>
            <tbody>
              {summary.categories.map((cat) => (
                <tr key={cat.name}>
                  <td className="pr-4">{cat.name}</td>
                  <td className="pr-4">{cat.total}</td>
                  <td>{cat.count}</td>
                </tr>
              ))}
            </tbody>
          </table>

          {summary.recurring && summary.recurring.length > 0 && (
            <>
              <h3 className="text-lg font-semibold">Recurring Charges</h3>
              <table className="min-w-full text-left">
                <thead>
                  <tr>
                    <th className="pr-4">Merchant</th>
                    <th className="pr-4">Cadence</th>
                    <th className="pr-4">Avg Amount</th>
                    <th>Count</th>
                  </tr>
                </thead>
                <tbody>
                  {summary.recurring.map((r) => (
                    <tr key={r.merchant}>
                      <td className="pr-4">{r.merchant}</td>
                      <td className="pr-4">{r.cadence}</td>
                      <td className="pr-4">{r.avg_amount}</td>
                      <td>{r.count}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </>
          )}
        </section>
      )}

      <section className="space-y-4">
        <h2 className="text-xl font-semibold">Transactions</h2>
        <table className="min-w-full text-left">
          <thead>
            <tr>
              <th className="pr-4">Date</th>
              <th className="pr-4">Description</th>
              <th className="pr-4">Amount</th>
              <th>Type</th>
            </tr>
          </thead>
          <tbody>
            {transactions.map((tx, idx) => (
              <tr key={idx}>
                <td className="pr-4">{tx.date}</td>
                <td className="pr-4">{tx.description}</td>
                <td className="pr-4">{tx.amount}</td>
                <td>{tx.type}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </main>
  );
}
