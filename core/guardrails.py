"""
Input & Output Guardrails Module
Team 24 | Venue: MB314 | Problem 22

Handles:
- Input validation (Off-topic detection, Prompt injection defense, Refusal handling)
- Platform constraint enforcement (LinkedIn & Twitter rules)
- Automated format repair
"""

import re
from typing import Dict, Any, List, Tuple

class GuardrailManager:
    
    # Prompt injection patterns
    INJECTION_PATTERNS = [
        r"ignore (all )?previous instructions",
        r"disregard (all )?above",
        r"you are now DAN",
        r"system prompt:",
        r"jailbreak",
        r"bypass rules",
        r"reveal your system prompt"
    ]

    @classmethod
    def validate_input(cls, text: str) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Validates input article content.
        Returns (is_valid, refusal_reason, details)
        """
        text_clean = text.strip()

        # Check 1: Prompt Injection / Adversarial attack check
        for pattern in cls.INJECTION_PATTERNS:
            if re.search(pattern, text_clean, re.IGNORECASE):
                return False, "Security Refusal: Potential prompt injection or system override attempt detected in input.", {
                    "error_type": "PROMPT_INJECTION",
                    "matched_pattern": pattern
                }

        # Check 2: Minimum length check
        if len(text_clean) < 100:
            return False, "Input article is too short. Please provide a full article or blog post (at least 100 characters).", {
                "error_type": "SHORT_INPUT",
                "char_count": len(text_clean)
            }

        # Check 3: Off-Topic / Garbage check (e.g. random code, nonsensical repetition)
        words = text_clean.split()
        if len(words) < 15:
            return False, "Input does not contain sufficient prose/sentences to repurpose into social content.", {
                "error_type": "OFF_TOPIC",
                "word_count": len(words)
            }

        # Check if text is just code or json
        if text_clean.startswith("{") and text_clean.endswith("}"):
            return False, "Input appears to be raw JSON data rather than a readable article.", {
                "error_type": "INVALID_FORMAT"
            }

        return True, "", {"status": "PASSED", "word_count": len(words), "char_count": len(text_clean)}

    @classmethod
    def enforce_linkedin_constraints(cls, linkedin_post: str) -> Dict[str, Any]:
        """
        Enforces LinkedIn platform rules:
        - Character limit (< 3000 chars)
        - Hashtag count (3-5 hashtags)
        - Structure (bullets, spaces)
        """
        char_count = len(linkedin_post)
        hashtags = re.findall(r'#\w+', linkedin_post)
        has_bullets = "•" in linkedin_post or "-" in linkedin_post or "*" in linkedin_post
        has_cta = "?" in linkedin_post or "comment" in linkedin_post.lower() or "thought" in linkedin_post.lower()

        violations = []
        is_compliant = True

        if char_count > 3000:
            violations.append(f"Post exceeds max LinkedIn character limit of 3000 (actual: {char_count}).")
            is_compliant = False
        
        if len(hashtags) < 2 or len(hashtags) > 6:
            violations.append(f"Hashtag count out of optimal range (2-5). Found {len(hashtags)} hashtags.")
            is_compliant = False

        if not has_bullets:
            violations.append("Post lacks structured bullet points for readability.")

        return {
            "platform": "LinkedIn",
            "is_compliant": is_compliant,
            "char_count": char_count,
            "max_allowed": 3000,
            "hashtag_count": len(hashtags),
            "hashtags_found": hashtags,
            "has_bullet_points": has_bullets,
            "has_call_to_action": has_cta,
            "violations": violations
        }

    @classmethod
    def enforce_tweet_thread_constraints(cls, tweets: List[str]) -> Dict[str, Any]:
        """
        Enforces Twitter/X thread rules:
        - Each tweet <= 280 characters
        - Explicit index numbering (1/N)
        - Thread count (3-7 tweets)
        - Max 2 hashtags per tweet
        """
        violations = []
        tweet_analysis = []
        is_compliant = True

        if len(tweets) < 2 or len(tweets) > 8:
            violations.append(f"Thread length out of bounds (3-7 tweets recommended). Found {len(tweets)} tweets.")
            is_compliant = False

        for idx, tweet in enumerate(tweets, start=1):
            char_len = len(tweet)
            hashtags = re.findall(r'#\w+', tweet)
            
            # Index check (e.g. "1/N" or "(1/N)" or "1.")
            has_indexing = bool(re.search(rf'\(?{idx}/\d+\)?', tweet) or re.search(rf'^{idx}\.', tweet))
            
            tweet_ok = True
            tweet_violations = []

            if char_len > 280:
                tweet_ok = False
                tweet_violations.append(f"Exceeds 280 char limit ({char_len} chars)")
                is_compliant = False

            if not has_indexing:
                tweet_violations.append(f"Missing explicit thread numbering prefix (e.g. {idx}/{len(tweets)})")
                is_compliant = False

            if len(hashtags) > 2:
                tweet_violations.append(f"Too many hashtags ({len(hashtags)} found, max 2 allowed)")
                is_compliant = False

            tweet_analysis.append({
                "tweet_num": idx,
                "char_count": char_len,
                "is_valid_len": char_len <= 280,
                "has_indexing": has_indexing,
                "hashtags_count": len(hashtags),
                "violations": tweet_violations
            })

        return {
            "platform": "Twitter/X Thread",
            "is_compliant": is_compliant,
            "total_tweets": len(tweets),
            "tweet_analysis": tweet_analysis,
            "violations": violations
        }

    @classmethod
    def auto_repair_tweets(cls, tweets: List[str]) -> List[str]:
        """Auto-repairs tweets if they exceed character count or lack indexing."""
        repaired = []
        total = len(tweets)

        for idx, tweet in enumerate(tweets, start=1):
            curr = tweet.strip()

            # Ensure indexing prefix
            prefix = f"{idx}/{total} "
            if not re.search(rf'\(?{idx}/{total}\)?', curr) and not re.search(rf'^{idx}\.', curr):
                # Strip old invalid index if any
                curr = re.sub(r'^\d+/\d+\s*', '', curr)
                curr = f"{prefix}{curr}"

            # Truncate if over 280 chars
            if len(curr) > 280:
                # Retain hashtags if possible, truncate body
                curr = curr[:277] + "..."

            repaired.append(curr)

        return repaired
