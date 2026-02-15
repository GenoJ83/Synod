import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Brain, Mail, Lock, User, ChevronRight, Loader2, ArrowLeft, CheckCircle2 } from 'lucide-react';
import { motion } from 'framer-motion';

const Signup = () => {
    const [name, setName] = useState('');
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const navigate = useNavigate();

    const handleSignup = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError('');

        // Simulated signup
        setTimeout(() => {
            if (name && email && password) {
                localStorage.setItem('synod_user', JSON.stringify({ name, email }));
                navigate('/dashboard');
            } else {
                setError('Please fill in all fields correctly.');
            }
            setLoading(false);
        }, 1200);
    };

    return (
        <div className="min-h-screen bg-zinc-950 text-zinc-100 font-sans flex flex-col justify-center items-center px-6 py-12">
            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="w-full max-w-md"
            >
                <div className="text-center mb-10">
                    <div className="inline-flex items-center gap-3 mb-6">
                        <div className="w-8 h-8 bg-zinc-100 rounded-lg flex items-center justify-center">
                            <Brain className="w-5 h-5 text-zinc-950" />
                        </div>
                        <span className="text-xl font-bold tracking-tight">Synod</span>
                    </div>
                    <h1 className="text-3xl font-bold tracking-tight mb-2">Create Account</h1>
                    <p className="text-zinc-500 font-medium">Join thousands of students saving time.</p>
                </div>

                <div className="bg-zinc-900/40 border border-zinc-800 rounded-2xl p-8 shadow-xl">
                    <form onSubmit={handleSignup} className="space-y-6">
                        <div className="space-y-2">
                            <label className="text-xs font-bold text-zinc-500 uppercase tracking-widest px-1">Full Name</label>
                            <div className="relative group">
                                <User className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-600 group-focus-within:text-zinc-100 transition-colors" />
                                <input
                                    type="text"
                                    required
                                    value={name}
                                    onChange={(e) => setName(e.target.value)}
                                    placeholder="Geno Joshua"
                                    className="w-full bg-zinc-950 border border-zinc-800 rounded-xl py-3 pl-12 pr-4 text-sm focus:outline-none focus:border-zinc-600 transition-all font-medium"
                                />
                            </div>
                        </div>

                        <div className="space-y-2">
                            <label className="text-xs font-bold text-zinc-500 uppercase tracking-widest px-1">Email Address</label>
                            <div className="relative group">
                                <Mail className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-600 group-focus-within:text-zinc-100 transition-colors" />
                                <input
                                    type="email"
                                    required
                                    value={email}
                                    onChange={(e) => setEmail(e.target.value)}
                                    placeholder="name@university.edu"
                                    className="w-full bg-zinc-950 border border-zinc-800 rounded-xl py-3 pl-12 pr-4 text-sm focus:outline-none focus:border-zinc-600 transition-all font-medium"
                                />
                            </div>
                        </div>

                        <div className="space-y-2">
                            <label className="text-xs font-bold text-zinc-500 uppercase tracking-widest px-1">Password</label>
                            <div className="relative group">
                                <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-600 group-focus-within:text-zinc-100 transition-colors" />
                                <input
                                    type="password"
                                    required
                                    value={password}
                                    onChange={(e) => setPassword(e.target.value)}
                                    placeholder="Create a strong password"
                                    className="w-full bg-zinc-950 border border-zinc-800 rounded-xl py-3 pl-12 pr-4 text-sm focus:outline-none focus:border-zinc-600 transition-all font-medium"
                                />
                            </div>
                        </div>

                        <div className="bg-zinc-950/50 border border-zinc-800/50 rounded-xl p-4 space-y-3">
                            {[
                                { label: 'Summarize Lectures', active: true },
                                { label: 'Generate Assessments', active: true },
                                { label: 'Organize History', active: true }
                            ].map((item, i) => (
                                <div key={i} className="flex items-center gap-2 text-[10px] font-bold text-zinc-500 uppercase tracking-widest">
                                    <CheckCircle2 className="w-3 h-3 text-emerald-500" />
                                    {item.label}
                                </div>
                            ))}
                        </div>

                        {error && (
                            <div className="p-3 bg-red-950/20 border border-red-900/50 rounded-lg text-red-500 text-xs font-bold text-center">
                                {error}
                            </div>
                        )}

                        <button
                            type="submit"
                            disabled={loading}
                            className="w-full bg-zinc-100 hover:bg-white text-zinc-950 py-4 rounded-xl font-bold text-sm transition-all shadow-sm flex items-center justify-center gap-2 disabled:opacity-50"
                        >
                            {loading ? (
                                <>
                                    <Loader2 className="w-4 h-4 animate-spin" />
                                    Creating Account...
                                </>
                            ) : (
                                <>
                                    Start Learning Free
                                    <ChevronRight className="w-4 h-4" />
                                </>
                            )}
                        </button>
                    </form>

                    <div className="mt-8 pt-8 border-t border-zinc-800/50 text-center">
                        <p className="text-sm text-zinc-500">
                            Already have an account? {' '}
                            <Link to="/login" className="text-zinc-100 font-bold hover:underline">Log in here</Link>
                        </p>
                    </div>
                </div>

                <button
                    onClick={() => navigate('/')}
                    className="mt-8 flex items-center gap-2 text-zinc-600 hover:text-zinc-400 text-sm font-bold transition-colors mx-auto"
                >
                    <ArrowLeft className="w-4 h-4" />
                    Back to landing
                </button>
            </motion.div>
        </div>
    );
};

export default Signup;
