# Blog Pipeline Architecture

## Complete System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         YOUR WORKFLOW                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. Write rough notes in drafts/my-idea.md                     │
│  2. git push                                                     │
│  3. Review PR (2-3 min later)                                   │
│  4. Merge → Auto-publish                                        │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘

                              ↓ [GitHub Push Event]

┌─────────────────────────────────────────────────────────────────┐
│                    GITHUB ACTIONS PIPELINE                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ STAGE 1: Intake & Structure                               │  │
│  │ ───────────────────────────────────────────────────────── │  │
│  │ Input:  drafts/my-idea.md (your rough notes)             │  │
│  │ AI:     Extract thesis, answer 5 W's, create outline     │  │
│  │ Output: JSON with structured content                      │  │
│  └──────────────────────────────────────────────────────────┘  │
│                              ↓                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ STAGE 2: Grounding & Research                             │  │
│  │ ───────────────────────────────────────────────────────── │  │
│  │ Input:  Stage 1 JSON                                      │  │
│  │ AI:     Generate targeted search queries                  │  │
│  │ Web:    Search Bing (prioritize Microsoft Learn)          │  │
│  │ AI:     Synthesize evidence, case studies, sources        │  │
│  │ Output: JSON with research findings                        │  │
│  └──────────────────────────────────────────────────────────┘  │
│                              ↓                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ STAGE 3: Expansion with Inverted Pyramid                  │  │
│  │ ───────────────────────────────────────────────────────── │  │
│  │ Input:  Stage 2 JSON (structure + research)              │  │
│  │ AI:     Write full draft:                                 │  │
│  │         - Lead paragraph (30-50 words)                    │  │
│  │         - Supporting paragraphs (descending importance)   │  │
│  │         - Include metrics, examples, citations            │  │
│  │ Output: JSON with markdown draft                          │  │
│  └──────────────────────────────────────────────────────────┘  │
│                              ↓                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ STAGE 4: Style & Polish                                    │  │
│  │ ───────────────────────────────────────────────────────── │  │
│  │ Input:  Stage 3 draft                                     │  │
│  │ AI:     Apply technical leadership voice:                 │  │
│  │         - Replace vague → specific                        │  │
│  │         - Passive → active voice                          │  │
│  │         - Remove filler words                              │  │
│  │         - Verify clarity and directness                    │  │
│  │ Output: JSON with polished draft                          │  │
│  └──────────────────────────────────────────────────────────┘  │
│                              ↓                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ STAGE 5: Technical Review                                  │  │
│  │ ───────────────────────────────────────────────────────── │  │
│  │ Input:  Stage 4 polished draft                            │  │
│  │ AI:     Quality check:                                     │  │
│  │         - Verify accuracy                                  │  │
│  │         - Confirm actionability                            │  │
│  │         - Check citations                                  │  │
│  │         - Rate quality (1-10)                              │  │
│  │ Output: posts/my-idea.md + metadata                       │  │
│  └──────────────────────────────────────────────────────────┘  │
│                              ↓                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ STAGE 6: Image Prompt Generation                           │  │
│  │ ───────────────────────────────────────────────────────── │  │
│  │ Input:  posts/my-idea.md + Stage 4 metadata               │  │
│  │ AI:     Analyze blog for visual opportunities:             │  │
│  │         - Create hero image prompt                         │  │
│  │         - Identify sections needing diagrams               │  │
│  │         - Generate detailed Nano Banana prompts            │  │
│  │ Output: JSON with image plan + prompts                    │  │
│  └──────────────────────────────────────────────────────────┘  │
│                              ↓                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ STAGE 7: Image Generation (Nano Banana)                    │  │
│  │ ───────────────────────────────────────────────────────── │  │
│  │ Input:  Stage 6 image plan                                │  │
│  │ API:    Gemini Imagen 3.0 (Nano Banana Pro):               │  │
│  │         - Generate hero image (16:9)                       │  │
│  │         - Generate section diagrams (16:9)                 │  │
│  │         - Retry with backoff on failure                    │  │
│  │ Output: PNG images + generation results JSON              │  │
│  └──────────────────────────────────────────────────────────┘  │
│                              ↓                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ STAGE 8: Image Assembly                                    │  │
│  │ ───────────────────────────────────────────────────────── │  │
│  │ Input:  Blog post + generated images                      │  │
│  │ Logic:  Insert images inline:                              │  │
│  │         - Hero image below frontmatter                    │  │
│  │         - Diagrams after matching H2 headings             │  │
│  │         - Copy images to posts/{slug}/ directory          │  │
│  │ Output: Final posts/my-idea.md with image references      │  │
│  └──────────────────────────────────────────────────────────┘  │
│                              ↓                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ Create Pull Request                                        │  │
│  │ ───────────────────────────────────────────────────────── │  │
│  │ - Title: "New Blog Post: my-idea"                         │  │
│  │ - Body: Pipeline summary + checklist                      │  │
│  │ - Branch: blog-post-my-idea                               │  │
│  │ - Labels: blog-post, automated-pipeline                   │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘

                              ↓ [You review & merge PR]

