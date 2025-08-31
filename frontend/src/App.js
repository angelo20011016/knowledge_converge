import React, { useState, useEffect, useCallback } from 'react';
import { Container, Typography, Box, CircularProgress, Alert, TextField, Button, Paper, Tabs, Tab, FormControl, InputLabel, Select, MenuItem, Grid, Card, CardContent, CardActions, Link } from '@mui/material';
import './App.css';

// Bubble Component for Individual Summaries
function SummaryBubble({ title, summary, url }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <Grid item xs={12} sm={6} md={4}>
      <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }} elevation={3}>
        <CardContent sx={{ flexGrow: 1 }}>
          <Typography variant="subtitle1" component="h3" sx={{ fontWeight: 'bold' }}>
            <Link href={url} target="_blank" rel="noopener noreferrer" underline="hover" color="inherit">
              {title}
            </Link>
          </Typography>
          <Typography variant="body2" sx={{ mt: 1, whiteSpace: 'pre-wrap', wordBreak: 'break-word', maxHeight: expanded ? 'none' : '100px', overflow: 'hidden' }}>
            {summary}
          </Typography>
        </CardContent>
        <CardActions>
          <Button size="small" onClick={() => setExpanded(!expanded)}>{expanded ? 'Collapse' : 'Expand'}</Button>
        </CardActions>
      </Card>
    </Grid>
  );
}

