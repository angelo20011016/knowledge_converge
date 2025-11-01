import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Sidebar from './components/Sidebar';
import SoloUrlPage from './pages/SoloUrlPage';
import AuthPage from './pages/AuthPage';
import LoginSuccessPage from './pages/LoginSuccessPage';
import ProtectedRoute from './components/ProtectedRoute';
import TemplateManagerModal from './components/TemplateManagerModal'; // Import the modal
import InteractiveSvgBackground from './components/InteractiveSvgBackground';
import './App.css';

function App() {
  const [templateModalOpen, setTemplateModalOpen] = useState(false);

  return (
    <Router>
      <InteractiveSvgBackground />
      <div className="app-layout">
        <Sidebar openTemplateModal={() => setTemplateModalOpen(true)} />
        <main className="main-content">
          <Routes>
            <Route path="/" element={<SoloUrlPage />} />
            {/* The /templates route is no longer needed as it's a modal */}
            <Route path="/auth" element={<AuthPage />} />
            <Route path="/login/success" element={<LoginSuccessPage />} />
          </Routes>
        </main>
        <TemplateManagerModal 
          open={templateModalOpen} 
          onClose={() => setTemplateModalOpen(false)} 
        />
      </div>
    </Router>
  );
}

export default App;
