import React, { useState, useRef } from 'react';
import axios from 'axios';
import {
    FileText, BookOpen, Brain, CheckCircle2, ChevronRight,
    Loader2, History as HistoryIcon, Upload, Search,
    Settings, User, Bell, ChevronLeft
} from 'lucide-react';
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';
import QuizSection from '../components/QuizSection';
import FileUploader from '../components/FileUploader';
import { useNavigate } from 'react-router-dom';

function cn(...inputs) {
    return twMerge(clsx(inputs));
}

const API_BASE_URL = 'http://localhost:8000';

function Dashboard() {
    const [text, setText] = useState('');
    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState(null);
    const [error, setError] = useState('');
    const [showQuiz, setShowQuiz] = useState(false);
    const [activeTab, setActiveTab] = useState('text'); // 'text' or 'file'
    const [sidebarOpen, setSidebarOpen] = useState(true);

    const quizRef = useRef(null);
    const navigate = useNavigate();

    const handleAnalyze = async (manualText) => {
        const textToAnalyze = manualText || text;
        if (!textToAnalyze) return;

        setLoading(true);
        setResult(null);
        setShowQuiz(false);
        setError('');
        try {
            const response = await axios.post(`${API_BASE_URL}/analyze`, { text: textToAnalyze });
            const data = response.data;
            setResult(data);

            const history = JSON.parse(localStorage.getItem('synod_history') || '[]');
            const newEntry = {
                id: Date.now(),
                date: new Date().toISOString(),
                title: textToAnalyze.slice(0, 50) + (textToAnalyze.length > 50 ? '...' : ''),
                ...data
            };
            localStorage.setItem('synod_history', JSON.stringify([newEntry, ...history].slice(0, 50)));

        } catch (err) {
            console.error(err);
            setError('Failed to analyze content. Please ensure the backend is running.');
        } finally {
            setLoading(false);
        }
    };

    const handleFileUploadSuccess = (data) => {
        setResult(data);
        const history = JSON.parse(localStorage.getItem('synod_history') || '[]');
        const newEntry = {
            id: Date.now(),
            date: new Date().toISOString(),
            title: "File Analysis: " + (data.summary.slice(0, 30) + "..."),
            ...data
        };
        localStorage.setItem('synod_history', JSON.stringify([newEntry, ...history].slice(0, 50)));
    };

    const startQuiz = () => {
        setShowQuiz(true);
        setTimeout(() => {
            quizRef.current?.scrollIntoView({ behavior: 'smooth' });
        }, 100);
    };

    return (
        <div className="flex h-screen bg-zinc-950 text-zinc-100 overflow-hidden font-sans">
            {/* Sidebar */}
            <aside className={cn(
                "bg-zinc-900/50 border-r border-zinc-800 transition-all duration-300 flex flex-col z-50",
                sidebarOpen ? "w-64" : "w-20"
            )}>
                <div className="p-6 flex items-center gap-3">
                    <div className="w-8 h-8 bg-zinc-100 rounded flex items-center justify-center shrink-0">
                        <Brain className="w-5 h-5 text-zinc-900" />
                    </div>
                    {sidebarOpen && <span className="font-bold tracking-tight text-xl">Synod</span>}
                </div>

                <nav className="flex-1 px-4 space-y-2 mt-4">
                    <button
                        onClick={() => navigate('/')}
                        className="w-full flex items-center gap-3 px-3 py-2 text-zinc-400 hover:text-white hover:bg-zinc-800 rounded-lg transition-colors"
                    >
                        <Search className="w-5 h-5" />
                        {sidebarOpen && <span>Explore</span>}
                    </button>
                    <button
                        className="w-full flex items-center gap-3 px-3 py-2 bg-zinc-800 text-white rounded-lg transition-colors"
                    >
                        <FileText className="w-5 h-5" />
                        {sidebarOpen && <span>Analysis</span>}
                    </button>
                    <button
                        onClick={() => navigate('/history')}
                        className="w-full flex items-center gap-3 px-3 py-2 text-zinc-400 hover:text-white hover:bg-zinc-800 rounded-lg transition-colors"
                    >
                        <HistoryIcon className="w-5 h-5" />
                        {sidebarOpen && <span>History</span>}
                    </button>
                </nav>

                <div className="p-4 border-t border-zinc-800 space-y-4">
                    {sidebarOpen && (
                        <div className="px-2 space-y-1">
                            <div className="flex items-center justify-between text-xs font-bold text-zinc-500 uppercase tracking-widest px-1">
                                <span>Account</span>
                                <Settings className="w-3 h-3" />
                            </div>
                            <div className="flex items-center gap-2 p-2 rounded-lg hover:bg-zinc-800 cursor-pointer transition-colors">
                                <div className="w-6 h-6 rounded-full bg-zinc-800 border border-zinc-700 flex items-center justify-center text-[10px] font-bold">JD</div>
                                <span className="text-sm font-medium">John Doe</span>
                            </div>
                        </div>
                    )}
                    <button
                        onClick={() => setSidebarOpen(!sidebarOpen)}
                        className="w-full flex justify-center p-2 text-zinc-500 hover:text-white hover:bg-zinc-800 rounded-lg transition-colors"
                    >
                        {sidebarOpen ? <ChevronLeft className="w-5 h-5" /> : <ChevronRight className="w-5 h-5" />}
                    </button>
                </div>
            </aside>

            {/* Main Content Area */}
            <div className="flex-1 flex flex-col overflow-hidden relative">
                <header className="h-16 border-b border-zinc-900 bg-zinc-950/50 backdrop-blur-md flex items-center justify-between px-8 z-10">
                    <h2 className="text-sm font-bold text-zinc-400 uppercase tracking-widest">Active Workspace</h2>
                    <div className="flex items-center gap-4">
                        <button className="p-2 text-zinc-500 hover:text-white rounded-lg transition-colors">
                            <Bell className="w-5 h-5" />
                        </button>
                        <div className="h-8 w-[1px] bg-zinc-800" />
                        <div className="px-3 py-1 bg-zinc-900 border border-zinc-800 rounded-md text-xs font-bold text-zinc-400">
                            Pro Member
                        </div>
                    </div>
                </header>

                <main className="flex-1 overflow-y-auto bg-zinc-950 scroll-smooth">
                    <div className="max-w-[1400px] mx-auto px-8 py-12">

                        {/* Split View Container */}
                        <div className={cn(
                            "flex flex-col xl:flex-row gap-12 transition-all duration-500",
                            result ? "items-start" : "items-center justify-center min-h-[70vh]"
                        )}>

                            {/* Input Section */}
                            <div className={cn(
                                "transition-all duration-500 w-full",
                                result ? "xl:w-1/2 sticky top-8" : "max-w-4xl"
                            )}>
                                <div className="mb-10 text-left">
                                    <h1 className="text-4xl font-bold tracking-tight mb-4">Lecture Analysis</h1>
                                    <p className="text-zinc-500 text-lg">Input your course materials to extract intelligence.</p>
                                </div>

                                <div className="bg-zinc-900/30 border border-zinc-800 rounded-2xl p-6 shadow-sm">
                                    <div className="flex gap-4 mb-6 border-b border-zinc-800 pb-4">
                                        <button
                                            onClick={() => setActiveTab('text')}
                                            className={cn(
                                                "text-sm font-bold uppercase tracking-widest px-4 py-2 rounded-md transition-all",
                                                activeTab === 'text' ? "bg-zinc-100 text-zinc-950" : "text-zinc-500 hover:text-zinc-300"
                                            )}
                                        >
                                            Raw Text
                                        </button>
                                        <button
                                            onClick={() => setActiveTab('file')}
                                            className={cn(
                                                "text-sm font-bold uppercase tracking-widest px-4 py-2 rounded-md transition-all",
                                                activeTab === 'file' ? "bg-zinc-100 text-zinc-950" : "text-zinc-500 hover:text-zinc-300"
                                            )}
                                        >
                                            Documents
                                        </button>
                                    </div>

                                    {activeTab === 'text' ? (
                                        <div className="space-y-4 animate-fade-in">
                                            <textarea
                                                value={text}
                                                onChange={(e) => setText(e.target.value)}
                                                placeholder="Paste lecture notes here..."
                                                className="w-full h-80 bg-zinc-950 border border-zinc-800 rounded-xl p-6 text-zinc-100 focus:border-zinc-500 transition-all resize-none font-mono text-sm leading-relaxed"
                                            />
                                            <div className="flex justify-between items-center">
                                                <span className="text-[10px] font-bold text-zinc-600 uppercase tracking-widest">{text.length} chars</span>
                                                <button
                                                    onClick={() => handleAnalyze()}
                                                    disabled={loading || !text}
                                                    className="bg-zinc-100 hover:bg-white text-zinc-950 px-6 py-3 rounded-lg font-bold text-sm transition-all flex items-center gap-2 disabled:opacity-50"
                                                >
                                                    {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : "Analyze Content"}
                                                    {!loading && <ChevronRight className="w-4 h-4" />}
                                                </button>
                                            </div>
                                        </div>
                                    ) : (
                                        <div className="animate-fade-in">
                                            <FileUploader onUploadSuccess={handleFileUploadSuccess} />
                                        </div>
                                    )}

                                    {error && <div className="mt-4 p-3 bg-red-950/20 border border-red-900/50 rounded-lg text-red-500 text-xs font-medium">{error}</div>}
                                </div>
                            </div>

                            {/* Results View */}
                            {result && (
                                <div className="w-full xl:w-1/2 space-y-8 animate-fade-in pb-20">
                                    <div className="pro-card p-8">
                                        <div className="flex items-center gap-3 mb-6 text-emerald-500">
                                            <CheckCircle2 className="w-5 h-5" />
                                            <h3 className="text-sm font-bold uppercase tracking-widest">Executive Summary</h3>
                                        </div>
                                        <p className="text-zinc-300 text-lg leading-relaxed font-medium">
                                            {result.summary}
                                        </p>
                                    </div>

                                    <div className="grid sm:grid-cols-2 gap-8">
                                        <div className="pro-card p-6">
                                            <div className="flex items-center gap-3 mb-4 text-zinc-400">
                                                <BookOpen className="w-4 h-4" />
                                                <h3 className="text-xs font-bold uppercase tracking-widest">Foundational Concepts</h3>
                                            </div>
                                            <div className="flex flex-wrap gap-2">
                                                {result.concepts.map((concept, i) => (
                                                    <span key={i} className="px-3 py-1 bg-zinc-800 border border-zinc-700 rounded-md text-[11px] font-bold text-zinc-400 uppercase">
                                                        {concept}
                                                    </span>
                                                ))}
                                            </div>
                                        </div>

                                        <div className="bg-zinc-100 text-zinc-950 rounded-xl p-8 flex flex-col items-center justify-center text-center">
                                            <Brain className="w-10 h-10 mb-4 opacity-80" />
                                            <h3 className="text-xl font-bold mb-2">Knowledge Check</h3>
                                            <p className="text-zinc-600 text-sm mb-6">Generated {result.quiz.mcqs.length + result.quiz.fill_in_the_blanks.length} questions for this session.</p>
                                            <button
                                                onClick={startQuiz}
                                                className="w-full bg-zinc-900 text-white py-3 rounded-lg font-bold hover:bg-black transition-colors"
                                            >
                                                Start Quiz
                                            </button>
                                        </div>
                                    </div>

                                    {showQuiz && (
                                        <div ref={quizRef} className="pt-8">
                                            <QuizSection
                                                quiz={result.quiz}
                                                onReset={() => {
                                                    setResult(null);
                                                    setShowQuiz(false);
                                                    setText('');
                                                }}
                                            />
                                        </div>
                                    )}
                                </div>
                            )}
                        </div>
                    </div>
                </main>
            </div>
        </div>
    );
}

export default Dashboard;