┌─────────────────────────────────────────────────────────────────┐
│                    GITHUB PAGES (Auto-publish)                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  posts/my-idea.md → your-blog.github.io/posts/my-idea           │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Data Flow Detail

### Input → Stage 1

**Your draft (example):**
```markdown
# AI-Readable Status Files

We're shipping code faster with AI tools but losing context.
Need machine-readable files that capture decisions + state.
Like .env but for context.
```

**Stage 1 output (JSON):**
```json
{
  "thesis": "AI-accelerated development needs machine-readable context files...",
  "five_ws": {
    "who": "Engineering teams using AI coding assistants",
    "what": "Losing context during rapid development",
    "why": "AI generates code faster than humans can document",
    "how": "Create .context files alongside code"
  },
  "outline": [...]
}
```

### Stage 1 → Stage 2

**Stage 2 searches for:**
- Microsoft Learn articles on documentation best practices
- Engineering blogs about AI-assisted development
- Case studies with metrics
- Research on developer productivity

**Stage 2 output adds:**
```json
{
  "research_synthesis": {
    "evidence": [
      {
        "claim": "GitHub Copilot users ship 55% faster",
        "source": "https://github.blog/...",
        "metric": "55% productivity increase"
      }
    ],
    "case_studies": [...]
  }
}
```

### Stage 2 → Stage 3

**Stage 3 writes inverted pyramid:**

```markdown
# AI-Readable Context Files: Bridging the Documentation Gap

AI coding assistants help teams ship features 55% faster, but this 
speed creates a critical problem: documentation can't keep pace. 
Teams using tools like GitHub Copilot and Microsoft Amplifier generate 
thousands of lines of code weekly while producing minimal documentation, 
leading to context loss that slows onboarding and increases technical debt.

[Most important evidence and examples]
[Supporting details with citations]
[Background context]
[Actionable recommendations]
```

### Stage 3 → Stage 4

**Stage 4 polishes:**
- ❌ "significantly improved" → ✅ "reduced by 40%"
- ❌ "The system was designed" → ✅ "We designed the system"
- ❌ "It's really important" → ✅ "This matters because"

### Stage 4 → Stage 5

**Stage 5 adds frontmatter:**

```markdown
---
title: "AI-Readable Context Files"
date: 2025-01-11
tags: technical-leadership, AI, documentation
---

<!-- Quality Score: 8/10, Ready to Publish ✅ -->

[polished content]
```

### Stage 5 → Stage 6

**Stage 6 analyzes the blog and creates image prompts:**

```json
{
  "hero": {
    "description": "Abstract visualization of AI context flowing between systems",
    "prompt": "Create a visually striking hero image... [detailed prompt]"
  },
  "diagrams": [
    {
      "image_id": "diagram_1",
      "target_section": "How Context Files Work",
      "diagram_type": "architecture",
      "prompt": "Create a system architecture diagram... [detailed prompt]"
    }
  ]
}
```

### Stage 6 → Stage 7

