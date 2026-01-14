#!/usr/bin/env python3
"""
Stage 5: Technical Review
Final quality check and preparation for publication.
Evaluates content against its own goals, not a fixed rubric.
"""

import os
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime

# Add pipeline directory to path
sys.path.insert(0, str(Path(__file__).parent))

from llm_client import create_client
from prompts import STAGE5_SYSTEM, STAGE5_USER

FRONTMATTER_TEMPLATE = """---
title: "{title}"
date: {date}
author: Adam
tags: {tags}
description: "{description}"
---

"""


def load_stage4_output(filepath: str) -> dict:
    """Load Stage 4 output."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def review_post(client, stage4_data: dict) -> dict:
    """Conduct quality review based on content type."""
    
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
    
    return json.loads(response)


def extract_title(content: str) -> str:
    """Extract title from markdown H1."""
    lines = content.split('\n')
    for line in lines:
        if line.startswith('# '):
            return line[2:].strip()
    return "Untitled Post"


def generate_tags(content_type: str) -> str:
    """Generate tags based on content type."""
    base_tags = ["technical-leadership"]
    
    type_tags = {
        "personal_insight": ["personal", "insights"],
        "technical_howto": ["tutorial", "how-to"],
        "business_case": ["business", "roi"],
        "thought_leadership": ["strategy", "leadership"]
    }
    
    tags = base_tags + type_tags.get(content_type, ["engineering"])
    return ", ".join(tags)


def create_final_post(stage4_data: dict, review_result: dict) -> str:
    """Create final blog post with frontmatter."""
    
    content = stage4_data['polished_content']
    content_type = stage4_data.get('content_type', 'unknown')
    
    # Extract title
    title = extract_title(content)
    
    # Remove H1 from content (it'll be in frontmatter/template)
    lines = content.split('\n')
    content_without_title = '\n'.join(
        [line for line in lines if not line.startswith('# ')]
    ).strip()
    
    # Generate frontmatter
    thesis = stage4_data.get('thesis', stage4_data.get('core_insight', ''))
    description = thesis[:150] + "..." if len(thesis) > 150 else thesis
    
    frontmatter = FRONTMATTER_TEMPLATE.format(
        title=title,
        date=datetime.now().strftime("%Y-%m-%d"),
        tags=generate_tags(content_type),
        description=description
    )
    
    # Add review notes as HTML comment
    review_comment = f"""<!-- 
Pipeline Review:
- Quality Score: {review_result.get('quality_score', 'N/A')}/10
- Content Type: {content_type}
- Voice Preserved: {review_result.get('voice_preserved', 'N/A')}
- Conclusion Quality: {review_result.get('conclusion_quality', 'N/A')}
- Status: {'✅ Ready to Publish' if review_result.get('ready_to_publish') else '⚠️ Needs Review'}
- Notes: {review_result.get('reviewer_notes', 'No notes')}
-->

"""
    
    return frontmatter + review_comment + content_without_title


def main():
    parser = argparse.ArgumentParser(description='Stage 5: Technical review')
    parser.add_argument('--input', required=True, help='Stage 4 output JSON')
    parser.add_argument('--output', required=True, help='Output markdown file')
    args = parser.parse_args()
    
    # Initialize client
    client = create_client()
    print(f"Using: {client.name}")
    
    # Load Stage 4 output
    print(f"Loading Stage 4 output from {args.input}...")
    stage4_data = load_stage4_output(args.input)
    
    # Conduct review
    print("Conducting quality review...")
    review_result = review_post(client, stage4_data)
    
    print(f"   Quality Score: {review_result.get('quality_score', 'N/A')}/10")
    print(f"   Voice Preserved: {review_result.get('voice_preserved', 'N/A')}")
    print(f"   Conclusion Quality: {review_result.get('conclusion_quality', 'N/A')}")
    print(f"   Ready to Publish: {review_result.get('ready_to_publish', False)}")
    
    if review_result.get('issues'):
        print(f"   Issues Found: {len(review_result['issues'])}")
        for issue in review_result['issues']:
            severity = issue.get('severity', 'medium').upper()
            print(f"     - [{severity}] {issue.get('issue', '')[:60]}...")
    
    # Create final post
    print("Creating final blog post...")
    final_post = create_final_post(stage4_data, review_result)
    
    # Save output
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(final_post)
    
    print(f"✅ Stage 5 complete. Output saved to {args.output}")
    
    if review_result.get('ready_to_publish'):
        print("✅ Post is ready to publish!")
    else:
        print("⚠️  Review recommended before publishing")


if __name__ == '__main__':
    main()
