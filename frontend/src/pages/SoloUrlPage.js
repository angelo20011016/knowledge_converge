import React, { useState, useEffect, useRef } from 'react';
import { FiZap } from 'react-icons/fi';
import ResultsDisplay from '../components/ResultsDisplay';
import axios from 'axios'; // Import axios

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:5001';

const SoloUrlPage = () => {
  const [url, setUrl] = useState('');
  const [language, setLanguage] = useState('en');
  const [templates, setTemplates] = useState([]); // State for templates
  const [selectedTemplateId, setSelectedTemplateId] = useState(''); // State for selected template
  
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
        const response = await axios.get(`${API_BASE_URL}/api/templates`, { withCredentials: true });
        setTemplates(response.data);
        if (response.data.length > 0) {
          setSelectedTemplateId(response.data[0].id); // Select the first template by default
        }
      } catch (err) {
        console.error("Error fetching templates:", err);
        // Optionally set an error state for the user
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
        const res = await axios.get(`${API_BASE_URL}/api/get-job-result/${jobId}`, { withCredentials: true });
        const data = res.data;

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
      const response = await axios.post(
        `${API_BASE_URL}/api/start-url-summary`,
        { url, language, template_id: selectedTemplateId },
        { withCredentials: true }
      );

      const data = response.data;
      
      if (data.job_id) {
        setStatusMessage('Analysis started, waiting for results...');
        pollJobResult(data.job_id);
      } else {
        throw new Error('Server did not return a job ID.');
      }

    } catch (err) {
      // Axios wraps the response error in err.response.data
      const errorMessage = err.response?.data?.error || err.message || 'Failed to start analysis. Check server connection.';
      setError(errorMessage);
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
