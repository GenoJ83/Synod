import { initializeApp } from "firebase/app";
import { getFirestore } from "firebase/firestore";

const firebaseConfig = {
  projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID,
  appId: import.meta.env.VITE_FIREBASE_APP_ID,
};

// Initialize Firebase for Firestore only (no auth config)
const app = initializeApp(firebaseConfig);
export const db = getFirestore(app);

// Proxy auth to backend (no API key leak)
const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const signInWithPopup = (provider) => {
  window.location.href = `${API_BASE}/auth/${provider}/login`;
};

export const signInWithEmailAndPassword = async (email, password) => {
  const response = await fetch(`${API_BASE}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  });
  const data = await response.json();
  if (!response.ok) throw new Error(data.detail || 'Login failed');
  localStorage.setItem('token', data.token);
  return data;
};

export const auth = {
  currentUser: null,
  onAuthStateChanged: (cb) => {
    const token = localStorage.getItem('token');
    cb(token ? { uid: 'proxy-user' } : null);
  },
  signOut: () => localStorage.removeItem('token'),
};
