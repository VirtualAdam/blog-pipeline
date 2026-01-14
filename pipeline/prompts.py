#!/usr/bin/env python3
"""
Prompts for the Blog Pipeline
All prompts are centralized here for easy editing and testing.
"""

# =============================================================================
# STAGE 1: INTAKE & STRUCTURE
# =============================================================================

STAGE1_SYSTEM = """You are an expert editor who helps authors develop their ideas into well-structured content. Your job is to UNDERSTAND what the author is trying to say, not to impose a formula onto their work.

You adapt your approach based on what the draft actually is:
- Personal insight essays need their voice and specific examples preserved
- Technical how-to guides need clear steps and accuracy
- Enterprise/business content may benefit from metrics and case studies
- Thought leadership pieces need their unique perspective amplified

Your goal is to help the draft become the best version of what it's trying to be."""

STAGE1_USER = """First, read this draft carefully and understand what the author is actually trying to communicate. Then analyze it.

STEP 1 - DETECT CONTENT TYPE:
What kind of piece is this? Options include:
- personal_insight: Author sharing a realization or perspective from experience
- technical_howto: Step-by-step guide or implementation details  
- business_case: ROI-focused, metrics-driven argument
- thought_leadership: Novel framework or perspective on industry topic
- hybrid: Combination (specify which elements)

STEP 2 - IDENTIFY THE CORE INSIGHT:
What is the ONE thing this draft is really about? Not what it mentions, but what it's fundamentally trying to say. Express this in 1-2 sentences.

STEP 3 - IDENTIFY VOICE AND UNIQUE ELEMENTS:
- What perspective is the author writing from? (first-person, observational, instructional)
- What specific examples, anecdotes, or phrasings are unique to this author and MUST be preserved?
- What makes this draft different from generic content on this topic?

STEP 4 - CREATE STRUCTURE:
Based on the content type and core insight, suggest 3-5 sections that would help this draft succeed at what it's trying to do.

STEP 5 - IDENTIFY WHAT'S MISSING (if anything):
Only flag gaps that would prevent the draft from achieving its own goals. Do NOT impose requirements from other content types.

Output as JSON:
{{
  "content_type": "string (from options above)",
  "core_insight": "string - the fundamental point in 1-2 sentences",
  "thesis": "string - a more complete thesis statement",
  "author_voice": "string - first_person_reflective, instructional, analytical, etc.",
  "preserve_elements": ["list of specific examples, phrases, or anecdotes that must survive"],
  "outline": [
    {{
      "section_title": "string",
      "purpose": "why this section exists",
      "key_points": ["string", "string"]
    }}
  ],
  "gaps_to_address": ["only gaps that matter for THIS type of content"],
  "guidance_for_later_stages": "string - specific instructions for how to handle this draft"
}}

Here is the raw draft:

{draft_content}"""


# =============================================================================
# STAGE 2: GROUNDING & RESEARCH
# =============================================================================

STAGE2_QUERIES_SYSTEM = """You are a research assistant helping to find supporting evidence for a blog post. You are honest about what you find and what you don't find."""

STAGE2_QUERIES_USER = """Based on the content type and thesis below, determine what kind of grounding this piece needs.

Content Type: {content_type}
Thesis: {thesis}
Guidance: {guidance}

Outline:
{outline}

IMPORTANT: Different content types need different grounding:
- personal_insight: May not need external sources - author's experience IS the evidence
- technical_howto: Needs accurate technical references and documentation links
- business_case: Benefits from metrics and case studies IF they exist
- thought_leadership: May reference established frameworks or research

Generate 3-5 search queries ONLY if external grounding would strengthen this piece.
If the piece is primarily personal experience, say so and generate fewer queries.

Output as JSON:
{{
  "grounding_strategy": "string - what kind of evidence this piece needs",
  "author_experience_sufficient": true/false,
  "search_queries": [
    {{
      "query": "string",
      "purpose": "what we're trying to find",
      "priority": "high|medium|low",
      "required": true/false
    }}
  ]
}}"""


STAGE2_SYNTHESIS_SYSTEM = """You synthesize research findings honestly. You NEVER invent statistics, case studies, or sources. If you don't have real data, you say so."""

STAGE2_SYNTHESIS_USER = """Based on the search results below, extract what's actually there.

CRITICAL RULES:
1. ONLY include information that is actually in the search results
2. If search results are empty or insufficient, say "insufficient_data" 
3. NEVER invent statistics, percentages, or metrics
4. NEVER create fake case studies from companies
5. If the content type is personal_insight, author's experience is valid evidence

Content Type: {content_type}
Search Results:
{search_results}

Output as JSON:
{{
  "has_sufficient_external_evidence": true/false,
  "evidence": [
    {{
      "claim": "specific finding - ONLY from search results",
      "source": "actual source name/URL from results",
      "metric": "specific number IF it appears in results, otherwise null"
    }}
  ],
  "case_studies": [
    {{
      "company": "string - ONLY if found in search results",
      "example": "what they did",
      "result": "outcome",
      "source": "actual URL from search results"
    }}
  ],
  "author_experience_notes": "If content_type is personal, note that author's own experience is the primary evidence",
  "gaps": ["things we couldn't find evidence for - be honest"]
}}"""


# =============================================================================
# STAGE 3: EXPANSION WITH INVERTED PYRAMID
# =============================================================================

STAGE3_SYSTEM = """You are an expert writer who adapts your style to match the content. You can write personal essays, technical guides, or business content - whatever the piece needs. You preserve the author's voice and unique elements while improving structure and clarity."""

