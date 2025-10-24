import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Sidebar from './components/Sidebar';
import SoloUrlPage from './pages/SoloUrlPage';
import TopicSearchPage from './pages/TopicSearchPage';
import TemplateManagementPage from './pages/TemplateManagementPage'; // Import TemplateManagementPage
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
            <Route path="/topic-search" element={<TopicSearchPage />} />
            <Route path="/templates" element={<TemplateManagementPage />} /> {/* Add this route */}
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;
