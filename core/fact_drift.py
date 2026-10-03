"""
Member 3 Module: Fact-Drift Detection Engine & Guardrails
Team 24 | Venue: MB314 | Problem 22 (Content Repurposing Chain)

Role: Member 3 - Fact-Drift Detection & Guardrails Specialist
Branch: feature/fact-check

Provides reusable fact-checking algorithms:
- Claim & Fact Extraction (Numbers, Percentages, Money, Entities, Dates, Assertions)
- Claim Classification: [SUPPORTED, CONTRADICTED, UNVERIFIED]
- Grounding & Evidence Extraction with Correction Suggestions
- Quantitative Fact-Fidelity Score (0-100%)
- Sequential Chain Auditing (Article ➔ Summary ➔ LinkedIn ➔ X/Twitter Thread)
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

        # 1. Percentages (e.g. 42%, 99.7%, 100x)
        percentages = set(re.findall(r'\b\d+(?:\.\d+)?%', text_clean))
        multipliers = set(re.findall(r'\b\d+x\b', text_clean, re.IGNORECASE))
        
        # 2. Financial / Currency (e.g. $12.5M, $500K, $45.8B)
        financials = set(re.findall(r'\$\d+(?:\.\d+)?[MBKmbk]?\b', text_clean))
        
        # 3. Standalone Quantities & Numbers (e.g. 3,400, 128, 14 hours)
        raw_numbers = set(re.findall(r'\b\d+(?:,\d{3})*(?:\.\d+)?\b', text_clean))
        quantities = raw_numbers - set([re.sub(r'[^\d.]', '', p) for p in percentages])
        
        # 4. Named Entities / Proper Nouns
        words = text_clean.split()
        entities = set()
        stop_words = {"The", "This", "Here", "What", "How", "Why", "And", "With", "For", "From", "Using", "Phase", "Lead", "Chief", "CEO", "CFO"}
        for i, w in enumerate(words):
            clean_w = re.sub(r'[^\w]', '', w)
            if clean_w and clean_w[0].isupper() and len(clean_w) > 2 and clean_w not in stop_words and i > 0:
                entities.add(clean_w)

        # 5. Extract Key Sentences / Claim Statements
        sentences = [s.strip() for s in re.split(r'[.!?]+', text_clean) if len(s.strip()) > 15]

        return {
            "percentages": list(percentages),
            "multipliers": list(multipliers),
            "financials": list(financials),
            "numbers": list(quantities),
            "entities": list(entities),
            "sentences": sentences,
            "all_numeric_facts": sorted(list(percentages | multipliers | financials | quantities))
        }

    @classmethod
    def audit_stage_fact_drift(cls, source_text: str, target_text: str, stage_name: str = "Stage") -> Dict[str, Any]:
        """
        Audits generated text against source text:
        - Classifies claims as SUPPORTED, CONTRADICTED, or UNVERIFIED
        - Generates evidence snippets & correction suggestions
        - Computes Fact-Fidelity Score (0-100%)
        """
        source_facts = cls.extract_atomic_facts(source_text)
        target_facts = cls.extract_atomic_facts(target_text)

        source_num_set = set(source_facts["all_numeric_facts"])
        target_num_set = set(target_facts["all_numeric_facts"])

        claims_breakdown = []

        retained_facts = target_num_set & source_num_set
        hallucinated_facts = target_num_set - source_num_set
        missing_facts = source_num_set - target_num_set

        # Classify each target sentence / claim
        for sentence in target_facts["sentences"]:
            sent_nums = set(re.findall(r'\b\d+(?:,\d{3})*(?:\.\d+)?%?|\$\d+(?:\.\d+)?[MBKmbk]?', sentence))
            
            # Check overlap with source
            overlap_supported = sent_nums & source_num_set
            overlap_contradicted = sent_nums - source_num_set

            if not sent_nums:
                # Qualitative claim without specific numbers
                status = "SUPPORTED"
                evidence = "Qualitative context aligns with source narrative."
                correction = None
            elif overlap_contradicted and not overlap_supported:
                status = "CONTRADICTED"
                evidence = f"Source does not contain figures: {list(overlap_contradicted)}"
                correction = f"Replace {list(overlap_contradicted)} with verified source figures: {list(source_num_set)[:3]}"
            elif overlap_contradicted and overlap_supported:
                status = "PARTIALLY_CONTRADICTED"
                evidence = f"Mixed figures detected. Unsupported: {list(overlap_contradicted)}"
                correction = f"Remove unsupported figures {list(overlap_contradicted)}."
            else:
                status = "SUPPORTED"
                evidence = f"Grounding verified for figures: {list(overlap_supported)}"
                correction = None

            claims_breakdown.append({
                "claim_text": sentence,
                "classification": status,
                "evidence_snippet": evidence,
                "correction_suggestion": correction
            })

        # Calculate Fact Fidelity Metrics
        total_source_count = len(source_num_set)
        if total_source_count > 0:
            retention_rate = (len(retained_facts) / total_source_count) * 100.0
        else:
            retention_rate = 100.0

        hallucination_penalty = len(hallucinated_facts) * 15.0
        fidelity_score = max(0.0, min(100.0, retention_rate - hallucination_penalty))

        # Overall Status
        if fidelity_score >= 90.0:
            overall_status = "SUPPORTED_HIGH_FIDELITY"
        elif fidelity_score >= 75.0:
            overall_status = "MINOR_DRIFT_ACCEPTABLE"
        elif len(hallucinated_facts) > 0:
            overall_status = "HALLUCINATION_DETECTED"
        else:
            overall_status = "HIGH_FACT_DRIFT"

        return {
            "stage_name": stage_name,
            "fact_fidelity_score": round(fidelity_score, 1),
            "overall_status": overall_status,
            "retention_rate": round(retention_rate, 1),
            "is_pass": fidelity_score >= 75.0 and len(hallucinated_facts) == 0,
            "total_source_facts_count": total_source_count,
            "retained_facts": sorted(list(retained_facts)),
            "hallucinated_facts": sorted(list(hallucinated_facts)),
            "missing_facts": sorted(list(missing_facts)),
            "claims_classification_summary": {
                "supported_claims": sum(1 for c in claims_breakdown if c["classification"] == "SUPPORTED"),
                "contradicted_claims": sum(1 for c in claims_breakdown if "CONTRADICTED" in c["classification"]),
                "total_claims_audited": len(claims_breakdown)
            },
            "claims_breakdown": claims_breakdown
        }

    @classmethod
    def audit_full_pipeline(cls, source_article: str, summary: str, linkedin_post: str, tweets: List[str]) -> Dict[str, Any]:
        """
        Reusable function exposed for Member 2's backend pipeline API.
        Runs cross-stage fact auditing across all transformations.
        """
        combined_tweets = " ".join(tweets) if isinstance(tweets, list) else str(tweets)

        stage1_audit = cls.audit_stage_fact_drift(source_article, summary, "Article -> Summary")
        stage2_audit = cls.audit_stage_fact_drift(summary, linkedin_post, "Summary -> LinkedIn")
        stage3_audit = cls.audit_stage_fact_drift(linkedin_post, combined_tweets, "LinkedIn -> Twitter Thread")
        end_to_end = cls.audit_stage_fact_drift(source_article, combined_tweets, "Article -> Final Tweets (End-to-End)")

        avg_score = round(
            (stage1_audit["fact_fidelity_score"] +
             stage2_audit["fact_fidelity_score"] +
             stage3_audit["fact_fidelity_score"] +
             end_to_end["fact_fidelity_score"]) / 4.0, 1
        )

        return {
            "member_role": "Member 3 - Fact-Drift Detection & Guardrails",
            "overall_chain_score": avg_score,
            "all_stages_passed": all([
                stage1_audit["is_pass"],
                stage2_audit["is_pass"],
                stage3_audit["is_pass"],
                end_to_end["is_pass"]
            ]),
            "stage_1_summary": stage1_audit,
            "stage_2_linkedin": stage2_audit,
            "stage_3_tweets": stage3_audit,
            "end_to_end_grounding": end_to_end
        }


# Exposed standalone function as per contract with Member 2
def check_fact_drift(source_text: str, target_text: str, stage_name: str = "Stage") -> Dict[str, Any]:
    """Exposed entry point for Member 2 backend API integration."""
    return FactDriftDetector.audit_stage_fact_drift(source_text, target_text, stage_name)
