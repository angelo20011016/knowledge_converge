import React, { useState, useEffect, useRef } from 'react';
import { FiZap } from 'react-icons/fi';
import ResultsDisplay from '../components/ResultsDisplay';

const SoloUrlPage = () => {
  const [url, setUrl] = useState('');
  const [title, setTitle] = useState('');
  const [language, setLanguage] = useState('en');
  
  const [status, setStatus] = useState({ main: "Idle", sub: "" });
  const [result, setResult] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  const pollingRef = useRef(null);
  const API_BASE_URL = "http://127.0.0.1:5000";

  useEffect(() => {
    return () => clearInterval(pollingRef.current);
  }, []);

  const pollStatus = () => {
    pollingRef.current = setInterval(() => {
      fetch(`${API_BASE_URL}/api/get-result`)
        .then(res => res.ok ? res.json() : Promise.reject(res))
        .then(data => {
          if (data.individual_summaries || data.final_content) {
            setResult(data);
          }
          if (data.status === "success") {
            setIsLoading(false);
            clearInterval(pollingRef.current);
          } else if (data.status === "error") {
            setError(data.message || "An unknown error occurred.");
            setIsLoading(false);
            clearInterval(pollingRef.current);
          }
          return fetch(`${API_BASE_URL}/status`);
        })
        .then(res => res.ok ? res.json() : Promise.reject(res))
        .then(statusData => setStatus(statusData))
        .catch(() => {
          setError("Failed to get results from the server.");
          setIsLoading(false);
          clearInterval(pollingRef.current);
        });
    }, 2000);
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!url) return;

    setResult(null);
    setError(null);
    setIsLoading(true);
    setStatus({ main: "Initializing...", sub: "" });
    clearInterval(pollingRef.current);

    fetch(`${API_BASE_URL}/api/summarize-url`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url, title, language }),
    })
      .then(res => res.ok ? pollStatus() : Promise.reject(res))
      .catch(() => {
        setError("Failed to start analysis. Check server connection.");
        setIsLoading(false);
      });
  };

  return (
    <div>
      <header className="page-header">
        <h2>Analyze a Single YouTube URL</h2>
        <p>Provide a direct link to a YouTube video for in-depth analysis.</p>
      </header>
      <div className="glass-card">
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label className="form-label">YouTube URL*</label>
            <input
              type="text"
              className="form-control"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="https://www.youtube.com/watch?v=..."
              required
            />
          </div>
          <div className="form-group">
            <label className="form-label">Custom Title (Optional)</label>
            <input
              type="text"
              className="form-control"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Enter a title (if blank, it will be fetched automatically)"
            />
          </div>
          <div className="form-group">
            <label className="form-label">Video Language</label>
            <select
              className="form-select"
              value={language}
              onChange={(e) => setLanguage(e.target.value)}
            >
              <option value="en">English (en)</option>
              <option value="zh">Chinese (zh)</option>
            </select>
          </div>
          <button type="submit" className="btn btn-primary w-100" disabled={isLoading}>
            <FiZap /> {isLoading ? 'Analyzing...' : 'Start Analysis'}
          </button>
        </form>
      </div>

      <ResultsDisplay 
        isLoading={isLoading}
        status={status}
        error={error}
        result={result}
      />
    </div>
  );
};

export default SoloUrlPage;
