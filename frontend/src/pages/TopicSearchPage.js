import React, { useState, useEffect, useRef } from 'react';
import { FiSearch } from 'react-icons/fi';
import ResultsDisplay from '../components/ResultsDisplay';
import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:5001';

const TopicSearchPage = () => {
  const [query, setQuery] = useState('');
  const [searchMode, setSearchMode] = useState('divergent');
  const [searchLanguage, setSearchLanguage] = useState('zh');
  const [templates, setTemplates] = useState([]);
  const [selectedTemplateId, setSelectedTemplateId] = useState('');

  // Simplified status management
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);
  const [statusMessage, setStatusMessage] = useState('Idle');

  const pollingRef = useRef(null);

  // Fetch templates on component mount
  useEffect(() => {
    const fetchTemplates = async () => {
      try {
        const response = await axios.get(`${API_BASE_URL}/api/templates`);
        setTemplates(response.data);
        if (response.data.length > 0) {
          // Set a default, but allow "No Template"
          setSelectedTemplateId(''); 
        }
      } catch (err) {
        console.error("Error fetching templates:", err);
      }
    };
    fetchTemplates();
  }, []);

  // Cleanup interval on component unmount
  useEffect(() => {
    return () => {
      if (pollingRef.current) {
        clearInterval(pollingRef.current);
      }
    };
  }, []);

  const pollJobResult = (jobId) => {
    if (pollingRef.current) {
      clearInterval(pollingRef.current);
    }

    pollingRef.current = setInterval(async () => {
      try {
        const res = await fetch(`${API_BASE_URL}/api/get-job-result/${jobId}`);
        
        if (!res.ok) {
          const errorData = await res.json().catch(() => ({ message: 'Server returned an error.' }));
          throw new Error(errorData.message || `HTTP error! Status: ${res.status}`);
        }

        const data = await res.json();

        setStatusMessage(`Job status: ${data.status}`);

        if (data.status === 'success') {
          clearInterval(pollingRef.current);
          setIsLoading(false);
          setResult(data.data);
          setError(null);
        } else if (data.status === 'error') {
          clearInterval(pollingRef.current);
          setIsLoading(false);
          setError(data.message || 'An unknown error occurred during analysis.');
          setResult(null);
        } else if (data.status === 'not_found') {
          clearInterval(pollingRef.current);
          setIsLoading(false);
          setError(`Job ID ${jobId} not found. The job may have expired or never existed.`);
          setResult(null);
        }

      } catch (err) {
        clearInterval(pollingRef.current);
        setIsLoading(false);
        setError(err.message || 'Failed to poll for job results. Check network connection.');
        setResult(null);
      }
    }, 3000); // Poll every 3 seconds
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!query || isLoading) return;

    setIsLoading(true);
    setResult(null);
    setError(null);
    setStatusMessage('Starting analysis...');
    if (pollingRef.current) {
      clearInterval(pollingRef.current);
    }

    try {
      const response = await fetch(`${API_BASE_URL}/api/start-topic-search`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          query, 
          process_audio: true,
          search_mode: searchMode,
          search_language: searchLanguage,
          template_id: selectedTemplateId
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ message: 'Failed to start analysis.' }));
        throw new Error(errorData.message || 'Server returned an error on job start.');
      }

      const data = await response.json();
      
      if (data.job_id) {
        setStatusMessage('Analysis started, waiting for results...');
        pollJobResult(data.job_id);
      } else {
        throw new Error('Server did not return a job ID.');
      }

    } catch (err) {
      setError(err.message || 'Failed to start analysis. Check server connection.');
      setIsLoading(false);
      setStatusMessage('Idle');
    }
  };

  const displayStatus = {
    main: isLoading ? 'Synthesizing' : (error ? 'Error' : (result ? 'Completed' : 'Idle')),
    sub: statusMessage
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
              disabled={isLoading}
            />
          </div>
          
          <div className="form-group">
            <label className="form-label">Search Mode</label>
            <div className="form-check">
              <input className="form-check-input" type="radio" name="searchMode" id="divergent" value="divergent" checked={searchMode === 'divergent'} onChange={(e) => setSearchMode(e.target.value)} disabled={isLoading} />
              <label className="form-check-label" htmlFor="divergent">
                Divergent (5 Chinese + 5 English results)
              </label>
            </div>
            <div className="form-check">
              <input className="form-check-input" type="radio" name="searchMode" id="focused" value="focused" checked={searchMode === 'focused'} onChange={(e) => setSearchMode(e.target.value)} disabled={isLoading} />
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
                disabled={isLoading}
              >
                <option value="zh">Chinese (zh)</option>
                <option value="en">English (en)</option>
                <option value="ja">Japanese (ja)</option>
                <option value="ko">Korean (ko)</option>
              </select>
            </div>
          )}

          {/* Template Selection Dropdown */}
          {templates.length > 0 && (
            <div className="form-group">
              <label className="form-label">Select Template (Optional)</label>
              <select
                className="form-select"
                value={selectedTemplateId}
                onChange={(e) => setSelectedTemplateId(e.target.value)}
                disabled={isLoading}
              >
                <option value="">-- No Template --</option>
                {templates.map((template) => (
                  <option key={template.id} value={template.id}>
                    {template.name}
                  </option>
                ))}
              </select>
            </div>
          )}

          <button type="submit" className="btn btn-primary w-100" disabled={isLoading}>
            <FiSearch /> {isLoading ? statusMessage : 'Search and Synthesize'}
          </button>
        </form>
      </div>

      <ResultsDisplay 
        isLoading={isLoading}
        status={displayStatus}
        error={error}
        result={result}
      />
    </div>
  );
};

export default TopicSearchPage;
