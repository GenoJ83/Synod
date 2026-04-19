import React from 'react';
import { motion } from 'framer-motion';
import { useNavigate, Link } from 'react-router-dom';
import { Brain, Search, BookOpen, Clock, FileText, ChevronRight, BarChart3, ArrowLeft, CheckCircle2 } from 'lucide-react';
import { useTheme } from '../context/ThemeContext';
import SEO from '../components/SEO';

const HowItWorks = () => {
    const navigate = useNavigate();
    const { theme, toggleTheme } = useTheme();

    const steps = [
        {
            step: "01",
            title: "Upload Content",
            description: "Paste your lecture text directly or upload files in PDF, DOCX, or TXT format. Our system accepts various input methods to analyze your study materials.",
            icon: FileText,
            details: ["Paste text directly", "Upload PDF files", "Upload DOCX files", "Upload TXT files"]
        },
        {
            step: "02",
            title: "AI Analysis",
            description: "Our NLP pipeline processes your content using state-of-the-art models. It extracts key concepts, generates summaries, and prepares quiz questions from the full text.",
            icon: Brain,
            details: ["Summarizes content", "Extracts key concepts", "Generates explanations", "Creates quiz questions"]
        },
        {
            step: "03",
            title: "Learn Concepts",
            description: "Browse the extracted foundational concepts. Click on any concept to see its educational definition and how it's discussed in your specific lecture content.",
            icon: BookOpen,
            details: ["View all concepts", "Click for explanations", "See related concepts", "Track learning progress"]
        },
        {
            step: "04",
            title: "Test Knowledge",
            description: "Take the interactive quiz to verify your understanding. Questions test both recall and comprehension across multiple question types.",
            icon: BarChart3,
            details: ["~29 questions", "4 question types", "Instant feedback", "Score tracking"]
        }
    ];

    const quizTypes = [
        { type: "Fill-in-the-Blank", count: 8, desc: "Recall key terms from context" },
        { type: "Multiple Choice", count: 8, desc: "Identify correct concepts" },
        { type: "True/False", count: 8, desc: "Verify factual understanding" },
        { type: "Comprehension", count: 5, desc: "Understand relationships" }
    ];

    return (
        <>
            <SEO 
                title="How It Works - Synod.ai"
                description="Learn how Synod.ai transforms lecture materials into interactive learning experiences. Upload, analyze, learn concepts, and test your knowledge in 4 simple steps."
                keywords="how it works, tutorial, lecture analysis, AI learning, study guide"
                ogTitle="How It Works - Synod.ai"
                ogDescription="Transform lecture materials into interactive knowledge graphs and quizzes in 4 simple steps."
            />
            <div className="min-h-screen bg-app-bg text-app-fg font-sans">
            <header className="h-16 border-b border-app-border bg-app-bg/80 backdrop-blur-md sticky top-0 z-50">
                <div className="max-w-[1600px] mx-auto px-8 h-full flex items-center justify-between">
                    <div className="flex items-center gap-6">
                        <button
                            onClick={() => navigate('/')}
                            className="p-2 -ml-2 text-app-muted hover:text-app-fg hover:bg-app-card rounded-lg transition-colors"
                        >
                            <ArrowLeft className="w-5 h-5" />
                        </button>
                        <div className="flex items-center gap-3">
                            <div className="w-8 h-8 bg-app-fg rounded flex items-center justify-center">
                                <Brain className="w-5 h-5 text-app-bg" />
                            </div>
                            <span className="text-xl font-bold tracking-tight">Synod</span>
                        </div>
                    </div>
                    <button
                        onClick={() => navigate('/documentation')}
                        className="px-5 py-2 text-sm font-bold text-app-muted hover:text-app-fg transition-colors mr-4"
                    >
                        Documentation
                    </button>
                    <button
                        onClick={() => navigate('/dashboard')}
                        className="px-5 py-2 bg-app-fg text-app-bg text-sm font-bold rounded-lg hover:opacity-90 transition-all"
                    >
                        Get Started
                    </button>
                </div>
            </header>

            <main className="max-w-[1200px] mx-auto px-8 py-16">
                <div className="text-center mb-16">
                    <h1 className="text-5xl font-bold mb-4">How It Works</h1>
                    <p className="text-app-muted text-xl max-w-2xl mx-auto">
                        A complete guide to using Lecture Assistant for your studies
                    </p>
                </div>

                {/* Steps */}
                <div className="space-y-8 mb-20">
                    {steps.map((step, i) => (
                        <motion.div
                            key={i}
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: i * 0.1 }}
                            className="bg-app-card border border-app-border rounded-2xl p-8"
                        >
                            <div className="flex flex-col md:flex-row gap-8">
                                <div className="flex-shrink-0">
                                    <div className="w-16 h-16 bg-blue-500/10 rounded-2xl flex items-center justify-center text-blue-500 mb-4">
                                        <step.icon className="w-8 h-8" />
                                    </div>
                                    <div className="text-[10px] font-bold text-blue-500">{step.step}</div>
                                </div>
                                <div className="flex-1">
                                    <h2 className="text-2xl font-bold mb-3">{step.title}</h2>
                                    <p className="text-app-muted text-lg mb-4">{step.description}</p>
                                    <div className="grid grid-cols-2 gap-3">
                                        {step.details.map((detail, j) => (
                                            <div key={j} className="flex items-center gap-2 text-sm text-app-muted">
                                                <CheckCircle2 className="w-4 h-4 text-green-500" />
                                                {detail}
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            </div>
                        </motion.div>
                    ))}
                </div>

                {/* Quiz Types */}
                <div className="mb-16">
                    <h2 className="text-3xl font-bold text-center mb-8">Quiz Question Types</h2>
                    <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
                        {quizTypes.map((quiz, i) => (
                            <div key={i} className="bg-app-card border border-app-border rounded-xl p-6 text-center">
                                <div className="text-3xl font-bold text-blue-500 mb-2">{quiz.count}</div>
                                <div className="text-sm font-bold uppercase tracking-wider mb-1">{quiz.type}</div>
                                <div className="text-app-muted text-xs">{quiz.desc}</div>
                            </div>
                        ))}
                    </div>
                    <p className="text-center mt-6 text-app-muted">
                        Total: <span className="text-blue-500 font-bold">~29 questions</span> per analysis
                    </p>
                </div>

                {/* CTA */}
                <div className="text-center">
                    <button
                        onClick={() => navigate('/dashboard')}
                        className="px-8 py-4 bg-app-fg text-app-bg font-bold rounded-xl hover:opacity-90 transition-all flex items-center gap-2 mx-auto"
                    >
                        Try It Now
                        <ChevronRight className="w-4 h-4" />
                    </button>
                </div>
            </main>
            </div>
        </>
    );
};

export default HowItWorks;
