#!/usr/bin/env python3
"""
Local Pipeline Runner
Runs all 5 stages locally for testing prompts and model outputs.
"""

import os
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from llm_client import create_client, LLMClient
from prompts import (
    STAGE1_SYSTEM, STAGE1_USER,
    STAGE2_QUERIES_SYSTEM, STAGE2_QUERIES_USER,
    STAGE2_SYNTHESIS_SYSTEM, STAGE2_SYNTHESIS_USER,
    STAGE3_SYSTEM, STAGE3_USER,
    STAGE4_SYSTEM, STAGE4_USER,
    STAGE5_SYSTEM, STAGE5_USER
)


def print_header(stage: int, title: str):
    """Print a formatted stage header."""
    print("\n" + "=" * 60)
    print(f"  STAGE {stage}: {title}")
    print("=" * 60)


def print_progress(message: str):
    """Print a progress message."""
    print(f"  → {message}")


def run_stage1(client: LLMClient, draft_content: str, verbose: bool = False) -> dict:
    """Stage 1: Intake & Structure"""
    print_header(1, "Intake & Structure")
    print_progress("Analyzing draft and extracting structure...")
    
    user_prompt = STAGE1_USER.format(draft_content=draft_content)
    
    response = client.chat(
        system_prompt=STAGE1_SYSTEM,
        user_prompt=user_prompt,
        temperature=0.3,
        json_mode=True
    )
    
    result = json.loads(response)
    result['original_draft'] = draft_content
    result['stage'] = 1
    
    print_progress(f"✅ Content type: {result.get('content_type', 'unknown')}")
    print_progress(f"✅ Core insight: {result.get('core_insight', result.get('thesis', ''))[:80]}...")
    print_progress(f"✅ Outline sections: {len(result.get('outline', []))}")
    
    if verbose:
        print(f"\n  Author voice: {result.get('author_voice', 'not detected')}")
        print(f"  Preserve elements: {len(result.get('preserve_elements', []))}")
        if result.get('preserve_elements'):
            for elem in result['preserve_elements'][:3]:
                print(f"    - {elem[:60]}...")
    
    return result


def run_stage2(client: LLMClient, stage1_data: dict, 
               skip_search: bool = True, verbose: bool = False) -> dict:
    """Stage 2: Grounding & Research"""
    print_header(2, "Grounding & Research")
    
    content_type = stage1_data.get('content_type', 'unknown')
    guidance = stage1_data.get('guidance_for_later_stages', '')
    
    # Generate search queries
    print_progress("Generating research queries...")
    
    outline_text = "\n".join([
        f"- {section['section_title']}: {', '.join(section.get('key_points', []))}"
        for section in stage1_data.get('outline', [])
    ])
    
    user_prompt = STAGE2_QUERIES_USER.format(
        content_type=content_type,
        thesis=stage1_data.get('thesis', stage1_data.get('core_insight', '')),
        guidance=guidance,
        outline=outline_text
    )
    
    response = client.chat(
        system_prompt=STAGE2_QUERIES_SYSTEM,
        user_prompt=user_prompt,
        temperature=0.3,
        json_mode=True
    )
    
    queries_result = json.loads(response)
    search_queries = queries_result.get('search_queries', [])
    print_progress(f"✅ Grounding strategy: {queries_result.get('grounding_strategy', 'standard')}")
    print_progress(f"✅ Generated {len(search_queries)} search queries")
    
    if queries_result.get('author_experience_sufficient'):
        print_progress("ℹ️  Author experience identified as primary evidence")
    
    if verbose and search_queries:
        for q in search_queries:
            print(f"    - [{q.get('priority', 'medium')}] {q.get('query', '')[:50]}...")
    
    # For local testing, we'll mock the search results
    if skip_search:
        print_progress("⚠️  Skipping web search (local mode)")
        
        # If author experience is sufficient, don't push for external evidence
        if queries_result.get('author_experience_sufficient') or content_type == 'personal_insight':
            print_progress("   Using author's experience as primary evidence...")
            search_results = f"""Content type: {content_type}
This is a personal insight piece. The author's own experience is the primary evidence.
Do not invent external statistics or case studies.
Thesis: {stage1_data.get('thesis', stage1_data.get('core_insight', ''))}"""
        else:
            print_progress("   Using LLM knowledge for grounding instead...")
            search_results = f"""Based on your knowledge, provide research findings to support this thesis:
Thesis: {stage1_data.get('thesis', stage1_data.get('core_insight', ''))}
Note: Only include information you're confident is accurate. Say 'insufficient_data' if unsure."""
    else:
        search_results = "No search results (API not configured)"
    
    # Synthesize research
    print_progress("Synthesizing research findings...")
    
    user_prompt = STAGE2_SYNTHESIS_USER.format(
        content_type=content_type,
        search_results=search_results
    )
    
    response = client.chat(
        system_prompt=STAGE2_SYNTHESIS_SYSTEM,
        user_prompt=user_prompt,
        temperature=0.3,
        json_mode=True
    )
    
    synthesis = json.loads(response)
    
    if synthesis.get('has_sufficient_external_evidence') == False:
        print_progress("ℹ️  Limited external evidence - will rely on author's experience")
    else:
        print_progress(f"✅ Evidence points: {len(synthesis.get('evidence', []))}")
        print_progress(f"✅ Case studies: {len(synthesis.get('case_studies', []))}")
    
    # Combine results
    result = {
        **stage1_data,
        'stage': 2,
        'grounding_strategy': queries_result.get('grounding_strategy', 'standard'),
        'search_queries': search_queries,
        'research_synthesis': synthesis
    }
    
    return result


