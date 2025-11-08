import React, { useState, useEffect, useRef } from 'react';
import { FiZap } from 'react-icons/fi';
import ResultsDisplay from '../components/ResultsDisplay';
import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:5001';

const SoloUrlPage = () => {
  const [url, setUrl] = useState('');
  const [language, setLanguage] = useState('en');
  const [templates, setTemplates] = useState([]);
  const [selectedTemplateId, setSelectedTemplateId] = useState('');
  
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);
  const [statusMessage, setStatusMessage] = useState('Idle');
  const [progress, setProgress] = useState(0); // Keep for UI consistency, though not updated in real-time

  const intervalRef = useRef(null);

  // Fetch templates on component mount
  useEffect(() => {
    const fetchTemplates = async () => {
      try {
        const response = await axios.get(`${API_BASE_URL}/api/templates`, { withCredentials: true });
        setTemplates(response.data);
        if (response.data.length > 0) {
          setSelectedTemplateId(response.data[0].id);
        }
      } catch (err) {
        console.error("Error fetching templates:", err);
      }
    };
    fetchTemplates();
  }, []);

  // Cleanup polling on component unmount
  useEffect(() => {
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!url || isLoading) return;

    // Clear any existing polling interval
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
    }

    setIsLoading(true);
    setResult(null);
    setError(null);
    setStatusMessage('Submitting job...');
    setProgress(5); // Set a small initial progress

    try {
      const response = await axios.post(
        `${API_BASE_URL}/api/start-url-summary`,
        { url, language, template_id: selectedTemplateId },
        { withCredentials: true }
      );

      const data = response.data;
      
      if (data.job_id) {
        const jobId = data.job_id;
        setStatusMessage('Job submitted. Periodically checking for result...');

        // Start polling
        intervalRef.current = setInterval(() => {
          axios.get(`${API_BASE_URL}/api/get-job-result/${jobId}`)
            .then(res => {
              const { status, data: resultData, message } = res.data;
              if (status === 'success') {
                setResult(resultData);
                setStatusMessage('Analysis complete!');
                setProgress(100);
                setIsLoading(false);
                clearInterval(intervalRef.current);
              } else if (status === 'error') {
                setError(message || 'An unknown error occurred.');
                setStatusMessage('Job failed.');
                setIsLoading(false);
                clearInterval(intervalRef.current);
              } else {
                setStatusMessage(`Job status: ${status}`);
              }
            })
            .catch(err => {
              console.error("Polling error:", err);
              setError('Failed to get job status.');
              setIsLoading(false);
              clearInterval(intervalRef.current);
            });
        }, 5000); // Poll every 5 seconds

      } else {
        throw new Error('Server did not return a job ID.');
      }

    } catch (err) {
      const errorMessage = err.response?.data?.error || err.message || 'Failed to start analysis.';
      setError(errorMessage);
      setIsLoading(false);
      setStatusMessage('Idle');
    }
  };

  const displayStatus = {
      main: isLoading ? 'Analyzing' : (error ? 'Error' : (result ? 'Completed' : 'Idle')),
      sub: statusMessage,
      progress: progress
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
            <FiZap /> {isLoading ? statusMessage : 'Start Analysis'}
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

export default SoloUrlPage;