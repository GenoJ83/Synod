import React from 'react';
import { CheckCircle2, Brain, Lightbulb } from 'lucide-react';

/** Renders **markdown bold** in summary text (no full markdown engine). */
function SummaryInlineText({ text }) {
    const parts = String(text).split(/(\*\*[^*]+\*\*)/g);
    return (
        <>
            {parts.map((part, i) => {
                const m = part.match(/^\*\*([^*]+)\*\*$/);
                if (m) {
                    return (
                        <strong key={i} className="font-semibold text-app-fg">
                            {m[1]}
                        </strong>
                    );
                }
                return <React.Fragment key={i}>{part}</React.Fragment>;
            })}
        </>
    );
}

function ResultsDisplay({ result, startQuiz, children }) {
    if (!result) return null;

    const totalQuestions = (result.quiz?.mcqs?.length || 0) +
        (result.quiz?.fill_in_the_blanks?.length || 0) +
        (result.quiz?.true_false?.length || 0) +
        (result.quiz?.comprehension?.length || 0);

    return (
        <div className="w-full xl:w-2/3 max-w-4xl mx-auto space-y-8 animate-fade-in pb-20">
            {/* Executive Summary Section */}
            <div className="pro-card p-8 shadow-sm">
                <div className="flex items-center gap-3 mb-6 text-emerald-500">
                    <CheckCircle2 className="w-6 h-6" />
                    <h3 className="text-sm font-bold uppercase tracking-widest">Comprehensive Summary</h3>
                </div>
                <div className="space-y-4">
                    {result.summary.split('\n\n').map((paragraph, index) => (
                        <p key={index} className="text-app-fg text-lg leading-relaxed font-medium">
                            <SummaryInlineText text={paragraph} />
                        </p>
                    ))}
                </div>

            </div>

            {/* Key Takeaways Section */}
            {result.takeaways && result.takeaways.length > 0 && (
                <div className="pro-card p-8 shadow-sm">
                    <div className="flex items-center gap-3 mb-6 text-blue-500">
                        <Lightbulb className="w-6 h-6" />
                        <h3 className="text-sm font-bold uppercase tracking-widest">Key Takeaways</h3>
                    </div>
                    <ul className="space-y-4">
                        {result.takeaways.map((takeaway, idx) => (
                            <li key={idx} className="flex gap-4 group items-start">
                                <span className="flex-shrink-0 w-6 h-6 rounded-full bg-blue-500/10 text-blue-500 flex items-center justify-center text-xs font-bold mt-0.5">
                                    {idx + 1}
                                </span>
                                <p className="text-app-fg text-base font-medium leading-relaxed group-hover:text-blue-500 transition-colors">
                                    {takeaway}
                                </p>
                            </li>
                        ))}
                    </ul>
                </div>
            )}

            {children}

            {/* Knowledge Check CTA */}
            <div className="relative overflow-hidden bg-gradient-to-br from-app-fg to-zinc-400 text-app-bg rounded-2xl p-10 flex flex-col items-center justify-center text-center shadow-xl group">
                {/* Decorative background elements */}
                <div className="absolute top-0 right-0 -mt-10 -mr-10 w-40 h-40 bg-white/20 rounded-full blur-3xl group-hover:bg-white/30 transition-all duration-500"></div>
                <div className="absolute bottom-0 left-0 -mb-10 -ml-10 w-32 h-32 bg-white/20 rounded-full blur-2xl group-hover:bg-white/30 transition-all duration-500"></div>

                <Brain className="w-12 h-12 mb-4 opacity-90 drop-shadow-md z-10" />
                <h3 className="text-2xl font-black mb-3 z-10 tracking-tight">Ready to test your knowledge?</h3>
                <p className="text-app-bg/80 text-base mb-8 font-semibold max-w-sm z-10">
                    We've generated {totalQuestions} interactive questions based on the concepts extracted from your document.
                </p>
                <button
                    onClick={startQuiz}
                    className="z-10 bg-app-bg text-app-fg px-10 py-4 rounded-xl font-bold text-lg hover:bg-zinc-800 transition-all hover:scale-105 active:scale-95 shadow-lg border border-app-bg"
                >
                    Start Knowledge Check
                </button>
            </div>
        </div>
    );
}

export default ResultsDisplay;
