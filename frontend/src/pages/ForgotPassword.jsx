import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { Brain, Mail, ArrowLeft, ChevronRight, Loader2, CheckCircle2 } from 'lucide-react';
import { useTheme } from '../context/ThemeContext';

const ForgotPassword = () => {
    const [email, setEmail] = useState('');
    const [loading, setLoading] = useState(false);
    const [submitted, setSubmitted] = useState(false);
    const navigate = useNavigate();
    const { toggleTheme, theme } = useTheme();

    const handleReset = async (e) => {
        e.preventDefault();
        setLoading(true);
        // Simulate email sending
        await new Promise(resolve => setTimeout(resolve, 2000));
        setLoading(false);
        setSubmitted(true);
    };

    return (
        <div className="min-h-screen bg-app-bg text-app-fg font-sans selection:bg-blue-500/30 transition-colors duration-300 flex flex-col items-center justify-center p-6 relative overflow-hidden">
            {/* Background Decoration */}
            <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-blue-500/10 blur-[120px] rounded-full pointer-events-none" />

            {/* Header / Nav */}
            <div className="absolute top-8 left-8 right-8 flex justify-between items-center max-w-[1600px] mx-auto w-full">
                <button
                    onClick={() => navigate('/login')}
                    className="flex items-center gap-2 text-app-muted hover:text-app-fg transition-colors group"
                >
                    <ArrowLeft className="w-4 h-4 group-hover:-translate-x-1 transition-transform" />
                    <span className="text-sm font-bold uppercase tracking-widest">Back to Login</span>
                </button>
            </div>

            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="w-full max-w-md relative z-10"
            >
                <div className="flex flex-col items-center mb-10">
                    <div className="w-16 h-16 bg-app-fg rounded-[2rem] flex items-center justify-center mb-6 shadow-2xl">
                        <Brain className="w-8 h-8 text-app-bg" />
                    </div>
                    <h1 className="text-3xl font-bold tracking-tight mb-2">Recover Account</h1>
                    <p className="text-app-muted text-center font-medium">We'll send you a link to reset your password.</p>
                </div>

                <div className="pro-card p-8 bg-app-bg/40 backdrop-blur-xl border border-app-border">
                    <AnimatePresence mode="wait">
                        {!submitted ? (
                            <motion.form
                                key="form"
                                initial={{ opacity: 0, x: -20 }}
                                animate={{ opacity: 1, x: 0 }}
                                exit={{ opacity: 0, x: 20 }}
                                onSubmit={handleReset}
                                className="space-y-6"
                            >
                                <div className="space-y-2">
                                    <label className="text-[10px] font-bold text-app-muted uppercase tracking-widest ml-1">Email Address</label>
                                    <div className="relative group">
                                        <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-app-muted group-focus-within:text-blue-500 transition-colors" />
                                        <input
                                            type="email"
                                            required
                                            value={email}
                                            onChange={(e) => setEmail(e.target.value)}
                                            placeholder="name@university.edu"
                                            className="w-full pl-10 pr-4 py-3 pro-input text-sm"
                                        />
                                    </div>
                                </div>

                                <button
                                    type="submit"
                                    disabled={loading}
                                    className="w-full bg-app-fg text-app-bg py-4 rounded-xl font-bold text-sm hover:opacity-90 active:scale-[0.98] transition-all flex items-center justify-center gap-2 group shadow-xl"
                                >
                                    {loading ? (
                                        <Loader2 className="w-4 h-4 animate-spin" />
                                    ) : (
                                        <>
                                            Send Reset Link
                                            <ChevronRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
                                        </>
                                    )}
                                </button>
                            </motion.form>
                        ) : (
                            <motion.div
                                key="success"
                                initial={{ opacity: 0, scale: 0.95 }}
                                animate={{ opacity: 1, scale: 1 }}
                                className="text-center py-4"
                            >
                                <div className="w-12 h-12 bg-emerald-500/10 text-emerald-500 rounded-full flex items-center justify-center mx-auto mb-4">
                                    <CheckCircle2 className="w-6 h-6" />
                                </div>
                                <h3 className="text-lg font-bold mb-2">Link Sent</h3>
                                <p className="text-app-muted text-sm mb-8">Please check <strong>{email}</strong> for instructions to reset your password.</p>
                                <button
                                    onClick={() => navigate('/login')}
                                    className="w-full bg-app-bg border border-app-border text-app-fg py-4 rounded-xl font-bold text-sm hover:bg-app-card transition-colors"
                                >
                                    Return to Login
                                </button>
                            </motion.div>
                        )}
                    </AnimatePresence>
                </div>

                <p className="mt-8 text-center text-app-muted text-xs font-medium">
                    Did you remember your password? <br />
                    <button onClick={() => navigate('/login')} className="text-app-fg font-bold hover:underline">Log in here</button>
                </p>
            </motion.div>
        </div>
    );
};

export default ForgotPassword;