def run_stage3(client: LLMClient, stage2_data: dict, verbose: bool = False) -> dict:
    """Stage 3: Expansion with Inverted Pyramid"""
    print_header(3, "Expansion with Inverted Pyramid")
    print_progress("Writing full draft...")
    
    # Get content type and guidance from Stage 1
    content_type = stage2_data.get('content_type', 'unknown')
    author_voice = stage2_data.get('author_voice', 'not specified')
    guidance = stage2_data.get('guidance_for_later_stages', '')
    preserve_elements = stage2_data.get('preserve_elements', [])
    
    # Format outline
    outline_text = "\n".join([
        f"{i+1}. {section['section_title']}\n   Purpose: {section.get('purpose', 'N/A')}\n   Points: {', '.join(section.get('key_points', []))}"
        for i, section in enumerate(stage2_data.get('outline', []))
    ])
    
    # Format evidence (being careful not to include hallucinated data)
    synthesis = stage2_data.get('research_synthesis', {})
    
    if synthesis.get('has_sufficient_external_evidence') == False:
        evidence_text = "Author's experience is the primary evidence. Do not add external statistics."
    else:
        evidence_text = "\n".join([
            f"- {e.get('claim', '')} (Source: {e.get('source', 'N/A')})"
            for e in synthesis.get('evidence', [])
        ]) or "No external evidence - rely on author's experience"
    
    # Format preserve elements
    preserve_text = "\n".join([f"- {elem}" for elem in preserve_elements]) or "No specific elements flagged"
    
    user_prompt = STAGE3_USER.format(
        content_type=content_type,
        author_voice=author_voice,
        guidance=guidance,
        thesis=stage2_data.get('thesis', stage2_data.get('core_insight', '')),
        preserve_elements=preserve_text,
        outline=outline_text,
        evidence=evidence_text,
        original_draft=stage2_data.get('original_draft', '')
    )
    
    response = client.chat(
        system_prompt=STAGE3_SYSTEM,
        user_prompt=user_prompt,
        temperature=0.5,
        max_tokens=4000
    )
    
    print_progress(f"✅ Draft complete: ~{len(response.split())} words")
    
    result = {
        **stage2_data,
        'stage': 3,
        'draft_content': response
    }
    
    return result


