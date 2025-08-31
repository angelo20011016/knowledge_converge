import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import App from './App';
import reportWebVitals from './reportWebVitals';

// Material UI Theme imports
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline'; // For baseline CSS

// Define a light theme with cool tones and modern aesthetics
const lightTheme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#2196f3', // Light Blue
      light: '#64b5f6',
      dark: '#1976d2',
      contrastText: '#fff',
    },
    secondary: {
      main: '#4caf50', // Light Green
      light: '#81c784',
      dark: '#388e3c',
      contrastText: '#fff',
    },
    background: {
      default: '#f5f5f5', // Light Gray background
      paper: '#ffffff', // White for cards/paper
    },
    text: {
      primary: '#212121', // Dark text
      secondary: '#757575', // Muted grey text
    },
    divider: '#e0e0e0',
  },
  typography: {
    fontFamily: '"Roboto", "Helvetica", "Arial", sans-serif', // Standard clean sans-serif
    h4: {
      fontWeight: 600,
      color: '#212121', // Dark text for main title
    },
    h5: {
      fontWeight: 500,
      color: '#212121', // Dark text for section titles
    },
  },
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: '8px', // Medium rounded corners
          textTransform: 'none', // No uppercase
        },
      },
    },
    MuiTextField: {
      styleOverrides: {
        root: {
          '& .MuiOutlinedInput-root': {
            borderRadius: '8px', // Medium rounded corners
            '& fieldset': {
              borderColor: '#bdbdbd', // Light gray border
            },
            '&:hover fieldset': {
              borderColor: '#9e9e9e', // Slightly darker on hover
            },
            '&.Mui-focused fieldset': {
              borderColor: '#2196f3', // Primary color on focus
            },
          },
          '& .MuiInputLabel-root': {
            color: '#757575', // Muted label color
          },
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          borderRadius: '8px', // Medium rounded corners for paper elements
        },
      },
    },
  },
});

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <ThemeProvider theme={lightTheme}>
      <CssBaseline /> {/* Apply baseline CSS */}
      <App />
    </ThemeProvider>
  </React.StrictMode>
);

// If you want to start measuring performance in your app, pass a function
// to log results (for example: reportWebVitals(console.log))
// or send to an analytics endpoint. Learn more: https://bit.ly/CRA-vitals
reportWebVitals();
