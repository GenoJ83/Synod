import random
from typing import List, Dict, Set, Tuple, Optional
from collections import Counter
import re
import spacy

# Bibliography / reference lines — not suitable for T/F negation or conceptual quizzes
_IEEE_OR_PUBLISHER = re.compile(
    r"(?i)\b(?:ieee|acm|springer|elsevier|arxiv|doi:|isbn|issn|pp\.|vol\.?|no\.|"
    r"transactions\s+on|journal\s+of|proceedings\s+of)\b"
)
_VOLUME_ISSUE_PAGES = re.compile(
    r"\b\d{1,3}\s*\(\s*\d{1,3}\s*\)\s*,\s*\d{3,5}\s*[–-]\s*\d{3,5}\b"
)
_URL_LIKE = re.compile(r"https?://|www\.\S+", re.I)
_SLIDE_INDEX = re.compile(r"^\s*\d{1,2}\s*[/.)]\s+\S", re.M)
_MOOC_OR_VENDOR = re.compile(
    r"(?i)\b(coursera|edx\b|udacity|udemy|pluralsight|skillshare|khan\s+academy|"
    r"linkedin\s+learning|datacamp|deeplearning\.ai|fast\.ai)\b"
)
# Title jammed to colon: "coursera:neuralnetworks" (spaces removed)
_TITLE_COLON_JAM = re.compile(r"(?i)[a-z]{3,20}:[a-z]{4,}")
_LECTURE_SLIDE = re.compile(
    r"(?i)(^|\.\s*)lecture\s+[\d.]+\s*[-–—]?\s*[a-z0-9]*|"
    r"\blecture\s+[\d.]+\s*[-–—][a-z0-9]+"
)
# Checkmarks / ballot boxes — slide UI leaked into OCR; breaks T/F and reads as nonsense
_SLIDE_TICK_OR_BOX = re.compile(
    r"[✓✔✗☑☐\u2713\u2714\u2717\u2718\u2705\u2610\u2611]"
)
# Tick glued to a letter (e.g. "✔Invariance") or "Does not✔"
_TICK_GLUED_TO_WORD = re.compile(
    r"(?i)[\u2713\u2714✓✔](?=[A-Za-z])|(?<=[A-Za-z.!?])[\u2713\u2714✓✔](?=\s|$)"
)


