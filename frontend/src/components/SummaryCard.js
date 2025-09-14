import React from 'react';
import { FiDownload } from 'react-icons/fi';

const SummaryCard = ({ title, url, summary, index }) => {
  const handleDownload = () => {
    // Prepare the content with title and URL
    const fileContent = `Title: ${title}\nURL: ${url}\n\n---\n\n${summary}`;
    const blob = new Blob([fileContent], { type: 'text/plain;charset=utf-8' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    // Replace characters that are invalid in filenames with an underscore, but keep the full title
    const safeFileName = title.replace(/[\\/:*?"<>|]/g, '_');
    link.download = `${safeFileName}.txt`;
    
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(link.href);
  };

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
            <button onClick={handleDownload} className="btn btn-outline-primary btn-sm">
              <FiDownload /> Download
            </button>
          </div>
          <hr />
          <p style={{ whiteSpace: 'pre-wrap' }}>{summary}</p>
        </div>
      </div>
    </div>
  );
};

export default SummaryCard;
