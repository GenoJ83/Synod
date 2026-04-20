import React, { useState, useRef, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { ArrowLeft, Search, Sun, Moon, LogOut, Trophy } from 'lucide-react';
import { useTheme } from '../context/ThemeContext';
import { useAuth } from '../context/AuthContext';
import ResultsDisplay from '../components/dashboard/ResultsDisplay';
import ConceptExplorer from '../components/dashboard/ConceptExplorer';
import NotesChatPanel from '../components/dashboard/NotesChatPanel';
import QuizSection from '../components/QuizSection';
import { db } from '../firebase';
import { doc, updateDoc } from 'firebase/firestore';
import { db } from '../firebase';
import { doc, updateDoc } from 'firebase/firestore';

function AnalysisResults() {
    const location = useLocation();
    const navigate = useNavigate();
    const { theme, toggleTheme } = useTheme();
    const { user, logout } = useAuth();

    // Extract result from navigation state
    const result = location.state?.result;

    const [showQuiz, setShowQuiz] = useState(false);
    const [selectedConcept, setSelectedConcept] = useState(null);
    const [viewedConcepts, setViewedConcepts] = useState([]);
    const quizRef = useRef(null);

    useEffect(() => {
        console.log("AnalysisResults mounted. Received state:", location.state);
        console.log("Extracted result:", result);
    }, [location.state, result]);

    // Redirect to dashboard if no result is found in state
    useEffect(() => {
        if (!result) {
            navigate('/dashboard', { replace: true });
        }
    }, [result, navigate]);

    const startQuiz = () => {
        setShowQuiz(true);
        setQuizCompleted(false);
        setQuizScoreData(null);
        setTimeout(() => {
            quizRef.current?.scrollIntoView({ behavior: 'smooth' });
        }, 100);
    };

    const handleQuizComplete = async (quizResult) => {
        // Save quiz score to Firestore history entry if we have an entry ID
        if (result?.id && user) {
            try {
                const historyRef = doc(db, "history", result.id);
                await updateDoc(historyRef, {
                    quizScore: quizResult.percentage,
                    quizDetails: {
                        score: quizResult.score,
                        total: quizResult.total,
                        answers: quizResult.answers,
                        completedAt: new Date().toISOString()
                    }
                });
                console.log("Quiz score saved to history");
            } catch (err) {
                console.error("Failed to save quiz score:", err);
            }
        }
    };

    if (!result) return null; // Prevent rendering during redirect

    return (
        <div className="flex h-screen bg-app-bg text-app-fg overflow-hidden font-sans transition-colors duration-300">
            <div className="flex-1 flex flex-col overflow-hidden relative">
                {/* Header */}
                <header className="h-16 border-b border-app-border bg-app-bg/80 backdrop-blur-md sticky top-0 z-50 shrink-0">
                    <div className="max-w-[1600px] mx-auto px-8 h-full flex items-center justify-between">
                        <div className="flex items-center gap-6">
                            <button
                                onClick={() => navigate('/dashboard')}
                                className="p-2 -ml-2 text-app-muted hover:text-app-fg hover:bg-app-card rounded-lg transition-colors flex items-center gap-2"
                            >
                                <ArrowLeft className="w-5 h-5" />
                                <span className="text-sm font-bold uppercase tracking-widest hidden sm:block">Back to Dashboard</span>
                            </button>
                        </div>
                        <div className="flex items-center gap-4">
                            <button
                                onClick={toggleTheme}
                                className="p-2 text-app-muted hover:text-app-fg rounded-lg transition-colors border border-app-border bg-app-card"
                                title={theme === 'dark' ? 'Switch to Light Mode' : 'Switch to Dark Mode'}
                            >
                                {theme === 'dark' ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
                            </button>
                            <div className="h-8 w-[1px] bg-app-border" />
                            <div className="flex items-center gap-2 px-2 py-1 bg-app-card border border-app-border rounded-lg group">
                                <div className="w-6 h-6 rounded-full bg-app-fg text-app-bg flex items-center justify-center text-[10px] font-bold">
                                    {user?.name?.split(' ').map(n => n[0]).join('') || 'JD'}
                                </div>
                                <button
                                    onClick={logout}
                                    className="text-[10px] font-bold uppercase tracking-widest text-app-muted hover:text-red-500 transition-colors flex items-center gap-1"
                                >
                                    <LogOut className="w-3 h-3" />
                                    Logout
                                </button>
                            </div>
                        </div>
                    </div>
                </header>

                {/* Main Content Area */}
                <main className="flex-1 overflow-y-auto bg-app-bg scroll-smooth">
                    <div className="max-w-[1400px] mx-auto px-8 py-12">
                        <div className="mb-10 text-center">
                            <h1 className="text-4xl font-bold tracking-tight mb-4">Analysis Results</h1>
                            <p className="text-zinc-500 text-lg">Review your generated summary, explore concepts, and test your knowledge.</p>
                        </div>

                        <div className="flex flex-col items-center">
                            <ResultsDisplay
                                result={result}
                                startQuiz={startQuiz}
                            >
                                <div className="w-full xl:w-2/3 max-w-4xl mx-auto mt-8 space-y-8">
                                    <ConceptExplorer
                                        result={result}
                                        selectedConcept={selectedConcept}
                                        setSelectedConcept={setSelectedConcept}
                                        viewedConcepts={viewedConcepts}
                                        setViewedConcepts={setViewedConcepts}
                                        setShowQuiz={setShowQuiz}
                                        quizRef={quizRef}
                                    />
                                    <NotesChatPanel
                                        sourceText={result.source_text}
                                        summary={result.summary}
                                    />
                                </div>
                            </ResultsDisplay>

                             {showQuiz && (
                                <div ref={quizRef} className="w-full xl:w-2/3 max-w-4xl mx-auto pt-16 pb-20">
                                    {result.quizScore != null && (
                                        <div className="mb-6 p-4 pro-card bg-blue-500/5 border-blue-500/20 rounded-xl flex items-center justify-between">
                                            <div className="flex items-center gap-3">
                                                <Trophy className="w-5 h-5 text-blue-500" />
                                                <span className="text-sm">
                                                    Previous attempt: <span className="font-bold text-blue-500">{result.quizScore}%</span>
                                                </span>
                                            </div>
                                            <span className="text-xs text-app-muted">Retaking will overwrite your score</span>
                                        </div>
                                    )}
                                    <QuizSection
                                        quiz={result.quiz}
                                        onQuizComplete={handleQuizComplete}
                                        onReset={() => {
                                            setShowQuiz(false);
                                            window.scrollTo({ top: 0, behavior: 'smooth' });
                                        }}
                                    />
                                </div>
                            )}
                        </div>
                    </div>
                </main>
            </div>
        </div>
    );
}

export default AnalysisResults;
