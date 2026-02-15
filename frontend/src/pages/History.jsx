```javascript
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  History as HistoryIcon, Search, Calendar, ChevronRight, 
  Trash2, ArrowLeft, Clock, Brain, Sun, Moon
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { useTheme } from '../context/ThemeContext';

const History = () => {
    const [history, setHistory] = useState([]);
    const [searchQuery, setSearchQuery] = useState('');
    const navigate = useNavigate();
    const { theme, toggleTheme } = useTheme();

    useEffect(() => {
        const savedHistory = JSON.parse(localStorage.getItem('synod_history') || '[]');
        setHistory(savedHistory);
    }, []);

    const deleteEntry = (id) => {
        const updated = history.filter(item => item.id !== id);
        setHistory(updated);
        localStorage.setItem('synod_history', JSON.stringify(updated));
    };

    const filteredHistory = history.filter(item => 
        item.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        item.summary.toLowerCase().includes(searchQuery.toLowerCase())
    );

    return (
        <div className="min-h-screen bg-app-bg text-app-fg font-sans transition-colors duration-300">
            {/* Header */}
            <header className="h-16 border-b border-app-border bg-app-bg/80 backdrop-blur-md sticky top-0 z-50">
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
                                    </div>
                                    <h3 className="text-lg font-bold text-zinc-400 mb-2">No archived analyses</h3>
                                    <p className="text-zinc-600 text-sm">Analyze your first lecture to see it here.</p>
                                </div>
                            )}
                        </AnimatePresence>
                    </div>
                </div>
            </main>
        </div>
    );
};

export default History;