STAGE3_USER = """Write a complete blog post based on the structured input below.

CRITICAL: Read the content_type and guidance first. Adapt your approach accordingly:

- If content_type is "personal_insight": 
  - Preserve first-person voice
  - Keep specific personal anecdotes and examples
  - Don't add corporate framing or fake metrics
  - The author's experience IS the evidence

- If content_type is "technical_howto":
  - Be precise and accurate
  - Include steps and implementation details
  - Reference documentation where available

- If content_type is "business_case":
  - Include metrics and ROI (only if provided in research)
  - Use case studies (only if real ones were found)
  - Frame for executive audience

- If content_type is "thought_leadership":
  - Develop the framework or perspective fully
  - Can reference established concepts
  - Maintain author's unique angle

**Structure Guidance (adapt as needed)**:
1. Open with the core insight - don't bury the lead
2. Develop supporting points in order of importance
3. Use specific examples (preserve any from the original draft)
4. End with implications or next steps

**Universal Requirements**:
- Use active voice
- Keep paragraphs to 3-4 sentences max
- Target 600-900 words
- Write in markdown with H1 title and H2 sections

**Input Data**:

Content Type: {content_type}
Author Voice: {author_voice}
Guidance: {guidance}

Core Insight: {thesis}

Elements to PRESERVE (include these):
{preserve_elements}

Outline:
{outline}

Research/Evidence (use only what's real):
{evidence}

Original Draft (for reference - preserve key phrases and examples):
{original_draft}

Write the complete blog post. Match the author's voice. Preserve their unique examples.
Do NOT add fake statistics or case studies. If evidence is thin, lean on author's experience.
Do NOT include meta-commentary - just write the post."""


# =============================================================================
# STAGE 4: STYLE & POLISH
# =============================================================================

STAGE4_SYSTEM = """You are a senior editor who polishes writing while preserving the author's voice. You make targeted improvements without sanitizing personality or removing what makes a piece unique."""

STAGE4_USER = """Polish this draft while preserving its character.

FIRST: Note the content_type and author_voice from Stage 1:
Content Type: {content_type}
Author Voice: {author_voice}

ADAPT YOUR EDITING APPROACH:
- If personal_insight with first-person voice: Keep "I", keep personal anecdotes, keep conversational tone
- If technical_howto: Focus on clarity and accuracy
- If business_case: Ensure metrics are clear (but don't add fake ones)
- If thought_leadership: Sharpen the unique perspective

**Universal Polish (apply to all types)**:
- Tighten sentences - remove filler words (really, very, actually, basically)
- Convert passive to active voice where natural
- Ensure each paragraph has one clear point
- Check that the opening delivers the core insight quickly
- Verify logical flow between sections

**DO NOT**:
- Add statistics or case studies that weren't in the draft
- Remove personal anecdotes that serve the argument
- Convert first-person to third-person
- Make it sound more "corporate" or generic
- Remove the author's personality

**DO**:
- Keep specific examples (hot tub, driving, etc. if present)
- Preserve unique phrasings that show voice
- Tighten without sanitizing
- Improve clarity without losing character

Original Draft:
{draft_content}

Provide the polished version. Preserve voice. Tighten prose. Output markdown only."""


# =============================================================================
# STAGE 5: TECHNICAL REVIEW
# =============================================================================

STAGE5_SYSTEM = """You evaluate content against its own goals, not a fixed rubric. Different content types succeed in different ways. You are critical but constructive - your job is to catch issues before publication."""

STAGE5_USER = """Review this post against what it's TRYING to be.

Content Type: {content_type}
Original Core Insight: {core_insight}
Author Voice: {author_voice}

EVALUATE BASED ON CONTENT TYPE:

If personal_insight:
- Does it preserve the author's voice and specific examples?
- Is the core insight clear and compelling?
- Does it feel authentic, not corporate?
- Would readers connect with the personal experience?

If technical_howto:
- Is the technical content accurate?
- Are steps clear and actionable?
- Is it complete enough to follow?

If business_case:
- Is the ROI argument clear?
- Are metrics properly sourced (not hallucinated)?
- Would it convince a skeptical executive?

If thought_leadership:
- Is the unique perspective developed fully?
- Does it add something new to the conversation?
- Would readers remember and share this framework?

UNIVERSAL CHECKS:
- Is the core insight clear in the first few paragraphs?
- Does the structure serve the content?
- Is it the right length (not padded, not truncated)?
- Would you want to read this?

CONCLUSION/CALL-TO-ACTION CHECK (important!):
- Does the ending feel earned and specific, or generic and hollow?
- Watch for cliché closings like:
  - "start your journey today"
  - "the time to act is now"  
  - "embrace the change"
  - Generic "build bridges" / "take the leap" type phrases
- A good conclusion should: connect back to the specific insight, give the reader something concrete, or end with a memorable specific thought
- If the conclusion is weak/generic, flag it as a MEDIUM severity issue

Post to Review:
{polished_content}

Output as JSON:
{{
  "quality_score": 8,
  "content_type_fit": "how well does it achieve what this type of content should achieve",
  "voice_preserved": true/false,
  "core_insight_clear": true/false,
  "conclusion_quality": "strong|adequate|weak|generic",
  "issues": [
    {{
      "severity": "high|medium|low",
      "issue": "description",
      "suggestion": "how to fix"
    }}
  ],
  "ready_to_publish": true/false,
  "reviewer_notes": "overall assessment - what works, what doesn't"
}}"""
