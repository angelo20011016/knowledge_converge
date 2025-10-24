import React from 'react';
import SummaryCard from './SummaryCard';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { FiDownload } from 'react-icons/fi'; // Import download icon

const ResultsDisplay = ({ isLoading, status, error, result }) => {

  const handleDownload = (content, filename) => {
    const blob = new Blob([content], { type: 'text/plain;charset=utf-8' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  if (error) {
    return (
      <div className="glass-card text-center mt-4">
        <h4>An Error Occurred</h4>
        <p>{error}</p>
        <button className="btn btn-primary" onClick={() => window.location.reload()}>Try Again</button>
      </div>
    );
  }

  const renderStatus = () => (
    <div className="status-section glass-card mt-4">
      <div className="spinner-border" role="status" />
      <h3>{status.main}</h3>
      <p>{status.sub}</p>
    </div>
  );

  const renderSingleUrlResult = () => (
    <div className="results-section glass-card mt-4">
      <h2>Analysis Results</h2>
      {result.summary && (
        <div className="summary-card mb-4">
          <div className="d-flex justify-content-end align-items-center mb-2">
            {result.full_transcript && (
                <button className="btn btn-sm btn-outline-secondary me-2" onClick={() => handleDownload(result.full_transcript, `${result.title || 'transcript'}_transcript.txt`)}>
                  <FiDownload /> Download Transcript
                </button>
            )}
            <button className="btn btn-sm btn-outline-primary" onClick={() => handleDownload(result.summary, `${result.title || 'summary'}.txt`)}>
              <FiDownload /> Download Summary
            </button>
          </div>
          <h3>Video Summary</h3>
          <div className="markdown-content">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>{result.summary}</ReactMarkdown>
          </div>
        </div>
      )}
    </div>
  );

  const renderTopicSearchResult = () => (
    <div className="results-section glass-card mt-4">
      <h2>Analysis Results</h2>
      {result.final_content && (
        <div className="summary-card mb-4">
          <div className="d-flex justify-content-between align-items-center mb-2">
            <h3>Final Combined Summary</h3>
            <button className="btn btn-sm btn-outline-primary" onClick={() => handleDownload(result.final_content, `topic_summary.txt`)}>
              <FiDownload /> Download Combined Summary
            </button>
          </div>
          <div className="markdown-content">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>{result.final_content}</ReactMarkdown>
          </div>
        </div>
      )}
      {result.individual_summaries?.length > 0 && (
        <>
          <h3 className="h4 my-3">Individual Video Summaries & Transcripts</h3>
          <div className="accordion" id="summariesAccordion">
            {result.individual_summaries.map((item, index) => (
              <SummaryCard 
                key={index}
                index={index}
                title={item.title}
                url={item.url}
                summary={item.summary}
                fullTranscript={item.full_transcript} // Pass full transcript
                handleDownload={handleDownload} // Pass download function
              />
            ))}
          </div>
        </>
      )}
    </div>
  );

  if (isLoading) {
    return (
      <>
        {renderStatus()}
        {result && (result.individual_summaries ? renderTopicSearchResult() : renderSingleUrlResult())}
      </>
    );
  }

  if (result) {
    return result.individual_summaries ? renderTopicSearchResult() : renderSingleUrlResult();
  }

  return null; // Nothing to display if not loading and no result/error
};

export default ResultsDisplay;
