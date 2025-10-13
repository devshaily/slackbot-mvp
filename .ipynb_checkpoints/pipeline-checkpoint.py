import re
from collections import defaultdict

# Topic seeds for grouping
_TOPIC_SEEDS = {
    "marketing": [
        "marketing", "ad", "ads", "advertis", "campaign",
        "performance", "roi", "cpc", "cpm", "content", "seo", "sem"
    ],
    "analytics": [
        "analytics", "metric", "kpi", "report", "dashboard", "attribution"
    ],
    "ai/llm": [
        "ai", "llm", "gpt", "agents", "prompt", "rag", "embedding", "vector"
    ],
    "social": [
        "facebook", "instagram", "twitter", "linkedin", "tiktok", "reels"
    ],
}

import re
from collections import defaultdict

def clean_keywords(raw_text: str) -> list[str]:
    """
    Takes a comma- or newline-separated string and returns
    a cleaned, deduplicated keyword list.
    """
    # Split on commas or newlines
    parts = re.split(r"[,\n]+", raw_text)
    # Strip spaces and lowercase
    cleaned = [p.strip().lower() for p in parts if p.strip()]
    # Deduplicate while preserving order
    seen = set()
    unique = []
    for kw in cleaned:
        if kw not in seen:
            seen.add(kw)
            unique.append(kw)
    return unique

def simple_group(keywords: list[str]) -> list[dict]:
    buckets = defaultdict(list)

    def match_topic(kw: str) -> str | None:
        for label, seeds in _TOPIC_SEEDS.items():
            for s in seeds:
                if s in kw:
                    return label
        return None

    # First pass by topic
    unassigned = []
    for kw in keywords:
        label = match_topic(kw)
        if label:
            buckets[label].append(kw)
        else:
            unassigned.append(kw)

    # Fallback: first-letter grouping for remaining
    for kw in unassigned:
        buckets[f"misc-{kw[0]}"].append(kw)

    # Format results
    groups = [{"label": label, "items": items} for label, items in buckets.items()]
    # Sort by size desc
    groups.sort(key=lambda g: len(g["items"]), reverse=True)
    return groups


# 3) Fake outline (template-based)
def fake_outline(group_label: str, items: list[str]) -> dict:
    example_kw = items[:3]
    return {
        "title": f"{group_label.title()} – Blog Outline",
        "sections": [
            {
                "heading": "Introduction",
                "bullets": [
                    f"What is {group_label}?",
                    "Who should care and why now",
                    f"Where {', '.join(example_kw)} fits in",
                ],
            },
            {
                "heading": "Key Concepts",
                "bullets": [
                    "Definitions",
                    "Common terms",
                    "Metrics that matter",
                ],
            },
            {
                "heading": "How-To / Steps",
                "bullets": [
                    "Step 1: Setup",
                    "Step 2: Execution",
                    "Step 3: Measure & iterate",
                ],
            },
            {
                "heading": "Best Practices",
                "bullets": [
                    "Do more with less",
                    "Automate repeatable parts",
                    "Create feedback loops",
                ],
            },
            {
                "heading": "Conclusion",
                "bullets": [
                    "Summary",
                    "Next steps",
                    "Resources",
                ],
            },
        ],
    }