def run_stage4(client: LLMClient, stage3_data: dict, verbose: bool = False) -> dict:
    """Stage 4: Style & Polish"""
    print_header(4, "Style & Polish")
    print_progress("Polishing while preserving voice...")
    
    content_type = stage3_data.get('content_type', 'unknown')
    author_voice = stage3_data.get('author_voice', 'not specified')
    
    user_prompt = STAGE4_USER.format(
        content_type=content_type,
        author_voice=author_voice,
        draft_content=stage3_data['draft_content']
    )
    
    response = client.chat(
        system_prompt=STAGE4_SYSTEM,
        user_prompt=user_prompt,
        temperature=0.3,
        max_tokens=4000
    )
    
    print_progress(f"✅ Polished: ~{len(response.split())} words")
    
    result = {
        **stage3_data,
        'stage': 4,
        'polished_content': response
    }
    
    return result


def run_stage5(client: LLMClient, stage4_data: dict, verbose: bool = False) -> dict:
    """Stage 5: Technical Review"""
    print_header(5, "Technical Review")
    print_progress("Conducting quality review...")
    
    content_type = stage4_data.get('content_type', 'unknown')
    author_voice = stage4_data.get('author_voice', 'not specified')
    core_insight = stage4_data.get('core_insight', stage4_data.get('thesis', ''))
    
    user_prompt = STAGE5_USER.format(
        content_type=content_type,
        core_insight=core_insight,
        author_voice=author_voice,
        polished_content=stage4_data['polished_content']
    )
    
    response = client.chat(
        system_prompt=STAGE5_SYSTEM,
        user_prompt=user_prompt,
        temperature=0.2,
        json_mode=True
    )
    
    review = json.loads(response)
    
    print_progress(f"✅ Quality Score: {review.get('quality_score', 'N/A')}/10")
    print_progress(f"✅ Voice Preserved: {review.get('voice_preserved', 'N/A')}")
    print_progress(f"✅ Ready to Publish: {review.get('ready_to_publish', False)}")
    
    if review.get('issues'):
        print_progress(f"⚠️  Issues found: {len(review['issues'])}")
        for issue in review['issues']:
            severity = issue.get('severity', 'medium').upper()
            print(f"      [{severity}] {issue.get('issue', '')[:50]}...")
    
    result = {
        **stage4_data,
        'stage': 5,
        'review': review
    }
    
    return result


def create_final_output(result: dict, output_path: Path) -> str:
    """Create the final blog post with frontmatter."""
    
    content = result['polished_content']
    review = result['review']
    
    # Extract title from H1
    title = "Untitled Post"
    lines = content.split('\n')
    for line in lines:
        if line.startswith('# '):
            title = line[2:].strip()
            break
    
    # Remove H1 from content
    content_without_title = '\n'.join(
        [line for line in lines if not line.startswith('# ')]
    ).strip()
    
    # Create frontmatter
    frontmatter = f"""---
title: "{title}"
date: {datetime.now().strftime("%Y-%m-%d")}
author: Adam
tags: technical-leadership, engineering
description: "{result['thesis'][:150]}..."
---

"""
    
    # Add review comment
    review_comment = f"""<!-- 
Pipeline Review:
- Quality Score: {review['quality_score']}/10
- Status: {'✅ Ready to Publish' if review['ready_to_publish'] else '⚠️ Needs Review'}
- Notes: {review.get('reviewer_notes', 'No notes')}
-->

"""
    
    final_content = frontmatter + review_comment + content_without_title
    
    # Save the file
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(final_content)
    
    return final_content


