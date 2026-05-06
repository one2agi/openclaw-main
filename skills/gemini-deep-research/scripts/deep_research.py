#!/usr/bin/env python3
"""
Gemini Deep Research API client
Performs complex, long-running research tasks via Gemini's Deep Research Agent
"""
import argparse, json, os, sys, time
from datetime import datetime
from pathlib import Path
import requests

API_BASE = "https://generativelanguage.googleapis.com/v1beta"
AGENT_MODEL = "deep-research-pro-preview-12-2025"
PROXIES = {"http": "http://172.20.112.1:6984", "https": "http://172.20.112.1:6984"}


def create_interaction(api_key, query, output_format=None, file_search_store=None):
    headers = {"Content-Type": "application/json", "x-goog-api-key": api_key}
    payload = {"input": query, "agent": AGENT_MODEL, "background": True}
    if output_format:
        payload["input"] = f"{query}\n\nFormat the output as follows:\n{output_format}"
    if file_search_store:
        payload["tools"] = [{"type": "file_search", "file_search_store_names": [file_search_store]}]
    response = requests.post(url=f"{API_BASE}/interactions", headers=headers, json=payload, proxies=PROXIES, timeout=30)
    if response.status_code != 200:
        print(f"Error creating interaction: {response.status_code}: {response.text}", file=sys.stderr)
        sys.exit(1)
    return response.json()


def poll_interaction(api_key, interaction_id, stream=False):
    headers = {"x-goog-api-key": api_key}
    while True:
        response = requests.get(url=f"{API_BASE}/interactions/{interaction_id}", headers=headers, proxies=PROXIES, timeout=30)
        if response.status_code != 200:
            print(f"Error polling: {response.status_code}", file=sys.stderr)
            sys.exit(1)
        data = response.json()
        status = data.get("status", "UNKNOWN")
        if stream and "statusMessage" in data:
            print(f"[{status}] {data['statusMessage']}", file=sys.stderr)
        if status == "completed":
            return data
        elif status == "failed":
            print(f"Research failed: {data.get('error', 'Unknown')}", file=sys.stderr)
            sys.exit(1)
        time.sleep(10)


def extract_report(data):
    if "output" in data:
        out = data["output"]
        if isinstance(out, dict): return out.get("text", "")
        if isinstance(out, str): return out
    for msg in reversed(data.get("messages", [])):
        if msg.get("role") == "model" and "parts" in msg:
            for part in msg["parts"]:
                if "text" in part: return part["text"]
    return None


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--query", required=True)
    p.add_argument("--format")
    p.add_argument("--file-search-store")
    p.add_argument("--stream", action="store_true")
    p.add_argument("--output-dir", default=".")
    p.add_argument("--api-key")
    args = p.parse_args()
    api_key = args.api_key or os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("Error: set GEMINI_API_KEY env var", file=sys.stderr); sys.exit(1)
    print(f"Starting deep research: {args.query}", file=sys.stderr)
    interaction = create_interaction(api_key, args.query, args.format, args.file_search_store)
    interaction_id = interaction.get("id")
    if not interaction_id:
        print(f"No interaction ID: {interaction}", file=sys.stderr); sys.exit(1)
    print(f"Interaction: {interaction_id}", file=sys.stderr)
    print("Polling for results...", file=sys.stderr)
    result = poll_interaction(api_key, interaction_id, args.stream)
    report = extract_report(result)
    if not report:
        print("Warning: no report extracted", file=sys.stderr)
        report = json.dumps(result, indent=2)
    ts = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    out_dir = Path(args.output_dir); out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / f"deep-research-{ts}.md").write_text(report)
    (out_dir / f"deep-research-{ts}.json").write_text(json.dumps(result, indent=2))
    print(f"\nResearch complete!\nReport: {out_dir}/deep-research-{ts}.md", file=sys.stderr)
    print(report)

if __name__ == "__main__":
    main()
