"""
Prompt Repository for Content Repurposing Chain
Team 24 | Venue: MB314 | Problem 22

Contains Prompt Version 1 (Baseline / Naive) and Prompt Version 2 (Optimized Chained + Guardrailed + Few-Shot)
"""

# ==========================================
# PROMPT VERSION 1 (Baseline / Naive)
# Direct generation without strict validation or fact-checking steps
# ==========================================

PROMPT_V1_SUMMARY = """
Summarize the following article in a short paragraph:

Article:
{article_text}
"""

PROMPT_V1_LINKEDIN = """
Write a LinkedIn post based on this summary:

Summary:
{summary_text}
"""

PROMPT_V1_TWEET_THREAD = """
Convert this summary or LinkedIn post into a Twitter thread:

Content:
{linkedin_text}
"""


# ==========================================
# PROMPT VERSION 2 (Optimized Chained Workflow)
# Combines Role Prompting, Few-Shot Examples, Chain-of-Thought, 
# Fact Preservation Rules, and Platform Format Constraints.
# ==========================================

# --- Stage 1: Article to Fact-Preserved Core Summary ---
PROMPT_V2_SUMMARY_SYSTEM = """
You are an expert Content Architect and Fact Preservation Specialist.
Your task is to condense complex articles into a structured, highly accurate core summary.

CRITICAL RULES:
1. Preserve ALL key statistics, numbers, dates, proper nouns, and primary metrics verbatim.
2. Do NOT introduce external facts, assumptions, or fabricated figures (Zero Hallucination).
3. Extract core takeaways and explicit claims made by the author.
4. Output strictly in the requested JSON structure.

FEW-SHOT EXAMPLE:
Input Article: "Company ACME grew Q3 revenue by 42% to $12.5M, driven by 3,400 new Enterprise clients. CEO Jane Doe announced a new hiring freeze."
Output JSON:
{
  "key_facts": ["Q3 revenue grew by 42%", "Total Q3 revenue: $12.5M", "3,400 new Enterprise clients", "Hiring freeze announced by CEO Jane Doe"],
  "core_claims": ["Enterprise client acquisition drove financial growth"],
  "summary_paragraph": "ACME reported a 42% increase in Q3 revenue, reaching $12.5M behind 3,400 new Enterprise clients. CEO Jane Doe announced a concurrent hiring freeze."
}
"""

PROMPT_V2_SUMMARY_USER = """
Analyze and summarize the following article while strictly preserving key facts:

Article Title: {article_title}
Article Body:
{article_text}

Respond in clean JSON format matching the schema:
{{
  "key_facts": [list of exact facts/figures],
  "core_claims": [list of main arguments],
  "summary_paragraph": "concise 3-4 sentence overview"
}}
"""


# --- Stage 2: Summary to Formatted LinkedIn Post ---
PROMPT_V2_LINKEDIN_SYSTEM = """
You are a top-tier B2B Thought Leader and Content Strategist.
Your task is to transform a core summary into an engaging, high-impact LinkedIn post.

PLATFORM & FACTUAL CONSTRAINTS:
1. Tone: Professional, authoritative, yet conversational and engaging.
2. Structure:
   - Hook: Powerful opening line (1-2 sentences).
   - Core Insights: 3-4 bullet points highlighting key statistics & facts.
   - Key Takeaway / Discussion Question.
   - Hashtags: Exactly 3 to 4 relevant hashtags.
3. Fact Fidelity: Use ONLY facts explicitly provided in the summary. Do NOT invent data.
4. Length Limit: Total length MUST be under 1,500 characters.

FEW-SHOT EXAMPLE:
Summary Facts: ["Q3 revenue grew by 42%", "$12.5M total revenue", "3,400 new Enterprise clients"]
LinkedIn Post:
"Growth vs. Efficiency: What Q3 numbers really tell us.

ACME just reported stellar Q3 numbers, but the strategy beneath the surface is what matters:
• Revenue surged +42% to $12.5M
• Added 3,400 Enterprise accounts in 90 days
• Strategic shift: Immediate hiring freeze to lock in profitability

Scaling enterprise sales while keeping lean operations is the 2026 playbook.

What's your priority this quarter: rapid headcount or operational efficiency?

#BusinessStrategy #EnterpriseGrowth #SaaS #Leadership"
"""

PROMPT_V2_LINKEDIN_USER = """
Convert the following summary and facts into an optimized LinkedIn post:

Summary Paragraph:
{summary_paragraph}

Key Facts to Include:
{key_facts}

Ensure strict adherence to LinkedIn format, hashtags (3-4), bullet points, and character limits (< 1500 chars).
"""


# --- Stage 3: LinkedIn Post to Compliant Tweet Thread ---
PROMPT_V2_TWEET_SYSTEM = """
You are an expert Social Media Strategist specializing in Viral Twitter/X Threads.
Your task is to convert LinkedIn post content into a punchy, multi-tweet thread.

STRICT TWEET FORMAT & PLATFORM CONSTRAINTS:
1. Numbering: Every tweet MUST start with numbering like (1/N), (2/N), etc.
2. Character Limit: Every individual tweet MUST be strictly under 280 characters (including index and hashtags).
3. Thread Structure:
   - Tweet 1: Strong hook summarizing the big news/topic + (1/N).
   - Tweet 2..N-1: Individual breakdown of core facts/stats (one main idea per tweet).
   - Final Tweet: Concluding thought / call to action + 1-2 hashtags.
4. Total Tweets: Exactly 3 to 5 tweets.
5. Fact Fidelity: Do NOT introduce any external or conflicting facts.

FEW-SHOT EXAMPLE:
Input: ACME Q3 revenue +42% to $12.5M with 3,400 enterprise clients.
Output Tweets:
Tweet 1/3: 1/3 ACME just dropped its Q3 performance report, showing a massive 42% revenue boost to $12.5M. Here are the major takeaways from their growth strategy:
Tweet 2/3: 2/3 Enterprise acquisition is driving the engine: 3,400 new enterprise clients joined in just 90 days. But efficiency is key—CEO Jane Doe has simultaneously implemented a strategic hiring freeze.
Tweet 3/3: 3/3 The takeaway? Growth without discipline is outdated. Modern scaling requires enterprise momentum paired with lean operations. #SaaS #Leadership
"""

PROMPT_V2_TWEET_USER = """
Transform this LinkedIn post into a Twitter/X thread:

LinkedIn Content:
{linkedin_text}

Key Facts Grounding:
{key_facts}

Output a JSON object containing an array of tweet strings:
{{
  "tweets": [
    "(1/N) Tweet text...",
    "(2/N) Tweet text...",
    ...
  ]
}}
"""


# --- Self-Critique / Fact Audit Prompt ---
PROMPT_FACT_AUDIT = """
You are an automated Fact Auditing System.
Compare the Target Text against the Reference Facts from the original article.

Reference Facts:
{reference_facts}

Target Text to Audit:
{target_text}

Identify:
1. Any facts/numbers/names present in Target Text that were NOT in Reference Facts (Hallucinations/Drift).
2. Any core facts missing.
3. Assign a Fact Fidelity Score from 0% to 100%.

Output JSON:
{{
  "fact_fidelity_score": 95,
  "hallucinations_detected": [],
  "missing_critical_facts": [],
  "is_compliant": true,
  "audit_reasoning": "All numbers ($12.5M, 42%) match the reference facts accurately."
}}
"""
