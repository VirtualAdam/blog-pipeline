#!/usr/bin/env python3
"""
Stage 8: Image Assembly
Combines the finished blog post with generated images by inserting
image references inline at the appropriate locations.

Places:
  - Hero image at the top of the post (below frontmatter)
  - Section diagrams after their corresponding H2 headings
  - Copies images into a post-specific images directory

Output structure:
  posts/{slug}.md          — final markdown with image references
  posts/{slug}/hero.png    — hero image
  posts/{slug}/*.png       — section diagrams
"""

import os
import sys
import json
import re
import shutil
import argparse
from pathlib import Path

# Add pipeline directory to path
sys.path.insert(0, str(Path(__file__).parent))


def load_blog_post(filepath: str) -> str:
    """Load the blog post markdown from Stage 5."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return f.read()


def load_stage7_results(filepath: str) -> dict:
    """Load Stage 7 image generation results."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_stage6_plan(filepath: str) -> dict:
    """Load Stage 6 image plan for section mapping."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def normalize_heading(heading: str) -> str:
    """Normalize a heading for fuzzy matching."""
    return re.sub(r'[^a-z0-9\s]', '', heading.lower()).strip()


def insert_images(blog_content: str, image_results: dict, image_plan: dict,
                  images_relative_dir: str) -> str:
    """
    Insert image references into the blog markdown.

    Args:
        blog_content: The original blog markdown.
        image_results: Stage 7 results with generated image paths.
        image_plan: Stage 6 plan with section mapping info.
        images_relative_dir: Relative path to images dir (e.g., "my-post").

    Returns:
        Updated markdown with image references inserted.
    """
    images = image_results.get('images', [])
    plan_diagrams = image_plan.get('image_plan', {}).get('diagrams', [])

    # Build lookup: image_id → generated image info
    image_map = {img['image_id']: img for img in images}

    # Build lookup: normalized section heading → diagram info (from plan)
    section_diagram_map = {}
    for diagram in plan_diagrams:
        target = diagram.get('target_section', '')
        image_id = diagram.get('image_id', '')
        if target and image_id:
            section_diagram_map[normalize_heading(target)] = {
                'image_id': image_id,
                'alt_text': diagram.get('alt_text', f'Diagram: {target}'),
                'caption': diagram.get('caption', ''),
            }

    lines = blog_content.split('\n')
    output_lines = []
    hero_inserted = False
    frontmatter_ended = False
    in_frontmatter = False

    for i, line in enumerate(lines):
        output_lines.append(line)

        # Track frontmatter boundaries
        if line.strip() == '---':
            if not in_frontmatter:
                in_frontmatter = True
            else:
                frontmatter_ended = True
                in_frontmatter = False
                continue

        # Insert hero image after frontmatter + review comment block
        if frontmatter_ended and not hero_inserted:
            # Wait until we're past the HTML comment block (pipeline review)
            if line.strip() == '-->' or (not line.strip().startswith('<!--') and
                                          not line.strip().startswith('-') and
                                          not line.strip().startswith('-->') and
                                          not in_html_comment(lines, i) and
                                          line.strip() != ''):
                if 'hero' in image_map:
                    hero = image_map['hero']
                    hero_filename = Path(hero['file_path']).name
                    hero_ref = f"{images_relative_dir}/{hero_filename}"
                    output_lines.append('')
                    output_lines.append(f'![Hero Image]({hero_ref})')
                    output_lines.append('')
                hero_inserted = True

        # Insert diagram after matching H2 heading
        if line.startswith('## '):
            heading = line[3:].strip()
            normalized = normalize_heading(heading)

            if normalized in section_diagram_map:
                diagram_info = section_diagram_map[normalized]
                image_id = diagram_info['image_id']

                if image_id in image_map:
                    img = image_map[image_id]
                    img_filename = Path(img['file_path']).name
                    img_ref = f"{images_relative_dir}/{img_filename}"
                    alt_text = diagram_info.get('alt_text', f'Diagram: {heading}')

                    output_lines.append('')
                    output_lines.append(f'![{alt_text}]({img_ref})')
                    if diagram_info.get('caption'):
                        output_lines.append(f'*{diagram_info["caption"]}*')
                    output_lines.append('')

    return '\n'.join(output_lines)


def in_html_comment(lines: list, current_idx: int) -> bool:
    """Check if we're currently inside an HTML comment block."""
    in_comment = False
    for i in range(current_idx + 1):
        line = lines[i].strip()
        if '<!--' in line and '-->' not in line:
            in_comment = True
        elif '-->' in line:
            in_comment = False
    return in_comment


def copy_images(image_results: dict, dest_dir: Path) -> list:
    """Copy generated images to the post's image directory."""
    dest_dir.mkdir(parents=True, exist_ok=True)
    copied = []

    for img in image_results.get('images', []):
        src = Path(img['file_path'])
        if src.exists():
            dest = dest_dir / src.name
            shutil.copy2(src, dest)
            copied.append(str(dest))

    return copied


def main():
    parser = argparse.ArgumentParser(description='Stage 8: Assemble blog with images')
    parser.add_argument('--blog-input', required=True, help='Stage 5 blog post markdown')
    parser.add_argument('--image-results', required=True, help='Stage 7 output JSON')
    parser.add_argument('--image-plan', required=True, help='Stage 6 output JSON')
    parser.add_argument('--output', required=True, help='Output markdown file (final blog post)')
    args = parser.parse_args()

    # Derive slug from output filename
    output_path = Path(args.output)
    slug = output_path.stem

    print(f"Assembling final blog post: {slug}")

    # Load inputs
    print(f"Loading blog post from {args.blog_input}...")
    blog_content = load_blog_post(args.blog_input)

    print(f"Loading image results from {args.image_results}...")
    image_results = load_stage7_results(args.image_results)

    print(f"Loading image plan from {args.image_plan}...")
    image_plan = load_stage6_plan(args.image_plan)

    # Copy images to post directory
    images_dir = output_path.parent / slug
    print(f"Copying images to {images_dir}...")
    copied = copy_images(image_results, images_dir)
    print(f"   Copied {len(copied)} images")

    # Insert image references into blog markdown
    print("Inserting image references into blog post...")
    final_content = insert_images(
        blog_content=blog_content,
        image_results=image_results,
        image_plan=image_plan,
        images_relative_dir=slug
    )

    # Write final output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(final_content)

    # Summary
    total_images = len(image_results.get('images', []))
    failures = len(image_results.get('failures', []))
    word_count = len(final_content.split())

    print(f"\n✅ Stage 8 complete. Output saved to {args.output}")
    print(f"   Images embedded: {total_images}")
    if failures:
        print(f"   ⚠️  Image failures: {failures} (post still valid, just missing those images)")
    print(f"   Final word count: ~{word_count}")
    print(f"   Images directory: {images_dir}")


if __name__ == '__main__':
    main()
