import React, { useState, useEffect } from 'react';
import api from '../api/api';
import { Modal, Box, Typography, TextField, Button, Card, CardContent, CardActions, Grid, IconButton } from '@mui/material';
import { FiEdit, FiTrash, FiPlusCircle } from 'react-icons/fi';

const style = {
  position: 'absolute',
  top: '50%',
  left: '50%',
  transform: 'translate(-50%, -50%)',
  width: '90%',
  maxWidth: '800px',
  bgcolor: 'background.paper',
  border: '2px solid #000',
  boxShadow: 24,
  p: 4,
  borderRadius: '8px',
  maxHeight: '90vh',
  overflowY: 'auto'
};

const TemplateManagerModal = ({ open, onClose }) => {
  const [templates, setTemplates] = useState([]);
  const [editingTemplate, setEditingTemplate] = useState(null);
  const [templateName, setTemplateName] = useState('');
  const [templateContent, setTemplateContent] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  useEffect(() => {
    if (open) {
      fetchTemplates();
    }
  }, [open]);

  const fetchTemplates = async () => {
    try {
      const response = await api.get('/api/templates');
      setTemplates(response.data);
    } catch (err) {
      setError('Failed to fetch templates: ' + (err.response?.data?.message || err.message));
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
      const method = editingTemplate ? 'put' : 'post';
      const url = editingTemplate ? `/api/templates/${editingTemplate.id}` : '/api/templates';
      await api[method](url, { name: templateName, content: templateContent });
      
      setSuccess(editingTemplate ? 'Template updated successfully!' : 'Template created successfully!');
      resetForm();
      fetchTemplates();
    } catch (err) {
      setError('Failed to save template: ' + (err.response?.data?.message || err.message));
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
        await api.delete(`/api/templates/${templateId}`);
        setSuccess('Template deleted successfully!');
        fetchTemplates();
      } catch (err) {
        setError('Failed to delete template: ' + (err.response?.data?.message || err.message));
      }
    }
  };

  const resetForm = () => {
    setEditingTemplate(null);
    setTemplateName('');
    setTemplateContent('');
    setError('');
    setSuccess('');
  }

  return (
    <Modal
      open={open}
      onClose={onClose}
      aria-labelledby="template-manager-modal-title"
    >
      <Box sx={style}>
        <Typography id="template-manager-modal-title" variant="h5" component="h2" gutterBottom>
          Manage Templates
        </Typography>

        {error && <Typography color="error">{error}</Typography>}
        {success && <Typography color="primary">{success}</Typography>}

        <Box component="form" onSubmit={handleCreateUpdateTemplate} sx={{ my: 2 }}>
          <Typography variant="h6">{editingTemplate ? 'Edit Template' : 'Create New Template'}</Typography>
          <TextField
            label="Template Name"
            fullWidth
            margin="normal"
            value={templateName}
            onChange={(e) => setTemplateName(e.target.value)}
            required
          />
          <TextField
            label="Template Content"
            fullWidth
            multiline
            rows={4}
            margin="normal"
            value={templateContent}
            onChange={(e) => setTemplateContent(e.target.value)}
            required
          />
          <Box sx={{ display: 'flex', justifyContent: 'flex-end', mt: 2 }}>
            {editingTemplate && (
              <Button onClick={resetForm} sx={{ mr: 1 }}>
                Cancel Edit
              </Button>
            )}
            <Button type="submit" variant="contained" startIcon={<FiPlusCircle />}>
              {editingTemplate ? 'Update Template' : 'Create Template'}
            </Button>
          </Box>
        </Box>

        <Typography variant="h6" sx={{ mt: 4, mb: 2 }}>Your Saved Templates</Typography>
        {templates.length === 0 ? (
          <Typography>No templates found. Create one above!</Typography>
        ) : (
          <Grid container spacing={2}>
            {templates.map((template) => (
              <Grid item xs={12} sm={6} key={template.id}>
                <Card variant="outlined" sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
                  <CardContent sx={{ flexGrow: 1 }}>
                    <Typography variant="h6">{template.name}</Typography>
                    <Typography variant="body2" color="text.secondary">
                      {template.content.substring(0, 100)}{template.content.length > 100 ? '...' : ''}
                    </Typography>
                  </CardContent>
                  <CardActions sx={{ justifyContent: 'flex-end' }}>
                    <IconButton size="small" onClick={() => handleEdit(template)}><FiEdit /></IconButton>
                    <IconButton size="small" onClick={() => handleDelete(template.id)}><FiTrash /></IconButton>
                  </CardActions>
                </Card>
              </Grid>
            ))}
          </Grid>
        )}
      </Box>
    </Modal>
  );
};

export default TemplateManagerModal;
