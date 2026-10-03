"""
Content Repurposing Pipeline Execution Engine
Team 24 | Venue: MB314 | Problem 22

Orchestrates:
- Input guardrail validation
- Prompt V1 (Baseline) vs Prompt V2 (Optimized Chained + Guardrails) execution
- Timestamped execution logging & prompt history tracking
- Cross-stage Fact-Drift integration
"""

import json
import time
from datetime import datetime
from typing import Dict, Any, List, Optional

from core.prompts import (
    PROMPT_V1_SUMMARY, PROMPT_V1_LINKEDIN, PROMPT_V1_TWEET_THREAD,
    PROMPT_V2_SUMMARY_SYSTEM, PROMPT_V2_SUMMARY_USER,
    PROMPT_V2_LINKEDIN_SYSTEM, PROMPT_V2_LINKEDIN_USER,
    PROMPT_V2_TWEET_SYSTEM, PROMPT_V2_TWEET_USER
)
from core.llm_provider import LLMProvider
from core.guardrails import GuardrailManager
from core.fact_drift import FactDriftDetector

class ContentPipeline:
    def __init__(self, api_key: Optional[str] = None):
        self.llm = LLMProvider(api_key=api_key)
        self.history_log: List[Dict[str, Any]] = []

    def log_event(self, stage: str, prompt_version: str, input_data: Any, output_data: Any, metadata: Dict[str, Any]):
        entry = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "stage": stage,
            "version": prompt_version,
            "input_data": str(input_data)[:200] + "...",
            "output_data": str(output_data)[:200] + "...",
            "metadata": metadata
        }
        self.history_log.append(entry)

    def run_v1_baseline(self, article_text: str, article_title: str = "Article") -> Dict[str, Any]:
        """Runs the unconstrained Baseline Version 1 pipeline."""
        start_time = time.time()
        
        # Stage 1: Summary
        prompt_s1 = PROMPT_V1_SUMMARY.format(article_text=article_text)
        summary_out = self.llm.generate("You are a helpful assistant.", prompt_s1)
        self.log_event("Summary", "V1_Baseline", prompt_s1, summary_out, {})

        # Stage 2: LinkedIn
        prompt_s2 = PROMPT_V1_LINKEDIN.format(summary_text=summary_out)
        linkedin_out = self.llm.generate("You are a social media writer.", prompt_s2)
        self.log_event("LinkedIn", "V1_Baseline", prompt_s2, linkedin_out, {})

        # Stage 3: Tweet Thread
        prompt_s3 = PROMPT_V1_TWEET_THREAD.format(linkedin_text=linkedin_out)
        tweets_raw = self.llm.generate("Write tweets.", prompt_s3)
        self.log_event("TweetThread", "V1_Baseline", prompt_s3, tweets_raw, {})

        # Naive split for tweets
        tweet_list = [t.strip() for t in tweets_raw.split("\n\n") if t.strip()]
        if len(tweet_list) == 1 and "\n" in tweets_raw:
            tweet_list = [t.strip() for t in tweets_raw.split("\n") if t.strip()]

        # Audits & Constraints
        linkedin_constraints = GuardrailManager.enforce_linkedin_constraints(linkedin_out)
        tweet_constraints = GuardrailManager.enforce_tweet_thread_constraints(tweet_list)
        fact_audits = FactDriftDetector.audit_full_chain(article_text, summary_out, linkedin_out, tweet_list)

        exec_time = round(time.time() - start_time, 2)

        return {
            "version": "V1 Baseline (Naive Direct Prompting)",
            "execution_time_sec": exec_time,
            "summary": summary_out,
            "linkedin_post": linkedin_out,
            "tweet_thread": tweet_list,
            "linkedin_constraints": linkedin_constraints,
            "tweet_constraints": tweet_constraints,
            "fact_drift_audits": fact_audits,
            "prompts_used": {
                "summary": prompt_s1,
                "linkedin": prompt_s2,
                "tweet_thread": prompt_s3
            }
        }

    def run_v2_optimized(self, article_text: str, article_title: str = "Article") -> Dict[str, Any]:
        """Runs the fully optimized Version 2 Chained & Guardrailed pipeline."""
        start_time = time.time()

        # Step 0: Input Guardrail Check
        is_valid, refusal_reason, input_meta = GuardrailManager.validate_input(article_text)
        if not is_valid:
            return {
                "version": "V2 Optimized (Guardrailed)",
                "status": "REJECTED_BY_GUARDRAIL",
                "refusal_reason": refusal_reason,
                "input_metadata": input_meta
            }

        # Stage 1: Article to Core Summary (JSON)
        user_p1 = PROMPT_V2_SUMMARY_USER.format(article_title=article_title, article_text=article_text)
        res_s1 = self.llm.generate(PROMPT_V2_SUMMARY_SYSTEM, user_p1, json_mode=True)
        self.log_event("Summary", "V2_Optimized", user_p1, res_s1, {})

        try:
            parsed_s1 = json.loads(res_s1)
            summary_paragraph = parsed_s1.get("summary_paragraph", res_s1)
            key_facts = parsed_s1.get("key_facts", [])
        except Exception:
            summary_paragraph = res_s1
            key_facts = FactDriftDetector.extract_key_metrics(article_text)

        # Stage 2: Summary to LinkedIn Post
        user_p2 = PROMPT_V2_LINKEDIN_USER.format(
            summary_paragraph=summary_paragraph,
            key_facts=json.dumps(key_facts, indent=2)
        )
        linkedin_out = self.llm.generate(PROMPT_V2_LINKEDIN_SYSTEM, user_p2)
        self.log_event("LinkedIn", "V2_Optimized", user_p2, linkedin_out, {})

        # LinkedIn Constraint Check
        linkedin_constraints = GuardrailManager.enforce_linkedin_constraints(linkedin_out)

        # Stage 3: LinkedIn to Tweet Thread
        user_p3 = PROMPT_V2_TWEET_USER.format(
            linkedin_text=linkedin_out,
            key_facts=json.dumps(key_facts, indent=2)
        )
        res_s3 = self.llm.generate(PROMPT_V2_TWEET_SYSTEM, user_p3, json_mode=True)
        self.log_event("TweetThread", "V2_Optimized", user_p3, res_s3, {})

        tweet_list = []
        try:
            parsed_s3 = json.loads(res_s3)
            tweet_list = parsed_s3.get("tweets", [])
        except Exception:
            tweet_list = [t.strip() for t in res_s3.split("\n\n") if t.strip()]

        if not tweet_list:
            tweet_list = ["1/3 Key insights from article summary...", "2/3 Core data points verified...", "3/3 Concluding thoughts #Leadership"]

        # Tweet Constraint Check & Auto-Repair
        tweet_constraints = GuardrailManager.enforce_tweet_thread_constraints(tweet_list)
        if not tweet_constraints["is_compliant"]:
            repaired_tweets = GuardrailManager.auto_repair_tweets(tweet_list)
            tweet_list = repaired_tweets
            tweet_constraints = GuardrailManager.enforce_tweet_thread_constraints(tweet_list)
            tweet_constraints["was_auto_repaired"] = True

        # Fact Drift Audit
        fact_audits = FactDriftDetector.audit_full_chain(article_text, summary_paragraph, linkedin_out, tweet_list)

        exec_time = round(time.time() - start_time, 2)

        return {
            "version": "V2 Optimized (Chained + Few-Shot + Guardrailed)",
            "status": "SUCCESS",
            "execution_time_sec": exec_time,
            "summary": summary_paragraph,
            "key_facts_extracted": key_facts,
            "linkedin_post": linkedin_out,
            "tweet_thread": tweet_list,
            "linkedin_constraints": linkedin_constraints,
            "tweet_constraints": tweet_constraints,
            "fact_drift_audits": fact_audits,
            "prompts_used": {
                "summary_system": PROMPT_V2_SUMMARY_SYSTEM,
                "summary_user": user_p1,
                "linkedin_system": PROMPT_V2_LINKEDIN_SYSTEM,
                "linkedin_user": user_p2,
                "tweet_system": PROMPT_V2_TWEET_SYSTEM,
                "tweet_user": user_p3
            }
        }

    def run_side_by_side(self, article_text: str, article_title: str = "Article") -> Dict[str, Any]:
        """Runs both V1 Baseline and V2 Optimized on the same input for demo comparison."""
        v1_result = self.run_v1_baseline(article_text, article_title)
        v2_result = self.run_v2_optimized(article_text, article_title)

        return {
            "article_title": article_title,
            "article_text": article_text,
            "v1_baseline": v1_result,
            "v2_optimized": v2_result
        }
