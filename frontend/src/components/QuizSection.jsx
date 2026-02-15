import React, { useState } from 'react';
import { CheckCircle2, XCircle, ChevronRight, HelpCircle, RotateCcw } from 'lucide-react';

const QuizSection = ({ quiz, onReset }) => {
    const [currentStep, setCurrentStep] = useState(0); // 0: intro, 1: mcqs, 2: fibs, 3: result
    const [mcqIndex, setMcqIndex] = useState(0);
    const [fibIndex, setFibIndex] = useState(0);
    const [score, setScore] = useState(0);
    const [selectedOption, setSelectedOption] = useState(null);
    const [fibAnswer, setFibAnswer] = useState('');
    const [showFeedback, setShowFeedback] = useState(false);
    const [isCorrect, setIsCorrect] = useState(false);

    const mcqs = quiz.mcqs || [];
    const fibs = quiz.fill_in_the_blanks || [];
    const totalQuestions = mcqs.length + fibs.length;

    const handleMcqSubmit = (option) => {
        if (showFeedback) return;
        setSelectedOption(option);
        const correct = option === mcqs[mcqIndex].answer;
        setIsCorrect(correct);
        if (correct) setScore(score + 1);
        setShowFeedback(true);
    };

    const nextQuestion = () => {
        setShowFeedback(false);
        setSelectedOption(null);
        setFibAnswer('');

        if (currentStep === 1) {
            if (mcqIndex < mcqs.length - 1) {
                setMcqIndex(mcqIndex + 1);
            } else if (fibs.length > 0) {
                setCurrentStep(2);
            } else {
                setCurrentStep(3);
            }
        } else if (currentStep === 2) {
            if (fibIndex < fibs.length - 1) {
                setFibIndex(fibIndex + 1);
            } else {
                setCurrentStep(3);
            }
        }
    };

    const handleFibSubmit = () => {
        if (showFeedback) return;
        const correct = fibAnswer.toLowerCase().trim() === fibs[fibIndex].answer.toLowerCase().trim();
        setIsCorrect(correct);
        if (correct) setScore(score + 1);
        setShowFeedback(true);
    };

    if (currentStep === 0) {
        return (
            <div className="bg-slate-900 border border-slate-800 rounded-3xl p-10 text-center shadow-2xl animate-in zoom-in duration-500">
                <HelpCircle className="w-16 h-16 text-blue-500 mx-auto mb-6 opacity-50" />
                <h3 className="text-3xl font-bold text-white mb-4">Ready for the Challenge?</h3>
                <p className="text-slate-400 mb-8 max-w-md mx-auto">We've generated {totalQuestions} questions based on your lecture. Multiple choice and fill-in-the-blanks await!</p>
                <button
                    onClick={() => setCurrentStep(mcqs.length > 0 ? 1 : 2)}
                    className="px-8 py-3 bg-blue-600 hover:bg-blue-500 text-white font-bold rounded-2xl transition-all shadow-lg shadow-blue-600/30"
                >
                    Start Quiz
                </button>
            </div>
        );
    }

    if (currentStep === 3) {
        return (
            <div className="bg-slate-900 border border-slate-800 rounded-3xl p-10 text-center shadow-2xl">
                <div className="relative w-32 h-32 mx-auto mb-6">
                    <div className="absolute inset-0 rounded-full border-4 border-slate-800"></div>
                    <div
                        className="absolute inset-0 rounded-full border-4 border-blue-500 shadow-[0_0_15px_rgba(59,130,246,0.5)]"
                        style={{ clipPath: `inset(0 0 ${100 - (score / totalQuestions) * 100}% 0)` }}
                    ></div>
                    <div className="absolute inset-0 flex items-center justify-center text-3xl font-bold text-white">
                        {Math.round((score / totalQuestions) * 100)}%
                    </div>
                </div>
                <h3 className="text-2xl font-bold text-white mb-2">Quiz Complete!</h3>
                <p className="text-slate-400 mb-8">You scored {score} out of {totalQuestions} correct.</p>
                <div className="flex gap-4 justify-center">
                    <button
                        onClick={onReset}
                        className="px-6 py-2 bg-slate-800 hover:bg-slate-700 text-white font-bold rounded-xl transition-all flex items-center gap-2"
                    >
                        <RotateCcw className="w-4 h-4" /> Reset
                    </button>
                    <button
                        className="px-6 py-2 bg-blue-600 hover:bg-blue-500 text-white font-bold rounded-xl transition-all"
                        onClick={() => {
                            setCurrentStep(0);
                            setScore(0);
                            setMcqIndex(0);
                            setFibIndex(0);
                        }}
                    >
                        Try Again
                    </button>
                </div>
            </div>
        );
    }

    const currentQuestion = currentStep === 1 ? mcqs[mcqIndex] : fibs[fibIndex];

    return (
        <div className="bg-slate-900 border border-slate-800 rounded-3xl p-8 md:p-10 shadow-2xl relative overflow-hidden">
            {/* Progress Bar */}
            <div className="absolute top-0 left-0 w-full h-1 bg-slate-800">
                <div
                    className="h-full bg-blue-500 transition-all duration-500"
                    style={{ width: `${((mcqIndex + (currentStep === 2 ? mcqs.length : 0) + fibIndex) / totalQuestions) * 100}%` }}
                ></div>
            </div>

            <div className="flex justify-between items-center mb-8">
                <span className="text-sm font-bold text-slate-500 uppercase tracking-widest">Question {mcqIndex + (currentStep === 2 ? mcqs.length : 0) + fibIndex + 1} of {totalQuestions}</span>
                <span className="px-3 py-1 bg-blue-500/10 text-blue-500 text-xs font-bold rounded-full border border-blue-500/20">
                    {currentStep === 1 ? 'Multiple Choice' : 'Fill in the Blank'}
                </span>
            </div>

            <h4 className="text-xl md:text-2xl font-semibold text-white mb-8 leading-relaxed">
                {currentQuestion.question}
            </h4>

            {currentStep === 1 ? (
                <div className="grid gap-3">
                    {currentQuestion.options.map((option, i) => (
                        <button
                            key={i}
                            onClick={() => handleMcqSubmit(option)}
                            className={`p-4 rounded-2xl border text-left transition-all ${selectedOption === option
                                    ? isCorrect
                                        ? 'bg-green-500/10 border-green-500 text-green-500'
                                        : 'bg-red-500/10 border-red-500 text-red-500'
                                    : showFeedback && option === currentQuestion.answer
                                        ? 'bg-green-500/10 border-green-500 text-green-500'
                                        : 'bg-slate-950 border-slate-800 text-slate-400 hover:border-slate-700 hover:bg-slate-900/50'
                                }`}
                            disabled={showFeedback}
                        >
                            <div className="flex items-center justify-between">
                                <span>{option}</span>
                                {showFeedback && option === currentQuestion.answer && <CheckCircle2 className="w-5 h-5" />}
                                {showFeedback && selectedOption === option && !isCorrect && <XCircle className="w-5 h-5" />}
                            </div>
                        </button>
                    ))}
                </div>
            ) : (
                <div className="space-y-4">
                    <input
                        type="text"
                        value={fibAnswer}
                        onChange={(e) => setFibAnswer(e.target.value)}
                        onKeyDown={(e) => e.key === 'Enter' && handleFibSubmit()}
                        placeholder="Type your answer..."
                        className={`w-full p-4 rounded-2xl bg-slate-950 border transition-all outline-none ${showFeedback
                                ? isCorrect ? 'border-green-500 text-green-500' : 'border-red-500 text-red-500'
                                : 'border-slate-800 text-slate-300 focus:border-blue-500'
                            }`}
                        disabled={showFeedback}
                    />
                    {!showFeedback && (
                        <button
                            onClick={handleFibSubmit}
                            className="w-full py-3 bg-blue-600 hover:bg-blue-500 text-white font-bold rounded-2xl"
                        >
                            Submit Answer
                        </button>
                    )}
                </div>
            )}

            {showFeedback && (
                <div className="mt-8 animate-in slide-in-from-top-4 duration-300">
                    <div className={`p-4 rounded-2xl border flex items-center justify-between ${isCorrect ? 'bg-green-500/10 border-green-500/50 text-green-400' : 'bg-red-500/10 border-red-500/50 text-red-400'}`}>
                        <div className="flex items-center gap-3">
                            {isCorrect ? <CheckCircle2 className="w-5 h-5" /> : <XCircle className="w-5 h-5" />}
                            <span className="font-bold">{isCorrect ? 'Impressive! Correct.' : `Incorrect. The answer is ${currentQuestion.answer}.`}</span>
                        </div>
                        <button
                            onClick={nextQuestion}
                            className="p-2 hover:bg-white/10 rounded-lg transition-colors"
                        >
                            <ChevronRight className="w-6 h-6" />
                        </button>
                    </div>
                </div>
            )}
        </div>
    );
};

export default QuizSection;
