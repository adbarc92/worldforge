"""Bulk upload documents to a WorldForge project."""

import argparse
import sys
import time
from pathlib import Path

import httpx

SUPPORTED_EXTENSIONS = {".md", ".txt", ".pdf"}
DEFAULT_BASE_URL = "http://localhost:8080/api/v1"


def collect_files(directory: Path) -> list[Path]:
    """Collect all uploadable files, sorted by path."""
    files = [
        f
        for f in sorted(directory.rglob("*"))
        if f.is_file() and f.suffix.lower() in SUPPORTED_EXTENSIONS
    ]
    return files


def create_project(client: httpx.Client, name: str, description: str | None) -> str:
    body = {"name": name}
    if description:
        body["description"] = description
    resp = client.post("/projects", json=body)
    resp.raise_for_status()
    project = resp.json()
    print(f"Created project: {project['name']} (id: {project['id']})")
    return project["id"]


def upload_file(client: httpx.Client, project_id: str, file_path: Path) -> dict:
    mime = "text/markdown" if file_path.suffix == ".md" else "text/plain"
    with open(file_path, "rb") as f:
        resp = client.post(
            f"/projects/{project_id}/documents/upload",
            files={"file": (file_path.name, f, mime)},
            timeout=120.0,
        )
    resp.raise_for_status()
    return resp.json()


def main():
    parser = argparse.ArgumentParser(description="Bulk upload documents to WorldForge")
    parser.add_argument("directory", type=Path, help="Directory containing documents")
    parser.add_argument("--project-name", required=True, help="Name for the project")
    parser.add_argument("--project-description", default=None, help="Project description")
    parser.add_argument("--project-id", default=None, help="Use existing project ID instead of creating one")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL, help=f"API base URL (default: {DEFAULT_BASE_URL})")
    parser.add_argument("--limit", type=int, default=0, help="Upload only first N files (0 = all)")
    parser.add_argument("--dry-run", action="store_true", help="List files without uploading")
    parser.add_argument("--delay", type=float, default=0.5, help="Delay between uploads in seconds (default: 0.5)")
    args = parser.parse_args()

    if not args.directory.is_dir():
        print(f"Error: {args.directory} is not a directory")
        sys.exit(1)

    files = collect_files(args.directory)
    if args.limit > 0:
        files = files[: args.limit]

    print(f"Found {len(files)} uploadable files")

    if args.dry_run:
        for f in files:
            print(f"  {f.relative_to(args.directory)}")
        return

    if not files:
        print("Nothing to upload.")
        return

    client = httpx.Client(base_url=args.base_url, timeout=30.0)

    # Verify API is reachable
    try:
        health_url = args.base_url.rsplit("/api", 1)[0] + "/health"
        resp = httpx.get(health_url, timeout=5.0)
        resp.raise_for_status()
        print(f"API is reachable at {args.base_url}")
    except (httpx.HTTPError, httpx.ConnectError):
        print(f"Error: Cannot reach API at {args.base_url}")
        print("Is Docker running? Start with: docker compose up -d --build")
        sys.exit(1)

    # Create or use existing project
    if args.project_id:
        project_id = args.project_id
        print(f"Using existing project: {project_id}")
    else:
        project_id = create_project(client, args.project_name, args.project_description)

    # Upload files
    succeeded = 0
    failed = 0
    start_time = time.time()

    for i, file_path in enumerate(files, 1):
        rel = file_path.relative_to(args.directory)
        print(f"[{i}/{len(files)}] Uploading {rel}...", end=" ", flush=True)
        try:
            result = upload_file(client, project_id, file_path)
            print(f"OK ({result['chunk_count']} chunks)")
            succeeded += 1
        except httpx.HTTPStatusError as e:
            print(f"FAILED ({e.response.status_code}: {e.response.text})")
            failed += 1
        except httpx.HTTPError as e:
            print(f"FAILED ({e})")
            failed += 1

        if i < len(files) and args.delay > 0:
            time.sleep(args.delay)

    elapsed = time.time() - start_time
    print(f"\nDone in {elapsed:.1f}s — {succeeded} succeeded, {failed} failed")
    print(f"Project ID: {project_id}")


if __name__ == "__main__":
    main()
