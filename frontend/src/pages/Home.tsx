import { Link } from 'react-router-dom';

export default function Home() {
  return (
    <main>
      <section className="bg-blue-50 text-center py-20 px-4">
        <h1 className="text-4xl font-bold mb-4">Understand your spending</h1>
        <p className="text-lg mb-8">
          Turn bank statements into actionable financial insights.
        </p>
        <div className="space-x-4">
          <Link to="/upload" className="px-6 py-3 rounded bg-blue-600 text-white hover:bg-blue-700">
            Upload
          </Link>
          <Link to="/rules" className="px-6 py-3 rounded bg-gray-200 text-gray-800 hover:bg-gray-300">
            Rules
          </Link>
        </div>
      </section>
      <section className="py-12 px-4 max-w-3xl mx-auto text-center">
        <h2 className="text-2xl font-semibold mb-4">Get started in three steps</h2>
        <ol className="list-decimal list-inside text-left space-y-2">
          <li>
            Clean your CSV using{' '}
            <a
              href="https://bankcleanr.uwu.ai/"
              className="text-blue-600 underline"
              target="_blank"
              rel="noreferrer"
            >
              Bankcleanr
            </a>
            .
          </li>
          <li>Upload the file to categorize transactions.</li>
          <li>Explore insights and refine rules.</li>
        </ol>
      </section>
      <section className="bg-gray-50 py-12">
        <div className="max-w-4xl mx-auto grid md:grid-cols-3 gap-6 text-center">
          <div className="p-6">
            <h3 className="font-semibold mb-2">Automatic categorization</h3>
            <p>Our rules engine groups your transactions instantly.</p>
          </div>
          <div className="p-6">
            <h3 className="font-semibold mb-2">Track spending</h3>
            <p>Visualize where your money goes each month.</p>
          </div>
          <div className="p-6">
            <h3 className="font-semibold mb-2">Privacy first</h3>
            <p>Your data stays on your machine.</p>
          </div>
        </div>
      </section>
    </main>
  );
}