**Stage 7 calls Gemini Nano Banana Pro to generate images:**
- Hero image → `pipeline/temp/images/{slug}/hero.png`
- Diagrams → `pipeline/temp/images/{slug}/diagram_1.png`, etc.
- Retries with exponential backoff on failure
- Skips images that already exist (idempotent)

### Stage 7 → Stage 8

**Stage 8 assembles the final post with images inline:**

```markdown
---
title: "AI-Readable Context Files"
---

![Hero Image](ai-readable-context-files/hero.png)

[intro paragraph]

## How Context Files Work

![Architecture diagram showing context file flow](ai-readable-context-files/diagram_1.png)

[section content]
```

## Technology Stack

```
┌─────────────────────────────────────┐
│ GitHub Actions (Orchestration)      │
│ - Ubuntu runner                      │
│ - Python 3.11                        │
│ - Triggered on push to drafts/      │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│ Azure OpenAI API                     │
│ - GPT-4 or GPT-3.5-Turbo             │
│ - 5 API calls per post               │
│ - JSON mode for structured output    │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│ Bing Search API (Optional)           │
│ - Web search for grounding           │
│ - ~5 searches per post               │
│ - Prioritizes Microsoft Learn        │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│ Gemini Nano Banana Pro (Images)      │
│ - Imagen 3.0 via Google GenAI SDK    │
│ - Hero images + section diagrams     │
│ - ~1-4 image generations per post    │
│ - Accurate text rendering            │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│ GitHub (Storage & PR)                │
│ - Stores all versions                │
│ - Creates PR for review              │
│ - Auto-publishes via Pages           │
└─────────────────────────────────────┘
```

## Cost Breakdown

Per blog post:

| Component | Cost | Notes |
|-----------|------|-------|
| Azure OpenAI (GPT-4) | $0.15 | 5 calls × ~2K tokens each |
| Azure OpenAI (GPT-3.5) | $0.03 | Alternative cheaper option |
| Bing Search | $0.03 | ~5 searches |
| Gemini Nano Banana (Images) | $0.08 | ~1-4 images per post |
| GitHub Actions | $0.00 | Free tier: 2000 min/month |
| **Total (GPT-4 + Images)** | **$0.26** | |
| **Total (GPT-3.5 + Images)** | **$0.14** | |

**Monthly estimate (10 posts):**
- GPT-4 + Images: $2.60/month
- GPT-3.5 + Images: $1.40/month

## File Structure

```
your-blog-repo/
├── .github/
│   └── workflows/
│       └── blog-pipeline.yml         # GitHub Actions workflow
│
├── pipeline/
│   ├── requirements.txt               # Python dependencies
│   ├── stage1_structure.py            # Extract thesis & outline
│   ├── stage2_grounding.py            # Research & evidence
│   ├── stage3_expansion.py            # Write full draft
│   ├── stage4_polish.py               # Apply style
│   ├── stage5_review.py               # Final review
│   ├── stage6_image_prompts.py        # Generate image prompts
│   ├── stage7_image_gen.py            # Call Gemini Nano Banana
│   ├── stage8_assemble.py             # Insert images into post
│   └── temp/                          # Temporary stage outputs
│       ├── stage1_output.json
│       ├── stage2_output.json
│       ├── ...
│       ├── stage6_output.json         # Image plan + prompts
│       ├── stage7_output.json         # Generation results
│       └── images/                    # Generated images (temp)
│           └── {slug}/
│               ├── hero.png
│               └── diagram_1.png
│
├── drafts/                            # Your rough notes (INPUT)
│   ├── example-ai-readable-status.md
│   └── your-ideas.md
│
├── posts/                             # Generated posts (OUTPUT)
│   ├── ai-readable-status.md
│   ├── ai-readable-status/            # Post images
│   │   ├── hero.png
│   │   └── diagram_1.png
│   └── your-ideas.md
│
└── _posts/                            # Or whatever your blog uses
    └── (same files, after merge)
```

## Security & Secrets

All sensitive data stored as GitHub Secrets:

