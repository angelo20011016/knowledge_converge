import React from 'react';
import SummaryCard from './SummaryCard';

const ResultsDisplay = ({ isLoading, status, error, result }) => {
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

  const renderResults = () => (
    <div className="results-section glass-card mt-4">
      <h2>Analysis Results</h2>
      {result.final_content && (
        <div className="summary-card mb-4">
          <h3>Final Summary</h3>
          <p style={{ whiteSpace: 'pre-wrap' }}>{result.final_content}</p>
        </div>
      )}
      {result.individual_summaries?.length > 0 && (
        <>
          <h3 className="h4 my-3">Individual Video Summaries</h3>
          <div className="accordion" id="summariesAccordion">
            {result.individual_summaries.map((item, index) => (
              <SummaryCard 
                key={index}
                index={index}
                title={item.title}
                url={item.url}
                summary={item.summary}
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
        {result && renderResults()}
      </>
    );
  }

  if (result) {
    return renderResults();
  }

  return null; // Nothing to display if not loading and no result/error
};

export default ResultsDisplay;
