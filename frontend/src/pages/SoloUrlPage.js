import React, { useState, useEffect, useRef } from 'react';
import { FiZap } from 'react-icons/fi';
import ResultsDisplay from '../components/ResultsDisplay';

const SoloUrlPage = () => {
  const [url, setUrl] = useState('');
  const [title, setTitle] = useState('');
  const [language, setLanguage] = useState('en');
  
  // Simplified status management
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);
  const [statusMessage, setStatusMessage] = useState('Idle');

  const pollingRef = useRef(null);

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
        const res = await fetch(`/api/get-job-result/${jobId}`);
        
        if (!res.ok) {
          const errorData = await res.json().catch(() => ({ message: 'Server returned an error.' }));
          throw new Error(errorData.message || `HTTP error! Status: ${res.status}`);
        }

        const data = await res.json();

        setStatusMessage(`Job status: ${data.status}`);

        if (data.status === 'success') {
          clearInterval(pollingRef.current);
          setIsLoading(false);
          setResult(data.data); // The actual result is nested in the 'data' property
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
    if (!url || isLoading) return;

    // Reset state for new submission
    setIsLoading(true);
    setResult(null);
    setError(null);
    setStatusMessage('Starting analysis...');
    if (pollingRef.current) {
      clearInterval(pollingRef.current);
    }

    try {
      const response = await fetch(`/api/start-url-summary`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url, title, language }),
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
      main: isLoading ? 'Analyzing' : (error ? 'Error' : (result ? 'Completed' : 'Idle')),
      sub: statusMessage
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
              disabled={isLoading}
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
              disabled={isLoading}
            />
          </div>
          <div className="form-group">
            <label className="form-label">Video Language</label>
            <select
              className="form-select"
              value={language}
              onChange={(e) => setLanguage(e.target.value)}
              disabled={isLoading}
            >
              <option value="en">English (en)</option>
              <option value="zh">Chinese (zh)</option>
            </select>
          </div>
          <button type="submit" className="btn btn-primary w-100" disabled={isLoading}>
            <FiZap /> {isLoading ? statusMessage : 'Start Analysis'}
          </button>
        </form>
      </div>

      <ResultsDisplay 
        isLoading={isLoading}
        status={displayStatus} // Pass the simplified status object
        error={error}
        result={result}
      />
    </div>
  );
};

export default SoloUrlPage;