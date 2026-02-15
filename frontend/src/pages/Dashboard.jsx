import React, { useState, useRef } from 'react';
import axios from 'axios';
import { FileText, BookOpen, Brain, CheckCircle2, ChevronRight, Loader2, History as HistoryIcon } from 'lucide-react';
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';
import QuizSection from '../components/QuizSection';
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
    const quizRef = useRef(null);
    const navigate = useNavigate();

    const handleAnalyze = async () => {
        if (!text) return;
        setLoading(true);
        setResult(null);
        setShowQuiz(false);
        setError('');
        try {
            const response = await axios.post(`${API_BASE_URL}/analyze`, { text });
            setResult(response.data);

            // Save to history
            const history = JSON.parse(localStorage.getItem('synod_history') || '[]');
            const newEntry = {
                id: Date.now(),
                date: new Date().toISOString(),
                title: text.slice(0, 50) + (text.length > 50 ? '...' : ''),
                ...response.data
            };
            localStorage.setItem('synod_history', JSON.stringify([newEntry, ...history].slice(0, 50)));

        } catch (err) {
            console.error(err);
            setError('Failed to analyze text. Please ensure the backend is running.');
        } finally {
            setLoading(false);
        }
    };

    const startQuiz = () => {
        setShowQuiz(true);
        setTimeout(() => {
            quizRef.current?.scrollIntoView({ behavior: 'smooth' });
        }, 100);
    };

    return (
        <div className="min-h-screen bg-slate-950 text-slate-200 font-sans selection:bg-blue-500/30">
            <header className="border-b border-slate-800 bg-slate-950/50 backdrop-blur-md sticky top-0 z-50">
                <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
                    <div className="flex items-center gap-3 cursor-pointer" onClick={() => navigate('/')}>
                        <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center shadow-[0_0_15px_rgba(37,99,235,0.4)]">
                            <Brain className="w-5 h-5 text-white" />
                        </div>
                        <h1 className="text-xl font-bold tracking-tighter text-white">SYNOD</h1>
                    </div>
                    <div className="flex items-center gap-4">
                        <button
                            onClick={() => navigate('/history')}
                            className="p-2 text-slate-400 hover:text-white transition-colors"
                            title="History"
                        >
                            <HistoryIcon className="w-5 h-5" />
                        </button>
                        <div className="w-8 h-8 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center text-xs font-bold">
                            JD
                        </div>
                    </div>
                </div>
            </header>

            <main className="max-w-5xl mx-auto px-6 py-12">
                <div className="text-center mb-12 animate-in fade-in slide-in-from-bottom-4 duration-700">
                    <h2 className="text-4xl font-extrabold mb-4 tracking-tight text-white">
                        Transform Lectures into <span className="text-blue-500">Knowledge</span>
                    </h2>
                    <p className="text-slate-400 text-lg max-w-2xl mx-auto">
                        Paste your notes below to get instant summaries and test your knowledge.
                    </p>
                </div>

                <div className="bg-slate-900/50 border border-slate-800 rounded-3xl p-8 mb-12 shadow-2xl backdrop-blur-sm">
                    <div className="flex items-center gap-2 mb-4">
                        <div className="p-2 bg-blue-500/10 rounded-lg text-blue-500">
                            <FileText className="w-5 h-5" />
                        </div>
                        <h3 className="font-bold text-white uppercase tracking-wider text-sm">Lecture Content</h3>
                    </div>
                    <textarea
                        value={text}
                        onChange={(e) => setText(e.target.value)}
                        placeholder="Paste your lecture notes or text here..."
                        className="w-full h-64 bg-slate-950 border border-slate-800 rounded-2xl p-6 text-slate-300 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 transition-all resize-none text-lg leading-relaxed"
                    />
                    <div className="mt-6 flex justify-between items-center">
                        <p className="text-xs text-slate-500 font-medium uppercase tracking-widest">{text.length} characters</p>
                        <button
                            onClick={handleAnalyze}
                            disabled={loading || !text}
                            className={cn(
                                "px-8 py-3 bg-blue-600 hover:bg-blue-500 text-white font-bold rounded-2xl transition-all shadow-lg shadow-blue-600/20 flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed group",
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
                    {error && <p className="mt-4 text-red-400 text-sm text-center font-medium">{error}</p>}
                </div>

                {result && (
                    <div className="space-y-12 animate-in fade-in slide-in-from-bottom-8 duration-700 pb-20">
                        <div className="bg-slate-900/50 border border-slate-800 rounded-3xl p-10 shadow-xl overflow-hidden relative">
                            <div className="absolute top-0 right-0 p-10 opacity-5 pointer-events-none">
                                <FileText className="w-40 h-40" />
                            </div>
                            <div className="flex items-center gap-2 mb-8">
                                <div className="p-2 bg-emerald-500/10 rounded-lg text-emerald-500">
                                    <CheckCircle2 className="w-5 h-5" />
                                </div>
                                <h3 className="text-2xl font-black text-white tracking-tight">Lecture Summary</h3>
                            </div>
                            <p className="text-slate-300 leading-relaxed text-xl font-medium">
                                {result.summary}
                            </p>
                        </div>

                        <div className="grid md:grid-cols-2 gap-8">
                            <div className="bg-slate-900/50 border border-slate-800 rounded-3xl p-10">
                                <div className="flex items-center gap-2 mb-6">
                                    <div className="p-2 bg-purple-500/10 rounded-lg text-purple-500">
                                        <BookOpen className="w-5 h-5" />
                                    </div>
                                    <h3 className="text-xl font-bold text-white tracking-tight">Key Concepts</h3>
                                </div>
                                <div className="flex flex-wrap gap-3">
                                    {result.concepts.map((concept, i) => (
                                        <span key={i} className="px-4 py-2 bg-slate-800 border border-slate-700 rounded-xl text-sm font-semibold text-slate-300 hover:border-purple-500/50 hover:text-white transition-all cursor-default">
                                            {concept}
                                        </span>
                                    ))}
                                </div>
                            </div>

                            <div className="bg-gradient-to-br from-blue-600/20 to-purple-600/20 border border-blue-500/20 rounded-3xl p-10 flex flex-col justify-center items-center text-center relative overflow-hidden group">
                                <div className="absolute -top-10 -right-10 w-40 h-40 bg-blue-500/10 blur-[80px] group-hover:bg-blue-500/20 transition-all" />
                                <Brain className="w-16 h-16 text-blue-500 mb-6 group-hover:scale-110 transition-transform duration-500" />
                                <h3 className="text-2xl font-black text-white mb-2">Quiz is Ready!</h3>
                                <p className="text-slate-400 font-medium mb-8">We've crafted {result.quiz.mcqs.length + result.quiz.fill_in_the_blanks.length} questions to challenge your memory.</p>
                                <button
                                    onClick={startQuiz}
                                    className="w-full px-8 py-4 bg-white text-slate-950 font-black rounded-2xl hover:bg-slate-200 transition-all shadow-xl"
                                >
                                    Take the Quiz
                                </button>
                            </div>
                        </div>

                        {showQuiz && (
                            <div ref={quizRef} className="pt-12 scroll-mt-24">
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
