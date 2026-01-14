# Quick Start Guide

Get your automated blog pipeline running in 5 minutes.

## Prerequisites Checklist

- [ ] GitHub repository (can be new or existing)
- [ ] Anthropic API key (Claude) - https://console.anthropic.com/
- [ ] Bing Search API key (optional, for external research)

## Step-by-Step Setup

### 1. Copy Files to Your Repo

```bash
# Clone or download this pipeline
git clone <this-repo-url> blog-pipeline

# Copy to your blog repository
cd your-blog-repo
cp -r ../blog-pipeline/.github .
cp -r ../blog-pipeline/pipeline .
cp ../blog-pipeline/.gitignore .

# Create directories
mkdir -p drafts posts
```

### 2. Configure Secrets

Go to your GitHub repo → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**

Add these secrets:

| Secret Name | Value | Where to Get It |
|------------|-------|-----------------|
| `ANTHROPIC_API_KEY` | `sk-ant-...` | https://console.anthropic.com/ |
| `BING_SEARCH_KEY` | Your Bing API key | Azure Portal (optional) |

**Alternative: Azure OpenAI** - If you prefer Azure, set `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_KEY`, and `AZURE_OPENAI_DEPLOYMENT` instead.

### 3. Create Your First Draft

```bash
# Create a draft - can be a personal insight or technical how-to!
cat > drafts/first-post.md << 'EOF'
# My First Blog Post Idea

I've been thinking about how our team handles technical debt.

Key observation: We defer tech debt tickets indefinitely, but they compound.

Last quarter:
- Started with 12 tech debt items
- Added 23 new ones
- Closed 3
- Now have 32 items

This isn't sustainable. Need a systematic approach.

Idea: Reserve 20% of each sprint for tech debt, tracked like features.

My experience: When I tried this on my last team, it worked. Morale improved
because engineers felt heard. Velocity actually went up after 3 sprints
because we fixed the things that kept slowing us down.

Questions to explore:
- How do other teams handle this?
- What metrics matter?
- How to prioritize which debt to tackle?
EOF
```

**Tip:** The pipeline will detect whether this is a personal insight piece (where your experience is the evidence) or something that needs external research. Write naturally - it adapts to you!

### 4. Push and Watch

```bash
# Commit and push
git add .
git commit -m "Add blog pipeline and first draft"
git push
```

### 5. Review the Output

1. Go to your repo on GitHub
2. Click **Actions** tab - watch the workflow run (~2-3 minutes)
3. Click **Pull Requests** tab - review the generated post
4. Make any edits via PR comments
5. Merge when ready!

## What Just Happened?

The pipeline:
1. ✅ **Detected your content type** (personal insight, technical how-to, etc.)
2. ✅ **Preserved your unique voice** and specific examples
3. ✅ **Researched** only when appropriate (not for personal insight pieces!)
4. ✅ Wrote a full draft with inverted pyramid structure
5. ✅ Polished while keeping your personality intact
6. ✅ Created a PR for your review

### Key Improvement: No Hallucinated Stats!

The pipeline is designed to **not** invent statistics or case studies. If your draft is a personal insight piece, it recognizes that your experience IS the evidence and won't try to add fake "Netflix did this" examples.

## Next Steps

### Write More Posts

```bash
# Just create new files in drafts/
vim drafts/my-next-idea.md

# Push when ready
git add drafts/my-next-idea.md
git commit -m "Draft: new post idea"
git push

# Pipeline runs automatically!
```

### Customize the Pipeline

Edit files in `pipeline/` to:
- Adjust prompts for different voices
- Add more research sources
- Change output format
- Modify quality checks

See the main [README.md](README.md) for details.

## Troubleshooting

### "Workflow not found"
- Make sure `.github/workflows/blog-pipeline.yml` exists
- Check it's in the `main` branch

### "Secrets not found" error
- Double-check secret names match exactly
- Verify secrets are at repository level, not environment

### Pipeline runs but fails
- Check Actions logs for specific error
- Most common: wrong deployment name or endpoint

### No PR created
- Verify `posts/` directory exists
- Check Actions logs for errors
- Ensure file was in `drafts/*.md`

## Success Indicators

You'll know it's working when:
1. ✅ Actions tab shows green checkmark
2. ✅ New PR appears with generated post
3. ✅ Post has frontmatter, citations, structured content
4. ✅ Quality score in HTML comment is 7+

## Getting Help

- Check the main [README.md](README.md) for detailed docs
- Review [GitHub Actions logs](../../actions) for errors  
- Look at the example draft in `drafts/example-ai-readable-status.md`

---

**Time to first post: ~5 minutes**
**Cost per post: ~$0.15 (with GPT-4)**
**Effort per post: Write notes, review PR, merge**

Happy blogging! 🚀
