import React from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Brain, BookOpen, FileText, BarChart3, ArrowLeft, Link2, Shield, Mail } from 'lucide-react';
import SEO from '../components/SEO';

const Documentation = () => {
    const navigate = useNavigate();

    const sections = [
        {
            title: "Getting Started",
            icon: BookOpen,
            items: [
                { text: "Creating an account", link: "#" },
                { text: "Logging in", link: "#" },
                { text: "Dashboard overview", link: "#" }
            ]
        },
        {
            title: "Content Analysis",
            icon: FileText,
            items: [
                { text: "Pasting lecture text", link: "#" },
                { text: "Uploading files", link: "#" },
                { text: "Understanding summaries", link: "#" }
            ]
        },
        {
            title: "Concepts & Explanations",
            icon: Brain,
            items: [
                { text: "Viewing extracted concepts", link: "#" },
                { text: "Reading explanations", link: "#" },
                { text: "Exploring related concepts", link: "#" }
            ]
        },
        {
            title: "Quiz System",
            icon: BarChart3,
            items: [
                { text: "Starting a quiz", link: "#" },
                { text: "Question types explained", link: "#" },
                { text: "Viewing results", link: "#" }
            ]
        }
    ];

    return (
        <>
            <SEO 
                title="Documentation - Synod.ai"
                description="Complete documentation for Synod.ai. Learn how to use AI-powered lecture analysis, extract concepts, generate summaries, and create interactive quizzes."
                keywords="documentation, help, guide, tutorial, how to use"
                ogTitle="Documentation - Synod.ai"
                ogDescription="Complete guide to using Synod.ai's AI-powered lecture analysis platform."
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
                        onClick={() => navigate('/how-it-works')}
                        className="px-5 py-2 text-sm font-bold text-app-muted hover:text-app-fg transition-colors mr-4"
                    >
                        How It Works
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
                    <h1 className="text-5xl font-bold mb-4">Documentation</h1>
                    <p className="text-app-muted text-xl max-w-2xl mx-auto">
                        Everything you need to know about using Lecture Assistant
                    </p>
                </div>

                <div className="grid md:grid-cols-2 gap-8 mb-16">
                    {sections.map((section, i) => (
                        <div key={i} className="bg-app-card border border-app-border rounded-2xl p-8">
                            <div className="flex items-center gap-3 mb-6">
                                <div className="w-10 h-10 bg-blue-500/10 rounded-lg flex items-center justify-center text-blue-500">
                                    <section.icon className="w-5 h-5" />
                                </div>
                                <h2 className="text-xl font-bold">{section.title}</h2>
                            </div>
                            <ul className="space-y-3">
                                {section.items.map((item, j) => (
                                    <li key={j}>
                                        <a href={item.link} className="flex items-center gap-2 text-app-muted hover:text-app-fg transition-colors">
                                            <Link2 className="w-4 h-4" />
                                            {item.text}
                                        </a>
                                    </li>
                                ))}
                            </ul>
                        </div>
                    ))}
                </div>

                {/* FAQ Section */}
                <div className="mb-16">
                    <h2 className="text-3xl font-bold text-center mb-8">Frequently Asked Questions</h2>
                    <div className="space-y-4">
                        {[
                            {
                                q: "Is my data secure?",
                                a: "Yes! We use industry-standard encryption and never share your data. Your lecture content is stored locally in your browser."
                            },
                            {
                                q: "How many questions does each quiz have?",
                                a: "Each quiz generates approximately 29 questions across 4 different question types to thoroughly test your understanding."
                            },
                            {
                                q: "What file formats are supported?",
                                a: "We support PDF, DOCX, and TXT files for upload, plus you can paste text directly."
                            },
                            {
                                q: "Is this free for students?",
                                a: "Yes! Lecture Assistant is completely free for students."
                            }
                        ].map((faq, i) => (
                            <div key={i} className="bg-app-card border border-app-border rounded-xl p-6">
                                <h3 className="font-bold mb-2">{faq.q}</h3>
                                <p className="text-app-muted text-sm">{faq.a}</p>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Contact */}
                <div className="bg-app-card border border-app-border rounded-2xl p-8 text-center">
                    <div className="w-12 h-12 bg-blue-500/10 rounded-xl flex items-center justify-center text-blue-500 mx-auto mb-4">
                        <Mail className="w-6 h-6" />
                    </div>
                    <h2 className="text-2xl font-bold mb-2">Need Help?</h2>
                    <p className="text-app-muted mb-4">Have questions or feedback? We'd love to hear from you.</p>
                    <a href="mailto:support@synod.ai" className="inline-flex items-center gap-2 text-blue-500 hover:underline">
                        Contact Support <Mail className="w-4 h-4" />
                    </a>
                </div>
            </main>
            </div>
        </>
    );
};

export default Documentation;
