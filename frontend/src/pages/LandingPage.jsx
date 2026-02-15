import React from 'react';
import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { Brain, Sparkles, Zap, Shield, ChevronRight, Layout, MessageSquare, BookOpen } from 'lucide-react';

const FeatureCard = ({ icon: Icon, title, description, delay }) => (
    <motion.div
        initial={{ opacity: 0, y: 20 }}
        whileInView={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay }}
        viewport={{ once: true }}
        className="p-8 bg-slate-900/50 border border-slate-800 rounded-3xl hover:border-blue-500/50 transition-all group backdrop-blur-sm"
    >
        <div className="w-12 h-12 bg-blue-500/10 rounded-2xl flex items-center justify-center text-blue-500 mb-6 group-hover:scale-110 transition-transform">
            <Icon className="w-6 h-6" />
        </div>
        <h3 className="text-xl font-bold text-white mb-3">{title}</h3>
        <p className="text-slate-400 leading-relaxed">{description}</p>
    </motion.div>
);

const LandingPage = () => {
    const navigate = useNavigate();

    return (
        <div className="min-h-screen bg-slate-950 text-slate-200 selection:bg-blue-500/30 overflow-hidden">
            {/* Decorative Background Elements */}
            <div className="absolute top-0 left-0 w-full h-full overflow-hidden pointer-events-none z-0">
                <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-blue-600/10 rounded-full blur-[120px]" />
                <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] bg-purple-600/10 rounded-full blur-[120px]" />
            </div>

            <header className="fixed top-0 w-full z-50 border-b border-white/5 bg-slate-950/80 backdrop-blur-md">
                <div className="max-w-7xl mx-auto px-6 h-20 flex items-center justify-between">
                    <div className="flex items-center gap-3">
                        <div className="w-10 h-10 bg-blue-600 rounded-xl flex items-center justify-center shadow-[0_0_20px_rgba(37,99,235,0.4)]">
                            <Brain className="w-6 h-6 text-white" />
                        </div>
                        <span className="text-2xl font-black tracking-tighter bg-gradient-to-r from-white to-slate-400 bg-clip-text text-transparent">SYNOD</span>
                    </div>
                    <button
                        onClick={() => navigate('/dashboard')}
                        className="px-6 py-2.5 bg-white text-slate-950 font-bold rounded-full hover:bg-slate-200 transition-all transform hover:scale-105"
                    >
                        Launch App
                    </button>
                </div>
            </header>

            <main className="relative z-10">
                {/* Hero Section */}
                <section className="pt-40 pb-20 px-6">
                    <div className="max-w-7xl mx-auto text-center">
                        <motion.div
                            initial={{ opacity: 0, y: 30 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ duration: 0.8 }}
                        >
                            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-blue-500/10 border border-blue-500/20 text-blue-400 text-sm font-semibold mb-8">
                                <Sparkles className="w-4 h-4" />
                                <span>Next Generation Learning</span>
                            </div>
                            <h1 className="text-6xl md:text-8xl font-black mb-8 tracking-tighter leading-[0.9]">
                                Master Your Lectures <br />
                                <span className="bg-gradient-to-r from-blue-400 via-purple-400 to-blue-400 bg-clip-text text-transparent bg-[length:200%_auto] animate-gradient">With AI Precision.</span>
                            </h1>
                            <p className="text-slate-400 text-xl md:text-2xl max-w-3xl mx-auto mb-12 leading-relaxed">
                                Synod transforms complex lecture notes and documents into concise summaries, key concepts, and interactive quizzes in seconds.
                            </p>
                            <div className="flex flex-col sm:flex-row items-center justify-center gap-6">
                                <button
                                    onClick={() => navigate('/dashboard')}
                                    className="w-full sm:w-auto px-10 py-5 bg-blue-600 hover:bg-blue-500 text-white text-lg font-bold rounded-2xl transition-all shadow-[0_20px_40px_-15px_rgba(37,99,235,0.4)] flex items-center justify-center gap-2 group"
                                >
                                    Start Learning Now
                                    <ChevronRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
                                </button>
                                <button className="w-full sm:w-auto px-10 py-5 bg-slate-900 border border-slate-800 text-white text-lg font-bold rounded-2xl hover:bg-slate-800 transition-all">
                                    Watch Demo
                                </button>
                            </div>
                        </motion.div>
                    </div>
                </section>

                {/* Features Section */}
                <section className="py-32 px-6">
                    <div className="max-w-7xl mx-auto">
                        <div className="text-center mb-20">
                            <h2 className="text-4xl md:text-5xl font-bold mb-6 tracking-tight text-white">Everything you need to excel.</h2>
                            <p className="text-slate-400 text-lg">Designed for students who value speed and clarity.</p>
                        </div>
                        <div className="grid md:grid-cols-3 gap-8">
                            <FeatureCard
                                icon={Zap}
                                title="Instant Summarization"
                                description="Our AI boils down hours of lectures into the essentials, saving you precious study time."
                                delay={0.1}
                            />
                            <FeatureCard
                                icon={Layout}
                                title="Smart Concept Mapping"
                                description="Automatically extract and link key definitions and concepts for better retention."
                                delay={0.2}
                            />
                            <FeatureCard
                                icon={MessageSquare}
                                title="Interactive Quizzes"
                                description="Test your knowledge with custom MCQs and fill-in-the-blanks generated from your content."
                                delay={0.3}
                            />
                            <FeatureCard
                                icon={Shield}
                                title="Secure & Private"
                                description="Your documents are processed securely and stay under your control."
                                delay={0.4}
                            />
                            <FeatureCard
                                icon={BookOpen}
                                title="Multi-format Support"
                                description="Upload PDFs, PowerPoints, or plain text. We handle it all seamlessly."
                                delay={0.5}
                            />
                            <FeatureCard
                                icon={Brain}
                                title="Deep Learning"
                                description="Powered by state-of-the-art NLP models optimized for educational content."
                                delay={0.6}
                            />
                        </div>
                    </div>
                </section>
            </main>

            <footer className="border-t border-white/5 py-20 px-6">
                <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-10">
                    <div className="flex items-center gap-3">
                        <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
                            <Brain className="w-5 h-5 text-white" />
                        </div>
                        <span className="text-xl font-black tracking-tighter text-white">SYNOD</span>
                    </div>
                    <div className="flex gap-8 text-slate-500 text-sm">
                        <a href="#" className="hover:text-white transition-colors">Documentation</a>
                        <a href="#" className="hover:text-white transition-colors">Privacy Policy</a>
                        <a href="#" className="hover:text-white transition-colors">Terms of Service</a>
                    </div>
                    <p className="text-slate-500 text-sm">© 2026 Synod. Elevating the study experience.</p>
                </div>
            </footer>
        </div>
    );
};

export default LandingPage;
