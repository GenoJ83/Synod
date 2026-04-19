import React from 'react';
import { motion } from 'framer-motion';
import { useNavigate, Link } from 'react-router-dom';
import { Brain, Search, BookOpen, Clock, FileText, ChevronRight, BarChart3, Globe, Sun, Moon } from 'lucide-react';
import { useTheme } from '../context/ThemeContext';
import SEO from '../components/SEO';

const LandingPage = () => {
    const navigate = useNavigate();
    const { theme, toggleTheme } = useTheme();

    return (
        <>
            <SEO 
                title="Synod.ai - Intelligent Lecture Synthesis"
                description="AI-powered lecture analysis. Extract concepts, generate summaries, and test knowledge instantly. Transform your study materials into interactive learning experiences."
                keywords="AI lecture analysis, study tool, concept extraction, PDF summarization, student learning, knowledge graphs, AI tutoring"
                ogTitle="Synod.ai - Intelligent Lecture Synthesis"
                ogDescription="Transform lecture materials into interactive knowledge graphs and quizzes. Get instant summaries and test your understanding."
            />
            <div className="min-h-screen bg-app-bg text-app-fg font-sans selection:bg-blue-500/30 transition-colors duration-300">
            <header className="fixed top-0 w-full z-50 border-b border-app-border bg-app-bg/80 backdrop-blur-md">
                <div className="max-w-[1600px] mx-auto px-8 h-16 flex items-center justify-between">
                    <div className="flex items-center gap-3">
                        <img src="/logo.png" alt="Synod" className="w-10 h-10 rounded-lg" />
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
                                AI-powered lecture analysis. Instant summaries, concept extraction, and knowledge testing.
                            </p>
                            <div className="flex items-center gap-6">
                                <button
                                    onClick={() => navigate('/dashboard')}
                                    className="px-10 py-4 bg-app-fg text-app-bg font-bold rounded-xl hover:opacity-90 transition-all flex items-center gap-2 shadow-2xl"
                                >
                                    Start Analysis
                                    <ChevronRight className="w-4 h-4" />
                                </button>
                            <div className="text-sm font-bold text-app-muted uppercase tracking-wider">
                                Free tier available
                            </div>
                            </div>
                        </motion.div>

                        <motion.div
                            initial={{ opacity: 0, scale: 0.95 }}
                            animate={{ opacity: 1, scale: 1 }}
                            transition={{ duration: 0.8, delay: 0.2 }}
                        >
                            {/* Right side empty for breathing room */}
                            <div className="h-[600px] flex items-center justify-center" />
                        </motion.div>
                    </div>
                </section>

                {/* Features Matrix */}
                <section className="py-32 px-8 bg-app-card/20">
                    <div className="max-w-[1600px] mx-auto">
                        <div className="grid md:grid-cols-4 gap-16">
                            {[
                                { icon: Search, title: "Universal Search", text: "Find anything instantly across all your lecture notes." },
                                { icon: Globe, title: "Multi-Format", text: "PDF, PPTX, TXT. OCR for images." },
                                { icon: Clock, title: "Save Time", text: "60% faster study with AI summaries." },
                                { icon: BookOpen, title: "Knowledge Graphs", text: "Interactive concept maps with explanations." }
                            ].map((f, i) => (
                                <div key={i} className="group">
                                    <div className="w-16 h-16 bg-app-card border border-app-border rounded-xl flex items-center justify-center text-app-muted mb-8 group-hover:bg-app-fg group-hover:text-app-bg transition-all">
                                        <f.icon className="w-8 h-8" />
                                    </div>
                                    <h3 className="text-lg font-bold mb-4">{f.title}</h3>
                                    <p className="text-app-muted leading-relaxed">{f.text}</p>
                                </div>
                            ))}
                        </div>
                    </div>
                </section>

                {/* How It Works */}
                <section id="how-it-works" className="py-32 px-8">
                    <div className="max-w-[1600px] mx-auto">
                        <div className="text-center mb-20">
                            <h2 className="text-5xl font-bold mb-6">How It Works</h2>
                            <p className="text-app-muted text-xl max-w-2xl mx-auto">
                                Four simple steps from upload to mastery
                            </p>
                        </div>
                        <div className="grid md:grid-cols-4 gap-12">
                            {[
                                { step: "01", title: "Upload", text: "PDFs, PPTX, images with OCR.", icon: FileText },
                                { step: "02", title: "Analyze", text: "Extract concepts + summaries.", icon: Brain },
                                { step: "03", title: "Learn", text: "Interactive explanations.", icon: BookOpen },
                                { step: "04", title: "Test", text: "29 questions to verify.", icon: BarChart3 }
                            ].map((item, i) => (
                                <div key={i} className="relative">
                                    <div className="bg-app-card border border-app-border rounded-3xl p-8 h-full hover:shadow-2xl transition-all">
                                        <div className="text-lg font-bold text-blue-500 mb-6">{item.step}</div>
                                        <div className="w-20 h-20 bg-blue-500/10 rounded-2xl flex items-center justify-center text-blue-500 mb-6">
                                            <item.icon className="w-10 h-10" />
                                        </div>
                                        <h3 className="text-2xl font-bold mb-4">{item.title}</h3>
                                        <p className="text-app-muted text-lg">{item.text}</p>
                                    </div>
                                    {i < 3 && (
                                        <div className="hidden md:block absolute top-1/2 -right-6 transform -translate-y-1/2 text-app-muted">
                                            <ChevronRight className="w-6 h-6" />
                                        </div>
                                    )}
                                </div>
                            ))}
                        </div>
                    </div>
                </section>

            </main>

            <footer className="py-20 px-8 border-t border-app-border text-app-muted">
                <div className="max-w-[1600px] mx-auto flex flex-col md:flex-row justify-between items-center gap-10">
                    <div className="flex items-center gap-3">
                        <img src="/logo.png" alt="Synod" className="w-6 h-6 rounded" />
                        <span className="font-bold text-app-fg">Synod</span>
                    </div>
                    <div className="flex gap-10 text-xs font-bold uppercase tracking-widest">
                        <a href="#" className="hover:text-app-fg transition-colors">Privacy</a>
                        <a href="#" className="hover:text-app-fg transition-colors">Terms</a>
                        <a href="#" className="hover:text-app-fg transition-colors">Contact</a>
                    </div>
                    <p className="text-xs font-medium">© 2026 Synod Systems. All rights reserved.</p>
                </div>
            </footer>
        </div>
        </>
    );
};

export default LandingPage;
