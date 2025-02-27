#!/usr/bin/env python3
import subprocess
from pathlib import Path
import os
import itertools


def derive_version_fingerprint(swift_tag: str) -> list[str]:
    """
    Derive a fingerprint from the Swift version tag by 
    """

    if swift_tag.startswith("swift-") and swift_tag.endswith("-RELEASE"):
        # HACK: swiftly doesn't understand swift-x.y.z-RELEASE tags
        swift_tag = swift_tag.removeprefix("swift-").removesuffix("-RELEASE")

    install = subprocess.run(["swiftly", "install", swift_tag])
    install.check_returncode()

    toolchain_version = subprocess.run(["swiftly", "run", "swift", "--version", f"+{swift_tag}"], capture_output=True).stdout.decode("utf-8").strip()
    result = toolchain_version.split("\n")[0]
    subprocess.run(["swiftly", "uninstall", "-y", swift_tag]).check_returncode()
    # swift.org toolchain has two fingerprint variants for the same version
    return [result, f"Apple {result}"]

def main():
    """
    Update the tag-by-version.json file with the latest data from the
    v1/builds/ directory.
    """
    import json

    builds_dir = Path("v1/builds")
    tag_by_version_path = Path("v1/tag-by-version.json")
    tag_by_version = {}
    if tag_by_version_path.exists():
        with open(tag_by_version_path, "r") as f:
            tag_by_version = json.load(f)

    build_files = sorted(builds_dir.glob("*.json"))
    for i, path in enumerate(build_files):
        print(f"Processing {i+1}/{len(build_files)}: {path}")
        with open(path, "r") as f:
            build_info = json.load(f)
            swift_tag = build_info['metadata']['versions']['swift']
        
        if swift_tag not in set(itertools.chain(*tag_by_version.values())):
            fingerprint = derive_version_fingerprint(swift_tag)
            for f in fingerprint:
                if f not in tag_by_version:
                    tag_by_version[f] = [swift_tag]
                else:
                    tags = tag_by_version[f]
                    if swift_tag not in tags:
                        tags.append(swift_tag)
                    tag_by_version[f] = sorted(tags)
                print(f"Derived fingerprint for {swift_tag}: {f}")

            with open(tag_by_version_path, "w") as f:
                json.dump(tag_by_version, f, indent=2)


if __name__ == "__main__":
    main()
