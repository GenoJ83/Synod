import React, { useState, useRef } from 'react';
import axios from 'axios';
import { FileText, BookOpen, Brain, CheckCircle2, ChevronRight, Loader2, History as HistoryIcon, Upload } from 'lucide-react';
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

            // Save to history
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

        // Save to history
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
        <div className="min-h-screen bg-slate-950 text-slate-200 font-sans selection:bg-blue-500/30">
            <header className="border-b border-white/5 bg-slate-950/50 backdrop-blur-xl sticky top-0 z-50">
                <div className="max-w-7xl mx-auto px-6 h-20 flex items-center justify-between">
                    <div className="flex items-center gap-3 cursor-pointer group" onClick={() => navigate('/')}>
                        <div className="w-10 h-10 bg-blue-600 rounded-xl flex items-center justify-center shadow-[0_0_20px_rgba(37,99,235,0.4)] group-hover:rotate-12 transition-transform">
                            <Brain className="w-6 h-6 text-white" />
                        </div>
                        <h1 className="text-2xl font-black tracking-tighter text-white">SYNOD</h1>
                    </div>
                    <div className="flex items-center gap-6">
                        <button
                            onClick={() => navigate('/history')}
                            className="flex items-center gap-2 px-4 py-2 text-slate-400 hover:text-white hover:bg-white/5 rounded-xl transition-all font-bold text-sm tracking-tight"
                        >
                            <HistoryIcon className="w-5 h-5" />
                            History
                        </button>
                        <div className="w-10 h-10 rounded-2xl bg-gradient-to-br from-blue-600 to-purple-600 p-[1px]">
                            <div className="w-full h-full rounded-2xl bg-slate-950 flex items-center justify-center text-xs font-black uppercase tracking-widest border border-white/10">
                                G
                            </div>
                        </div>
                    </div>
                </div>
            </header>

            <main className="max-w-5xl mx-auto px-6 py-16">
                <div className="text-center mb-16 animate-in fade-in slide-in-from-bottom-4 duration-1000">
                    <h2 className="text-5xl font-black mb-6 tracking-tight text-white leading-[1.1]">
                        Unlock the power of <br /><span className="text-blue-500">Your Course Materials.</span>
                    </h2>
                    <p className="text-slate-400 text-xl max-w-2xl mx-auto leading-relaxed">
                        Choose your preferred input method and let Synod handle the rest.
                    </p>
                </div>

                {/* Input Method Tabs */}
                <div className="flex justify-center mb-10">
                    <div className="bg-slate-900/50 p-1.5 rounded-2xl border border-slate-800 flex gap-1">
                        <button
                            onClick={() => setActiveTab('text')}
                            className={cn(
                                "flex items-center gap-2 px-6 py-3 rounded-xl font-bold transition-all",
                                activeTab === 'text' ? "bg-blue-600 text-white shadow-lg shadow-blue-600/20" : "text-slate-500 hover:text-slate-300"
                            )}
                        >
                            <FileText className="w-5 h-5" />
                            Text Input
                        </button>
                        <button
                            onClick={() => setActiveTab('file')}
                            className={cn(
                                "flex items-center gap-2 px-6 py-3 rounded-xl font-bold transition-all",
                                activeTab === 'file' ? "bg-blue-600 text-white shadow-lg shadow-blue-600/20" : "text-slate-500 hover:text-slate-300"
                            )}
                        >
                            <Upload className="w-5 h-5" />
                            File Upload
                        </button>
                    </div>
                </div>

                <div className="bg-slate-900/40 border border-slate-800 rounded-[2.5rem] p-4 md:p-8 mb-16 shadow-2xl backdrop-blur-sm relative overflow-hidden">
                    <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-transparent via-blue-500/50 to-transparent opacity-30" />

                    {activeTab === 'text' ? (
                        <div className="space-y-6 animate-in fade-in slide-in-from-right-4 duration-500">
                            <div className="flex items-center gap-2 px-2">
                                <div className="p-2 bg-blue-500/10 rounded-lg text-blue-500">
                                    <FileText className="w-5 h-5" />
                                </div>
                                <h3 className="font-black text-white uppercase tracking-widest text-xs">Analyze Notes</h3>
                            </div>
                            <textarea
                                value={text}
                                onChange={(e) => setText(e.target.value)}
                                placeholder="Paste your lecture notes, snippets, or articles here..."
                                className="w-full h-80 bg-slate-950/60 border border-slate-800/50 rounded-3xl p-8 text-slate-300 focus:outline-none focus:ring-2 focus:ring-blue-500/30 focus:border-blue-500/50 transition-all resize-none text-lg leading-relaxed shadow-inner"
                            />
                            <div className="flex justify-between items-center px-2">
                                <p className="text-xs text-slate-600 font-bold uppercase tracking-widest">{text.length} characters</p>
                                <button
                                    onClick={() => handleAnalyze()}
                                    disabled={loading || !text}
                                    className={cn(
                                        "px-10 py-4 bg-blue-600 hover:bg-blue-500 text-white font-black rounded-2xl transition-all shadow-xl shadow-blue-600/20 flex items-center gap-3 disabled:opacity-50 disabled:cursor-not-allowed group",
                                        loading && "animate-pulse"
                                    )}
                                >
                                    {loading ? (
                                        <>
                                            <Loader2 className="w-5 h-5 animate-spin" />
                                            Analyzing...
                                        </>
                                    ) : (
                                        <>
                                            Analyze Content
                                            <ChevronRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
                                        </>
                                    )}
                                </button>
                            </div>
                        </div>
                    ) : (
                        <div className="animate-in fade-in slide-in-from-left-4 duration-500">
                            <FileUploader onUploadSuccess={handleFileUploadSuccess} />
                        </div>
                    )}

                    {error && (
                        <div className="mt-6 p-4 bg-red-500/10 border border-red-500/20 rounded-2xl text-red-400 text-sm text-center font-bold tracking-tight">
                            {error}
                        </div>
                    )}
                </div>

                {result && (
                    <div className="space-y-16 animate-in fade-in slide-in-from-bottom-8 duration-1000 pb-32">
                        <div className="bg-slate-900/40 border border-slate-800 rounded-[2.5rem] p-12 shadow-2xl relative overflow-hidden group">
                            <div className="absolute top-0 right-0 p-16 opacity-5 pointer-events-none group-hover:scale-110 transition-transform duration-700">
                                <FileText className="w-64 h-64" />
                            </div>
                            <div className="flex items-center gap-3 mb-10">
                                <div className="p-3 bg-emerald-500/10 rounded-xl text-emerald-500">
                                    <CheckCircle2 className="w-6 h-6" />
                                </div>
                                <h3 className="text-3xl font-black text-white tracking-tighter">Instant Summary</h3>
                            </div>
                            <p className="text-slate-300 leading-relaxed text-2xl font-medium tracking-tight">
                                {result.summary}
                            </p>
                        </div>

                        <div className="grid md:grid-cols-2 gap-10">
                            <div className="bg-slate-900/40 border border-slate-800 rounded-[2.5rem] p-12">
                                <div className="flex items-center gap-3 mb-8">
                                    <div className="p-3 bg-purple-500/10 rounded-xl text-purple-500">
                                        <BookOpen className="w-6 h-6" />
                                    </div>
                                    <h3 className="text-2xl font-black text-white tracking-tighter">Key Concepts</h3>
                                </div>
                                <div className="flex flex-wrap gap-3">
                                    {result.concepts.map((concept, i) => (
                                        <span key={i} className="px-5 py-2.5 bg-slate-800/80 border border-slate-700/50 rounded-2xl text-[13px] font-black text-slate-400 hover:border-purple-500/50 hover:text-white hover:bg-slate-800 transition-all cursor-default uppercase tracking-tight">
                                            {concept}
                                        </span>
                                    ))}
                                </div>
                            </div>

                            <div className="bg-gradient-to-br from-blue-600/10 to-purple-600/10 border border-blue-500/20 rounded-[2.5rem] p-12 flex flex-col justify-center items-center text-center relative overflow-hidden group">
                                <div className="absolute top-[-20%] right-[-20%] w-64 h-64 bg-blue-500/10 blur-[100px] group-hover:bg-blue-500/20 transition-all duration-700" />
                                <Brain className="w-20 h-20 text-blue-500 mb-8 group-hover:scale-110 transition-transform duration-700" />
                                <h3 className="text-3xl font-black text-white mb-3 tracking-tighter">Your Quiz is Ready.</h3>
                                <p className="text-slate-400 font-bold mb-10 text-lg">We've generated {result.quiz.mcqs.length + result.quiz.fill_in_the_blanks.length} questions from your materials.</p>
                                <button
                                    onClick={startQuiz}
                                    className="w-full px-10 py-5 bg-white text-slate-950 font-black rounded-2xl hover:bg-slate-200 transition-all shadow-2xl transform active:scale-95"
                                >
                                    Start Assessment
                                </button>
                            </div>
                        </div>

                        {showQuiz && (
                            <div ref={quizRef} className="pt-20 scroll-mt-24">
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
            </main>
        </div>
    );
}

export default Dashboard;
