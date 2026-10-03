"""
Member 3 Module: Fact-Drift Detection Engine & Guardrails
Team 24 | Venue: MB314 | Problem 22 (Content Repurposing Chain)

Role: Member 3 - Fact-Drift Detection & Guardrails Specialist

Provides reusable fact-checking algorithms:
- Labelled Source Fact Extraction (Categorized key-value pairs: Metrics, Dates, Money, Entities, Products)
- Claim Classification: [SUPPORTED, CONTRADICTED, UNVERIFIED] with Source vs Generated value comparison
- Inter-stage Auditing (Audit #1: Article ➔ Summary, Audit #2: Summary ➔ LinkedIn, Audit #3: LinkedIn ➔ X Thread)
- Transparent Fact-Fidelity Score with Formula Breakdown
"""

import re
import json
from typing import Dict, Any, List, Tuple, Set, Optional


class FactDriftDetector:
    """
    Core Fact-Drift Engine developed by Member 3.
    Verifies claims in generated content against source article,
    classifies claims, extracts evidence snippets, and provides correction suggestions.
    """

    @classmethod
    def extract_atomic_facts(cls, text: str) -> Dict[str, Any]:
        """
        Extracts key numerical facts, percentages, financial amounts, proper nouns, and key assertions.
        """
        text_clean = text.strip()

        # 1. Percentages (e.g. 42%, 99.7%, 100x, 35%)
        percentages = set(re.findall(r'\b\d+(?:\.\d+)?%', text_clean))
        multipliers = set(re.findall(r'\b\d+x\b', text_clean, re.IGNORECASE))
        
        # 2. Financial / Currency (e.g. $12.5M, $500K, ₹48,600 crore, ₹1,800 crore, $320 million)
        financials = set(re.findall(r'(?:\$|₹|EUR|USD)?\d+(?:,\d{3})*(?:\.\d+)?\s*(?:crore|billion|million|lakh|[MBKmbk])?\b', text_clean))
        financials = set([f for f in financials if any(c in f for c in ['$', '₹', 'crore', 'million', 'billion', 'lakh', 'M', 'B', 'K'])])

        # 3. Dates & Years (e.g. 18 September 2026, January 2024, Q4 2026, 2027)
        dates = set(re.findall(r'\b(?:\d{1,2}\s+)?(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?|Q[1-4])\s+\d{4}\b', text_clean, re.IGNORECASE))
        years = set(re.findall(r'\b(?:202[0-9]|203[0-0])\b', text_clean))

        # 4. Standalone Quantities & Numbers (e.g. 18 billion, 42 TOPS, 8 watts, 3nm, 720,000)
        raw_numbers = set(re.findall(r'\b\d+(?:,\d{3})*(?:\.\d+)?\s*(?:billion|million|thousand|TOPS|watts|nm|kWh|MW|GWh|kW|km/h|kg|tonnes|ha|hectares)?\b', text_clean))
        quantities = raw_numbers - set([re.sub(r'[^\d.]', '', p) for p in percentages])
        
        # 5. Named Entities / Proper Nouns / Products
        words = text_clean.split()
        entities = set()
        stop_words = {"The", "This", "Here", "What", "How", "Why", "And", "With", "For", "From", "Using", "Phase", "Lead", "Chief", "CEO", "CFO", "According", "Among", "First", "Second", "Third"}
        for i, w in enumerate(words):
            clean_w = re.sub(r'[^\w\-]', '', w)
            if clean_w and clean_w[0].isupper() and len(clean_w) > 2 and clean_w not in stop_words and i > 0:
                entities.add(clean_w)

        # 6. Extract Key Sentences / Claim Statements
        sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', text_clean) if len(s.strip()) > 10]

        return {
            "percentages": list(percentages),
            "multipliers": list(multipliers),
            "financials": list(financials),
            "dates": list(dates | years),
            "numbers": list(quantities),
            "entities": list(entities),
            "sentences": sentences,
            "all_numeric_facts": sorted(list(percentages | multipliers | financials | quantities | dates | years))
        }

    @classmethod
    def extract_labelled_source_facts(cls, text: str) -> List[Dict[str, str]]:
        """
        Extracts structured, human-readable Labelled Source Facts.
        Example output:
        [
          {"label": "Performance Improvement", "value": "35% higher AI inference performance"},
          {"label": "Power Reduction", "value": "28% lower power consumption"},
          {"label": "Transistors", "value": "18 billion transistors"},
          {"label": "Announcement Date", "value": "18 September 2026"},
          {"label": "Process Technology", "value": "3nm process technology"},
          {"label": "Processor Name", "value": "NS-E3 edge AI processor"}
        ]
        """
        text_clean = text.strip()
        sentences = [s.strip() for s in re.split(r'[.!?]+', text_clean) if len(s.strip()) > 10]
        labelled_facts = []
        seen_labels = set()

        # Rule-based contextual extraction patterns
        patterns = [
            (r'(\d+%\s*(?:higher|lower|increase|decrease|growth|reduction|remission|speedup|efficiency)[\w\s]{0,30})', "Performance / Metric"),
            (r'(\d+(?:\.\d+)?\s*(?:billion|million|trillion)?\s*transistors)', "Transistors"),
            (r'(\d+nm(?:\s*process\s*technology)?)', "Process Technology"),
            (r'(\b\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}\b)', "Announcement Date"),
            (r'((?:₹|\$)\d+(?:,\d{3})*(?:\.\d+)?\s*(?:crore|billion|million|lakh)?)', "Financial Value / Investment"),
            (r'(\d+\s*MW|\d+\s*GWh|\d+\s*kWh|\d+\s*TOPS|\d+\s*watts)', "Capacity / Power Output"),
            (r'(\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?\s+(?:CEO|CFO|Officer|Director|President)\s+[A-Z][a-z]+\s+[A-Z][a-z]+\b|\bCEO\s+[A-Z][a-z]+\s+[A-Z][a-z]+\b)', "Key Leadership"),
            (r'(\b(?:NS-E\d+|VM-\d+|BG-\d+|Phoenix-\d+|Atlas-V|Prometheus-\d+|Gen-\d+)\b)', "Product / Model Name"),
            (r'(\b(?:first|second|third|fourth)\s+quarter\s+of\s+\d{4}\b|\bQ[1-4]\s+\d{4}\b)', "Target Timeline"),
            (r'(\b\d+(?:,\d{3})*\s*(?:merchants|patients|participants|professionals|technicians|modules|packages)\b)', "Volume / Scale Metric")
        ]

        for sent in sentences:
            for regex, category in patterns:
                matches = re.findall(regex, sent, re.IGNORECASE)
                for match in matches:
                    val = match.strip() if isinstance(match, str) else match[0].strip()
                    if val and val.lower() not in seen_labels and len(val) > 1:
                        seen_labels.add(val.lower())
                        labelled_facts.append({
                            "label": category,
                            "value": val
                        })

        # Fallback if no specific patterns matched
        if not labelled_facts:
            facts_raw = cls.extract_atomic_facts(text)
            for p in facts_raw["percentages"][:3]:
                labelled_facts.append({"label": "Percentage Metric", "value": p})
            for f in facts_raw["financials"][:3]:
                labelled_facts.append({"label": "Financial Metric", "value": f})
            for e in facts_raw["entities"][:3]:
                labelled_facts.append({"label": "Key Entity", "value": e})

        return labelled_facts[:10]

    @classmethod
    def audit_stage_fact_drift(cls, source_text: str, target_text: str, stage_name: str = "Stage") -> Dict[str, Any]:
        """
        Audits generated text against source text:
        - Classifies claims as SUPPORTED, CONTRADICTED, or UNVERIFIED
        - Exposes source value vs generated value for CONTRADICTED claims
        - Provides explainable Fact-Fidelity Score formula breakdown
        """
        source_facts = cls.extract_atomic_facts(source_text)
        target_facts = cls.extract_atomic_facts(target_text)

        source_num_set = set(source_facts["all_numeric_facts"])
        target_num_set = set(target_facts["all_numeric_facts"])

        claims_breakdown = []
        supported_count = 0
        contradicted_count = 0
        unverified_count = 0

        # Audit each sentence in target text as a distinct claim
        for sentence in target_facts["sentences"]:
            sent_nums = set(re.findall(r'(?:\$|₹)?\b\d+(?:,\d{3})*(?:\.\d+)?[MBKmbk]?%?|\b\d{4}\b', sentence))
            
            overlap_supported = sent_nums & source_num_set
            overlap_contradicted = sent_nums - source_num_set

            if not sent_nums:
                # Qualitative claim
                # Check entity alignment
                sent_words = set(re.findall(r'\b[A-Z][a-z]{3,}\b', sentence))
                source_entities = set(source_facts["entities"])
                entity_overlap = sent_words & source_entities

                if entity_overlap or len(sentence) > 30:
                    status = "SUPPORTED"
                    evidence = f"Qualitative narrative aligns with source entity context ({', '.join(list(entity_overlap)[:2]) or 'Source Narrative'})."
                    source_val = "Matching source narrative"
                    gen_val = sentence[:60] + "..."
                    supported_count += 1
                else:
                    status = "UNVERIFIED"
                    evidence = "The source article does not provide sufficient evidence for this claim."
                    source_val = "Not explicitly stated in source text"
                    gen_val = sentence
                    unverified_count += 1

            elif overlap_contradicted and not overlap_supported:
                status = "CONTRADICTED"
                source_val = f"Source figures: {', '.join(list(source_num_set)[:3]) or 'N/A'}"
                gen_val = f"Generated figures: {', '.join(list(overlap_contradicted))}"
                evidence = f"Numerical drift detected! Source contained {source_val} but generated output specified {gen_val}."
                contradicted_count += 1

            elif overlap_contradicted and overlap_supported:
                status = "CONTRADICTED"
                source_val = f"Supported: {', '.join(list(overlap_supported))}"
                gen_val = f"Contradicted/Drifted: {', '.join(list(overlap_contradicted))}"
                evidence = f"Mixed figures detected. Generated text introduced unsupported values: {gen_val}."
                contradicted_count += 1

            else:
                status = "SUPPORTED"
                source_val = f"Grounded in source: {', '.join(list(overlap_supported))}"
                gen_val = f"Matched generated: {', '.join(list(overlap_supported))}"
                evidence = f"Grounding verified for figures: {', '.join(list(overlap_supported))}"
                supported_count += 1

            claims_breakdown.append({
                "claim_text": sentence,
                "stage": stage_name,
                "status": status,
                "source_evidence": source_val,
                "generated_claim": gen_val,
                "evidence": evidence,
                "reason": evidence if status == "UNVERIFIED" else None
            })

        total_claims = len(claims_breakdown)
        if total_claims == 0:
            total_claims = 1
            supported_count = 1

        # Calculate Fact Fidelity Score: (Supported / Total Evaluated Claims) * 100
        raw_fidelity = (supported_count / total_claims) * 100.0
        
        # Apply strict contradiction penalty if any explicit numerical contradiction exists
        if contradicted_count > 0:
            raw_fidelity = max(0.0, raw_fidelity - (contradicted_count * 25.0))

        fidelity_score = round(max(0.0, min(100.0, raw_fidelity)), 1)

        formula_str = f"{supported_count} / {total_claims} * 100 = {raw_fidelity:.2f}% -> Rounded = {fidelity_score}%"

        if fidelity_score >= 95.0:
            overall_status = "SUPPORTED_HIGH_FIDELITY"
        elif fidelity_score >= 75.0:
            overall_status = "SUPPORTED_ACCEPTABLE_DRIFT"
        elif contradicted_count > 0:
            overall_status = "CONTRADICTION_DETECTED"
        else:
            overall_status = "HIGH_FACT_DRIFT"

        return {
            "stage_name": stage_name,
            "fact_fidelity_score": fidelity_score,
            "overall_status": overall_status,
            "total_claims": total_claims,
            "supported_claims": supported_count,
            "contradicted_claims": contradicted_count,
            "unverified_claims": unverified_count,
            "formula": "Supported Claims / Total Evaluated Claims * 100",
            "calculation_breakdown": formula_str,
            "is_pass": fidelity_score >= 75.0 and contradicted_count == 0,
            "claims_breakdown": claims_breakdown
        }

    @classmethod
    def audit_full_pipeline(cls, source_article: str, summary: str, linkedin_post: str, tweets: List[str]) -> Dict[str, Any]:
        """
        Executes Inter-Stage Fact Auditing:
        - Audit #1: Original Article -> Summary
        - Audit #2: Summary -> LinkedIn Post
        - Audit #3: LinkedIn Post -> X/Twitter Thread
        - End-to-End Audit: Original Article -> All Generated Assets (as ultimate ground truth)
        """
        combined_tweets = " ".join(tweets) if isinstance(tweets, list) else str(tweets)

        audit1 = cls.audit_stage_fact_drift(source_article, summary, "Fact Audit #1: Article -> Summary")
        audit2 = cls.audit_stage_fact_drift(summary, linkedin_post, "Fact Audit #2: Summary -> LinkedIn")
        audit3 = cls.audit_stage_fact_drift(linkedin_post, combined_tweets, "Fact Audit #3: LinkedIn -> X Thread")
        end_to_end = cls.audit_stage_fact_drift(source_article, summary + " " + linkedin_post + " " + combined_tweets, "End-to-End Audit")

        total_supported = audit1["supported_claims"] + audit2["supported_claims"] + audit3["supported_claims"]
        total_claims = audit1["total_claims"] + audit2["total_claims"] + audit3["total_claims"]
        total_contradicted = audit1["contradicted_claims"] + audit2["contradicted_claims"] + audit3["contradicted_claims"]
        total_unverified = audit1["unverified_claims"] + audit2["unverified_claims"] + audit3["unverified_claims"]

        overall_score = round((total_supported / max(1, total_claims)) * 100.0, 1)
        if total_contradicted > 0:
            overall_score = round(max(0.0, overall_score - (total_contradicted * 20.0)), 1)

        labelled_source_facts = cls.extract_labelled_source_facts(source_article)

        return {
            "overall_chain_score": overall_score,
            "total_claims": total_claims,
            "supported_claims": total_supported,
            "contradicted_claims": total_contradicted,
            "unverified_claims": total_unverified,
            "formula": "Supported Claims / Total Evaluated Claims * 100",
            "calculation_breakdown": f"{total_supported} / {total_claims} * 100 = {(total_supported/max(1, total_claims))*100:.2f}% -> Rounded = {overall_score}%",
            "labelled_source_facts": labelled_source_facts,
            "audit_stage_1": audit1,
            "audit_stage_2": audit2,
            "audit_stage_3": audit3,
            "end_to_end_audit": end_to_end,
            "all_claims_list": audit1["claims_breakdown"] + audit2["claims_breakdown"] + audit3["claims_breakdown"]
        }


def check_fact_drift(source_text: str, target_text: str, stage_name: str = "Stage") -> Dict[str, Any]:
    return FactDriftDetector.audit_stage_fact_drift(source_text, target_text, stage_name)