function App() {
  // Input states
  const [queryInput, setQueryInput] = useState('');
  const [urlInput, setUrlInput] = useState('');
  const [urlLanguage, setUrlLanguage] = useState('zh');

  // App mode state
  const [tabValue, setTabValue] = useState(0);

  // Data and status states
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);
  const [analysisInProgress, setAnalysisInProgress] = useState(false);
  const [mainStatus, setMainStatus] = useState('Idle');
  const [subStatus, setSubStatus] = useState('');

  // --- Core Logic: Asynchronous Analysis Flow ---

  const startAnalysis = useCallback(async (endpoint, body) => {
    setData(null);
    setError(null);
    setLoading(true);
    setAnalysisInProgress(true);

    try {
      const response = await fetch(`http://127.0.0.1:5000${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });
      if (response.status !== 202) {
        const errorData = await response.json();
        throw new Error(errorData.error || `Failed to start analysis. Status: ${response.status}`);
      }
      console.log("Analysis started successfully.");
    } catch (e) {
      setError(e.message);
      setLoading(false);
      setAnalysisInProgress(false);
    }
  }, []);

  useEffect(() => {
    if (!analysisInProgress) {
      return; // Do nothing if no analysis is running
    }

    const poll = async () => {
      // Fetch status text
      try {
        const statusResponse = await fetch('http://127.0.0.1:5000/status');
        if (statusResponse.ok) {
          const statusData = await statusResponse.json();
          setMainStatus(statusData.main);
          setSubStatus(statusData.sub);

          if (statusData.main === "Completed" || statusData.main === "Error" || statusData.main === "Finished") {
            setAnalysisInProgress(false); // Stop polling
            setLoading(false);
          }
        }
      } catch (e) {
        console.error("Status poll failed:", e);
        setError("Failed to get status from server.");
        setAnalysisInProgress(false);
        setLoading(false);
      }

      // Fetch partial or full results
      try {
        const resultResponse = await fetch('http://127.0.0.1:5000/api/get-result');
        if (resultResponse.ok) {
          const resultData = await resultResponse.json();
          if(resultData.status !== 'idle' && resultData.status !== 'running') {
             setData(resultData);
          }
        }
      } catch (e) {
        console.error("Result fetch failed:", e);
        // Don't set a fatal error here, as it might be a temporary network issue
      }
    };

    const intervalId = setInterval(poll, 2000); // Poll every 2 seconds

    return () => clearInterval(intervalId); // Cleanup on unmount or when analysis stops
  }, [analysisInProgress]);

  // --- UI Handlers ---

  const handleTopicSubmit = () => {
    if (!queryInput.trim()) return;
    startAnalysis('/analyze', { query: queryInput });
  };

  const handleUrlSubmit = () => {
    if (!urlInput.trim()) return;
    startAnalysis('/api/summarize-url', { url: urlInput, language: urlLanguage });
  };

  const handleTabChange = (event, newValue) => {
    setTabValue(newValue);
    setQueryInput('');
    setUrlInput('');
    setData(null);
    setError(null);
    setLoading(false);
    setAnalysisInProgress(false);
    setMainStatus('Idle');
    setSubStatus('');
  };

  return (
    <Container maxWidth="lg" sx={{ mt: 6, p: 5, bgcolor: 'background.default', borderRadius: '12px', boxShadow: '0px 4px 20px rgba(0, 0, 0, 0.1)' }}>
      <Typography variant="h4" component="h1" gutterBottom sx={{ textAlign: 'center', mb: 4, color: 'primary.dark' }}>
        Video Knowledge Convergence
      </Typography>

      <Paper elevation={3} sx={{ my: 4, p: 3, border: '1px solid', borderColor: 'primary.light', borderRadius: '8px', bgcolor: 'background.paper' }}>
        <Typography variant="h6" component="h2" sx={{ color: 'primary.main', mb: 1 }}>
          Status: <span style={{ fontWeight: 'bold' }}>{mainStatus}</span>
        </Typography>
        {subStatus && <Typography variant="body2" color="text.secondary">Details: {subStatus}</Typography>}
      </Paper>

      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 4 }}>
        <Tabs value={tabValue} onChange={handleTabChange} centered>
          <Tab label="Analyze by Topic" disabled={loading} />
          <Tab label="Summarize by URL" disabled={loading} />
        </Tabs>
      </Box>

      {tabValue === 0 ? (
        <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
          <TextField label="Enter your topic of interest" variant="outlined" fullWidth value={queryInput} onChange={(e) => setQueryInput(e.target.value)} onKeyPress={(e) => e.key === 'Enter' && handleTopicSubmit()} disabled={loading} />
          <Button variant="contained" onClick={handleTopicSubmit} disabled={!queryInput.trim() || loading} sx={{ height: '56px', px: 4 }}>Analyze</Button>
        </Box>
      ) : (
        <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
          <TextField label="Enter a single YouTube URL" variant="outlined" fullWidth value={urlInput} onChange={(e) => setUrlInput(e.target.value)} onKeyPress={(e) => e.key === 'Enter' && handleUrlSubmit()} disabled={loading} />
          <FormControl sx={{ minWidth: 120 }} disabled={loading}>
            <InputLabel id="language-select-label">Language</InputLabel>
            <Select labelId="language-select-label" value={urlLanguage} label="Language" onChange={(e) => setUrlLanguage(e.target.value)}>
              <MenuItem value={'zh'}>Chinese</MenuItem>
              <MenuItem value={'en'}>English</MenuItem>
            </Select>
          </FormControl>
          <Button variant="contained" onClick={handleUrlSubmit} disabled={!urlInput.trim() || loading} sx={{ height: '56px', px: 4 }}>Summarize</Button>
        </Box>
      )}

      {loading && (
        <Box sx={{ display: 'flex', justifyContent: 'center', mt: 6 }}>
          <CircularProgress color="primary" />
          <Typography variant="body1" sx={{ ml: 2, color: 'text.primary' }}>Analyzing... Please wait.</Typography>
        </Box>
      )}
      {error && <Alert severity="error" sx={{ mt: 6 }}>Error: {error}</Alert>}

      {data && (
        <Box sx={{ mt: 6 }}>
          {data.individual_summaries && data.individual_summaries.length > 0 && (
            <Box sx={{ mb: 5 }}>
              <Typography variant="h5" component="h2" gutterBottom sx={{ color: 'primary.main', mb: 3 }}>Individual Video Summaries</Typography>
              <Grid container spacing={3}>
                {data.individual_summaries.map((item, index) => (
                  <SummaryBubble key={index} title={item.title} summary={item.summary} url={item.url} />
                ))}
              </Grid>
            </Box>
          )}

          {data.status === 'success' && data.final_content && (
            <Box>
              <Typography variant="h5" component="h2" gutterBottom sx={{ color: 'primary.main', mb: 3 }}>Final Analysis</Typography>
              <Paper elevation={3} sx={{ p: 3, border: '1px solid', borderColor: 'secondary.light', borderRadius: '8px', bgcolor: 'background.paper' }}>
                <Typography variant="body1" sx={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>{data.final_content}</Typography>
              </Paper>
            </Box>
          )}

          {data.status === 'error' && <Alert severity="warning" sx={{ mt: 2 }}>{data.message || 'An error occurred during analysis.'}</Alert>}
        </Box>
      )}
    </Container>
  );
}

export default App;