import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import ReportViewer from '../components/ReportViewer';

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
  const [costs, setCosts] = useState<
    | {
        tokens_in: number;
        tokens_out: number;
        total_tokens: number;
        estimated_cost_gbp: number;
      }
    | null
  >(null);
  const [summaryUrl, setSummaryUrl] = useState<string | null>(null);
  const [reportUrl, setReportUrl] = useState<string | null>(null);

  const linkClasses =
    'rounded-md bg-blue-600 px-4 py-2 text-white focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-blue-500';

  useEffect(() => {
    async function loadData() {
      const [summaryRes, txRes, costRes] = await Promise.all([
        fetch(`/summary/${jobId}`),
        fetch(`/transactions/${jobId}`),
        fetch(`/costs/${jobId}`),
      ]);

      if (summaryRes.ok) {
        setSummary(await summaryRes.json());
      }
      if (txRes.ok) {
        setTransactions(await txRes.json());
      }
      if (costRes.ok) {
        setCosts(await costRes.json());
      }
    }
    if (jobId) {
      loadData();
    }
  }, [jobId]);

  useEffect(() => {
    async function loadUrls() {
      const [reportResult, summaryResult] = await Promise.allSettled([
        fetch(`/report/${jobId}`),
        fetch(`/download/${jobId}/summary`),
      ]);

      if (
        reportResult.status === 'fulfilled' &&
        reportResult.value.ok
      ) {
        const data = await reportResult.value.json();
        setReportUrl(data.url);
      }

      if (
        summaryResult.status === 'fulfilled' &&
        summaryResult.value.ok
      ) {
        const data = await summaryResult.value.json();
        setSummaryUrl(data.url);
      }
    }
    if (jobId) {
      loadUrls();
    }
  }, [jobId]);

  return (
    <main className="p-4 space-y-4">
      <h1 className="text-2xl font-bold">Results</h1>
      <div className="flex gap-4">
        {summaryUrl && (
          <a href={summaryUrl} className={linkClasses} download>
            Download Summary
          </a>
        )}
        {reportUrl && (
          <a href={reportUrl} className={linkClasses} download>
            Download Report
          </a>
        )}
      </div>

      <ReportViewer url={reportUrl} />

      {costs && (
        <section>
          <h2 className="text-xl font-semibold">Costs</h2>
          <table className="min-w-full text-left">
            <tbody>
              <tr>
                <td className="pr-4">Tokens In</td>
                <td>{costs.tokens_in}</td>
              </tr>
              <tr>
                <td className="pr-4">Tokens Out</td>
                <td>{costs.tokens_out}</td>
              </tr>
              <tr>
                <td className="pr-4">Total Tokens</td>
                <td>{costs.total_tokens}</td>
              </tr>
              <tr>
                <td className="pr-4">Estimated Cost</td>
                <td>{costs.estimated_cost_gbp}</td>
              </tr>
            </tbody>
          </table>
        </section>
      )}

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
