import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { FiEdit, FiTrash, FiPlusCircle } from 'react-icons/fi';
import './TemplateManagementPage.css';

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:5001'; // Use 5001 for direct backend access

const TemplateManagementPage = () => {
  const [templates, setTemplates] = useState([]);
  const [editingTemplate, setEditingTemplate] = useState(null);
  const [templateName, setTemplateName] = useState('');
  const [templateContent, setTemplateContent] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  useEffect(() => {
    fetchTemplates();
  }, []);

  const fetchTemplates = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/templates`);
      setTemplates(response.data);
    } catch (err) {
      setError('Failed to fetch templates: ' + (err.response?.data?.error || err.message));
    }
  };

  const handleCreateUpdateTemplate = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');

    if (!templateName || !templateContent) {
      setError('Template name and content cannot be empty.');
      return;
    }

    try {
      if (editingTemplate) {
        // Update existing template
        await axios.put(`${API_BASE_URL}/api/templates/${editingTemplate.id}`, 
          { name: templateName, content: templateContent }
        );
        setSuccess('Template updated successfully!');
      } else {
        // Create new template
        await axios.post(`${API_BASE_URL}/api/templates`, 
          { name: templateName, content: templateContent }
        );
        setSuccess('Template created successfully!');
      }
      setTemplateName('');
      setTemplateContent('');
      setEditingTemplate(null);
      fetchTemplates(); // Refresh the list
    } catch (err) {
      setError('Failed to save template: ' + (err.response?.data?.error || err.message));
    }
  };

  const handleEdit = (template) => {
    setEditingTemplate(template);
    setTemplateName(template.name);
    setTemplateContent(template.content);
    setError('');
    setSuccess('');
  };

  const handleDelete = async (templateId) => {
    if (window.confirm('Are you sure you want to delete this template?')) {
      try {
        await axios.delete(`${API_BASE_URL}/api/templates/${templateId}`);
        setSuccess('Template deleted successfully!');
        fetchTemplates(); // Refresh the list
      } catch (err) {
        setError('Failed to delete template: ' + (err.response?.data?.error || err.message));
      }
    }
  };

  return (
    <div className="container mt-4">
      <header className="page-header">
        <h2>Manage Your Custom Templates</h2>
        <p>Create, edit, and delete templates for AI analysis prompts.</p>
      </header>

      {error && <div className="alert alert-danger">{error}</div>}
      {success && <div className="alert alert-success">{success}</div>}

      <div className="glass-card mb-4 p-4">
        <h3>{editingTemplate ? 'Edit Template' : 'Create New Template'}</h3>
        <form onSubmit={handleCreateUpdateTemplate}>
          <div className="mb-3">
            <label htmlFor="templateName" className="form-label">Template Name</label>
            <input
              type="text"
              className="form-control"
              id="templateName"
              placeholder="e.g., 'Summarize in 3 bullet points'"
              value={templateName}
              onChange={(e) => setTemplateName(e.target.value)}
              required
            />
          </div>
          <div className="mb-3">
            <label htmlFor="templateContent" className="form-label">Template Content</label>
            <textarea
              className="form-control"
              id="templateContent"
              placeholder="e.g., 'Summarize this video in 3 bullet points, focusing on key takeaways and action items.'"
              value={templateContent}
              onChange={(e) => setTemplateContent(e.target.value)}
              rows="6"
              required
            ></textarea>
          </div>
          <div className="d-flex justify-content-end">
            {editingTemplate && (
              <button 
                type="button" 
                className="btn btn-secondary me-2" 
                onClick={() => { setEditingTemplate(null); setTemplateName(''); setTemplateContent(''); setError(''); setSuccess(''); }}
              >
                Cancel Edit
              </button>
            )}
            <button type="submit" className="btn btn-primary">
              <FiPlusCircle className="me-2" /> {editingTemplate ? 'Update Template' : 'Create Template'}
            </button>
          </div>
        </form>
      </div>

      <h3 className="mb-3">Your Saved Templates</h3>
      {templates.length === 0 ? (
        <div className="glass-card p-4 text-center">
          <p className="mb-0">No templates found. Create one above!</p>
        </div>
      ) : (
        <div className="row">
          {templates.map((template) => (
            <div key={template.id} className="col-md-6 col-lg-4 mb-4">
              <div className="glass-card h-100 p-3 d-flex flex-column">
                <h5 className="mb-2">{template.name}</h5>
                <p className="text-muted small flex-grow-1">{template.content.substring(0, 150)}{template.content.length > 150 ? '...' : ''}</p>
                <div className="d-flex justify-content-end mt-3">
                  <button 
                    className="btn btn-sm btn-outline-primary me-2" 
                    onClick={() => handleEdit(template)}
                  >
                    <FiEdit /> Edit
                  </button>
                  <button 
                    className="btn btn-sm btn-outline-danger" 
                    onClick={() => handleDelete(template.id)}
                  >
                    <FiTrash /> Delete
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default TemplateManagementPage;