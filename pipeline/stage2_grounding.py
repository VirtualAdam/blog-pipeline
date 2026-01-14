#!/usr/bin/env python3
"""
Stage 2: Grounding & Research
Searches for evidence and synthesizes research to support the thesis.
Does NOT hallucinate - only uses real findings or author's experience.
"""

import os
import sys
import json
import argparse
import requests
from pathlib import Path
from typing import List, Dict

# Add pipeline directory to path
sys.path.insert(0, str(Path(__file__).parent))

from llm_client import create_client
from prompts import (
    STAGE2_QUERIES_SYSTEM, STAGE2_QUERIES_USER,
    STAGE2_SYNTHESIS_SYSTEM, STAGE2_SYNTHESIS_USER
)


def load_stage1_output(filepath: str) -> dict:
    """Load Stage 1 output."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def generate_search_queries(client, stage1_data: dict) -> dict:
    """Generate targeted search queries based on content type."""
    
    content_type = stage1_data.get('content_type', 'unknown')
    guidance = stage1_data.get('guidance_for_later_stages', '')
    
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
    
    return json.loads(response)


def search_web(query: str, bing_key: str) -> List[Dict]:
    """Search using Bing Search API."""
    
    endpoint = "https://api.bing.microsoft.com/v7.0/search"
    headers = {"Ocp-Apim-Subscription-Key": bing_key}
    params = {
        "q": query,
        "count": 5,
        "responseFilter": "Webpages"
    }
    
    try:
        response = requests.get(endpoint, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()
        
        results = []
        if 'webPages' in data and 'value' in data['webPages']:
            for item in data['webPages']['value']:
                results.append({
                    "title": item.get('name', ''),
                    "url": item.get('url', ''),
                    "snippet": item.get('snippet', '')
                })
        
        return results
        
    except Exception as e:
        print(f"  Search error for '{query}': {e}")
        return []


def synthesize_research(client, content_type: str, search_results: str) -> dict:
    """Synthesize research findings without hallucinating."""
    
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
    
    return json.loads(response)


def main():
    parser = argparse.ArgumentParser(description='Stage 2: Ground with research')
    parser.add_argument('--input', required=True, help='Stage 1 output JSON')
    parser.add_argument('--output', required=True, help='Output JSON file')
    args = parser.parse_args()
    
    # Initialize client
    client = create_client()
    print(f"Using: {client.name}")
    
    # Load Stage 1 output
    print(f"Loading Stage 1 output from {args.input}...")
    stage1_data = load_stage1_output(args.input)
    
    content_type = stage1_data.get('content_type', 'unknown')
    print(f"Content type: {content_type}")
    
    # Generate search queries
    print("Generating research queries...")
    queries_result = generate_search_queries(client, stage1_data)
    
    grounding_strategy = queries_result.get('grounding_strategy', 'standard')
    search_queries = queries_result.get('search_queries', [])
    author_exp_sufficient = queries_result.get('author_experience_sufficient', False)
    
    print(f"   Grounding strategy: {grounding_strategy}")
    print(f"   Search queries: {len(search_queries)}")
    
    if author_exp_sufficient:
        print("   ℹ️  Author experience identified as primary evidence")
    
    # Perform web search if Bing key is available and needed
    bing_key = os.environ.get('BING_SEARCH_KEY')
    all_results = []
    
    if bing_key and search_queries and not author_exp_sufficient:
        print("Searching web for supporting evidence...")
        for query_info in search_queries:
            query = query_info.get('query', '')
            if query:
                print(f"   Searching: {query[:50]}...")
                results = search_web(query, bing_key)
                all_results.extend(results)
        
        search_results_text = json.dumps(all_results, indent=2) if all_results else "No results found"
    else:
        if not bing_key:
            print("   ⚠️  No Bing Search API key - skipping web search")
        
        # For personal insight or when no search is needed
        if content_type == 'personal_insight' or author_exp_sufficient:
            search_results_text = f"""Content type: {content_type}
This is a personal insight piece. The author's own experience is the primary evidence.
Do not invent external statistics or case studies.
Thesis: {stage1_data.get('thesis', stage1_data.get('core_insight', ''))}"""
        else:
            search_results_text = "No search results available. Use only information from the original draft."
    
    # Synthesize research
    print("Synthesizing research findings...")
    synthesis = synthesize_research(client, content_type, search_results_text)
    
    if synthesis.get('has_sufficient_external_evidence') == False:
        print("   ℹ️  Limited external evidence - will rely on author's experience")
    else:
        print(f"   Evidence points: {len(synthesis.get('evidence', []))}")
        print(f"   Case studies: {len(synthesis.get('case_studies', []))}")
    
    # Combine results
    result = {
        **stage1_data,
        'stage': 2,
        'grounding_strategy': grounding_strategy,
        'search_queries': search_queries,
        'research_synthesis': synthesis
    }
    
    # Save output
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2)
    
    print(f"✅ Stage 2 complete. Output saved to {args.output}")


if __name__ == '__main__':
    main()
