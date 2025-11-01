import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import api from '../api/api';
import ResultsDisplay from '../components/ResultsDisplay';
import './SoloUrlPage.css';

// MUI Components
import { Box, Typography, TextField, Button, Select, MenuItem, FormControl, InputLabel, CircularProgress } from '@mui/material';

const SoloUrlPage = () => {
  const { isAuthenticated } = useAuth();
  const [url, setUrl] = useState('');
  const [language, setLanguage] = useState('en');
  const [templates, setTemplates] = useState([]);
  const [selectedTemplateId, setSelectedTemplateId] = useState('');
  
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);
  const [statusMessage, setStatusMessage] = useState('Idle');

  useEffect(() => {
    const fetchTemplates = async () => {
      // Since auth is removed from backend, we can fetch templates regardless
      try {
        const response = await api.get('/api/templates');
        setTemplates(response.data);
      } catch (err) {
        console.error("Error fetching templates:", err);
        // Do not show auth-related errors since we removed it
        // setError("Failed to fetch templates. Please try again."); 
      }
    };
    fetchTemplates();
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!url || isLoading) return;

    setIsLoading(true);
    setResult(null);
    setError(null);
    setStatusMessage('Analysis in progress...');

    try {
      // The backend is now synchronous and returns the full result directly
      const response = await api.post('/api/start-url-summary', {
        url,
        language,
        template_id: selectedTemplateId,
      });
      
      // Check if the response contains the successful result
      if (response.data && response.data.status === 'success') {
        // The simplified backend returns the result nested under a 'result' key
        setResult(response.data.result);
        setError(null);
      } else {
        // Handle cases where the backend returns a structured error
        throw new Error(response.data.error || response.data.message || 'Analysis failed.');
      }

    } catch (err) {
      const errorMsg = err.response?.data?.error || err.response?.data?.message || err.message || 'Failed to start analysis.';
      setError(errorMsg);
      setResult(null);
    } finally {
      setIsLoading(false);
      setStatusMessage('Idle');
    }
  };

  const displayStatus = {
      main: isLoading ? 'Analyzing' : (error ? 'Error' : (result ? 'Completed' : 'Idle')),
      sub: statusMessage
  };

  return (
    <div className="solo-url-page-container">
      <div className="control-panel">
        <Box component="form" onSubmit={handleSubmit} className="control-card">
          <Typography variant="h5" component="h2" gutterBottom>
            Analyze YouTube URL
          </Typography>
          <TextField
            label="YouTube URL"
            fullWidth
            variant="outlined"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="https://www.youtube.com/watch?v=..."
            required
            disabled={isLoading}
            margin="normal"
          />
          <FormControl fullWidth margin="normal" disabled={isLoading}>
            <InputLabel>Language</InputLabel>
            <Select
              value={language}
              label="Language"
              onChange={(e) => setLanguage(e.target.value)}
            >
              <MenuItem value="en">English (en)</MenuItem>
              <MenuItem value="zh">Chinese (zh)</MenuItem>
            </Select>
          </FormControl>

          {/* Always show template selector now that auth is removed */}
          <FormControl fullWidth margin="normal" disabled={isLoading}>
            <InputLabel>Template (Optional)</InputLabel>
            <Select
              value={selectedTemplateId}
              label="Template (Optional)"
              onChange={(e) => setSelectedTemplateId(e.target.value)}
            >
              <MenuItem value=""><em>-- No Template --</em></MenuItem>
              {templates.map((template) => (
                <MenuItem key={template.id} value={template.id}>
                  {template.name}
                </MenuItem>
              ))}
            </Select>
          </FormControl>

          <Button 
            type="submit" 
            variant="contained" 
            size="large" 
            fullWidth 
            disabled={isLoading}
            sx={{ mt: 2, py: 1.5 }}
          >
            {isLoading ? <CircularProgress size={24} color="inherit" /> : 'Start Analysis'}
          </Button>
        </Box>
      </div>
      <div className="results-panel">
        <Box className="results-card">
          <ResultsDisplay 
            isLoading={isLoading}
            status={displayStatus}
            error={error}
            result={result}
          />
        </Box>
      </div>
    </div>
  );
};

export default SoloUrlPage;