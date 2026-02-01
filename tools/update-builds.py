#!/usr/bin/env python3

import json
import os
import requests
import re
from pathlib import Path
from typing import Dict


def request_github_api(url: str) -> list[dict]:
    """
    Request the GitHub API and return the JSON response.
    """
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    token = os.getenv("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()


def extract_versions(release: dict) -> Dict[str, str] | None:
    """
    Extract the version from the release data
    """
    versions: Dict[str, str] = {}
    patterns = {
        "swift": r'^\| `apple/swift` \| https://github.com/apple/swift/releases/tag/(.+) \|$',
        "swiftwasm-build": r'^\| `swiftwasm/swiftwasm-build` \| https://github.com/swiftwasm/swiftwasm-build/commit/(.+) \|$'
    }
    release_notes = release['body']
    lines = release_notes.splitlines()
    for line in lines:
        for key, pattern in patterns.items():
            match = re.match(pattern, line)
            if match:
                versions[key] = match.group(1)
                break
    for key in patterns.keys():
        if key not in versions:
            return None

    return versions


def identify_target(asset_name: str, release: dict) -> str:
    """
    Identify the target platform from asset name

    e.g.
    * swift-wasm-6.1-SNAPSHOT-2025-02-21-a-wasm32-unknown-wasi.artifactbundle.zip -> wasm32-unknown-wasi
    * swift-wasm-6.1-SNAPSHOT-2025-02-21-a-wasm32-unknown-wasip1-threads.artifactbundle.zip -> wasm32-unknown-wasip1-threads
    """
    release_tag = release['tag_name']
    asset_name = asset_name.removeprefix(release_tag + '-')
    asset_name = asset_name.removesuffix('.artifactbundle.zip')
    return asset_name


def process_release(release: dict, versions: dict) -> dict:
    """
    Process release assets and return structured build data
    """
    build_info = {
        "$schema": "../build.schema.json",
        "metadata": {
            "versions": versions
        },
        "swift-sdks": {}
    }

    for asset in release['assets']:
        if not asset['name'].endswith('.artifactbundle.zip'):
            continue
        target = identify_target(asset['name'], release)
        artifact_id = asset['name'].removesuffix(
            '.artifactbundle.zip').removeprefix("swift-wasm-")

        # Calculate checksum
        sha256_url = asset['browser_download_url'] + '.sha256'
        sha256_response = requests.get(sha256_url)
        if sha256_response.status_code == 404:
            checksum = None
        else:
            checksum = sha256_response.text.strip()

        # Add SDK data
        sdk_info = {
            "id": artifact_id,
            "url": asset['browser_download_url'],
        }
        if checksum:
            sdk_info['checksum'] = checksum
        build_info['swift-sdks'][target] = sdk_info

    return build_info


def update_builds_directory(releases: list[dict]):
    """
    Update the v1/builds/ directory with the latest data
    """
    builds_dir = Path('v1/builds')
    builds_dir.mkdir(parents=True, exist_ok=True)

    for release in releases:
        versions = extract_versions(release)
        if not versions:
            print(f"Warning: Skipping release {release['tag_name']} due to missing version info")
            continue
        path = builds_dir / f"{versions['swift']}.json"
        if path.exists():
            continue
        build_data = process_release(release, versions)

        # Skip releases with empty SDK sections
        if not build_data['swift-sdks']:
            print(f"Skipping {path} because it has no SDKs")
            continue

        # Write individual release files
        print(f"Writing {path}")
        with open(path, 'w') as f:
            json.dump(build_data, f, indent=4)


def main():
    """
    Get the list of releases from the swiftwasm/swift GitHub repo
    and update the v1/builds/ directory with the latest data.

    TODO: The build file should be updated as a part of the release process
    instead of fetching release data from GitHub.
    """

    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--pages", type=int, default=1,
                        help="The number of pages to retrieve")
    args = parser.parse_args()

    for page in range(args.pages):
        releases = request_github_api(
            f"https://api.github.com/repos/swiftwasm/swift/releases?page={page}")
        print(f"Number of releases retrieved: {len(releases)}")
        update_builds_directory(releases)
        print("v1/builds/ directory update completed")


if __name__ == "__main__":
    main()
