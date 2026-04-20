import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
    History as HistoryIcon, Search, Calendar, ChevronRight,
    Trash2, ArrowLeft, Clock, Sun, Moon, LogOut, Trophy
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { useTheme } from '../context/ThemeContext';
import { useAuth } from '../context/AuthContext';

import { db } from '../firebase';
import { collection, query, where, getDocs, deleteDoc, doc } from 'firebase/firestore';

const History = () => {
    const [history, setHistory] = useState([]);
    const [searchQuery, setSearchQuery] = useState('');
    const [loadingHistory, setLoadingHistory] = useState(true);
    const navigate = useNavigate();
    const { theme, toggleTheme } = useTheme();
    const { user, logout } = useAuth();

    useEffect(() => {
        const fetchHistory = async () => {
            if (!user) { 
                console.log("History: User not logged in, clearing list.");
                setLoadingHistory(false); 
                return; 
            }
            
            setLoadingHistory(true);
            const lookupId = user.uid || 'anonymous_user';
            console.log(`History: Fetching records for userId: ${lookupId}`);
            
            console.log(`History: Attempting to query 'history' collection for userId: ${lookupId}...`);
            try {
                const historyRef = collection(db, "history");
                const q = query(historyRef, where("userId", "==", lookupId));
                
                console.log("History: Awaiting Firestore response...");
                const snapshot = await getDocs(q);
                console.log(`History: Response received! Found ${snapshot.size} records.`);
                
                const items = snapshot.docs.map(docSnap => {
                    const data = docSnap.data();
                    return { id: docSnap.id, ...data };
                });
                console.log("History: Data mapping complete.");
                
                items.sort((a, b) => new Date(b.date || 0) - new Date(a.date || 0));
                setHistory(items);
            } catch (e) {
                console.error('History: Error loading Firestore data:', e);
            } finally {
                setLoadingHistory(false);
            }
        };
        fetchHistory();
    }, [user]);

    const deleteEntry = async (id) => {
        try {
            await deleteDoc(doc(db, "history", id));
            setHistory(prev => prev.filter(item => item.id !== id));
        } catch (e) {
            console.error('Error deleting document:', e);
        }
    };

    const filteredHistory = history.filter(item =>
        (item.title && item.title.toLowerCase().includes(searchQuery.toLowerCase())) ||
        (item.summary && item.summary.toLowerCase().includes(searchQuery.toLowerCase()))
    );

    return (
        <div className="min-h-screen bg-app-bg text-app-fg font-sans transition-colors duration-300 flex flex-col">
            {/* Header */}
            <header className="h-16 border-b border-app-border bg-app-bg/80 backdrop-blur-md sticky top-0 z-50 shrink-0">
                <div className="max-w-[1600px] mx-auto px-8 h-full flex items-center justify-between">
                    <div className="flex items-center gap-6">
                        <button
                            onClick={() => navigate('/dashboard')}
                            className="p-2 -ml-2 text-app-muted hover:text-app-fg hover:bg-app-card rounded-lg transition-colors"
                        >
                            <ArrowLeft className="w-5 h-5" />
                        </button>
                        <div className="flex items-center gap-3">
                            <HistoryIcon className="w-5 h-5 text-app-muted" />
                            <h1 className="text-sm font-bold uppercase tracking-widest">Knowledge Archive</h1>
                        </div>
                    </div>
                    <div className="flex items-center gap-4">
                        <div className="relative">
                            <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-app-muted" />
                            <input
                                type="text"
                                placeholder="Search history..."
                                value={searchQuery}
                                onChange={(e) => setSearchQuery(e.target.value)}
                                className="pl-10 pr-4 py-2 bg-app-card border border-app-border rounded-lg text-sm focus:ring-1 focus:ring-blue-500/50 outline-none w-64 transition-all"
                            />
                        </div>
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

            <main className="flex-1 overflow-y-auto">
                <div className="max-w-[1600px] mx-auto px-8 py-12">
                    <div className="mb-12">
                        <h2 className="text-4xl font-bold tracking-tight mb-4">Past Analysis</h2>
                        <p className="text-app-muted">Manage and revisit your synthesized lecture knowledge.</p>
                    </div>

                    {filteredHistory.length === 0 ? (
                        <div className="pro-card p-20 flex flex-col items-center text-center">
                            <div className="w-16 h-16 bg-app-card border border-app-border rounded-2xl flex items-center justify-center text-app-muted mb-6">
                                <Clock className="w-8 h-8" />
                            </div>
                            <h3 className="text-xl font-bold mb-2">No history found</h3>
                            <p className="text-app-muted max-w-sm">
                                {searchQuery ? "No entries match your search." : "You haven't analyzed any lectures yet. Start your first analysis in the dashboard."}
                            </p>
                            {!searchQuery && (
                                <button
                                    onClick={() => navigate('/dashboard')}
                                    className="mt-8 px-6 py-2 bg-app-fg text-app-bg font-bold rounded-lg hover:opacity-90 transition-all"
                                >
                                    Go to Dashboard
                                </button>
                            )}
                        </div>
                    ) : (
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                            <AnimatePresence mode="popLayout">
                                {filteredHistory.map((item) => (
                                    <motion.div
                                        key={item.id}
                                        layout
                                        initial={{ opacity: 0, scale: 0.95 }}
                                        animate={{ opacity: 1, scale: 1 }}
                                        exit={{ opacity: 0, scale: 0.95 }}
                                        className="pro-card p-6 flex flex-col h-full group"
                                    >
                                        <div className="flex justify-between items-start mb-4">
                                            <div className="flex items-center gap-2 text-[10px] font-bold text-app-muted uppercase tracking-widest">
                                                <Calendar className="w-3 h-3" />
                                                {item.date ? new Date(item.date).toLocaleDateString() : (item.id ? new Date(item.id).toLocaleDateString() : 'Unknown Date')}
                                            </div>
                                            <button
                                                onClick={(e) => { e.stopPropagation(); deleteEntry(item.id); }}
                                                className="p-2 text-app-muted hover:text-red-500 hover:bg-red-500/10 rounded-lg transition-all md:opacity-0 group-hover:opacity-100"
                                            >
                                                <Trash2 className="w-4 h-4" />
                                            </button>
                                        </div>
                                         <h3 className="text-lg font-bold mb-3 group-hover:text-blue-500 transition-colors line-clamp-2 flex items-start gap-2">
                                            {item.quizScore != null && <Trophy className="w-4 h-4 text-amber-500 mt-1 shrink-0" />}
                                            {item.title || 'Untitled Analysis'}
                                         </h3>
                                         <p className="text-app-muted text-sm line-clamp-3 mb-4 flex-1 italic">"{item.summary || 'No summary available'}"</p>

                                         {item.quizScore != null && (
                                            <div className="mb-4">
                                                <div className="flex items-center gap-2">
                                                    <span className="text-xs text-app-muted uppercase tracking-wider">Quiz Score</span>
                                                    <div className={`h-2 w-2 rounded-full ${item.quizScore >= 70 ? 'bg-emerald-500' : item.quizScore >= 50 ? 'bg-amber-500' : 'bg-red-500'}`}></div>
                                                </div>
                                                <div className="flex items-center gap-2 mt-1">
                                                    <div className="flex-1 h-1.5 bg-app-border rounded-full overflow-hidden">
                                                        <div 
                                                            className={`h-full ${item.quizScore >= 70 ? 'bg-emerald-500' : item.quizScore >= 50 ? 'bg-amber-500' : 'bg-red-500'}`}
                                                            style={{ width: `${item.quizScore}%` }}
                                                        />
                                                    </div>
                                                    <span className="text-xs font-bold text-app-fg">{item.quizScore}%</span>
                                                </div>
                                            </div>
                                         )}

                                         {item.quizScore != null && (
                                            <div className="mb-4">
                                                <div className="flex items-center gap-2 mb-1">
                                                    <span className="text-xs font-bold text-app-muted uppercase tracking-wider">Quiz Score</span>
                                                    <div className={`h-2 w-2 rounded-full ${item.quizScore >= 70 ? 'bg-emerald-500' : item.quizScore >= 50 ? 'bg-amber-500' : 'bg-red-500'}`}></div>
                                                </div>
                                                <div className="flex items-center gap-3">
                                                    <div className="flex-1 h-2 bg-app-border rounded-full overflow-hidden">
                                                        <div 
                                                            className={`h-full transition-all ${item.quizScore >= 70 ? 'bg-emerald-500' : item.quizScore >= 50 ? 'bg-amber-500' : 'bg-red-500'}`}
                                                            style={{ width: `${item.quizScore}%` }}
                                                        />
                                                    </div>
                                                    <span className="text-sm font-bold text-app-fg">{item.quizScore}%</span>
                                                </div>
                                            </div>
                                         )}

                                        <div className="pt-6 border-t border-app-border flex items-center justify-between">
                                            <div className="flex gap-1">
                                                {(item.concepts || []).slice(0, 2).map((c, i) => (
                                                    <span key={i} className="px-2 py-1 bg-app-card border border-app-border rounded-md text-[10px] font-bold text-app-muted">
                                                        {c}
                                                    </span>
                                                ))}
                                                {(item.concepts || []).length > 2 && <span className="text-[10px] text-app-muted font-bold self-center">+{(item.concepts || []).length - 2}</span>}
                                            </div>
                                            <button
                                                onClick={() => navigate('/analysis', { state: { result: item } })}
                                                className="flex items-center gap-1 text-xs font-bold text-app-fg hover:gap-2 transition-all"
                                            >
                                                Revisit <ChevronRight className="w-3 h-3" />
                                            </button>
                                        </div>
                                    </motion.div>
                                ))}
                            </AnimatePresence>
                        </div>
                    )}
                </div>
            </main>
        </div>
    );
};

export default History;
