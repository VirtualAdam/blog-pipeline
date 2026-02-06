#!/usr/bin/env python3
"""
Stage 7: Image Generation
Executes the image plan from Stage 6 by calling Gemini's Nano Banana Pro
model for both hero images and section diagrams.

Handles:
  - Calling Gemini image generation API
  - Fallback and retry logic
  - Saving images to the output directory
  - Skipping images that already exist (idempotency)
"""

import os
import sys
import json
import time
import base64
import argparse
import logging
from pathlib import Path

# Add pipeline directory to path
sys.path.insert(0, str(Path(__file__).parent))

logger = logging.getLogger(__name__)


def load_stage6_output(filepath: str) -> dict:
    """Load Stage 6 image plan."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def generate_image_gemini(prompt: str, output_path: Path, aspect_ratio: str = "16:9",
                          max_retries: int = 3) -> bool:
    """
    Generate an image using the Gemini Nano Banana Pro model.

    Args:
        prompt: The image generation prompt.
        output_path: Where to save the generated image.
        aspect_ratio: Aspect ratio for the image (e.g., "16:9", "1:1").
        max_retries: Number of retries on failure.

    Returns:
        True if the image was generated successfully.
    """
    try:
        from google import genai
        from google.genai import types
    except ImportError:
        raise ImportError(
            "Please install the Google GenAI SDK: pip install google-genai"
        )

    api_key = os.environ.get('GEMINI_API_KEY')
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable not set")

    client = genai.Client(api_key=api_key)

    for attempt in range(1, max_retries + 1):
        try:
            response = client.models.generate_images(
                model="imagen-3.0-generate-002",
                prompt=prompt,
                config=types.GenerateImagesConfig(
                    number_of_images=1,
                    aspect_ratio=aspect_ratio,
                    safety_filter_level="BLOCK_ONLY_HIGH",
                ),
            )

            if response.generated_images:
                image_data = response.generated_images[0].image
                # image_data is a google.genai.types.Image with .image_bytes
                output_path.parent.mkdir(parents=True, exist_ok=True)
                output_path.write_bytes(image_data.image_bytes)
                return True
            else:
                print(f"     ⚠️  No image returned (attempt {attempt}/{max_retries})")
                if attempt < max_retries:
                    time.sleep(2 ** attempt)

        except Exception as e:
            print(f"     ⚠️  Generation error (attempt {attempt}/{max_retries}): {e}")
            if attempt < max_retries:
                time.sleep(2 ** attempt)

    return False


def main():
    parser = argparse.ArgumentParser(description='Stage 7: Generate images')
    parser.add_argument('--input', required=True, help='Stage 6 output JSON (image plan)')
    parser.add_argument('--output-dir', required=True, help='Directory to save generated images')
    parser.add_argument('--output', required=True, help='Output JSON file with generation results')
    args = parser.parse_args()

    # Load image plan
    print(f"Loading image plan from {args.input}...")
    stage6_data = load_stage6_output(args.input)
    image_plan = stage6_data.get('image_plan', {})

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    results = {
        'stage': 7,
        'blog_post_file': stage6_data.get('blog_post_file', ''),
        'images': [],
        'failures': []
    }

    # ── Generate Hero Image ─────────────────────────────────────
    hero = image_plan.get('hero', {})
    if hero and hero.get('prompt'):
        hero_path = output_dir / "hero.png"
        if hero_path.exists():
            print(f"   Skipping hero — already exists at {hero_path}")
            results['images'].append({
                'image_id': 'hero',
                'image_type': 'hero',
                'file_path': str(hero_path),
                'prompt_used': hero['prompt'][:100] + '...'
            })
        else:
            print("Generating hero image...")
            success = generate_image_gemini(
                prompt=hero['prompt'],
                output_path=hero_path,
                aspect_ratio="16:9"
            )
            if success:
                print(f"   ✅ Hero image saved to {hero_path}")
                results['images'].append({
                    'image_id': 'hero',
                    'image_type': 'hero',
                    'file_path': str(hero_path),
                    'prompt_used': hero['prompt'][:100] + '...'
                })
            else:
                print("   ❌ Hero image generation failed")
                results['failures'].append({
                    'image_id': 'hero',
                    'error': 'All retries exhausted'
                })

    # ── Generate Section Diagrams ───────────────────────────────
    diagrams = image_plan.get('diagrams', [])
    for i, diagram in enumerate(diagrams):
        diagram_id = diagram.get('image_id', f'section_{i + 1}')
        diagram_prompt = diagram.get('prompt', '')
        diagram_type = diagram.get('diagram_type', 'infographic')
        target_section = diagram.get('target_section', 'unknown')

        if not diagram_prompt:
            print(f"   Skipping diagram {diagram_id} — no prompt")
            continue

        diagram_path = output_dir / f"{diagram_id}.png"

        if diagram_path.exists():
            print(f"   Skipping {diagram_id} — already exists at {diagram_path}")
            results['images'].append({
                'image_id': diagram_id,
                'image_type': 'diagram',
                'diagram_type': diagram_type,
                'target_section': target_section,
                'file_path': str(diagram_path),
                'prompt_used': diagram_prompt[:100] + '...'
            })
            continue

        print(f"Generating diagram: {diagram_id} [{diagram_type}] for \"{target_section}\"...")

        # Diagrams get 16:9 for wide blog layout
        success = generate_image_gemini(
            prompt=diagram_prompt,
            output_path=diagram_path,
            aspect_ratio="16:9"
        )

        if success:
            print(f"   ✅ Diagram saved to {diagram_path}")
            results['images'].append({
                'image_id': diagram_id,
                'image_type': 'diagram',
                'diagram_type': diagram_type,
                'target_section': target_section,
                'file_path': str(diagram_path),
                'prompt_used': diagram_prompt[:100] + '...'
            })
        else:
            print(f"   ❌ Diagram {diagram_id} generation failed")
            results['failures'].append({
                'image_id': diagram_id,
                'target_section': target_section,
                'error': 'All retries exhausted'
            })

        # Small delay between API calls to avoid rate limiting
        if i < len(diagrams) - 1:
            time.sleep(1)

    # ── Summary ─────────────────────────────────────────────────
    total = 1 + len(diagrams)
    succeeded = len(results['images'])
    failed = len(results['failures'])

    print(f"\n   Generated {succeeded}/{total} images ({failed} failures)")

    # Save results
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)

    print(f"✅ Stage 7 complete. Output saved to {args.output}")


if __name__ == '__main__':
    main()
