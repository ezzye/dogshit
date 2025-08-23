import { Link } from 'react-router-dom';

export default function NavBar() {
  return (
    <nav aria-label="Main navigation" className="p-4 space-x-4 bg-gray-100">
      <Link to="/" className="font-semibold">Home</Link>
      <Link to="/upload" className="font-semibold">Upload</Link>
      <Link to="/rules" className="font-semibold">Rules</Link>
      <span className="text-gray-400">Results</span>
      <span className="text-gray-400">Progress</span>
    </nav>
  );
}
