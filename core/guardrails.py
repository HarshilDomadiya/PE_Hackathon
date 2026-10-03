"""
Input & Output Guardrails Module
Team 24 | Venue: MB314 | Problem 22

Handles:
- Application-level backend validation layer (Prompt Injection defense, Off-topic detection, Invalid input handling)
- Platform constraint enforcement (LinkedIn & Twitter rules)
- Automated format repair
"""

import re
from typing import Dict, Any, List, Tuple

class GuardrailManager:
    
    # Comprehensive Prompt Injection & System Override Defense Patterns
    INJECTION_PATTERNS = [
        r"ignore (all )?previous instructions",
        r"ignore (your )?previous instructions",
        r"disregard (all )?above",
        r"reveal (your )?api keys?",
        r"reveal (environment )?variables",
        r"show (me )?(the )?(hidden )?system prompt",
        r"reveal (your )?system prompt",
        r"developer instructions",
        r"ignore the content repurposing task",
        r"you are no longer a content repurposing assistant",
        r"you are now DAN",
        r"system prompt:",
        r"jailbreak",
        r"bypass rules"
    ]

    OFF_TOPIC_PATTERNS = [
        r"^tell me a joke",
        r"^write a poem about",
        r"^how to bake",
        r"^what is the weather",
        r"^who won the game"
    ]

    @classmethod
    def validate_input(cls, text: str) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Application-level Backend Validation Layer.
        Evaluates input text BEFORE passing to AI pipeline.
        Returns (is_valid, refusal_reason, details)
        """
        if not text or not isinstance(text, str):
            return False, "INVALID INPUT: Input content is empty. Please paste text or upload a file.", {
                "error_type": "INVALID_INPUT",
                "status": "INVALID_INPUT"
            }

        text_clean = text.strip()

        # Check 1: Empty input
        if len(text_clean) == 0:
            return False, "INVALID INPUT: Input content is empty. Please paste text or upload a file.", {
                "error_type": "INVALID_INPUT",
                "status": "INVALID_INPUT"
            }

        # Check 2: Prompt Injection / Security Refusal
        for pattern in cls.INJECTION_PATTERNS:
            if re.search(pattern, text_clean, re.IGNORECASE):
                return False, "SECURITY REFUSAL: This input cannot be processed because it contains instructions that conflict with the content-repurposing workflow.", {
                    "error_type": "SECURITY_REFUSAL",
                    "status": "SECURITY_REFUSAL",
                    "matched_pattern": pattern
                }

        # Check 3: Short input (< 50 chars)
        if len(text_clean) < 50:
            return False, "INVALID INPUT: Input article is too short. Please provide a full article or blog post (at least 50 characters).", {
                "error_type": "INVALID_INPUT",
                "status": "INVALID_INPUT",
                "char_count": len(text_clean)
            }

        # Check 4: Off-topic input check
        for pattern in cls.OFF_TOPIC_PATTERNS:
            if re.search(pattern, text_clean, re.IGNORECASE):
                return False, "OFF-TOPIC INPUT: Input content is off-topic and does not contain article/report content to repurpose.", {
                    "error_type": "OFF_TOPIC_INPUT",
                    "status": "OFF_TOPIC_INPUT",
                    "matched_pattern": pattern
                }

        words = text_clean.split()
        if len(words) < 8 and not any(char.isdigit() for char in text_clean):
            return False, "OFF-TOPIC INPUT: Input does not contain sufficient prose or factual data to repurpose into social content.", {
                "error_type": "OFF_TOPIC_INPUT",
                "status": "OFF_TOPIC_INPUT",
                "word_count": len(words)
            }

        return True, "", {"status": "PASSED", "word_count": len(words), "char_count": len(text_clean)}

    @classmethod
    def enforce_linkedin_constraints(cls, linkedin_post: str) -> Dict[str, Any]:
        """
        Enforces LinkedIn platform rules programmatically:
        - Character limit (< 1500 chars)
        - Bullet point structure
        - Hashtags (3-4 hashtags)
        """
        char_count = len(linkedin_post)
        hashtags = re.findall(r'#\w+', linkedin_post)
        has_bullets = "•" in linkedin_post or "-" in linkedin_post or "*" in linkedin_post

        violations = []
        is_compliant = True

        if char_count >= 1500:
            violations.append(f"LinkedIn post exceeds 1,500 character limit (actual: {char_count} chars).")
            is_compliant = False

        if len(hashtags) < 2 or len(hashtags) > 5:
            violations.append(f"Hashtag count outside target 3–4 range (actual: {len(hashtags)}).")
            is_compliant = False

        if not has_bullets:
            violations.append("Post lacks structured bullet points for readability.")

        status_text = "VALIDATION PASSED" if is_compliant else "VALIDATION FAILED"

        return {
            "platform": "LinkedIn",
            "status_title": status_text,
            "is_compliant": is_compliant,
            "char_count": char_count,
            "max_allowed": 1500,
            "hashtag_count": len(hashtags),
            "hashtags_found": hashtags,
            "has_bullet_points": has_bullets,
            "violations": violations,
            "summary_message": f"{status_text}: {char_count} chars (Limit: 1500) | {len(hashtags)} hashtags" if is_compliant else f"{status_text}: {', '.join(violations)}"
        }

    @classmethod
    def enforce_tweet_thread_constraints(cls, tweets: List[str]) -> Dict[str, Any]:
        """
        Enforces Twitter/X thread rules programmatically:
        - 3-6 tweets
        - Each tweet <= 280 characters
        - Explicit index numbering (1/N, 2/N)
        """
        violations = []
        tweet_analysis = []
        is_compliant = True

        if len(tweets) < 3 or len(tweets) > 6:
            violations.append(f"Thread count out of 3–6 tweet range (actual: {len(tweets)} tweets).")
            is_compliant = False

        for idx, tweet in enumerate(tweets, start=1):
            char_len = len(tweet)
            hashtags = re.findall(r'#\w+', tweet)
            
            has_indexing = bool(re.search(rf'\(?{idx}/{len(tweets)}\)?', tweet) or re.search(rf'^{idx}/{len(tweets)}', tweet))
            
            tweet_violations = []

            if char_len > 280:
                overflow = char_len - 280
                tweet_violations.append(f"Tweet {idx} exceeds 280-character limit by {overflow} characters (actual: {char_len} chars).")
                is_compliant = False

            if not has_indexing:
                tweet_violations.append(f"Tweet {idx} missing thread numbering prefix {idx}/{len(tweets)}")
                is_compliant = False

            tweet_analysis.append({
                "tweet_num": idx,
                "char_count": char_len,
                "is_valid_len": char_len <= 280,
                "has_indexing": has_indexing,
                "violations": tweet_violations
            })

        status_text = "VALIDATION PASSED" if is_compliant else "VALIDATION FAILED"

        return {
            "platform": "Twitter/X Thread",
            "status_title": status_text,
            "is_compliant": is_compliant,
            "total_tweets": len(tweets),
            "tweet_analysis": tweet_analysis,
            "violations": violations,
            "summary_message": f"{status_text}: {len(tweets)} tweets (All <= 280 chars, indexed 1/N)" if is_compliant else f"{status_text}: {', '.join(violations)}"
        }

    @classmethod
    def auto_repair_tweets(cls, tweets: List[str]) -> List[str]:
        """Auto-repairs tweets if they exceed character count or lack indexing."""
        repaired = []
        total = len(tweets)

        for idx, tweet in enumerate(tweets, start=1):
            curr = tweet.strip()

            prefix = f"{idx}/{total} "
            if not re.search(rf'^\d+/\d+\s*', curr):
                curr = f"{prefix}{curr}"
            else:
                curr = re.sub(r'^\d+/\d+\s*', prefix, curr)

            # Strict 280 character enforcement
            if len(curr) > 280:
                curr = curr[:277] + "..."

            repaired.append(curr)

        return repaired
