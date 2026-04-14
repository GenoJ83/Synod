import React, { useCallback, useRef, useState } from 'react';
import { motion } from 'framer-motion';
import { BookOpen, Loader2 } from 'lucide-react';
import { API_BASE_URL } from '../../config';

function ConceptExplorer({
    result,
    selectedConcept,
    setSelectedConcept,
    viewedConcepts,
    setViewedConcepts,
    setShowQuiz,
    quizRef
}) {
    const [explanationDetail, setExplanationDetail] = useState(null);
    const [explainLoading, setExplainLoading] = useState(false);
    const [explainError, setExplainError] = useState('');
    const explainCache = useRef({});

    const fetchExplanation = useCallback(async (concept) => {
        if (!concept) return;

        setExplainLoading(true);
        setExplainError('');
        setExplanationDetail(null);

        const cached = explainCache.current[concept];
        if (cached) {
            setExplanationDetail(cached);
            setExplainLoading(false);
            return;
        }

        try {
            const legacy = result.explanations?.concepts?.find((c) => c.term === concept);
            if (legacy && (legacy.definition || legacy.context)) {
                explainCache.current[concept] = legacy;
                setExplanationDetail(legacy);
                return;
            }

            if (!result.source_text) {
                setExplainError(
                    'This analysis has no stored source text. Run a new analysis from the dashboard to load explanations.'
                );
                return;
            }

            const res = await fetch(`${API_BASE_URL}/explain-concept`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ text: result.source_text, concept }),
            });

            const body = await res.json().catch(() => ({}));
            if (!res.ok) {
                const msg = typeof body.detail === 'string' ? body.detail : Array.isArray(body.detail)
                    ? body.detail.map((d) => d.msg || d).join(' ')
                    : res.statusText;
                throw new Error(msg || 'Request failed');
            }

            explainCache.current[concept] = body;
            setExplanationDetail(body);
        } catch (e) {
            setExplainError(e.message || 'Could not load explanation.');
        } finally {
            setExplainLoading(false);
        }
    }, [result.explanations, result.source_text]);

    if (!result?.concepts) return null;

    const openConcept = (concept) => {
        setSelectedConcept(concept);
        if (!viewedConcepts.includes(concept)) {
            setViewedConcepts([...viewedConcepts, concept]);
        }
        fetchExplanation(concept);
    };

    const closePanel = () => {
        setSelectedConcept(null);
        setExplanationDetail(null);
        setExplainError('');
        setExplainLoading(false);
    };

    return (
        <div className="pro-card p-6">
            <div className="flex items-center gap-3 mb-4 text-app-muted">
                <BookOpen className="w-4 h-4" />
                <h3 className="text-xs font-bold uppercase tracking-widest">Key concepts</h3>
                <span className="ml-auto text-[10px] text-blue-400">
                    {viewedConcepts.length}/{result.concepts.length} explored
                </span>
            </div>
            <p className="text-[11px] text-app-muted mb-3 leading-relaxed">
                Click a term to generate a short definition and a matching sentence from your material.
            </p>
            <div className="flex flex-wrap gap-2">
                {result.concepts.map((concept, i) => {
                    const detail = result.concept_details?.find((d) => d.term === concept);
                    const relevance = detail?.relevance || 0;
                    return (
                        <button
                            key={i}
                            type="button"
                            onClick={() => openConcept(concept)}
                            className={`px-3 py-1 bg-app-card border rounded-md text-[11px] font-bold uppercase transition-all cursor-pointer flex items-center gap-2 ${selectedConcept === concept
                                ? 'border-blue-500 bg-blue-500/20 text-blue-400'
                                : viewedConcepts.includes(concept)
                                    ? 'border-green-500/30 text-green-400/70'
                                    : 'border-app-border text-app-muted hover:bg-blue-500/20 hover:border-blue-500/50 hover:text-blue-400'
                                }`}
                        >
                            {concept}
                            {relevance > 0 && (
                                <span className={`text-[8px] px-1 rounded ${relevance > 0.7 ? 'bg-emerald-500/20 text-emerald-500' : 'bg-blue-500/20 text-blue-500'}`}>
                                    {(relevance * 100).toFixed(0)}%
                                </span>
                            )}
                        </button>
                    );
                })}
            </div>

            {selectedConcept && (
                <motion.div
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="mt-4 p-5 bg-gradient-to-br from-blue-500/10 to-purple-500/10 border border-blue-500/30 rounded-xl"
                >
                    <div className="flex items-start justify-between gap-4 mb-3">
                        <div className="flex items-center gap-2">
                            <div className="w-8 h-8 rounded-lg bg-blue-500/20 flex items-center justify-center">
                                <BookOpen className="w-4 h-4 text-blue-400" />
                            </div>
                            <div>
                                <h4 className="text-base font-bold text-blue-400">{selectedConcept}</h4>
                                {result.concept_details?.find((d) => d.term === selectedConcept) && (
                                    <p className="text-[10px] text-app-muted font-bold uppercase">
                                        Semantic confidence:{' '}
                                        {(result.concept_details.find((d) => d.term === selectedConcept).relevance * 100).toFixed(1)}%
                                    </p>
                                )}
                            </div>
                        </div>
                        <button
                            type="button"
                            onClick={closePanel}
                            className="text-app-muted hover:text-app-fg p-1 hover:bg-app-card rounded"
                            aria-label="Close"
                        >
                            ×
                        </button>
                    </div>

                    {explainLoading && (
                        <div className="flex items-center gap-2 text-sm text-app-muted py-4">
                            <Loader2 className="w-4 h-4 animate-spin text-blue-400" />
                            Generating explanation…
                        </div>
                    )}

                    {explainError && !explainLoading && (
                        <p className="text-sm text-red-400/90 leading-relaxed mb-4">{explainError}</p>
                    )}

                    {!explainLoading && explanationDetail && (
                        <>
                            <p className="text-sm text-app-fg leading-relaxed mb-4">
                                <span className="font-bold">Definition:</span> {explanationDetail.definition}
                            </p>
                            {explanationDetail.context && (
                                <p className="text-sm text-app-fg leading-relaxed mb-4 italic border-l-2 border-blue-500/30 pl-3">
                                    <span className="font-bold not-italic">In context:</span> {explanationDetail.context}
                                </p>
                            )}
                        </>
                    )}

                    <div className="pt-3 border-t border-blue-500/20">
                        <p className="text-[10px] font-bold text-app-muted uppercase tracking-wider mb-2">Related concepts</p>
                        <div className="flex flex-wrap gap-1">
                            {result.concepts.filter((c) => c !== selectedConcept).slice(0, 4).map((related, i) => (
                                <button
                                    type="button"
                                    key={i}
                                    onClick={() => openConcept(related)}
                                    className="px-2 py-1 bg-app-card/50 border border-app-border/50 rounded text-[10px] text-app-muted hover:text-blue-400 hover:border-blue-500/50 transition-all"
                                >
                                    {related}
                                </button>
                            ))}
                        </div>
                    </div>

                    <div className="flex gap-2 mt-4">
                        <button
                            type="button"
                            onClick={() => {
                                setShowQuiz(true);
                                setTimeout(() => quizRef.current?.scrollIntoView({ behavior: 'smooth' }), 100);
                            }}
                            className="flex-1 py-2 bg-blue-500 text-white text-xs font-bold rounded-lg hover:bg-blue-600 transition-colors"
                        >
                            Test your knowledge
                        </button>
                    </div>
                </motion.div>
            )}
        </div>
    );
}

export default ConceptExplorer;
