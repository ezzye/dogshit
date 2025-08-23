import { BrowserRouter, Routes, Route } from 'react-router-dom';
import NavBar from './components/NavBar';
import Home from './pages/Home';
import Upload from './pages/Upload';
import Progress from './pages/Progress';
import Results from './pages/Results';
import Rules from './pages/Rules';

export default function App() {
  return (
    <BrowserRouter>
      <NavBar />
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/upload" element={<Upload />} />
        <Route path="/progress/:jobId" element={<Progress />} />
        <Route path="/results/:jobId" element={<Results />} />
        <Route path="/rules" element={<Rules />} />
      </Routes>
    </BrowserRouter>
  );
}
