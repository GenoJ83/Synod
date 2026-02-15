import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Brain, ArrowLeft, Calendar, FileText, ChevronRight, Trash2, Search, Filter } from 'lucide-react';
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
        <div className="min-h-screen bg-zinc-950 text-zinc-100 font-sans flex flex-col">
            <header className="border-b border-zinc-900 bg-zinc-950/50 backdrop-blur-md sticky top-0 z-50 h-16 shrink-0">
                <div className="max-w-[1600px] mx-auto px-8 h-full flex items-center justify-between">
                    <div className="flex items-center gap-6">
                        <button
                            onClick={() => navigate('/dashboard')}
                            className="p-2 hover:bg-zinc-900 rounded-lg transition-all group"
                        >
                            <ArrowLeft className="w-5 h-5 group-hover:-translate-x-1 transition-transform" />
                        </button>
                        <div className="flex items-center gap-3">
                            <div className="w-6 h-6 bg-zinc-100 rounded flex items-center justify-center shrink-0">
                                <Brain className="w-4 h-4 text-zinc-950" />
                            </div>
                            <h1 className="text-sm font-bold uppercase tracking-widest">Knowledge Archive</h1>
                        </div>
                    </div>
                </div>
            </header>

            <main className="flex-1 overflow-y-auto">
                <div className="max-w-[1200px] mx-auto px-8 py-16">
                    <div className="flex flex-col md:flex-row items-center justify-between gap-8 mb-12">
                        <div className="text-left w-full md:w-auto">
                            <h2 className="text-4xl font-bold tracking-tight mb-2">History</h2>
                            <p className="text-zinc-500">Manage and revisit your analyzed course materials.</p>
                        </div>
                        <div className="relative w-full md:w-96 group">
                            <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-600 group-focus-within:text-zinc-100 transition-colors" />
                            <input
                                type="text"
                                placeholder="Search archives..."
                                value={search}
                                onChange={(e) => setSearch(e.target.value)}
                                className="w-full bg-zinc-900 border border-zinc-800 rounded-xl py-3 pl-12 pr-6 text-sm focus:outline-none focus:border-zinc-600 transition-all font-medium"
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
                                        initial={{ opacity: 0, scale: 0.98 }}
                                        animate={{ opacity: 1, scale: 1 }}
                                        exit={{ opacity: 0, scale: 0.95 }}
                                        transition={{ duration: 0.2 }}
                                        className="group bg-zinc-900/30 border border-zinc-800 hover:border-zinc-700 p-6 rounded-2xl transition-all cursor-pointer relative flex items-start gap-6"
                                        onClick={() => navigate('/dashboard')}
                                    >
                                        <div className="w-12 h-12 bg-zinc-900 border border-zinc-800 rounded-xl flex items-center justify-center text-zinc-500 shrink-0 group-hover:bg-zinc-100 group-hover:text-zinc-950 transition-all">
                                            <FileText className="w-6 h-6" />
                                        </div>
                                        <div className="flex-1 min-w-0">
                                            <div className="flex items-center gap-3 text-[10px] font-bold text-zinc-600 uppercase tracking-[0.1em] mb-2">
                                                <Calendar className="w-3 h-3" />
                                                {new Date(item.date).toLocaleDateString(undefined, {
                                                    month: 'short',
                                                    day: 'numeric',
                                                    year: 'numeric'
                                                })}
                                            </div>
                                            <h3 className="text-lg font-bold text-zinc-200 mb-2 truncate">{item.title}</h3>
                                            <p className="text-zinc-500 line-clamp-2 leading-relaxed text-sm italic pr-12">
                                                "{item.summary}"
                                            </p>
                                            <div className="flex flex-wrap gap-2 mt-4">
                                                {item.concepts.slice(0, 5).map((concept, i) => (
                                                    <span key={i} className="px-2 py-0.5 bg-zinc-800/50 border border-zinc-800 rounded text-[9px] font-bold text-zinc-400 uppercase tracking-tight">
                                                        {concept}
                                                    </span>
                                                ))}
                                            </div>
                                        </div>
                                        <div className="absolute top-6 right-6 flex flex-col gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                                            <button
                                                onClick={(e) => deleteEntry(item.id, e)}
                                                className="p-2 text-zinc-600 hover:text-red-500 hover:bg-red-950/20 rounded-lg transition-all"
                                            >
                                                <Trash2 className="w-4 h-4" />
                                            </button>
                                            <div className="p-2 text-zinc-500">
                                                <ChevronRight className="w-5 h-5" />
                                            </div>
                                        </div>
                                    </motion.div>
                                ))
                            ) : (
                                <div className="py-32 text-center border-2 border-dashed border-zinc-900 rounded-[2.5rem]">
                                    <div className="w-16 h-16 bg-zinc-900 rounded-2xl flex items-center justify-center mx-auto mb-6 text-zinc-700 border border-zinc-800">
                                        <FileText className="w-8 h-8" />
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
