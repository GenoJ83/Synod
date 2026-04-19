import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { HelmetProvider } from 'react-helmet-async';
import { ThemeProvider } from './context/ThemeContext';
import { AuthProvider } from './context/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';
import LandingPage from './pages/LandingPage';
import Dashboard from './pages/Dashboard';
import History from './pages/History';
import Login from './pages/Login';
import Signup from './pages/Signup';
import ForgotPassword from './pages/ForgotPassword';
import HowItWorks from './pages/HowItWorks';
import Documentation from './pages/Documentation';
import AnalysisResults from './pages/AnalysisResults';

function App() {
  return (
    <HelmetProvider>
      <ThemeProvider>
        <AuthProvider>
          <Router>
          <Routes>
            <Route path="/" element={<LandingPage />} />
            <Route path="/how-it-works" element={<HowItWorks />} />
            <Route path="/documentation" element={<Documentation />} />
            <Route
              path="/dashboard"
              element={
                <ProtectedRoute>
                  <Dashboard />
                </ProtectedRoute>
              }
            />
            <Route
              path="/history"
              element={
                <ProtectedRoute>
                  <History />
                </ProtectedRoute>
              }
            />
            <Route
              path="/analysis"
              element={
                <ProtectedRoute>
                  <AnalysisResults />
                </ProtectedRoute>
              }
            />
            <Route path="/login" element={<Login />} />
            <Route path="/signup" element={<Signup />} />
            <Route path="/forgot-password" element={<ForgotPassword />} />
          </Routes>
          </Router>
        </AuthProvider>
      </ThemeProvider>
    </HelmetProvider>
  );
}

export default App;
