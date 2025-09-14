import React, { useState, useEffect, useRef } from 'react';
import { FiSearch } from 'react-icons/fi';
import ResultsDisplay from '../components/ResultsDisplay';

const TopicSearchPage = () => {
  const [query, setQuery] = useState('');
  const [searchMode, setSearchMode] = useState('divergent');
  const [searchLanguage, setSearchLanguage] = useState('zh-TW');

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
    if (!query) return;

    setResult(null);
    setError(null);
    setIsLoading(true);
    setStatus({ main: "Initializing...", sub: "" });
    clearInterval(pollingRef.current);

    fetch(`${API_BASE_URL}/analyze`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ 
        query, 
        process_audio: true,
        search_mode: searchMode,
        search_language: searchLanguage
      }),
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
        <h2>Synthesize Knowledge on a Topic</h2>
        <p>Explore any topic to gather and summarize insights from multiple videos.</p>
      </header>
      <div className="glass-card">
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label className="form-label">Topic/Question*</label>
            <input
              type="text"
              className="form-control"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="e.g., 'Quantum Computing Explained'"
              required
            />
          </div>
          
          <div className="form-group">
            <label className="form-label">Search Mode</label>
            <div className="form-check">
              <input className="form-check-input" type="radio" name="searchMode" id="divergent" value="divergent" checked={searchMode === 'divergent'} onChange={(e) => setSearchMode(e.target.value)} />
              <label className="form-check-label" htmlFor="divergent">
                Divergent (5 Chinese + 5 English results)
              </label>
            </div>
            <div className="form-check">
              <input className="form-check-input" type="radio" name="searchMode" id="focused" value="focused" checked={searchMode === 'focused'} onChange={(e) => setSearchMode(e.target.value)} />
              <label className="form-check-label" htmlFor="focused">
                Focused (10 results in one language)
              </label>
            </div>
          </div>

          {searchMode === 'focused' && (
            <div className="form-group">
              <label htmlFor="languageSelect" className="form-label">Language for Focused Search</label>
              <select
                id="languageSelect"
                className="form-select"
                value={searchLanguage}
                onChange={(e) => setSearchLanguage(e.target.value)}
              >
                <option value="zh-TW">Chinese - Traditional (zh-TW)</option>
                <option value="en">English (en)</option>
                <option value="ja">Japanese (ja)</option>
                <option value="ko">Korean (ko)</option>
              </select>
            </div>
          )}

          <button type="submit" className="btn btn-primary w-100" disabled={isLoading}>
            <FiSearch /> {isLoading ? 'Synthesizing...' : 'Search and Synthesize'}
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

export default TopicSearchPage;