def main():
    parser = argparse.ArgumentParser(
        description='Run the blog pipeline locally for testing',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run with Claude (default)
  python run_pipeline.py --input ../drafts/my-idea.md
  
  # Run with Azure OpenAI
  python run_pipeline.py --input ../drafts/my-idea.md --provider azure
  
  # Run specific stages only
  python run_pipeline.py --input ../drafts/my-idea.md --stages 1,2,3
  
  # Save intermediate outputs
  python run_pipeline.py --input ../drafts/my-idea.md --save-intermediate
        """
    )
    
    parser.add_argument('--input', '-i', required=True, 
                        help='Input draft file (markdown)')
    parser.add_argument('--output', '-o', 
                        help='Output file path (default: output/<basename>.md)')
    parser.add_argument('--provider', '-p', default='claude',
                        choices=['claude', 'azure'],
                        help='LLM provider to use (default: claude)')
    parser.add_argument('--stages', '-s', default='1,2,3,4,5',
                        help='Comma-separated list of stages to run (default: 1,2,3,4,5)')
    parser.add_argument('--save-intermediate', action='store_true',
                        help='Save intermediate JSON files for each stage')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Show verbose output')
    parser.add_argument('--skip-search', action='store_true', default=True,
                        help='Skip web search in stage 2 (default: True)')
    
    args = parser.parse_args()
    
    # Parse stages
    stages_to_run = [int(s.strip()) for s in args.stages.split(',')]
    
    # Determine output path
    input_path = Path(args.input)
    if args.output:
        output_path = Path(args.output)
    else:
        output_path = Path(__file__).parent / 'output' / f"{input_path.stem}.md"
    
    # Load draft
    print("\n" + "=" * 60)
    print("  BLOG PIPELINE - LOCAL TEST")
    print("=" * 60)
    
    if not input_path.exists():
        print(f"\n❌ Error: Input file not found: {input_path}")
        sys.exit(1)
    
    with open(input_path, 'r', encoding='utf-8') as f:
        draft_content = f.read()
    
    print(f"\n📄 Input: {input_path}")
    print(f"📤 Output: {output_path}")
    print(f"🔢 Stages: {stages_to_run}")
    
    # Initialize LLM client
    try:
        client = create_client(args.provider)
        print(f"🤖 Using: {client.name}")
    except ValueError as e:
        print(f"\n❌ Error: {e}")
        print("\nMake sure you have set the required environment variables:")
        if args.provider == 'claude':
            print("  export ANTHROPIC_API_KEY=your-key-here")
        else:
            print("  export AZURE_OPENAI_KEY=your-key")
            print("  export AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/")
            print("  export AZURE_OPENAI_DEPLOYMENT=gpt-4")
        sys.exit(1)
    
    # Run pipeline
    result = {'original_draft': draft_content}
    intermediate_dir = Path(__file__).parent / 'output' / 'intermediate'
    
    try:
        if 1 in stages_to_run:
            result = run_stage1(client, draft_content, args.verbose)
            if args.save_intermediate:
                intermediate_dir.mkdir(parents=True, exist_ok=True)
                with open(intermediate_dir / 'stage1.json', 'w') as f:
                    json.dump(result, f, indent=2)
        
        if 2 in stages_to_run:
            result = run_stage2(client, result, args.skip_search, args.verbose)
            if args.save_intermediate:
                with open(intermediate_dir / 'stage2.json', 'w') as f:
                    json.dump(result, f, indent=2)
        
        if 3 in stages_to_run:
            result = run_stage3(client, result, args.verbose)
            if args.save_intermediate:
                with open(intermediate_dir / 'stage3.json', 'w') as f:
                    json.dump(result, f, indent=2)
        
        if 4 in stages_to_run:
            result = run_stage4(client, result, args.verbose)
            if args.save_intermediate:
                with open(intermediate_dir / 'stage4.json', 'w') as f:
                    json.dump(result, f, indent=2)
        
        if 5 in stages_to_run:
            result = run_stage5(client, result, args.verbose)
            if args.save_intermediate:
                with open(intermediate_dir / 'stage5.json', 'w') as f:
                    json.dump(result, f, indent=2)
        
        # Create final output
        if 5 in stages_to_run:
            print("\n" + "=" * 60)
            print("  FINAL OUTPUT")
            print("=" * 60)
            
            final_content = create_final_output(result, output_path)
            
            print(f"\n✅ Pipeline complete!")
            print(f"📄 Output saved to: {output_path}")
            print(f"📊 Quality Score: {result['review']['quality_score']}/10")
            
            if result['review']['ready_to_publish']:
                print("✅ Ready to publish!")
            else:
                print("⚠️  Review recommended before publishing")
        
    except json.JSONDecodeError as e:
        print(f"\n❌ Error parsing LLM response as JSON: {e}")
        print("This sometimes happens with certain prompts. Try running again.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        raise


if __name__ == '__main__':
    main()
