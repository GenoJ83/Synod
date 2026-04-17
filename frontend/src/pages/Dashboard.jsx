import React, { useState, useRef, useEffect } from 'react';
import { motion } from 'framer-motion';
import axios from 'axios';
import {
    FileText, BookOpen, Brain, CheckCircle2, ChevronRight,
    Loader2, History as HistoryIcon, Upload, Search,
    Settings, User, Bell, ChevronLeft, Sun, Moon, LogOut
} from 'lucide-react';
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';
import { useNavigate, useLocation } from 'react-router-dom';
import { useTheme } from '../context/ThemeContext';
import { useAuth } from '../context/AuthContext';
import { cn } from '../utils/cn';

import AnalysisInput from '../components/dashboard/AnalysisInput';

import { API_BASE_URL } from '../config';
import { db } from '../firebase';
import { collection, addDoc } from 'firebase/firestore';

function Dashboard() {
    const [text, setText] = useState('');
    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState(null);
    const [error, setError] = useState('');
    const [showQuiz, setShowQuiz] = useState(false);
    const [activeTab, setActiveTab] = useState('text'); // 'text' or 'file'
    const [sidebarOpen, setSidebarOpen] = useState(true);
    const [selectedConcept, setSelectedConcept] = useState(null);
    const [viewedConcepts, setViewedConcepts] = useState([]);

    const quizRef = useRef(null);
    const navigate = useNavigate();
    const location = useLocation();
    const { theme, toggleTheme } = useTheme();
    const { user, token, logout } = useAuth();



    const handleAnalyze = async (manualText) => {
        const textToAnalyze = manualText || text;
        if (!textToAnalyze) return;

        setLoading(true);
        setResult(null);
        setShowQuiz(false);
        setError('');
        try {
            const response = await axios.post(
                `${API_BASE_URL}/analyze`, 
                { text: textToAnalyze },
                { headers: { Authorization: `Bearer ${token}` } }
            );
            const data = response.data;
            setResult(data);

            const newEntry = {
                date: new Date().toISOString(),
                userId: user?.uid || user?.email || 'anonymous',
                title: textToAnalyze.slice(0, 50) + (textToAnalyze.length > 50 ? '...' : ''),
                ...data
            };
            try {
                const docRef = await addDoc(collection(db, "history"), newEntry);
                newEntry.id = docRef.id;
            } catch (fbErr) {
                console.error("Firebase err:", fbErr);
                newEntry.id = Date.now().toString();
            }
            navigate('/analysis', { state: { result: newEntry } });

        } catch (err) {
            console.error(err);
            if (err.response?.status === 429) {
                setError(err.response.data.detail || 'Daily rate limit reached (5 analyses per day).');
            } else {
                setError('Failed to analyze content. Please ensure the backend is running and you are logged in.');
            }
        } finally {
            setLoading(false);
        }
    };

    const handleFileUploadSuccess = async (data) => {
        setResult(data);
        const newEntry = {
            date: new Date().toISOString(),
            userId: user?.uid || user?.email || 'anonymous',
            title: "File Analysis: " + ((data?.summary || "Uploaded file").slice(0, 30) + "..."),
            ...data
        };
        try {
            const docRef = await addDoc(collection(db, "history"), newEntry);
            newEntry.id = docRef.id;
        } catch (fbErr) {
            console.error("Firebase err:", fbErr);
            newEntry.id = Date.now().toString();
        }
        navigate('/analysis', { state: { result: newEntry } });
    };

    const startQuiz = () => {
        setShowQuiz(true);
        setTimeout(() => {
            quizRef.current?.scrollIntoView({ behavior: 'smooth' });
        }, 100);
    };

    return (
        <div className="flex h-screen bg-app-bg text-app-fg overflow-hidden font-sans transition-colors duration-300">
            {/* Sidebar */}
            <aside className={cn(
                "bg-app-bg border-r border-app-border transition-all duration-300 flex flex-col z-50",
                sidebarOpen ? "w-64" : "w-20"
            )}>
                <div className="p-6 flex items-center gap-3">
                    <div className="w-8 h-8 bg-app-fg rounded flex items-center justify-center shrink-0">
                        <Brain className="w-5 h-5 text-app-bg" />
                    </div>
                    {sidebarOpen && <span className="font-bold tracking-tight text-xl">Synod</span>}
                </div>

                <nav className="flex-1 px-4 space-y-2 mt-4">
                    <button
                        onClick={() => navigate('/')}
                        className="w-full flex items-center gap-3 px-3 py-2 text-app-muted hover:text-app-fg hover:bg-app-card rounded-lg transition-colors"
                    >
                        <Search className="w-5 h-5" />
                        {sidebarOpen && <span>Explore</span>}
                    </button>
                    <button
                        className="w-full flex items-center gap-3 px-3 py-2 bg-app-card text-app-fg rounded-lg transition-colors"
                    >
                        <FileText className="w-5 h-5" />
                        {sidebarOpen && <span>Analysis</span>}
                    </button>
                    <button
                        onClick={() => navigate('/history')}
                        className="w-full flex items-center gap-3 px-3 py-2 text-app-muted hover:text-app-fg hover:bg-app-card rounded-lg transition-colors"
                    >
                        <HistoryIcon className="w-5 h-5" />
                        {sidebarOpen && <span>History</span>}
                    </button>
                </nav>

                <div className="p-4 border-t border-app-border space-y-4">
                    {sidebarOpen && (
                        <div className="px-2 space-y-1">
                            <div className="flex items-center justify-between text-xs font-bold text-app-muted uppercase tracking-widest px-1">
                                <span>Account</span>
                                <Settings className="w-3 h-3" />
                            </div>
                            <div className="flex items-center justify-between p-2 rounded-lg hover:bg-app-card group cursor-pointer transition-colors">
                                <div className="flex items-center gap-2">
                                    <div className="w-6 h-6 rounded-full bg-app-card border border-app-border flex items-center justify-center text-[10px] font-bold">
                                        {user?.name?.split(' ').map(n => n[0]).join('') || 'JD'}
                                    </div>
                                    <span className="text-sm font-medium">{user?.name || 'John Doe'}</span>
                                </div>
                                <button
                                    onClick={logout}
                                    className="p-1 px-2 text-[10px] font-bold uppercase tracking-widest text-app-muted hover:text-red-500 hover:bg-red-500/10 rounded transition-all flex items-center gap-1 shrink-0"
                                    title="Logout"
                                >
                                    <LogOut className="w-3 h-3" />
                                    <span>Logout</span>
                                </button>
                            </div>
                        </div>
                    )}
                    <button
                        onClick={() => setSidebarOpen(!sidebarOpen)}
                        className="w-full flex justify-center p-2 text-app-muted hover:text-app-fg hover:bg-app-card rounded-lg transition-colors"
                    >
                        {sidebarOpen ? <ChevronLeft className="w-5 h-5" /> : <ChevronRight className="w-5 h-5" />}
                    </button>
                </div>
            </aside>

            {/* Main Content Area */}
            <div className="flex-1 flex flex-col overflow-hidden relative">
                <header className="h-16 border-b border-app-border bg-app-bg/50 backdrop-blur-md flex items-center justify-between px-8 z-10">
                    <h2 className="text-sm font-bold text-app-muted uppercase tracking-widest">{user?.name || user?.email || 'User'}'s Active Workspace</h2>
                    <div className="flex items-center gap-4">
                        <button
                            onClick={toggleTheme}
                            className="p-2 text-app-muted hover:text-app-fg rounded-lg transition-colors bg-app-card border border-app-border"
                            title={theme === 'dark' ? 'Switch to Light Mode' : 'Switch to Dark Mode'}
                        >
                            {theme === 'dark' ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
                        </button>
                        <button className="p-2 text-app-muted hover:text-app-fg rounded-lg transition-colors">
                            <Bell className="w-5 h-5" />
                        </button>
                        <div className="h-8 w-[1px] bg-app-border" />
                        <div className="px-3 py-1 bg-app-card border border-app-border rounded-md text-xs font-bold text-app-muted">
                            Pro Member
                        </div>
                    </div>
                </header>

                <main className="flex-1 overflow-y-auto bg-app-bg scroll-smooth">
                    <div className="max-w-[1400px] mx-auto px-8 py-12">

                        {/* Split View Container */}
                        <div className="flex flex-col items-center justify-center min-h-[70vh] gap-12 transition-all duration-500">

                            {/* Input Section */}
                            <div className="transition-all duration-500 w-full max-w-4xl">
                                <div className="mb-10 text-left">
                                    <h1 className="text-4xl font-bold tracking-tight mb-4">Welcome back, {user?.name?.split(' ')[0] || user?.email?.split('@')[0] || 'Scholar'}.</h1>
                                    <p className="text-zinc-500 text-lg">Input your course materials below to extract intelligence for this session.</p>
                                </div>

                                <AnalysisInput
                                    activeTab={activeTab}
                                    setActiveTab={setActiveTab}
                                    text={text}
                                    setText={setText}
                                    handleAnalyze={handleAnalyze}
                                    handleFileUploadSuccess={handleFileUploadSuccess}
                                    loading={loading}
                                    error={error}
                                    setError={setError}
                                />
                            </div>

                        </div>
                    </div>
                </main>
            </div>
        </div>
    );
}

export default Dashboard;