class QuizGenerator:
    """Builds MCQ, True/False, and comprehension items grounded in lecture text."""

    def __init__(self):
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            self.nlp = None

        self.fallback_distractors = [
            "Data preprocessing",
            "Hyperparameter tuning",
            "Loss function",
            "Backpropagation",
            "Gradient descent",
            "Feature engineering",
            "Cross-validation",
            "Overfitting",
            "Stochastic process",
            "Linear regression",
            "Dimensionality reduction",
            "Unsupervised learning",
        ]

    # --- text utilities ---

    def _split_candidate_sentences(self, text: str) -> List[str]:
        """Split on sentence ends, blank lines, and semicolons (slides); dedupe."""
        raw = re.split(r"(?<=[.!?])\s+|(?:\n\n|\n)|(?<=;)\s+", text or "")
        seen: Set[str] = set()
        out: List[str] = []
        for s in raw:
            t = re.sub(r"\s+", " ", s.strip())
            if len(t) < 14:
                continue
            if _URL_LIKE.search(t) or _SLIDE_INDEX.match(t):
                continue
            key = t.lower()
            if key in seen:
                continue
            seen.add(key)
            out.append(t)
        return out

    def _normalize_question_key(self, q: str) -> str:
        return re.sub(r"\s+", " ", (q or "").lower())[:220]

    def _trim_option(self, s: str, max_len: int = 200) -> str:
        s = re.sub(r"\s+", " ", (s or "").strip())
        if len(s) <= max_len:
            return s
        return s[: max_len - 1].rstrip() + "…"

    def _lexical_jaccard(self, a: str, b: str) -> float:
        wa = set(re.findall(r"[a-z0-9]+", (a or "").lower()))
        wb = set(re.findall(r"[a-z0-9]+", (b or "").lower()))
        if not wa or not wb:
            return 0.0
        return len(wa & wb) / max(len(wa | wb), 1)

    def _is_bibliographic_or_citation(self, s: str) -> bool:
        t = re.sub(r"\s+", " ", (s or "").strip())
        if len(t) < 8:
            return True
        tl = t.lower()
        if _IEEE_OR_PUBLISHER.search(t):
            return True
        if _VOLUME_ISSUE_PAGES.search(t):
            return True
        if re.search(r"\bet\s+al\b", tl):
            return True
        if re.search(r"^\s*\[\s*\d+\s*\]", t):
            return True
        if t.count(",") >= 2 and len(re.findall(r"\d+", t)) >= 3 and "(" in t and ")" in t:
            if not re.search(
                r"(?i)\b(is|are|was|were|shows|proposes|demonstrates|found|observed|argued)\b",
                tl,
            ):
                return True
        return False

    def _is_courseware_or_title_slide(self, s: str) -> bool:
        """
        Slide / MOOC metadata: lecture numbers, Coursera-style headers, course titles + (year),
        OCR-jammed tokens — not factual claims suitable for T/F or blanks.
        """
        t = re.sub(r"\s+", " ", (s or "").strip())
        if len(t) < 6:
            return True
        tl = t.lower()
        words = t.split()

        if _MOOC_OR_VENDOR.search(t):
            return True
        compact = re.sub(r"\s+", "", tl)
        if _TITLE_COLON_JAM.search(compact) or re.search(r"(?i)\b[a-z]{2,12}:\s*[A-Za-z]", t):
            return True
        if _LECTURE_SLIDE.search(tl):
            return True
        if re.search(r"(?i)^\s*week\s+\d+", tl) or re.search(r"(?i)\bmodule\s+\d+\s*[:—-]", tl):
            return True

        # Catalog line: ends with (2012) and reads like a course title, not a definition
        if re.search(r"\(\s*(?:19|20)\d{2}\s*\)\s*\.?\s*$", tl):
            if len(words) <= 14 and not re.search(
                r"(?i)\b(is|are|was|were|defines|means|requires|uses|trains|computes|shows|states)\b",
                tl,
            ):
                return True

        # OCR: impossibly long single "word" (two words merged)
        for w in words:
            w2 = re.sub(r"^[^A-Za-z0-9]+|[^A-Za-z0-9]+$", "", w)
            if len(w2) >= 18 and "-" not in w2 and "_" not in w2:
                return True
            if re.search(
                r"(?i)^(for|the|and|in|on|of)(machine|learning|network|layer|model|works|ment|prop)",
                w2,
            ):
                return True

        # Short slide label: "Lecture 3 overview" without a factual predicate
        if len(words) <= 8 and re.search(r"(?i)\b(lecture|week|part)\s+\d", tl):
            if not re.search(
                r"(?i)\b(is|are|was|were|because|therefore|means|defines|covers|includes|states)\b",
                tl,
            ):
                return True

        return False

    def _has_slide_checkbox_or_tick_noise(self, s: str) -> bool:
        """True if line contains slide ticks/boxes or OCR-glued tick+word (unreliable for quizzes)."""
        if not s:
            return True
        if _SLIDE_TICK_OR_BOX.search(s):
            return True
        if _TICK_GLUED_TO_WORD.search(s):
            return True
        # Two imperatives / fragments jammed: "... , reduce the ..." after a negation clause
        if re.search(r"(?i)does\s+not\s+[^.!?]{0,80},\s*(reduce|increase|decrease|add|remove|use)\b", s):
            return True
        # OCR: "Does not Invariance to ..." (no verb between "does not" and capitalized head noun)
        if re.search(r"(?i)^does not\s+[A-Z][a-z]{5,}\s+to\b", s):
            if not re.search(
                r"(?i)^does not\s+(apply|matter|seem|appear|work|refer|translate|extend|lead)\b",
                s,
            ):
                return True
        return False

    def _tf_dedupe_fingerprint(self, q: str) -> str:
        x = re.sub(r"\s+", " ", (q or "").lower())
        x = re.sub(r"\bnot\b", "", x)
        x = re.sub(r"[\d\(\),;:\-–—]+", " ", x)
        x = re.sub(r"\s+", " ", x).strip()[:140]
        return x

    def _concepts_mentioned(self, sentence: str, concepts: List[str]) -> List[str]:
        """Match concepts with word boundaries for short tokens; substring for multi-word phrases."""
        sl = sentence.lower()
        found: List[str] = []
        for c in concepts:
            ck = (c or "").strip()
            if len(ck) < 2:
                continue
            cl = ck.lower()
            if " " in ck or len(cl) > 14:
                if cl in sl:
                    found.append(c)
            else:
                if re.search(rf"(?<![a-z0-9]){re.escape(cl)}(?![a-z0-9])", sl):
                    found.append(c)
        return found

    def _rank_sentences_for_quiz(self, sentences: List[str], concepts: List[str]) -> List[str]:
        """Prefer informative lines: length, concept hits, light verb signal."""

        def score(s: str) -> float:
            w = len(s.split())
            cm = len(self._concepts_mentioned(s, concepts))
            verbish = 1.0 if re.search(r"(?i)\b(is|are|was|were|has|have|uses|use|means|allows|requires|enables|helps|shows|includes|consists)\b", s) else 0.65
            return w * 0.35 + cm * 5.0 + verbish * 3.0

        return sorted(sentences, key=score, reverse=True)

    # --- quality gates ---

    def _is_sentence_specific(self, sentence: str, concepts: List[str]) -> bool:
        bullets = "❑●•*-◦▪"
        sentence = sentence.lstrip(bullets).strip()

        if self._is_bibliographic_or_citation(sentence):
            return False
        if self._is_courseware_or_title_slide(sentence):
            return False
        if self._has_slide_checkbox_or_tick_noise(sentence):
            return False

        words = sentence.split()
        if len(words) < 6:
            return False
        if sentence.endswith(":"):
            return False

        first_word = words[0].lower().strip(".,!?;:\"'")
        vague_pronouns = {"it", "they", "this", "these", "those", "that", "he", "she"}
        if first_word in vague_pronouns:
            if self._count_unique_concepts(sentence, concepts) < 2:
                return False

        objective_patterns = [
            "should be able to",
            "learning outcomes",
            "lecture objectives",
            "learning objectives",
            "by the end of",
        ]
        if any(pat in sentence.lower() for pat in objective_patterns):
            return False

        objective_verbs = {
            "understand",
            "learn",
            "know",
            "discuss",
            "explain",
            "describe",
            "identify",
            "analyze",
            "evaluate",
            "synthesize",
            "apply",
        }
        if first_word in objective_verbs:
            return False

        if len(words) < 9 and self._count_unique_concepts(sentence, concepts) < 1:
            return False

        return True

    def _count_unique_concepts(self, sentence: str, concepts: List[str]) -> int:
        return len(self._concepts_mentioned(sentence, concepts))

    def _statement_to_question(self, statement: str) -> str:
        statement = statement.strip()
        if not statement:
            return ""

        bad_starts = (
            "however",
            "therefore",
            "additionally",
            "furthermore",
            "why",
            "how",
            "when",
            "what",
            "which",
        )
        words = statement.split()
        if words and words[0].lower().strip(".,!?;:\"'") in bad_starts and len(words) > 1:
            statement = " ".join(words[1:])

        statement = statement.strip()
        if not statement:
            return ""

        statement = statement[0].upper() + statement[1:]
        if statement.endswith("?"):
            statement = statement[:-1] + "."
        elif not statement.endswith("."):
            statement = statement + "."

        return statement

    # --- false statements ---

    def _false_negation_is_plausible(self, original: str, negated: str) -> bool:
        nl = negated.lower()
        bad_fragments = (
            " not and ",
            " not or ",
            " not ,",
            " not.",
            " not )",
            " not-",
            "does not does",
            "is not not",
        )
        if any(b in nl for b in bad_fragments):
            return False
        if negated.count(" not") + negated.lower().count(" does not") > 2:
            return False
        return True

    def _false_via_negation(self, sentence: str) -> Optional[str]:
        if not self.nlp:
            return None
        doc = self.nlp(sentence)
        for token in doc:
            if (token.pos_ == "VERB" or token.pos_ == "AUX") and token.dep_ == "ROOT":
                if token.lemma_ == "be":
                    idx = token.idx + len(token.text)
                    candidate = sentence[:idx] + " not" + sentence[idx:]
                else:
                    neg = (
                        "does not "
                        if token.tag_ == "VBZ"
                        else "did not "
                        if token.tag_ == "VBD"
                        else "do not "
                    )
                    candidate = (
                        sentence[: token.idx]
                        + neg
                        + token.lemma_
                        + sentence[token.idx + len(token.text) :]
                    )
                if self._false_negation_is_plausible(sentence, candidate):
                    return candidate
                return None
        return None

    def _false_via_concept_swap(self, sentence: str, concepts: List[str]) -> Optional[Tuple[str, str]]:
        """
        Replace one mentioned concept with another from the lecture (verifiably false if
        the swap contradicts the original claim). Returns (new_sentence, explanation_note).
        """
        if len(concepts) < 2:
            return None
        matched = self._concepts_mentioned(sentence, concepts)
        if not matched:
            return None
        random.shuffle(matched)
        for victim in matched:
            candidates = [
                c
                for c in concepts
                if c.lower() != victim.lower()
                and victim.lower() not in c.lower()
                and c.lower() not in victim.lower()
                and len(c.strip()) >= 3
            ]
            if not candidates:
                continue
            replacement = random.choice(candidates)
            pat = re.compile(rf"(?<![a-z0-9]){re.escape(victim)}(?![a-z0-9])", re.IGNORECASE)
            if not pat.search(sentence):
                pat = re.compile(re.escape(victim), re.IGNORECASE)
            out = pat.sub(replacement, sentence, count=1)
            if out.strip().lower() == sentence.strip().lower():
                continue
            note = (
                f"The material ties this idea to “{victim}”, not to “{replacement}” in this context."
            )
            return (out, note)
        return None

    def _create_false_statement(self, sentence: str, concepts: List[str]) -> Tuple[str, str]:
        """
        Returns (false_statement, explanation_hint). Empty string false if none.
        """
        if self._is_bibliographic_or_citation(sentence):
            return "", ""

        neg = self._false_via_negation(sentence)
        if neg:
            return neg, ""

        swapped = self._false_via_concept_swap(sentence, concepts)
        if swapped:
            return swapped[0], swapped[1]

        return "", ""

    def _four_shuffled_options(
        self, answer: str, all_concepts: List[str], extractor
    ) -> Optional[List[str]]:
        """Three distractors + correct, shuffled; distinct case-insensitive strings."""
        other = [
            c
            for c in all_concepts
            if c.lower() != answer.lower()
            and answer.lower() not in c.lower()
            and c.lower() not in answer.lower()
        ]
        distractors: List[str] = []

        if extractor and getattr(extractor, "has_deps", False) and len(other) > 5:
            try:
                import numpy as np
                from sentence_transformers import util

                ans_emb = extractor.model.encode([answer], convert_to_tensor=True)
                cand_embs = extractor.model.encode(other, convert_to_tensor=True)
                scores = util.cos_sim(ans_emb, cand_embs).cpu().numpy().flatten()
                order = np.argsort(scores)
                n = len(order)
                lo = max(1, n // 8)
                hi = max(lo + 3, (7 * n) // 8)
                band = list(order[lo:hi])
                random.shuffle(band)
                for i in band:
                    c = other[int(i)]
                    if c not in distractors:
                        distractors.append(c)
                    if len(distractors) >= 3:
                        break
            except Exception:
                pass

        if len(distractors) < 3:
            pool = [c for c in other if c not in distractors]
            random.shuffle(pool)
            for c in pool:
                if c not in distractors:
                    distractors.append(c)
                if len(distractors) >= 3:
                    break

        if len(distractors) < 3:
            fb = [d for d in self.fallback_distractors if d.lower() != answer.lower()]
            random.shuffle(fb)
            for d in fb:
                if d not in distractors:
                    distractors.append(d)
                if len(distractors) >= 3:
                    break

        if len(distractors) < 3:
            return None
        distractors = distractors[:3]
        opts = distractors + [answer]
        if len({o.strip().lower() for o in opts}) < 4:
            return None
        random.shuffle(opts)
        return opts

    # --- generators ---

    def generate_fill_in_the_blanks(
        self, text: str, concepts: List[str], all_concepts: List[str], extractor=None
    ) -> List[Dict]:
        """
        Word-choice blanks (same UX as MCQ but labeled Fill-in-the-blank in the UI).
        Prefers shorter in-sentence terms to reduce overlap with long-span MCQs.
        """
        if not concepts:
            return []

        out: List[Dict] = []
        used_sentence_keys: Set[str] = set()
        used_question_keys: Set[str] = set()

        sentences = self._split_candidate_sentences(text)
        sentences = self._rank_sentences_for_quiz(sentences, concepts)
        random.shuffle(sentences)

        for sentence in sentences:
            if not self._is_sentence_specific(sentence, concepts):
                continue
            sk = self._normalize_question_key(sentence)
            if sk in used_sentence_keys:
                continue

            matched = self._concepts_mentioned(sentence, concepts)
            eligible = [m for m in matched if len(m.strip()) >= 4]
            if not eligible:
                continue
            best = min(eligible, key=len)

            blanked = re.compile(re.escape(best), re.IGNORECASE).sub("__________", sentence, count=1)
            if "__________" not in blanked:
                continue
            qtext = f"Fill in the blank: {blanked.strip()}"
            qk = self._normalize_question_key("fib|" + qtext)
            if qk in used_question_keys:
                continue

            opts = self._four_shuffled_options(best, all_concepts, extractor)
            if not opts:
                continue

            used_sentence_keys.add(sk)
            used_question_keys.add(qk)
            out.append(
                {
                    "type": "fill_in_the_blank",
                    "question": qtext,
                    "options": opts,
                    "answer": best,
                }
            )
            if len(out) >= 10:
                break

        random.shuffle(out)
        return out

    def generate_mcqs(
        self, text: str, concepts: List[str], all_concepts: List[str], extractor=None
    ) -> List[Dict]:
        if not concepts:
            return []

        questions: List[Dict] = []
        used_sentence_keys: Set[str] = set()
        used_question_keys: Set[str] = set()
        concept_counts: Counter = Counter()
        max_per_concept = 2

        sentences = self._split_candidate_sentences(text)
        sentences = self._rank_sentences_for_quiz(sentences, concepts)
        random.shuffle(sentences)

        for sentence in sentences:
            if not self._is_sentence_specific(sentence, concepts):
                continue
            sk = self._normalize_question_key(sentence)
            if sk in used_sentence_keys:
                continue

            matched = self._concepts_mentioned(sentence, concepts)
            if not matched:
                continue

            best_concept = max(matched, key=len)
            if concept_counts[best_concept.lower()] >= max_per_concept:
                continue

            question_text = re.compile(re.escape(best_concept), re.IGNORECASE).sub(
                "__________", sentence, count=1
            )
            if "__________" not in question_text:
                continue
            qk = self._normalize_question_key(question_text)
            if qk in used_question_keys:
                continue

            options = self._four_shuffled_options(best_concept, all_concepts, extractor)
            if not options:
                continue

            used_sentence_keys.add(sk)
            used_question_keys.add(qk)
            concept_counts[best_concept.lower()] += 1

            leads = (
                "",
                "According to the lecture: ",
                "Based on the course material: ",
                "Which option best completes this? ",
            )
            lead = leads[len(questions) % len(leads)]
            q_final = (lead + question_text.strip()).strip()

            questions.append(
                {
                    "type": "mcq",
                    "question": q_final,
                    "options": options,
                    "answer": best_concept,
                }
            )

        random.shuffle(questions)
        return questions[:18]

    def generate_true_false(self, text: str, concepts: List[str]) -> List[Dict]:
        sentences = self._split_candidate_sentences(text)
        sentences = [s for s in sentences if self._is_sentence_specific(s, concepts)]
        sentences = self._rank_sentences_for_quiz(sentences, concepts)
        random.shuffle(sentences)

        true_items: List[Tuple[str, str]] = []
        false_items: List[Tuple[str, str]] = []
        seen_true: Set[str] = set()
        seen_false: Set[str] = set()

        for sentence in sentences:
            nk = self._normalize_question_key(sentence)
            if nk in seen_true:
                continue
            true_items.append((sentence.strip(), self._trim_option(sentence, 180)))
            seen_true.add(nk)

            fstmt, hint = self._create_false_statement(sentence, concepts)
            if not fstmt or fstmt.strip().lower() == sentence.strip().lower():
                continue
            fq = self._statement_to_question(fstmt)
            tk = self._normalize_question_key(fq)
            if not tk or tk in seen_false or tk == nk:
                continue
            expl = (
                hint
                if hint
                else self._trim_option(
                    f"The lecture states: {sentence}", 200
                )
            )
            false_items.append((fstmt, expl))
            seen_false.add(tk)

        true_qs: List[Dict] = []
        for stmt, expl in true_items[:14]:
            q = self._statement_to_question(stmt)
            if q and len(q) > 22:
                true_qs.append(
                    {
                        "type": "true_false",
                        "question": q,
                        "correct": True,
                        "explanation": expl,
                    }
                )

        false_qs: List[Dict] = []
        for stmt, expl in false_items[:14]:
            q = self._statement_to_question(stmt)
            if q and len(q) > 22:
                false_qs.append(
                    {
                        "type": "true_false",
                        "question": q,
                        "correct": False,
                        "explanation": expl,
                    }
                )

        random.shuffle(true_qs)
        random.shuffle(false_qs)
        merged: List[Dict] = []
        for k in range(max(len(true_qs), len(false_qs))):
            if k < len(true_qs):
                merged.append(true_qs[k])
            if k < len(false_qs):
                merged.append(false_qs[k])
        random.shuffle(merged)

        deduped: List[Dict] = []
        seen_q: Set[str] = set()
        seen_fp: Set[str] = set()
        for q in merged:
            qu = q.get("question", "")
            k = self._normalize_question_key(qu)
            fp = self._tf_dedupe_fingerprint(qu)
            if k in seen_q or fp in seen_fp:
                continue
            seen_q.add(k)
            seen_fp.add(fp)
            deduped.append(q)

        random.shuffle(deduped)
        return deduped[:12]

    def generate_comprehension(self, text: str, concepts: List[str]) -> List[Dict]:
        sentences = self._split_candidate_sentences(text)
        good = [
            s
            for s in sentences
            if self._is_sentence_specific(s, concepts) and len(s.split()) >= 8
        ]
        if len(good) < 4:
            return []

        good = self._rank_sentences_for_quiz(good, concepts)
        used_question_keys: Set[str] = set()
        concept_comp_count: Counter = Counter()
        questions: List[Dict] = []

        def _wrong_candidates(correct: str, must_exclude_substrings: List[str]) -> List[str]:
            scored: List[Tuple[float, str]] = []
            for s in good:
                if s == correct:
                    continue
                if any(ex.lower() in s.lower() for ex in must_exclude_substrings if ex):
                    continue
                jac = self._lexical_jaccard(correct, s)
                scored.append((jac, s))
            scored.sort(key=lambda x: x[0])
            low_sim = [s for j, s in scored if j < 0.42]
            mid = [s for j, s in scored if 0.25 <= j <= 0.55]
            pool = low_sim if len(low_sim) >= 6 else [s for _, s in scored[: max(20, len(scored) // 2)]]
            if len(pool) < 4 and mid:
                pool = list(dict.fromkeys(pool + mid))
            return pool

        def _add_mcq(
            qtext: str, raw_options: List[str], correct_sentence: str, explanation: str
        ) -> None:
            if len(raw_options) != 4:
                return
            try:
                correct_idx = raw_options.index(correct_sentence)
            except ValueError:
                return
            trimmed = [self._trim_option(x) for x in raw_options]
            if len({x.lower() for x in trimmed}) < 4:
                return
            flags = [i == correct_idx for i in range(4)]
            bundle = list(zip(trimmed, flags))
            random.shuffle(bundle)
            options = [b[0] for b in bundle]
            try:
                answer = next(i for i, b in enumerate(bundle) if b[1])
            except StopIteration:
                return
            qk = self._normalize_question_key(qtext + "|" + "|".join(sorted(options)))
            if qk in used_question_keys:
                return
            used_question_keys.add(qk)
            questions.append(
                {
                    "type": "comprehension",
                    "question": qtext,
                    "options": options,
                    "answer": answer,
                    "explanation": self._trim_option(explanation, 240),
                }
            )

        process_keywords = [
            "because",
            "therefore",
            "however",
            "although",
            "means",
            "enables",
            "allows",
            "helps",
            "results",
            "leads to",
            "used for",
            "involves",
            "depends on",
            "consists of",
            "includes",
            "requires",
        ]

        seen_proc: Set[str] = set()
        for sentence in good[:40]:
            sl = sentence.lower()
            hit = next((k for k in process_keywords if k in sl), None)
            if not hit:
                continue
            sc = self._concepts_mentioned(sentence, concepts)
            if not sc:
                continue
            sk = self._normalize_question_key(sentence)
            if sk in seen_proc:
                continue
            seen_proc.add(sk)

            main = sc[0]
            pool = _wrong_candidates(sentence, [main])
            if len(pool) < 3:
                pool = [s for s in good if s != sentence][:15]
            if len(pool) < 3:
                continue
            wrong_pick = random.sample(pool, 3)
            raw_opts = [sentence] + wrong_pick
            qtext = (
                f'According to the lecture, which passage best fits the idea of "{main}" '
                f'given the role of "{hit}" in that passage?'
            )
            _add_mcq(qtext, raw_opts, sentence, sentence)

        n = len(good)
        windows = [good[: max(1, n // 3)], good[n // 3 : 2 * n // 3], good[2 * n // 3 :]]
        random.shuffle(concepts)
        for concept in concepts:
            if concept_comp_count[concept.lower()] >= 1:
                continue
            with_c = [s for s in good if concept.lower() in s.lower()]
            if not with_c:
                continue
            random.shuffle(windows)
            picked_win = next((w for w in windows if any(s in w for s in with_c)), good)
            pool_c = [s for s in picked_win if concept.lower() in s.lower()]
            if not pool_c:
                pool_c = with_c
            correct = max(pool_c, key=lambda s: len(s.split()))

            pool_wrong = _wrong_candidates(correct, [concept])
            if len(pool_wrong) < 3:
                continue
            wrong_pick = random.sample(pool_wrong, 3)
            raw_opts = [correct] + wrong_pick
            qtext = (
                f'Which excerpt from the lecture best reflects how "{concept}" is discussed?'
            )
            _add_mcq(qtext, raw_opts, correct, correct)
            concept_comp_count[concept.lower()] += 1
            if len(questions) >= 16:
                break

        random.shuffle(questions)
        return questions[:14]


if __name__ == "__main__":
    test_text = """
    Natural Language Processing is a subfield of artificial intelligence that focuses on the interaction between computers and humans. 
    Machine learning is a method of teaching computers to learn from data. Deep learning uses neural networks with many layers.
    Neural networks are computing systems inspired by biological neural networks. Transfer learning allows models to transfer knowledge between tasks.
    Computer vision enables computers to interpret visual information. Speech recognition converts spoken words into text.
    The transformer architecture has revolutionized natural language processing. Attention mechanisms help models focus on relevant information.
    Tokenization breaks text into smaller units. Embeddings represent words as dense vectors. Sentiment analysis determines the emotional tone of text.
    Named entity recognition identifies specific entities in text. Text summarization creates shorter versions of documents.
    Question answering systems can extract answers from large documents. Language models predict the probability of word sequences.
    Why deep convolutional neural network is useful? Because it preserves spatial integrity.
    """
    test_concepts = [
        "artificial intelligence",
        "machine learning",
        "neural networks",
        "deep learning",
        "computer vision",
        "speech recognition",
        "transformer",
        "attention",
        "tokenization",
        "embeddings",
        "sentiment analysis",
        "named entity recognition",
        "text summarization",
        "question answering",
        "language models",
    ]
    qg = QuizGenerator()
    mcqs = qg.generate_mcqs(test_text, test_concepts, test_concepts)
    fib = qg.generate_fill_in_the_blanks(test_text, test_concepts, test_concepts)
    tf = qg.generate_true_false(test_text, test_concepts)
    comp = qg.generate_comprehension(test_text, test_concepts)
    print(f"MCQs {len(mcqs)} FIB {len(fib)} TF {len(tf)} comp {len(comp)}")
    for q in tf[:3]:
        print(q["correct"], q["question"][:70], "…")
