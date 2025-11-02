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
  const [progress, setProgress] = useState(0); // Add state for progress percentage

  const eventSourceRef = useRef(null);

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

  // Cleanup EventSource on component unmount
  useEffect(() => {
    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }
    };
  }, []);

  const listenToJobProgress = (jobId) => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
    }

    const url = `${API_BASE_URL}/stream?channel=${jobId}`;
    eventSourceRef.current = new EventSource(url);

    eventSourceRef.current.addEventListener('progress', (event) => {
      const data = JSON.parse(event.data);
      setProgress(data.percentage || 0);
      setStatusMessage(data.message || '');
    });

    eventSourceRef.current.addEventListener('final', (event) => {
      const data = JSON.parse(event.data);
      setIsLoading(false);
      if (data.status === 'success') {
        // Fetch the final result from the standard API endpoint
        axios.get(`${API_BASE_URL}/api/get-job-result/${jobId}`, { withCredentials: true })
          .then(res => {
            setResult(res.data.data);
            setError(null);
            setStatusMessage('Completed');
            setProgress(100);
          })
          .catch(err => {
            setError(err.message || 'Failed to fetch final result.');
            setResult(null);
          });
      } else {
        setError(data.message || 'An unknown error occurred during analysis.');
        setResult(null);
        setStatusMessage('Error');
      }
      eventSourceRef.current.close();
    });

    eventSourceRef.current.onerror = (err) => {
      console.error("EventSource failed:", err);
      setError('Connection to server lost. Please try again.');
      setIsLoading(false);
      eventSourceRef.current.close();
    };
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!url || isLoading) return;

    // Reset state for new submission
    setIsLoading(true);
    setResult(null);
    setError(null);
    setStatusMessage('Submitting job...');
    setProgress(0);
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
    }

    try {
      const response = await axios.post(
        `${API_BASE_URL}/api/start-url-summary`,
        { url, language, template_id: selectedTemplateId },
        { withCredentials: true }
      );

      const data = response.data;
      
      if (data.job_id) {
        setStatusMessage('Job submitted, waiting for progress updates...');
        listenToJobProgress(data.job_id);
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
      sub: statusMessage,
      progress: progress // Pass progress percentage
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
