# Local Pipeline Testing

Test the blog pipeline locally before deploying to GitHub Actions.

## Quick Start

### 1. Install Dependencies

```bash
cd local
pip install -r requirements.txt
```

### 2. Set Up Your API Key

**Option A: Environment Variable (recommended for quick testing)**
```bash
# Windows PowerShell
$env:ANTHROPIC_API_KEY = "sk-ant-your-key-here"

# Windows CMD
set ANTHROPIC_API_KEY=sk-ant-your-key-here

# Linux/Mac
export ANTHROPIC_API_KEY=sk-ant-your-key-here
```

**Option B: .env File**
```bash
cp .env.example .env
# Edit .env and add your key
```

### 3. Run the Pipeline

```bash
# Test with the sample draft
python run_pipeline.py --input sample_draft.md

# Or with your own draft
python run_pipeline.py --input ../drafts/your-draft.md
```

## Usage Options

```bash
# Run all 5 stages (default)
python run_pipeline.py --input sample_draft.md

# Run only specific stages (useful for debugging prompts)
python run_pipeline.py --input sample_draft.md --stages 1,2,3

# Save intermediate JSON files for inspection
python run_pipeline.py --input sample_draft.md --save-intermediate

# Verbose output
python run_pipeline.py --input sample_draft.md --verbose

# Use Azure OpenAI instead of Claude
python run_pipeline.py --input sample_draft.md --provider azure

# Custom output location
python run_pipeline.py --input sample_draft.md --output ../posts/my-post.md
```

## Output

- **Final blog post**: `output/<draft-name>.md`
- **Intermediate files** (with `--save-intermediate`): `output/intermediate/stage1.json`, etc.

## Editing Prompts

All prompts are in `prompts.py`. Edit them there and re-run the pipeline to test changes.

Key prompt files:
- `STAGE1_USER` - Structure extraction
- `STAGE2_QUERIES_USER` - Research query generation
- `STAGE3_USER` - Draft writing (inverted pyramid)
- `STAGE4_USER` - Polish and style
- `STAGE5_USER` - Quality review

## Switching Between Claude and Azure OpenAI

The `llm_client.py` provides an abstraction layer. Both providers use similar prompts but may respond differently.

**For Claude:**
```bash
export ANTHROPIC_API_KEY=sk-ant-xxx
python run_pipeline.py --input draft.md --provider claude
```

**For Azure OpenAI:**
```bash
export AZURE_OPENAI_KEY=xxx
export AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
export AZURE_OPENAI_DEPLOYMENT=gpt-4
python run_pipeline.py --input draft.md --provider azure
```

## Troubleshooting

### "ANTHROPIC_API_KEY environment variable not set"
Make sure you've exported your API key in the current terminal session.

### JSON Parse Errors
Sometimes the LLM doesn't return perfect JSON. Try running again - this is usually transient.

### Rate Limits
If you hit rate limits, wait a minute and try again. Consider running fewer stages at once.

## Cost Estimation

Each full pipeline run uses approximately:
- **Claude**: ~8,000-15,000 tokens input, ~3,000-5,000 tokens output
- Estimated cost per run: ~$0.05-0.15 depending on draft length

## Next Steps

Once you're happy with the prompts locally:
1. Update `pipeline/requirements.txt` to include `anthropic`
2. Update the stage scripts to use the new `llm_client.py` abstraction
3. Add `ANTHROPIC_API_KEY` to GitHub Secrets
4. Update the workflow to use Claude
