import React from 'react';
import { motion } from 'framer-motion';
import { useNavigate, Link } from 'react-router-dom';
import { Brain, Search, BookOpen, Clock, FileText, ChevronRight, BarChart3, Globe, Sun, Moon } from 'lucide-react';
import { useTheme } from '../context/ThemeContext';

const LandingPage = () => {
    const navigate = useNavigate();
    const { theme, toggleTheme } = useTheme();

    return (
        <div className="min-h-screen bg-app-bg text-app-fg font-sans selection:bg-blue-500/30 transition-colors duration-300">
            <header className="fixed top-0 w-full z-50 border-b border-app-border bg-app-bg/80 backdrop-blur-md">
                <div className="max-w-[1600px] mx-auto px-8 h-16 flex items-center justify-between">
                    <div className="flex items-center gap-3">
                        <div className="w-8 h-8 bg-app-fg rounded flex items-center justify-center">
                            <Brain className="w-5 h-5 text-app-bg" />
                        </div>
                        <span className="text-xl font-bold tracking-tight">Synod</span>
                        <span className="text-[8px] bg-blue-500 text-white px-1.5 py-0.5 rounded-full font-bold uppercase tracking-tighter">v2.0</span>
                    </div>
                    <div className="flex items-center gap-8">
                        <nav className="hidden md:flex items-center gap-6 text-sm font-medium text-app-muted">
                            <Link to="/how-it-works" className="hover:text-app-fg transition-colors">How it works</Link>
                            <Link to="/documentation" className="hover:text-app-fg transition-colors">Documentation</Link>
                        </nav>
                        <div className="flex items-center gap-4">
                            <button
                                onClick={toggleTheme}
                                className="p-2 text-app-muted hover:text-app-fg rounded-lg transition-colors border border-app-border"
                                title={theme === 'dark' ? 'Switch to Light Mode' : 'Switch to Dark Mode'}
                            >
                                {theme === 'dark' ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
                            </button>
                            <button
                                onClick={() => navigate('/dashboard')}
                                className="px-5 py-2 bg-app-fg text-app-bg text-sm font-bold rounded-lg hover:opacity-90 transition-all"
                            >
                                Get Started
                            </button>
                        </div>
                    </div>
                </div>
            </header>

            <main className="pt-16">
                {/* Full-width Hero */}
                <section className="relative py-24 md:py-40 px-8 border-b border-app-border overflow-hidden">
                    {/* Video Background */}
                    <div className="absolute inset-0 z-0">
                        <video
                            autoPlay
                            loop
                            muted
                            playsInline
                            poster="https://images.pexels.com/photos/255379/pexels-photo-255379.jpeg?auto=compress&cs=tinysrgb&w=1260&h=750&dpr=1"
                            onPlay={() => console.log("Video started playing")}
                            onError={(e) => {
                                console.error("Video error:", e);
                                // Set a data attribute for remote debugging if needed
                                e.currentTarget.setAttribute('data-error', 'true');
                            }}
                            className="w-full h-full object-cover opacity-60 dark:opacity-40"
                        >
                            <source src="https://videos.pexels.com/video-files/3129957/3129957-uhd_2560_1440_25fps.mp4" type="video/mp4" />
                            Your browser does not support the video tag.
                        </video>
                        {/* Gradient Overlay for Readability */}
                        <div className="absolute inset-0 bg-gradient-to-b from-app-bg/90 via-app-bg/20 to-app-bg" />
                        <div className="absolute inset-0 bg-gradient-to-r from-app-bg/70 via-transparent to-transparent" />
                    </div>

                    <div className="max-w-[1600px] mx-auto grid lg:grid-cols-2 gap-20 items-center relative z-10">
                        <motion.div
                            initial={{ opacity: 0, x: -30 }}
                            animate={{ opacity: 1, x: 0 }}
                            transition={{ duration: 0.6 }}
                        >
                            <div className="inline-flex items-center text-app-muted font-bold uppercase tracking-[0.2em] text-[10px] mb-6 px-3 py-1 border border-app-border rounded-full bg-app-bg/50 backdrop-blur-sm">
                                Professional Learning Infrastructure
                            </div>
                            <h1 className="text-6xl md:text-8xl font-bold tracking-tight mb-8 leading-[0.95]">
                                Intelligent <br />
                                <span className="text-app-muted">Lecture Synthesis.</span>
                            </h1>
                            <p className="text-app-muted text-xl md:text-2xl max-w-xl mb-12 leading-relaxed">
                                Synod extracts core knowledge from lecture materials, providing instant summaries and automated assessments for serious students.
                            </p>
                            <div className="flex items-center gap-6">
                                <button
                                    onClick={() => navigate('/dashboard')}
                                    className="px-10 py-4 bg-app-fg text-app-bg font-bold rounded-xl hover:opacity-90 transition-all flex items-center gap-2 shadow-2xl"
                                >
                                    Start Analysis
                                    <ChevronRight className="w-4 h-4" />
                                </button>
                                <div className="text-sm font-medium text-app-muted">
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
                            <div className="bg-app-card border border-app-border rounded-2xl p-4 shadow-2xl">
                                <div className="flex items-center gap-2 mb-4 px-2">
                                    <div className="w-3 h-3 rounded-full bg-app-border" />
                                    <div className="w-3 h-3 rounded-full bg-app-border" />
                                    <div className="w-3 h-3 rounded-full bg-app-border" />
                                </div>
                                <div className="grid grid-cols-3 gap-4">
                                    <div className="col-span-2 space-y-4">
                                        <div className="h-4 bg-app-border rounded w-3/4" />
                                        <div className="h-4 bg-app-border rounded w-1/2" />
                                        <div className="h-32 bg-app-card rounded-xl" />
                                        <div className="h-4 bg-app-border rounded w-2/3" />
                                    </div>
                                    <div className="space-y-4">
                                        <div className="h-24 bg-app-card rounded-xl" />
                                        <div className="h-24 bg-app-card rounded-xl" />
                                    </div>
                                </div>
                            </div>
                            {/* Floating Decoration */}
                            <div className="absolute -bottom-10 -left-10 bg-app-bg border border-app-border p-6 rounded-2xl shadow-xl flex items-center gap-4 max-w-xs animate-bounce" style={{ animationDuration: '4s' }}>
                                <div className="w-12 h-12 bg-blue-500/20 rounded-xl flex items-center justify-center text-blue-500">
                                    <BarChart3 className="w-6 h-6" />
                                </div>
                                <div className="text-left">
                                    <p className="text-xs font-bold text-app-muted uppercase tracking-widest">Accuracy</p>
                                    <p className="text-lg font-bold">99.4% NLP Precision</p>
                                </div>
                            </div>
                        </motion.div>
                    </div>
                </section>

                {/* Features Matrix */}
                <section className="py-24 px-8 bg-app-card/20">
                    <div className="max-w-[1600px] mx-auto">
                        <div className="grid md:grid-cols-4 gap-12">
                            {[
                                { icon: Search, title: "Universal Search", text: "Index and search through all your lecture history instantly." },
                                { icon: Globe, title: "Multi-Format", text: "Support for PDF, PPTX, and TXT documents. Effortless ingestion." },
                                { icon: Clock, title: "Save Time", text: "Reduce study hours by 60% with AI-driven summaries." },
                                { icon: BookOpen, title: "Knowledge Graphs", text: "Extract concepts and link them for deeper mental models." }
                            ].map((f, i) => (
                                <div key={i} className="group">
                                    <div className="w-10 h-10 bg-app-card border border-app-border rounded-lg flex items-center justify-center text-app-muted mb-6 group-hover:bg-app-fg group-hover:text-app-bg transition-all">
                                        <f.icon className="w-5 h-5" />
                                    </div>
                                    <h3 className="text-sm font-bold uppercase tracking-widest mb-3">{f.title}</h3>
                                    <p className="text-app-muted text-sm leading-relaxed">{f.text}</p>
                                </div>
                            ))}
                        </div>
                    </div>
                </section>

                {/* How It Works */}
                <section id="how-it-works" className="py-24 px-8">
                    <div className="max-w-[1600px] mx-auto">
                        <div className="text-center mb-16">
                            <h2 className="text-4xl font-bold mb-4">How It Works</h2>
                            <p className="text-app-muted text-lg max-w-2xl mx-auto">
                                Upload your lecture materials and get instant analysis with interactive quizzes
                            </p>
                        </div>
                        <div className="grid md:grid-cols-4 gap-8">
                            {[
                                { step: "01", title: "Upload Content", text: "Paste lecture text or upload PDF, DOCX, or TXT files.", icon: FileText },
                                { step: "02", title: "AI Analysis", text: "Our NLP extracts key concepts and generates summaries.", icon: Brain },
                                { step: "03", title: "Learn Concepts", text: "Click any concept for explanations with lecture context.", icon: BookOpen },
                                { step: "04", title: "Test Knowledge", text: "Take quizzes with 30+ questions to verify understanding.", icon: BarChart3 }
                            ].map((item, i) => (
                                <div key={i} className="relative">
                                    <div className="bg-app-card border border-app-border rounded-2xl p-6 h-full">
                                        <div className="text-[10px] font-bold text-blue-500 mb-4">{item.step}</div>
                                        <div className="w-12 h-12 bg-blue-500/10 rounded-xl flex items-center justify-center text-blue-500 mb-4">
                                            <item.icon className="w-6 h-6" />
                                        </div>
                                        <h3 className="text-lg font-bold mb-2">{item.title}</h3>
                                        <p className="text-app-muted text-sm">{item.text}</p>
                                    </div>
                                    {i < 3 && (
                                        <div className="hidden md:block absolute top-1/2 -right-4 transform -translate-y-1/2 text-app-muted">
                                            <ChevronRight className="w-5 h-5" />
                                        </div>
                                    )}
                                </div>
                            ))}
                        </div>
                    </div>
                </section>

                {/* Quiz Types */}
                <section id="quiz-types" className="py-24 px-8 bg-app-card/20">
                    <div className="max-w-[1600px] mx-auto">
                        <div className="text-center mb-16">
                            <h2 className="text-4xl font-bold mb-4">Comprehensive Testing</h2>
                            <p className="text-app-muted text-lg max-w-2xl mx-auto">
                                Four question types test both recall and comprehension
                            </p>
                        </div>
                        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
                            {[
                                { type: "Fill-in-Blank", count: "8", desc: "Recall key terms from context", color: "blue" },
                                { type: "Multiple Choice", count: "8", desc: "Identify correct concepts", color: "green" },
                                { type: "True/False", count: "8", desc: "Verify factual understanding", color: "purple" },
                                { type: "Comprehension", count: "5", desc: "Understand relationships", color: "orange" }
                            ].map((quiz, i) => (
                                <div key={i} className="bg-app-card border border-app-border rounded-xl p-6 text-center">
                                    <div className={`text-4xl font-bold text-${quiz.color}-500 mb-2`}>{quiz.count}</div>
                                    <div className="text-sm font-bold uppercase tracking-wider mb-1">{quiz.type}</div>
                                    <div className="text-app-muted text-xs">{quiz.desc}</div>
                                </div>
                            ))}
                        </div>
                        <div className="text-center mt-8">
                            <p className="text-app-muted">Total: <span className="text-blue-500 font-bold">~29 questions</span> per analysis</p>
                        </div>
                    </div>
                </section>
            </main>

            <footer className="py-20 px-8 border-t border-app-border text-app-muted">
                <div className="max-w-[1600px] mx-auto flex flex-col md:flex-row justify-between items-center gap-10">
                    <div className="flex items-center gap-3">
                        <div className="w-6 h-6 bg-app-card rounded flex items-center justify-center">
                            <Brain className="w-4 h-4" />
                        </div>
                        <span className="font-bold text-app-fg">Synod</span>
                    </div>
                    <div className="flex gap-10 text-xs font-bold uppercase tracking-widest">
                        <a href="#" className="hover:text-app-fg transition-colors">Privacy</a>
                        <a href="#" className="hover:text-app-fg transition-colors">Terms</a>
                        <a href="#" className="hover:text-app-fg transition-colors">Contact</a>
                    </div>
                    <p className="text-xs font-medium">© 2026 Synod Systems. Built for precision.</p>
                </div>
            </footer>
        </div>
    );
};

export default LandingPage;
