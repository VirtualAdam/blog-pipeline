#!/usr/bin/env python3
"""
PR Comment Revision Handler

Processes PR review comments as revision prompts for the LLM.
Takes a comment on a specific line and uses it to guide revisions.
"""

import argparse
import json
import os
import sys
from pathlib import Path

from llm_client import create_client


REVISION_SYSTEM_PROMPT = """You are an expert editor helping revise a technical blog post based on reviewer feedback.

Your task:
1. Read the entire blog post for context
2. Focus on the specific line indicated by the reviewer
3. Apply the reviewer's suggestion while maintaining:
   - Consistency with the rest of the document
   - The author's voice and tone
   - Technical accuracy
   - Professional language appropriate for technical leaders

Guidelines:
- Make targeted, minimal changes that address the feedback
- If the feedback requires changing just one line, change only that line
- If the feedback implies broader changes (like "use more formal tone throughout"), apply them document-wide
- Preserve markdown formatting
- Keep the document structure intact

You must respond with a JSON object containing:
{
  "revised_content": "The full revised markdown content",
  "changes_made": "A brief summary of what was changed (1-2 sentences)",
  "lines_affected": "Description of which lines were modified"
}
"""


def read_file_content(file_path: str) -> str:
    """Read the content of the file to be revised."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()


def get_line_context(content: str, line_number: int, context_lines: int = 5) -> dict:
    """Extract the target line and surrounding context."""
    lines = content.split('\n')
    
    # Adjust for 0-based indexing
    line_idx = line_number - 1
    
    # Get the target line
    target_line = lines[line_idx] if 0 <= line_idx < len(lines) else ""
    
    # Get surrounding context
    start_idx = max(0, line_idx - context_lines)
    end_idx = min(len(lines), line_idx + context_lines + 1)
    
    context_before = lines[start_idx:line_idx]
    context_after = lines[line_idx + 1:end_idx]
    
    return {
        "target_line": target_line,
        "line_number": line_number,
        "context_before": context_before,
        "context_after": context_after
    }


def build_revision_prompt(file_content: str, line_number: int, comment: str) -> str:
    """Build the prompt for the LLM revision request."""
    line_context = get_line_context(file_content, line_number)
    
    prompt = f"""## Full Document Content

{file_content}

---

## Reviewer Feedback

**Location**: Line {line_number}

**Target Line**:
```
{line_context['target_line']}
```

**Surrounding Context** (for reference):
```
{chr(10).join(line_context['context_before'])}
>>> {line_context['target_line']}  <<<  [LINE {line_number} - REVIEWER COMMENT HERE]
{chr(10).join(line_context['context_after'])}
```

**Reviewer's Comment/Request**:
{comment}

---

Please revise the document according to the reviewer's feedback. Focus primarily on the indicated line but consider the broader context if the feedback warrants it.
"""
    return prompt


def apply_revision(file_path: str, line_number: int, comment: str) -> dict:
    """Process the revision request using the LLM."""
    
    # Read current file content
    content = read_file_content(file_path)
    
    # Build the prompt
    user_prompt = build_revision_prompt(content, line_number, comment)
    
    # Get LLM client
    client = create_client()
    print(f"Using LLM: {client.name}")
    
    # Send to LLM
    print(f"Processing revision for {file_path} line {line_number}...")
    print(f"Comment: {comment[:100]}..." if len(comment) > 100 else f"Comment: {comment}")
    
    response = client.chat(
        system_prompt=REVISION_SYSTEM_PROMPT,
        user_prompt=user_prompt,
        temperature=0.3,
        json_mode=True,
        max_tokens=8000  # Allow for full document revision
    )
    
    # Parse response
    try:
        result = json.loads(response)
    except json.JSONDecodeError as e:
        print(f"Error parsing LLM response: {e}")
        print(f"Raw response: {response[:500]}...")
        raise
    
    return result


def save_revision(file_path: str, result: dict):
    """Save the revised content back to the file."""
    revised_content = result.get('revised_content', '')
    
    if not revised_content:
        raise ValueError("LLM did not return revised content")
    
    # Write revised content
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(revised_content)
    
    print(f"✓ Saved revised content to {file_path}")
    
    # Save summary for GitHub Actions to use
    summary = result.get('changes_made', 'Changes applied.')
    lines_affected = result.get('lines_affected', 'See diff for details.')
    
    temp_dir = Path('pipeline/temp')
    temp_dir.mkdir(parents=True, exist_ok=True)
    
    summary_file = temp_dir / 'revision_summary.txt'
    with open(summary_file, 'w', encoding='utf-8') as f:
        f.write(f"**Changes Made**: {summary}\n\n")
        f.write(f"**Lines Affected**: {lines_affected}")
    
    print(f"✓ Saved revision summary to {summary_file}")


def main():
    parser = argparse.ArgumentParser(
        description="Process PR comment as a revision request"
    )
    parser.add_argument(
        '--file', 
        required=True,
        help='Path to the file to revise'
    )
    parser.add_argument(
        '--line',
        type=int,
        required=True,
        help='Line number the comment was made on'
    )
    parser.add_argument(
        '--comment',
        help='The revision comment/instruction'
    )
    parser.add_argument(
        '--comment-file',
        help='File containing the revision comment (for multi-line comments)'
    )
    
    args = parser.parse_args()
    
    # Get comment from either argument or file
    if args.comment_file and os.path.exists(args.comment_file):
        with open(args.comment_file, 'r', encoding='utf-8') as f:
            comment = f.read().strip()
    elif args.comment:
        comment = args.comment
    else:
        print("Error: Must provide either --comment or --comment-file")
        sys.exit(1)
    
    # Validate file exists
    if not os.path.exists(args.file):
        print(f"Error: File not found: {args.file}")
        sys.exit(1)
    
    print(f"=" * 60)
    print(f"PR Comment Revision Pipeline")
    print(f"=" * 60)
    print(f"File: {args.file}")
    print(f"Line: {args.line}")
    print(f"Comment: {comment}")
    print(f"=" * 60)
    
    try:
        # Process the revision
        result = apply_revision(args.file, args.line, comment)
        
        # Save the revised content
        save_revision(args.file, result)
        
        print(f"\n✓ Revision completed successfully!")
        print(f"  Changes: {result.get('changes_made', 'See diff')}")
        
    except Exception as e:
        print(f"\n✗ Error during revision: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
