import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App.tsx';
import './index.css';
import { OrganizationProvider } from './context/OrganizationContext.tsx';
import { AuthProvider } from './context/AuthContext.tsx';
import { BrowserRouter } from 'react-router-dom';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <AuthProvider>
      <OrganizationProvider>
        <BrowserRouter>
          <App />
        </BrowserRouter>
      </OrganizationProvider>
    </AuthProvider>
  </React.StrictMode>,
);
