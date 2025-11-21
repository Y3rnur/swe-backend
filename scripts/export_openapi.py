"""Export OpenAPI schema to file.

This script fetches the OpenAPI schema from the running API
and saves it to a file for documentation purposes.
"""

import json
import sys
from pathlib import Path

import httpx


def export_openapi(
    base_url: str = "http://localhost:8000", output_file: str = "openapi.json"
) -> None:
    """Export OpenAPI schema from API."""
    openapi_url = f"{base_url}/openapi.json"
    output_path = Path(output_file)

    print(f"📥 Fetching OpenAPI schema from {openapi_url}...")

    try:
        response = httpx.get(openapi_url, timeout=10.0)
        response.raise_for_status()

        schema = response.json()

        # Write to file
        output_path.write_text(json.dumps(schema, indent=2), encoding="utf-8")

        print(f"✅ OpenAPI schema exported to {output_path}")
        print(f"   File size: {output_path.stat().st_size:,} bytes")
        print(f"   Endpoints: {len(schema.get('paths', {}))}")

    except httpx.RequestError as e:
        print(f"❌ Error connecting to API: {e}")
        print(f"   Make sure the API is running at {base_url}")
        sys.exit(1)
    except httpx.HTTPStatusError as e:
        print(f"❌ HTTP error: {e.response.status_code}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Export OpenAPI schema from API")
    parser.add_argument(
        "--url",
        default="http://localhost:8000",
        help="Base URL of the API (default: http://localhost:8000)",
    )
    parser.add_argument(
        "--output",
        default="docs/openapi.json",
        help="Output file path (default: docs/openapi.json)",
    )

    args = parser.parse_args()
    export_openapi(args.url, args.output)
