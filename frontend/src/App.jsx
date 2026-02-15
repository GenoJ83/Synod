import React, { useState, useRef } from 'react';
import axios from 'axios';
import { Upload, FileText, BookOpen, Brain, CheckCircle2, ChevronRight, Loader2 } from 'lucide-react';
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';
import QuizSection from './components/QuizSection';

function cn(...inputs) {
  return twMerge(clsx(inputs));
}

const API_BASE_URL = 'http://localhost:8000';

function App() {
  const [text, setText] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');
  const [showQuiz, setShowQuiz] = useState(false);
  const quizRef = useRef(null);

  const handleAnalyze = async () => {
    if (!text) return;
    setLoading(true);
    setResult(null);
    setShowQuiz(false);
    setError('');
    try {
      const response = await axios.post(`${API_BASE_URL}/analyze`, { text });
      setResult(response.data);
    } catch (err) {
      console.error(err);
      setError('Failed to analyze text. Please ensure the backend is running.');
    } finally {
      setLoading(false);
    }
  };

  const startQuiz = () => {
    setShowQuiz(true);
    setTimeout(() => {
      quizRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, 100);
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-200 font-sans selection:bg-blue-500/30">
      {/* Header */}
      <header className="border-b border-slate-800 bg-slate-950/50 backdrop-blur-md sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2 group">
            <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center group-hover:rotate-12 transition-transform duration-300 shadow-[0_0_15px_rgba(37,99,235,0.4)]">
              <Brain className="w-5 h-5 text-white" />
            </div>
            <h1 className="text-xl font-bold tracking-tight bg-gradient-to-r from-white to-slate-400 bg-clip-text text-transparent">Synod</h1>
          </div>
          <nav className="hidden md:flex items-center gap-6">
            <a href="#" className="text-sm font-medium text-slate-400 hover:text-white transition-colors">Documentation</a>
            <a href="#" className="text-sm font-medium text-slate-400 hover:text-white transition-colors" target="_blank">GitHub</a>
          </nav>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-4 py-12">
        {/* Hero Section */}
        <div className="text-center mb-12 animate-in fade-in slide-in-from-bottom-4 duration-1000">
          <h2 className="text-4xl md:text-5xl font-extrabold mb-4 tracking-tight">
            Transform Lectures into <span className="text-blue-500">Knowledge</span>
          </h2>
          <p className="text-slate-400 text-lg max-w-2xl mx-auto">
            Synod uses advanced NLP to summarize course materials, extract key concepts, and generate custom revision quizzes in seconds.
          </p>
        </div>

        {/* Input Area */}
        <div className="bg-slate-900/50 border border-slate-800 rounded-2xl p-6 mb-12 shadow-2xl backdrop-blur-sm">
          <div className="flex items-center gap-2 mb-4">
            <div className="p-2 bg-blue-500/10 rounded-lg text-blue-500">
              <FileText className="w-5 h-5" />
            </div>
            <h3 className="font-semibold text-white">Paste Lecture Content</h3>
          </div>
          <textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder="Paste your lecture notes or text here..."
            className="w-full h-48 bg-slate-950 border border-slate-800 rounded-xl p-4 text-slate-300 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 transition-all resize-none"
          />
          <div className="mt-4 flex justify-end">
            <button
              onClick={handleAnalyze}
              disabled={loading || !text}
              className={cn(
                "px-6 py-2.5 bg-blue-600 hover:bg-blue-500 text-white font-semibold rounded-xl transition-all shadow-lg shadow-blue-600/20 flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed",
                loading && "animate-pulse"
              )}
            >
              {loading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Analyzing...
                </>
              ) : (
                <>
                  Analyze Content
                  <ChevronRight className="w-4 h-4" />
                </>
              )}
            </button>
          </div>
          {error && <p className="mt-4 text-red-400 text-sm text-center">{error}</p>}
        </div>

        {/* Results Section */}
        {result && (
          <div className="space-y-8 animate-in fade-in slide-in-from-bottom-8 duration-700">
            {/* Summary */}
            <div className="bg-slate-900/50 border border-slate-800 rounded-2xl p-8 shadow-xl">
              <div className="flex items-center gap-2 mb-6">
                <div className="p-2 bg-green-500/10 rounded-lg text-green-500">
                  <CheckCircle2 className="w-5 h-5" />
                </div>
                <h3 className="text-xl font-bold text-white">Lecture Summary</h3>
              </div>
              <p className="text-slate-300 leading-relaxed text-lg">
                {result.summary}
              </p>
            </div>

            {/* Concepts Grid */}
            <div className="grid md:grid-cols-2 gap-8">
              <div className="bg-slate-900/50 border border-slate-800 rounded-2xl p-8">
                <div className="flex items-center gap-2 mb-6">
                  <div className="p-2 bg-purple-500/10 rounded-lg text-purple-500">
                    <BookOpen className="w-5 h-5" />
                  </div>
                  <h3 className="text-xl font-bold text-white">Key Concepts</h3>
                </div>
                <div className="flex flex-wrap gap-2">
                  {result.concepts.map((concept, i) => (
                    <span key={i} className="px-3 py-1 bg-slate-800 border border-slate-700 rounded-full text-sm text-slate-300 hover:border-purple-500/50 transition-colors">
                      {concept}
                    </span>
                  ))}
                </div>
              </div>

              {/* Quiz Teaser */}
              <div className="bg-gradient-to-br from-blue-600/10 to-purple-600/10 border border-blue-500/20 rounded-2xl p-8 flex flex-col justify-center items-center text-center">
                <Brain className="w-12 h-12 text-blue-500 mb-4 animate-bounce duration-[3s]" />
                <h3 className="text-xl font-bold text-white mb-2">Quiz Generated!</h3>
                <p className="text-slate-400 text-sm mb-6">Ready to test your knowledge? We've created {result.quiz.mcqs.length + result.quiz.fill_in_the_blanks.length} questions for you.</p>
                <button
                  onClick={startQuiz}
                  className="px-6 py-2 bg-white text-slate-950 font-bold rounded-xl hover:bg-slate-200 transition-colors"
                >
                  Take the Quiz
                </button>
              </div>
            </div>

            {/* Interactive Quiz Section */}
            {showQuiz && (
              <div ref={quizRef} className="pt-12 border-t border-slate-900">
                <QuizSection
                  quiz={result.quiz}
                  onReset={() => {
                    setResult(null);
                    setShowQuiz(false);
                    setText('');
                  }}
                />
              </div>
            )}
          </div>
        )}
      </main>

      <footer className="mt-20 border-t border-slate-900 py-12 text-center text-slate-500 text-sm">
        <p>© 2026 Synod NLP Assistant. Built for smarter learning.</p>
      </footer>
    </div>
  );
}

export default App;
