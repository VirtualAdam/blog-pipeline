#!/usr/bin/env python3
"""
Stage 3: Expansion with Inverted Pyramid
Writes the full draft, adapting style to content type and preserving author voice.
"""

import os
import sys
import json
import argparse
from pathlib import Path

# Add pipeline directory to path
sys.path.insert(0, str(Path(__file__).parent))

from llm_client import create_client
from prompts import STAGE3_SYSTEM, STAGE3_USER


def load_stage2_output(filepath: str) -> dict:
    """Load Stage 2 output."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def expand_to_draft(client, stage2_data: dict) -> str:
    """Generate full draft following inverted pyramid, preserving voice."""
    
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
    
    return response


def main():
    parser = argparse.ArgumentParser(description='Stage 3: Expand to full draft')
    parser.add_argument('--input', required=True, help='Stage 2 output JSON')
    parser.add_argument('--output', required=True, help='Output JSON file')
    args = parser.parse_args()
    
    # Initialize client
    client = create_client()
    print(f"Using: {client.name}")
    
    # Load Stage 2 output
    print(f"Loading Stage 2 output from {args.input}...")
    stage2_data = load_stage2_output(args.input)
    
    # Generate draft
    print(f"Generating full draft (content type: {stage2_data.get('content_type', 'unknown')})...")
    draft_content = expand_to_draft(client, stage2_data)
    
    # Combine with previous data
    output_data = {
        **stage2_data,
        'stage': 3,
        'draft_content': draft_content
    }
    
    # Save output
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2)
    
    print(f"✅ Stage 3 complete. Output saved to {args.output}")
    print(f"   Draft length: {len(draft_content)} characters")
    print(f"   Word count: ~{len(draft_content.split())} words")


if __name__ == '__main__':
    main()
