#!/usr/bin/env python3
"""
Stage 6: Image Prompt Generator
Analyzes the finished blog post and creates targeted image prompts.

Two types of images:
  1. Hero image — artistic, eye-catching, sets the mood for the post
  2. Section diagrams — infographics, flow diagrams, architecture visuals
     (only for sections that benefit from visual aids)

Image generation uses Gemini Nano Banana Pro for both hero and diagrams,
leveraging its strengths in accurate text rendering and clean layouts.
"""

import os
import sys
import json
import argparse
from pathlib import Path

# Add pipeline directory to path
sys.path.insert(0, str(Path(__file__).parent))

from llm_client import create_client
from prompts import STAGE6_SYSTEM, STAGE6_USER


def load_stage5_post(filepath: str) -> str:
    """Load the finished blog post from Stage 5."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return f.read()


def load_stage4_data(filepath: str) -> dict:
    """Load Stage 4 JSON for metadata (content type, thesis, etc.)."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def generate_image_plan(client, blog_content: str, metadata: dict) -> dict:
    """
    Analyze the blog post and generate an image plan with prompts.

    Returns a JSON structure with hero and diagram specs.
    """
    content_type = metadata.get('content_type', 'unknown')
    core_insight = metadata.get('core_insight', metadata.get('thesis', ''))
    author_voice = metadata.get('author_voice', 'not specified')

    # Extract section headings from the blog content
    sections = []
    for line in blog_content.split('\n'):
        if line.startswith('## '):
            sections.append(line[3:].strip())

    sections_text = "\n".join(f"- {s}" for s in sections) if sections else "No H2 sections found"

    user_prompt = STAGE6_USER.format(
        content_type=content_type,
        core_insight=core_insight,
        author_voice=author_voice,
        sections=sections_text,
        blog_content=blog_content
    )

    response = client.chat(
        system_prompt=STAGE6_SYSTEM,
        user_prompt=user_prompt,
        temperature=0.4,
        json_mode=True
    )

    return json.loads(response)


def main():
    parser = argparse.ArgumentParser(description='Stage 6: Generate image prompts')
    parser.add_argument('--input', required=True, help='Stage 5 blog post markdown file')
    parser.add_argument('--metadata', required=True, help='Stage 4 output JSON (for content metadata)')
    parser.add_argument('--output', required=True, help='Output JSON file with image plan')
    args = parser.parse_args()

    # Initialize client
    client = create_client()
    print(f"Using: {client.name}")

    # Load inputs
    print(f"Loading blog post from {args.input}...")
    blog_content = load_stage5_post(args.input)

    print(f"Loading metadata from {args.metadata}...")
    metadata = load_stage4_data(args.metadata)

    # Generate image plan
    print("Analyzing blog for image opportunities...")
    image_plan = generate_image_plan(client, blog_content, metadata)

    hero = image_plan.get('hero', {})
    diagrams = image_plan.get('diagrams', [])

    print(f"   Hero image: {hero.get('description', 'N/A')[:60]}...")
    print(f"   Section diagrams: {len(diagrams)}")
    for i, d in enumerate(diagrams):
        dtype = d.get('diagram_type', 'infographic')
        section = d.get('target_section', 'unknown')
        print(f"     {i + 1}. [{dtype}] for \"{section}\"")

    # Save output
    output_data = {
        'stage': 6,
        'blog_post_file': args.input,
        'content_type': metadata.get('content_type', 'unknown'),
        'image_plan': image_plan
    }

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2)

    print(f"✅ Stage 6 complete. Output saved to {args.output}")
    print(f"   Total images planned: {1 + len(diagrams)}")


if __name__ == '__main__':
    main()
