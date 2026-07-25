# /// script
# requires-python = ">=3.10"
# dependencies = ["apify-client", "python-dotenv"]
# ///
"""Discover local date venues and events via Apify.

Three sources:
  - google : Google Maps businesses (restaurants, venues, activities)
  - events : Facebook events (festivals, classes, pop-ups)
  - insta  : Instagram hashtag posts (local scene, trending spots)

Usage:
    python3 discover_local.py google "cat cafe" --location "Indianapolis, IN" --max 5
    python3 discover_local.py events "pottery class Indianapolis"
    python3 discover_local.py insta "indianapolisfoodie" --max 10
    python3 discover_local.py google "cat cafe" --location "Indianapolis, IN" --dry-run

Requires APIFY_TOKEN in .env or environment.
Exit codes: 0 = success, 1 = partial failure, 2 = config error (no token, bad input).
"""

import sys
import os
import json
import argparse

from dotenv import load_dotenv

try:
    from apify_client import ApifyClient
except ImportError:
    sys.stderr.write(
        "apify-client not installed.\n"
        "  With uv:  uv run discover_local.py  (auto-installs)\n"
        "  With pip: pip install apify-client\n"
    )
    sys.exit(2)

# Load .env from script's parent directory (the skill root)
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".env"))

# --- Actor configs ---
# Schema sources verified 2025-07:
#   compass/crawler-google-places  → apify.com/compass/crawler-google-places/input-schema
#   apify/facebook-events-scraper  → apify.com/apify/facebook-events-scraper/input-schema
#   instagram-scraper/instagram-hashtags-scraper → apify.com/instagram-scraper/instagram-hashtags-scraper/input-schema

ACTORS = {
    "google": {
        "id": "compass/crawler-google-places",
        # searchStrings, location, maxCrawledPlacesPerSearch, language
        "build_input": lambda query, location, max_items: {
            "searchStringsArray": [f"{query} {location}" if location else query],
            "location": location or "Indianapolis, IN, USA",
            "maxCrawledPlacesPerSearch": max_items,
            "language": "en",
        },
    },
    "events": {
        "id": "apify/facebook-events-scraper",
        # searchQueries array, maxEvents
        "build_input": lambda query, location, max_items: {
            "searchQueries": [f"{query} {location}" if location else query],
            "maxEvents": max_items,
        },
    },
    "insta": {
        "id": "instagram-scraper/instagram-hashtags-scraper",
        # hashtags array, resultsLimit per hashtag
        "build_input": lambda query, location, max_items: {
            "hashtags": [query.lstrip("#")],
            "resultsLimit": max_items,
        },
    },
}


def run_actor(client, source, query, location, max_items, dry_run=False):
    """Run one Apify actor. Returns result dict."""
    config = ACTORS[source]
    run_input = config["build_input"](query, location, max_items)

    if dry_run:
        return {
            "source": source,
            "query": query,
            "actor_id": config["id"],
            "input": run_input,
            "dry_run": True,
        }

    try:
        actor = client.actor(config["id"])
        run = actor.call(run_input=run_input, max_items=max_items)

        if run is None:
            return {"source": source, "query": query, "error": "Actor returned no run"}

        dataset_id = run.default_dataset_id
        items = list(client.dataset(dataset_id).iterate_items())

        return {
            "source": source,
            "query": query,
            "actor_id": config["id"],
            "item_count": len(items),
            "items": items,
            "status": "ok",
        }

    except Exception as e:
        return {"source": source, "query": query, "error": str(e)}


def main():
    parser = argparse.ArgumentParser(
        description="Discover local date venues and events via Apify."
    )
    parser.add_argument(
        "source",
        choices=["google", "events", "insta"],
        help="google=Google Maps venues, events=FB events, insta=IG hashtag",
    )
    parser.add_argument("query", help='Search term (e.g. "cat cafe", "pottery class")')
    parser.add_argument(
        "--location", "-l", default=None, help="Location (default: Indianapolis, IN)"
    )
    parser.add_argument(
        "--max", "-m", type=int, default=5, help="Max results (default: 5)"
    )
    parser.add_argument(
        "--output", "-o", default=None, help="Output file (default: stdout)"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Show actor input without calling Apify"
    )
    args = parser.parse_args()

    if args.dry_run:
        result = run_actor(None, args.source, args.query, args.location, args.max,
                           dry_run=True)
        print(json.dumps(result, indent=2))
        return

    token = os.environ.get("APIFY_TOKEN")
    if not token:
        sys.stderr.write(
            "APIFY_TOKEN not set. Get one at "
            "https://console.apify.com/account/integrations\n"
        )
        sys.exit(2)

    client = ApifyClient(token)
    sys.stderr.write(f"Searching {args.source} for '{args.query}'...\n")
    result = run_actor(client, args.source, args.query, args.location, args.max)

    output = json.dumps(result, indent=2, default=str)
    if args.output:
        with open(args.output, "w") as f:
            f.write(output)
        sys.stderr.write(f"\nResults written to {args.output}\n")
    else:
        print(output)

    sys.exit(1 if "error" in result else 0)


if __name__ == "__main__":
    main()
