#!/usr/bin/env python3
"""
Stage 4: Style & Polish
Polishes the draft while preserving the author's voice and unique elements.
"""

import os
import sys
import json
import argparse
from pathlib import Path

# Add pipeline directory to path
sys.path.insert(0, str(Path(__file__).parent))

from llm_client import create_client
from prompts import STAGE4_SYSTEM, STAGE4_USER


def load_stage3_output(filepath: str) -> dict:
    """Load Stage 3 output."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def polish_draft(client, stage3_data: dict) -> str:
    """Polish the draft while preserving voice and character."""
    
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
    
    return response


def main():
    parser = argparse.ArgumentParser(description='Stage 4: Polish the draft')
    parser.add_argument('--input', required=True, help='Stage 3 output JSON')
    parser.add_argument('--output', required=True, help='Output JSON file')
    args = parser.parse_args()
    
    # Initialize client
    client = create_client()
    print(f"Using: {client.name}")
    
    # Load Stage 3 output
    print(f"Loading Stage 3 output from {args.input}...")
    stage3_data = load_stage3_output(args.input)
    
    # Polish draft
    print(f"Polishing draft (preserving {stage3_data.get('author_voice', 'unknown')} voice)...")
    polished_content = polish_draft(client, stage3_data)
    
    # Combine with previous data
    output_data = {
        **stage3_data,
        'stage': 4,
        'polished_content': polished_content
    }
    
    # Save output
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2)
    
    print(f"✅ Stage 4 complete. Output saved to {args.output}")
    print(f"   Polished length: {len(polished_content)} characters")


if __name__ == '__main__':
    main()
