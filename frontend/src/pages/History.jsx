import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Brain, ArrowLeft, Calendar, FileText, ChevronRight, Trash2, Search } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

const History = () => {
    const [history, setHistory] = useState([]);
    const [search, setSearch] = useState('');
    const navigate = useNavigate();

    useEffect(() => {
        const savedHistory = JSON.parse(localStorage.getItem('synod_history') || '[]');
        setHistory(savedHistory);
    }, []);

    const deleteEntry = (id, e) => {
        e.stopPropagation();
        const newHistory = history.filter(item => item.id !== id);
        setHistory(newHistory);
        localStorage.setItem('synod_history', JSON.stringify(newHistory));
    };

    const filteredHistory = history.filter(item =>
        item.title.toLowerCase().includes(search.toLowerCase()) ||
        item.summary.toLowerCase().includes(search.toLowerCase())
    );

    return (
        <div className="min-h-screen bg-slate-950 text-slate-200">
            <header className="border-b border-slate-800 bg-slate-950/50 backdrop-blur-md sticky top-0 z-50">
                <div className="max-w-7xl mx-auto px-6 h-20 flex items-center justify-between">
                    <div className="flex items-center gap-6">
                        <button
                            onClick={() => navigate('/dashboard')}
                            className="p-3 hover:bg-slate-900 rounded-2xl transition-all border border-transparent hover:border-slate-800 group"
                        >
                            <ArrowLeft className="w-5 h-5 group-hover:-translate-x-1 transition-transform" />
                        </button>
                        <div className="flex items-center gap-3">
                            <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
                                <Brain className="w-5 h-5 text-white" />
                            </div>
                            <h1 className="text-xl font-bold tracking-tighter text-white">Study History</h1>
                        </div>
                    </div>
                </div>
            </header>

            <main className="max-w-4xl mx-auto px-6 py-12">
                <div className="mb-12">
                    <div className="relative group">
                        <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-500 group-focus-within:text-blue-500 transition-colors" />
                        <input
                            type="text"
                            placeholder="Search your previous sessions..."
                            value={search}
                            onChange={(e) => setSearch(e.target.value)}
                            className="w-full bg-slate-900/50 border border-slate-800 rounded-2xl py-4 pl-12 pr-6 text-lg focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 transition-all font-medium"
                        />
                    </div>
                </div>

                <div className="space-y-4">
                    <AnimatePresence mode='popLayout'>
                        {filteredHistory.length > 0 ? (
                            filteredHistory.map((item, index) => (
                                <motion.div
                                    key={item.id}
                                    layout
                                    initial={{ opacity: 0, x: -20 }}
                                    animate={{ opacity: 1, x: 0 }}
                                    exit={{ opacity: 0, scale: 0.95 }}
                                    transition={{ delay: index * 0.05 }}
                                    className="group bg-slate-900/40 border border-slate-800 hover:border-slate-700 p-6 rounded-3xl transition-all cursor-pointer relative overflow-hidden"
                                >
                                    <div className="flex items-start justify-between gap-4">
                                        <div className="flex-1">
                                            <div className="flex items-center gap-3 text-slate-500 text-xs font-bold uppercase tracking-widest mb-3">
                                                <Calendar className="w-3.5 h-3.5" />
                                                {new Date(item.date).toLocaleDateString(undefined, {
                                                    month: 'long',
                                                    day: 'numeric',
                                                    year: 'numeric',
                                                    hour: '2-digit',
                                                    minute: '2-digit'
                                                })}
                                            </div>
                                            <h3 className="text-xl font-bold text-white mb-3 group-hover:text-blue-400 transition-colors">{item.title}</h3>
                                            <p className="text-slate-400 line-clamp-2 leading-relaxed text-sm italic">
                                                "{item.summary}"
                                            </p>
                                            <div className="flex flex-wrap gap-2 mt-4">
                                                {item.concepts.slice(0, 3).map((concept, i) => (
                                                    <span key={i} className="px-3 py-1 bg-slate-800/50 border border-slate-700/50 rounded-lg text-[10px] font-black text-slate-500 uppercase tracking-tighter">
                                                        {concept}
                                                    </span>
                                                ))}
                                                {item.concepts.length > 3 && (
                                                    <span className="px-3 py-1 bg-blue-500/10 text-blue-500 rounded-lg text-[10px] font-black uppercase tracking-tighter">
                                                        +{item.concepts.length - 3} more
                                                    </span>
                                                )}
                                            </div>
                                        </div>
                                        <div className="flex flex-col gap-2">
                                            <button
                                                onClick={(e) => deleteEntry(item.id, e)}
                                                className="p-3 text-slate-600 hover:text-red-500 hover:bg-red-500/10 rounded-xl transition-all"
                                            >
                                                <Trash2 className="w-5 h-5" />
                                            </button>
                                            <div className="p-3 text-slate-700 group-hover:text-blue-500 transition-colors">
                                                <ChevronRight className="w-6 h-6" />
                                            </div>
                                        </div>
                                    </div>
                                </motion.div>
                            ))
                        ) : (
                            <div className="py-20 text-center">
                                <div className="w-20 h-20 bg-slate-900 rounded-3xl flex items-center justify-center mx-auto mb-6 text-slate-700 border border-slate-800">
                                    <FileText className="w-10 h-10" />
                                </div>
                                <h3 className="text-xl font-bold text-slate-400 mb-2">No history yet</h3>
                                <p className="text-slate-600">Start an analysis to build your knowledge base.</p>
                            </div>
                        )}
                    </AnimatePresence>
                </div>
            </main>
        </div>
    );
};

export default History;