```
Repository Secrets:
├── AZURE_OPENAI_ENDPOINT      # Your Azure endpoint
├── AZURE_OPENAI_KEY           # API key (encrypted)
├── AZURE_OPENAI_DEPLOYMENT    # Model deployment name
├── BING_SEARCH_KEY            # Bing API key (optional)
└── GEMINI_API_KEY             # Google Gemini API key (for Nano Banana images)
```

**Never committed to repo:**
- API keys
- Endpoints
- Credentials

## PR Comment Revision Pipeline

After the initial pipeline creates a PR, reviewers can request revisions by adding comments directly on specific lines in the "Files Changed" tab. These comments are processed by a secondary pipeline that uses the LLM to apply the feedback.

```
┌─────────────────────────────────────────────────────────────────┐
│                    PR COMMENT REVISION FLOW                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. Reviewer adds comment on line in PR "Files Changed" tab     │
│     Example: Line says "I was freaking out"                     │
│              Comment: "Let's use a more formal tone"            │
│                                                                  │
│  2. GitHub Actions triggers on pull_request_review_comment      │
│                                                                  │
│  3. Pipeline extracts:                                           │
│     - File path (posts/my-idea.md)                              │
│     - Line number (e.g., line 42)                               │
│     - Comment text ("Let's use a more formal tone")             │
│                                                                  │
│  4. LLM receives:                                                │
│     - Full document for context                                  │
│     - Target line highlighted                                    │
│     - Reviewer's feedback as instruction                        │
│                                                                  │
│  5. LLM revises document:                                        │
│     - "I was freaking out" → "I was concerned"                  │
│     - Maintains document consistency                             │
│     - Preserves author voice                                     │
│                                                                  │
│  6. Changes committed to PR branch automatically                 │
│                                                                  │
│  7. Bot replies to comment with summary of changes              │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Supported Comment Types

| Comment Type | Example | LLM Behavior |
|-------------|---------|--------------|
| Tone adjustment | "Use more formal language" | Revises target line with formal equivalent |
| Clarity request | "This is unclear, please simplify" | Rewrites for clarity |
| Technical accuracy | "This metric seems wrong" | Checks and corrects the claim |
| Style guidance | "Make this more actionable" | Adds concrete recommendations |
| Broader feedback | "The whole section feels too casual" | May revise multiple related lines |

### Workflow File

The PR comment revision is handled by `.github/workflows/pr-comment-revision.yml` which:
- Triggers only on PRs with the `blog-post` label
- Checks out the PR branch (not main)
- Runs `pipeline/pr_comment_revision.py`
- Commits changes back to the PR
- Replies to the original comment with a summary

## Customization Points

Each stage script has customizable variables:

```python
# stage1_structure.py
STAGE1_PROMPT = """..."""  # ← Edit this for different extraction

# stage2_grounding.py
def search_web(query, bing_key):
    enhanced_query = f"{query} site:learn.microsoft.com"  # ← Change sources

# stage3_expansion.py
temperature=0.5  # ← Adjust creativity

# stage4_polish.py
STAGE4_PROMPT = """..."""  # ← Customize voice

# stage5_review.py
FRONTMATTER_TEMPLATE = """..."""  # ← Change metadata format
```

## Error Handling

Pipeline is resilient:

1. **Stage fails** → GitHub Actions shows which stage and why
2. **API timeout** → Retries automatically (GitHub Actions built-in)
3. **No search results** → Continues without web research
4. **Low quality score** → Still creates PR, flags in review
5. **Multiple drafts pushed** → Processes most recent only

## Monitoring

Track pipeline health:

- GitHub Actions tab shows all runs
- Each run logs show stage-by-stage progress
- PR descriptions include quality metrics
- Metadata files track review scores

```
Actions → Blog Pipeline → [Latest run]
  ✅ Stage 1: 12s
  ✅ Stage 2: 45s (5 searches)
  ✅ Stage 3: 38s
  ✅ Stage 4: 22s
  ✅ Stage 5: 15s
  ✅ Stage 6: 8s (1 hero + 2 diagrams planned)
  ✅ Stage 7: 25s (3 images generated)
  ✅ Stage 8: 2s (images assembled)
  ✅ Create PR
```
