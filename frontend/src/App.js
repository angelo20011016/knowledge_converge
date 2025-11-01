import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Sidebar from './components/Sidebar';
import SoloUrlPage from './pages/SoloUrlPage';
import TemplateManagementPage from './pages/TemplateManagementPage';
import HistoryPage from './pages/HistoryPage';
import InteractiveSvgBackground from './components/InteractiveSvgBackground';
import './App.css';

function App() {
  return (
    <Router>
      <InteractiveSvgBackground />
      <div className="app-layout">
        <Sidebar />
        <main className="main-content">
          <Routes>
            <Route path="/" element={<SoloUrlPage />} />
            <Route path="/history" element={<HistoryPage />} />
            <Route path="/templates" element={<TemplateManagementPage />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;
