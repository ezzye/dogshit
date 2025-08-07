import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Upload from './pages/Upload';
import Progress from './pages/Progress';
import Results from './pages/Results';

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Upload />} />
        <Route path="/progress/:jobId" element={<Progress />} />
        <Route path="/results/:jobId" element={<Results />} />
      </Routes>
    </BrowserRouter>
  );
}
