"""
Demo seed script — inserts sample incidents through the five-agent workflow.
Run ONLY after the Flask backend is initialised.
Usage: python scripts/seed_demo.py [--url http://localhost:5000]
"""
import sys
import json
import argparse
import urllib.request
import urllib.error

def main():
    parser = argparse.ArgumentParser(description="Seed demo incidents")
    parser.add_argument("--url", default="http://localhost:5000", help="Backend URL")
    args = parser.parse_args()
    base = args.url.rstrip("/")

    with open("sample_data/incidents.json", encoding="utf-8") as f:
        incidents = json.load(f)

    for i, inc in enumerate(incidents, 1):
        print(f"[{i}/{len(incidents)}] Submitting: {inc['raw_report'][:60]}...")
        data = json.dumps(inc).encode()
        req = urllib.request.Request(
            f"{base}/api/incidents",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                body = json.loads(resp.read())
                print(f"  ✓ Created incident {body.get('incident_id', '?')} "
                      f"status={body.get('status')} "
                      f"severity={body.get('risk_assessment', {}).get('severity', '?')}")
        except urllib.error.HTTPError as e:
            print(f"  ✗ HTTP {e.code}: {e.read().decode()}")
        except Exception as e:
            print(f"  ✗ Error: {e}")

    print("\nDemo seeding complete.")

if __name__ == "__main__":
    main()
