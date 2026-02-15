import React from 'react';
import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { Brain, Search, BookOpen, Clock, FileText, ChevronRight, BarChart3, Globe } from 'lucide-react';

const LandingPage = () => {
    const navigate = useNavigate();

    return (
        <div className="min-h-screen bg-zinc-950 text-zinc-100 font-sans selection:bg-blue-500/30">
            <header className="fixed top-0 w-full z-50 border-b border-zinc-900 bg-zinc-950/80 backdrop-blur-md">
                <div className="max-w-[1600px] mx-auto px-8 h-16 flex items-center justify-between">
                    <div className="flex items-center gap-3">
                        <div className="w-8 h-8 bg-zinc-100 rounded flex items-center justify-center">
                            <Brain className="w-5 h-5 text-zinc-950" />
                        </div>
                        <span className="text-xl font-bold tracking-tight">Synod</span>
                    </div>
                    <div className="flex items-center gap-8">
                        <nav className="hidden md:flex items-center gap-6 text-sm font-medium text-zinc-400">
                            <a href="#" className="hover:text-white transition-colors">How it works</a>
                            <a href="#" className="hover:text-white transition-colors">Documentation</a>
                        </nav>
                        <button
                            onClick={() => navigate('/dashboard')}
                            className="px-5 py-2 bg-white text-zinc-950 text-sm font-bold rounded-lg hover:bg-zinc-200 transition-all"
                        >
                            Get Started
                        </button>
                    </div>
                </div>
            </header>

            <main className="pt-16">
                {/* Full-width Hero */}
                <section className="relative py-24 md:py-40 px-8 border-b border-zinc-900">
                    <div className="max-w-[1600px] mx-auto grid lg:grid-cols-2 gap-20 items-center">
                        <motion.div
                            initial={{ opacity: 0, x: -30 }}
                            animate={{ opacity: 1, x: 0 }}
                            transition={{ duration: 0.6 }}
                        >
                            <div className="inline-flex items-center text-zinc-500 font-bold uppercase tracking-[0.2em] text-[10px] mb-6 px-3 py-1 border border-zinc-800 rounded-full">
                                Professional Learning Infrastructure
                            </div>
                            <h1 className="text-6xl md:text-8xl font-bold tracking-tight mb-8 leading-[0.95]">
                                Intelligent <br />
                                <span className="text-zinc-500">Lecture Synthesis.</span>
                            </h1>
                            <p className="text-zinc-400 text-xl md:text-2xl max-w-xl mb-12 leading-relaxed">
                                Synod extracts core knowledge from lecture materials, providing instant summaries and automated assessments for serious students.
                            </p>
                            <div className="flex items-center gap-6">
                                <button
                                    onClick={() => navigate('/dashboard')}
                                    className="px-10 py-4 bg-white text-zinc-950 font-bold rounded-xl hover:bg-zinc-200 transition-all flex items-center gap-2"
                                >
                                    Start Analysis
                                    <ChevronRight className="w-4 h-4" />
                                </button>
                                <div className="text-sm font-medium text-zinc-500">
                                    No credit card required. <br />Free for students.
                                </div>
                            </div>
                        </motion.div>

                        <motion.div
                            initial={{ opacity: 0, scale: 0.95 }}
                            animate={{ opacity: 1, scale: 1 }}
                            transition={{ duration: 0.8, delay: 0.2 }}
                            className="hidden lg:block relative"
                        >
                            <div className="bg-zinc-900 border border-zinc-800 rounded-2xl p-4 shadow-2xl">
                                <div className="flex items-center gap-2 mb-4 px-2">
                                    <div className="w-3 h-3 rounded-full bg-zinc-800" />
                                    <div className="w-3 h-3 rounded-full bg-zinc-800" />
                                    <div className="w-3 h-3 rounded-full bg-zinc-800" />
                                </div>
                                <div className="grid grid-cols-3 gap-4">
                                    <div className="col-span-2 space-y-4">
                                        <div className="h-4 bg-zinc-800 rounded w-3/4" />
                                        <div className="h-4 bg-zinc-800 rounded w-1/2" />
                                        <div className="h-32 bg-zinc-800/50 rounded-xl" />
                                        <div className="h-4 bg-zinc-800 rounded w-2/3" />
                                    </div>
                                    <div className="space-y-4">
                                        <div className="h-24 bg-zinc-800/50 rounded-xl" />
                                        <div className="h-24 bg-zinc-800/50 rounded-xl" />
                                    </div>
                                </div>
                            </div>
                            {/* Floating Decoration */}
                            <div className="absolute -bottom-10 -left-10 bg-zinc-800 border border-zinc-700 p-6 rounded-2xl shadow-xl flex items-center gap-4 max-w-xs animate-bounce" style={{ animationDuration: '4s' }}>
                                <div className="w-12 h-12 bg-blue-500/20 rounded-xl flex items-center justify-center text-blue-500">
                                    <BarChart3 className="w-6 h-6" />
                                </div>
                                <div className="text-left">
                                    <p className="text-xs font-bold text-zinc-400 uppercase tracking-widest">Accuracy</p>
                                    <p className="text-lg font-bold text-white">99.4% NLP Precision</p>
                                </div>
                            </div>
                        </motion.div>
                    </div>
                </section>

                {/* Features Matrix */}
                <section className="py-24 px-8 bg-zinc-900/20">
                    <div className="max-w-[1600px] mx-auto">
                        <div className="grid md:grid-cols-4 gap-12">
                            {[
                                { icon: Search, title: "Universal Search", text: "Index and search through all your lecture history instantly." },
                                { icon: Globe, title: "Multi-Format", text: "Support for PDF, PPTX, and TXT documents. Effortless ingestion." },
                                { icon: Clock, title: "Save Time", text: "Reduce study hours by 60% with AI-driven summaries." },
                                { icon: BookOpen, title: "Knowledge Graphs", text: "Extract concepts and link them for deeper mental models." }
                            ].map((f, i) => (
                                <div key={i} className="group">
                                    <div className="w-10 h-10 bg-zinc-900 border border-zinc-800 rounded-lg flex items-center justify-center text-zinc-400 mb-6 group-hover:bg-zinc-100 group-hover:text-zinc-950 transition-all">
                                        <f.icon className="w-5 h-5" />
                                    </div>
                                    <h3 className="text-sm font-bold uppercase tracking-widest mb-3">{f.title}</h3>
                                    <p className="text-zinc-500 text-sm leading-relaxed">{f.text}</p>
                                </div>
                            ))}
                        </div>
                    </div>
                </section>
            </main>

            <footer className="py-20 px-8 border-t border-zinc-900 text-zinc-500">
                <div className="max-w-[1600px] mx-auto flex flex-col md:flex-row justify-between items-center gap-10">
                    <div className="flex items-center gap-3">
                        <div className="w-6 h-6 bg-zinc-800 rounded flex items-center justify-center">
                            <Brain className="w-4 h-4" />
                        </div>
                        <span className="font-bold text-zinc-300">Synod</span>
                    </div>
                    <div className="flex gap-10 text-xs font-bold uppercase tracking-widest">
                        <a href="#" className="hover:text-white transition-colors">Privacy</a>
                        <a href="#" className="hover:text-white transition-colors">Terms</a>
                        <a href="#" className="hover:text-white transition-colors">Contact</a>
                    </div>
                    <p className="text-xs font-medium">© 2026 Synod Systems. Built for precision.</p>
                </div>
            </footer>
        </div>
    );
};

export default LandingPage;
