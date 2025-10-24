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
    <div className="template-management-page">
      <h2>Manage Your Custom Templates</h2>
      {error && <div className="error-message">{error}</div>}
      {success && <div className="success-message">{success}</div>}

      <form onSubmit={handleCreateUpdateTemplate} className="template-form">
        <input
          type="text"
          placeholder="Template Name"
          value={templateName}
          onChange={(e) => setTemplateName(e.target.value)}
          required
        />
        <textarea
          placeholder="Template Content (e.g., 'Summarize this video in 3 bullet points...')"
          value={templateContent}
          onChange={(e) => setTemplateContent(e.target.value)}
          rows="6"
          required
        ></textarea>
        <button type="submit">
          <FiPlusCircle /> {editingTemplate ? 'Update Template' : 'Create New Template'}
        </button>
        {editingTemplate && (
          <button type="button" onClick={() => { setEditingTemplate(null); setTemplateName(''); setTemplateContent(''); setError(''); setSuccess(''); }}>
            Cancel Edit
          </button>
        )}
      </form>

      <h3>Your Templates</h3>
      {templates.length === 0 ? (
        <p>No templates found. Create one above!</p>
      ) : (
        <ul className="template-list">
          {templates.map((template) => (
            <li key={template.id} className="template-item">
              <div className="template-details">
                <h4>{template.name}</h4>
                <p>{template.content.substring(0, 100)}...</p>
              </div>
              <div className="template-actions">
                <button onClick={() => handleEdit(template)}><FiEdit /> Edit</button>
                <button onClick={() => handleDelete(template.id)}><FiTrash /> Delete</button>
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
};

export default TemplateManagementPage;