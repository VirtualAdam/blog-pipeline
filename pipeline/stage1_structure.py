#!/usr/bin/env python3
"""
Stage 1: Intake & Structure
Analyzes the draft to understand content type, extract core insight, and create structure.
"""

import os
import sys
import json
import argparse
from pathlib import Path

# Add pipeline directory to path
sys.path.insert(0, str(Path(__file__).parent))

from llm_client import create_client
from prompts import STAGE1_SYSTEM, STAGE1_USER


def load_draft(filepath: str) -> str:
    """Load the draft content from file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return f.read()


def structure_draft(client, draft_content: str) -> dict:
    """Analyze and structure the draft."""
    
    user_prompt = STAGE1_USER.format(draft_content=draft_content)
    
    response = client.chat(
        system_prompt=STAGE1_SYSTEM,
        user_prompt=user_prompt,
        temperature=0.3,
        json_mode=True
    )
    
    return json.loads(response)


def main():
    parser = argparse.ArgumentParser(description='Stage 1: Structure the draft')
    parser.add_argument('--input', required=True, help='Input draft file')
    parser.add_argument('--output', required=True, help='Output JSON file')
    args = parser.parse_args()
    
    # Initialize LLM client (auto-detects provider)
    client = create_client()
    print(f"Using: {client.name}")
    
    # Load and process draft
    print(f"Loading draft from {args.input}...")
    draft_content = load_draft(args.input)
    
    print("Running Stage 1: Analyzing and structuring draft...")
    structured_data = structure_draft(client, draft_content)
    
    # Add metadata
    structured_data['original_draft'] = draft_content
    structured_data['stage'] = 1
    
    # Save output
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(structured_data, f, indent=2)
    
    print(f"✅ Stage 1 complete. Output saved to {args.output}")
    print(f"   Content type: {structured_data.get('content_type', 'unknown')}")
    print(f"   Core insight: {structured_data.get('core_insight', '')[:80]}...")
    print(f"   Sections: {len(structured_data.get('outline', []))}")


if __name__ == '__main__':
    main()
