"""Attach a complete, verified artifact set to a draft prerelease only."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.build_release import bundle, read_lock, require, run, version


def publish(folder, release_version):
    release_version = version(release_version)
    repository = read_lock()["repository"]
    manifest = json.loads((folder / "release-manifest.json").read_bytes())
    commit = run(["git", "rev-parse", "HEAD"]).strip()
    require(manifest["source_commit"] == commit and manifest["version"] == release_version, "Release target differs")
    sums = (folder / "SHA256SUMS").read_text("ascii").splitlines()
    expected = {"SHA256SUMS"}
    for line in sums:
        digest, name = line.split("  ", 1)
        require(Path(name).name == name and name not in expected, "Invalid checksum inventory")
        require(bundle.sha((folder / name).read_bytes()) == digest, "Artifact checksum differs: " + name)
        expected.add(name)
    require({p.name for p in folder.iterdir()} == expected, "Unexpected release files")
    tag = "v" + release_version
    lookup = subprocess.run(["gh", "release", "view", tag, "--repo", repository,
                             "--json", "isDraft,targetCommitish"], capture_output=True, text=True)
    if lookup.returncode == 0:
        existing = json.loads(lookup.stdout)
        require(existing["isDraft"] and existing["targetCommitish"] == commit,
                "Refusing to replace a published release or a draft from another commit")
        run(["gh", "release", "edit", tag, "--repo", repository, "--draft", "--prerelease",
             "--notes-file", folder / "RELEASE_NOTES.md"])
    else:
        run(["gh", "release", "create", tag, "--repo", repository, "--draft", "--prerelease",
             "--target", commit, "--title", f"HyperRig MINI {release_version}",
             "--notes-file", folder / "RELEASE_NOTES.md"])
    run(["gh", "release", "upload", tag, "--repo", repository, "--clobber",
         *[folder / name for name in sorted(expected)]])
    print(f"Draft prerelease prepared: https://github.com/{repository}/releases")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifacts", type=Path, required=True)
    parser.add_argument("--version", type=version, required=True)
    args = parser.parse_args()
    publish(args.artifacts, args.version)
