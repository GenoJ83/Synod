import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
    CheckCircle2, AlertCircle, ChevronRight,
    HelpCircle, Trophy, RefreshCw
} from 'lucide-react';

const QuizSection = ({ quiz }) => {
    const [currentQuestion, setCurrentQuestion] = useState(0);
    const [selectedAnswer, setSelectedAnswer] = useState(null);
    const [showResults, setShowResults] = useState(false);
    const [score, setScore] = useState(0);
    const [answeredTotal, setAnsweredTotal] = useState(0);

    const shuffleInPlace = (arr) => {
        for (let i = arr.length - 1; i > 0; i--) {
            const j = Math.floor(Math.random() * (i + 1));
            [arr[i], arr[j]] = [arr[j], arr[i]];
        }
        return arr;
    };

    /** Round-robin across types so the deck mixes MCQ, blanks, T/F, and comprehension. */
    const interleaveByType = (mcqQ, fibQ, tfQ, compQ) => {
        const pools = [mcqQ, fibQ, tfQ, compQ].map((p) => [...p]);
        const out = [];
        let guard = 0;
        const max = mcqQ.length + fibQ.length + tfQ.length + compQ.length + 10;
        while (pools.some((p) => p.length > 0) && guard < max) {
            for (const pool of pools) {
                if (pool.length > 0) out.push(pool.shift());
            }
            guard += 1;
        }
        return shuffleInPlace(out);
    };

    // Combine all question types into a single quiz array
    const quizData = React.useMemo(() => {
        if (!quiz) return [];
        const mcqs = quiz.mcqs || [];
        const fibs = quiz.fill_in_the_blanks || [];
        const trueFalse = quiz.true_false || [];
        const comprehension = quiz.comprehension || [];

        const mcqQuestions = mcqs.map((q) => {
            const opts = q.options || [];
            let idx = q.answer != null ? opts.indexOf(q.answer) : 0;
            if (idx < 0) idx = 0;
            return {
                question: q.question,
                options: opts,
                correct: idx,
                type: 'mcq'
            };
        });

        const fibQuestions = fibs.map((q) => {
            const opts = q.options && q.options.length >= 2 ? q.options : [q.answer].filter(Boolean);
            let idx = q.answer != null ? opts.indexOf(q.answer) : 0;
            if (idx < 0) idx = 0;
            return {
                question: q.question,
                options: opts,
                correct: idx,
                type: 'fib',
                explanation: q.explanation
            };
        });

        const tfQuestions = trueFalse.map((q) => ({
            question: q.question,
            options: ['True', 'False'],
            correct: q.correct ? 0 : 1,
            type: 'true_false',
            explanation: q.explanation
        }));

        const compQuestions = comprehension.map((q) => ({
            question: q.question,
            options: q.options || [],
            correct: q.answer != null ? q.answer : 0,
            type: 'comprehension',
            explanation: q.explanation
        }));

        return interleaveByType(mcqQuestions, fibQuestions, tfQuestions, compQuestions);
    }, [quiz]);

    const [shuffledQuestions, setShuffledQuestions] = React.useState(null);
    React.useEffect(() => {
        setShuffledQuestions(null);
    }, [quiz]);
    React.useEffect(() => {
        if (quizData.length > 0 && !shuffledQuestions) {
            setShuffledQuestions(shuffleInPlace([...quizData]));
        }
    }, [quizData, shuffledQuestions]);
    
    const displayQuestions = shuffledQuestions || quizData;

    const handleAnswer = (index) => {
        if (selectedAnswer !== null) return;
        setSelectedAnswer(index);
        setAnsweredTotal(prev => prev + 1);

        if (index === displayQuestions[currentQuestion].correct) {
            setScore(prev => prev + 1);
        }
    };

    const nextQuestion = () => {
        if (currentQuestion < displayQuestions.length - 1) {
            setCurrentQuestion(prev => prev + 1);
            setSelectedAnswer(null);
        } else {
            setShowResults(true);
        }
    };

    const resetQuiz = () => {
        setCurrentQuestion(0);
        setSelectedAnswer(null);
        setShowResults(false);
        setScore(0);
        setAnsweredTotal(0);
    };

    const endQuizEarly = () => {
        setShowResults(true);
    };

    const downloadReport = () => {
        const content = `Synod Analysis Assessment Report\n================================\nScore: ${score} / ${answeredTotal || displayQuestions.length} (${Math.round((score / Math.max(1, answeredTotal || displayQuestions.length)) * 100)}%)\n\nThank you for using Synod!`;
        const blob = new Blob([content], { type: 'text/plain;charset=utf-8' });
        const link = document.createElement('a');
        link.href = URL.createObjectURL(blob);
        link.download = `synod_assessment_report_${Date.now()}.txt`;
        link.click();
    };

    if (showResults) {
        return (
            <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                className="pro-card p-12 text-center"
            >
                <div className="w-20 h-20 bg-blue-500/10 text-blue-500 rounded-[2rem] flex items-center justify-center mx-auto mb-8">
                    <Trophy className="w-10 h-10" />
                </div>
                <h3 className="text-3xl font-bold mb-2">Synthesis Complete</h3>
                <p className="text-app-muted mb-8 italic">"You've mastered the core concepts of this lecture."</p>

                <div className="flex justify-center gap-12 mb-12">
                    <div>
                        <p className="text-[10px] font-bold text-app-muted uppercase tracking-widest mb-1">Score</p>
                        <p className="text-4xl font-bold text-blue-500">{Math.round((score / Math.max(1, answeredTotal || displayQuestions.length)) * 100)}%</p>
                    </div>
                    <div className="w-[1px] bg-app-border" />
                    <div>
                        <p className="text-[10px] font-bold text-app-muted uppercase tracking-widest mb-1">Correct</p>
                        <p className="text-4xl font-bold">{score}/{answeredTotal || displayQuestions.length}</p>
                    </div>
                </div>

                <div className="flex gap-4">
                    <button
                        onClick={resetQuiz}
                        className="flex-1 py-4 bg-app-card border border-app-border rounded-2xl font-bold flex items-center justify-center gap-2 hover:bg-app-bg transition-all"
                    >
                        <RefreshCw className="w-4 h-4" />
                        Retake Assessment
                    </button>
                    <button onClick={downloadReport} className="flex-1 py-4 bg-app-fg text-app-bg rounded-2xl font-bold shadow-xl hover:opacity-90 transition-all">
                        Download Report
                    </button>
                </div>
            </motion.div>
        );
    }

    const question = displayQuestions[currentQuestion] || { question: "No questions available", options: [], correct: 0 };

    // Get question type label
    const getQuestionTypeLabel = (type) => {
        switch(type) {
            case 'mcq': return 'Multiple Choice';
            case 'fib': return 'Fill in the Blank';
            case 'true_false': return 'True or False';
            case 'comprehension': return 'Comprehension';
            default: return 'Question';
        }
    };

    return (
        <div className="space-y-8">
            <div className="flex items-center justify-between px-2">
                <div className="flex items-center gap-3">
                    <div className="w-8 h-8 bg-app-card border border-app-border rounded-lg flex items-center justify-center text-app-muted">
                        <HelpCircle className="w-4 h-4" />
                    </div>
                    <div>
                        <h3 className="text-xs font-bold uppercase tracking-widest">{getQuestionTypeLabel(question.type)}</h3>
                        <p className="text-[10px] font-bold text-app-muted uppercase tracking-tighter">Question {currentQuestion + 1} of {displayQuestions.length}</p>
                    </div>
                </div>
                <div className="flex gap-1">
                    {displayQuestions.map((_, i) => (
                        <div
                            key={i}
                            className={`h-1 w-6 rounded-full transition-all duration-500 ${i <= currentQuestion ? 'bg-blue-500' : 'bg-app-border'}`}
                        />
                    ))}
                </div>
            </div>

            <motion.div
                key={currentQuestion}
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                className="pro-card p-10 bg-app-card/30"
            >
                <h4 className="text-xl font-bold mb-10 leading-tight">{question.question}</h4>

                <div className="grid grid-cols-1 gap-4">
                    {question.options.map((option, i) => {
                        const isSelected = selectedAnswer === i;
                        const isCorrect = i === question.correct;
                        const showCorrect = selectedAnswer !== null && isCorrect;
                        const showWrong = isSelected && !isCorrect;

                        return (
                            <button
                                key={i}
                                onClick={() => handleAnswer(i)}
                                disabled={selectedAnswer !== null}
                                className={`
                                    p-6 rounded-2xl border text-left transition-all flex items-center justify-between group
                                    ${isSelected ? 'scale-[1.02]' : 'hover:scale-[1.01]'}
                                    ${showCorrect ? 'bg-emerald-500/10 border-emerald-500 text-emerald-500' :
                                        showWrong ? 'bg-red-500/10 border-red-500 text-red-500' :
                                            isSelected ? 'border-blue-500 bg-blue-500/5 text-blue-500' :
                                                'border-app-border bg-app-card/50 hover:bg-app-card hover:border-app-muted'}
                                `}
                            >
                                <div className="flex items-center gap-4">
                                    <div className={`w-8 h-8 rounded-lg border flex items-center justify-center font-bold text-xs transition-colors
                                        ${showCorrect ? 'bg-emerald-500 border-emerald-400 text-white' :
                                            showWrong ? 'bg-red-500 border-red-400 text-white' :
                                                isSelected ? 'bg-blue-500 border-blue-400 text-white' :
                                                    'bg-app-bg border-app-border text-app-muted group-hover:border-app-muted'}
                                    `}>
                                        {String.fromCharCode(65 + i)}
                                    </div>
                                    <span className="font-medium">{option}</span>
                                </div>
                                {showCorrect && <CheckCircle2 className="w-5 h-5" />}
                                {showWrong && <AlertCircle className="w-5 h-5" />}
                            </button>
                        );
                    })}
                </div>

                <AnimatePresence>
                    {selectedAnswer !== null && (
                        <motion.div
                            initial={{ opacity: 0, y: 10 }}
                            animate={{ opacity: 1, y: 0 }}
                            className="mt-10 flex items-center justify-between pt-10 border-t border-app-border"
                        >
                            <p className="text-sm font-medium text-app-muted italic">
                                {selectedAnswer === question.correct ?
                                    "Excellent deduction. Onward." :
                                    "A learning opportunity. The correct path is clear now."}
                            </p>
                            <div className="flex items-center gap-4">
                                <button
                                    onClick={endQuizEarly}
                                    className="px-6 py-3 border border-app-border rounded-xl font-bold text-sm hover:bg-app-card transition-all"
                                >
                                    End Early
                                </button>
                                <button
                                    onClick={nextQuestion}
                                    className="px-8 py-3 bg-app-fg text-app-bg rounded-xl font-bold text-sm flex items-center gap-2 hover:opacity-90 transition-all shadow-lg"
                                >
                                    {currentQuestion === displayQuestions.length - 1 ? 'Finish Assessment' : 'Next Question'}
                                    <ChevronRight className="w-4 h-4" />
                                </button>
                            </div>
                        </motion.div>
                    )}
                </AnimatePresence>
            </motion.div>
        </div>
    );
};

export default QuizSection;
