import { BrowserRouter, Routes, Route, Link } from 'react-router-dom';
import Upload from './pages/Upload';
import Progress from './pages/Progress';
import Results from './pages/Results';
import Rules from './pages/Rules';

export default function App() {
  return (
    <BrowserRouter>
      <nav aria-label="Main navigation" className="p-4 space-x-4">
        <Link to="/">Upload</Link>
        <Link to="/rules">Rules</Link>
      </nav>
      <Routes>
        <Route path="/" element={<Upload />} />
        <Route path="/progress/:jobId" element={<Progress />} />
        <Route path="/results/:jobId" element={<Results />} />
        <Route path="/rules" element={<Rules />} />
      </Routes>
    </BrowserRouter>
  );
}
