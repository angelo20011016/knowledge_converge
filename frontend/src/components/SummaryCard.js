import React from 'react';
import { FiDownload } from 'react-icons/fi';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

const SummaryCard = ({ title, url, summary, fullTranscript, index, handleDownload }) => {
  const collapseId = `collapse-${index}`;

  return (
    <div className="accordion-item">
      <h2 className="accordion-header">
        <button className="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target={`#${collapseId}`}>
          {title}
        </button>
      </h2>
      <div id={collapseId} className="accordion-collapse collapse" data-bs-parent="#summariesAccordion">
        <div className="accordion-body">
          <div className="d-flex justify-content-between align-items-center mb-3">
            <p className="mb-0"><strong>Source:</strong> <a href={url} target="_blank" rel="noopener noreferrer" title={url}>{url.length > 50 ? `${url.slice(0, 50)}...` : url}</a></p>
            <div>
              {fullTranscript && (
                <button onClick={() => handleDownload(fullTranscript, `${title || 'transcript'}_transcript.txt`)} className="btn btn-outline-secondary btn-sm me-2">
                  <FiDownload /> Download Transcript
                </button>
              )}
              {summary && (
                <button onClick={() => handleDownload(summary, `${title || 'summary'}.txt`)} className="btn btn-outline-primary btn-sm">
                  <FiDownload /> Download Summary
                </button>
              )}
            </div>
          </div>
          <hr />
          {summary && (
            <>
              <h4>Summary</h4>
              <div className="markdown-content mb-3">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>{summary}</ReactMarkdown>
              </div>
            </>
          )}
          
        </div>
      </div>
    </div>
  );
};

export default SummaryCard;
