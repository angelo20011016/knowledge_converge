import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Accordion, Button } from 'react-bootstrap';
import ReactMarkdown from 'react-markdown';

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:5001';

const HistoryPage = () => {
  const [history, setHistory] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchHistory = async () => {
      setIsLoading(true);
      try {
        const response = await axios.get(`${API_BASE_URL}/api/history`, { withCredentials: true });
        setHistory(response.data);
        setError(null);
      } catch (err) {
        setError(err.response?.data?.error || "Failed to fetch history. You might need to log in.");
        setHistory([]);
      } finally {
        setIsLoading(false);
      }
    };

    fetchHistory();
  }, []);

  const downloadTextFile = (content, filename) => {
    const blob = new Blob([content], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  if (isLoading) {
    return <div className="status-section"><h3>Loading history...</h3></div>;
  }

  if (error) {
    return <div className="status-section" style={{ color: 'red' }}><h3>{error}</h3></div>;
  }

  return (
    <div>
      <header className="page-header">
        <h2>Analysis History</h2>
        <p>Review and download your past analysis results.</p>
      </header>

      {history.length === 0 ? (
        <div className="glass-card">
          <p>No history found. Analyze a video to get started!</p>
        </div>
      ) : (
        <Accordion>
          {history.map((item, index) => (
            <Accordion.Item eventKey={String(index)} key={item.job_id}>
              <Accordion.Header>
                <div className="w-100 d-flex justify-content-between align-items-center">
                  <span className="flex-grow-1 text-truncate pe-3">
                    {item.video_title || 'Untitled Analysis'}
                  </span>
                  <div className="d-flex align-items-center">
                    {item.status === 'success' && (
                      <div onClick={(e) => e.stopPropagation()} className="me-3">
                        <Button variant="outline-primary" size="sm" onClick={() => downloadTextFile(item.summary, `${item.video_title || 'Untitled'}_summary.txt`)} title="Download Summary">
                          Summary
                        </Button>
                        <Button variant="outline-secondary" size="sm" className="ms-2" onClick={() => downloadTextFile(item.full_transcript, `${item.video_title || 'Untitled'}_transcript.txt`)} title="Download Transcript">
                          Transcript
                        </Button>
                      </div>
                    )}
                    <small className="text-muted text-nowrap">
                    {new Date(item.created_at).toLocaleString()}
                  </small>
                  </div>
                </div>
              </Accordion.Header>
              <Accordion.Body>
                {item.status === 'success' ? (
                  <div>
                    <h5>Summary</h5>
                    <div className="markdown-content summary-card">
                      <ReactMarkdown>{item.summary || 'No summary available.'}</ReactMarkdown>
                    </div>
                  </div>
                ) : (
                  <p>Status: <strong>{item.status}</strong></p>
                )}
              </Accordion.Body>
            </Accordion.Item>
          ))}
        </Accordion>
      )}
    </div>
  );
};

export default HistoryPage;
