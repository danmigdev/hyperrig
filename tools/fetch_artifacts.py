"""Fetch exactly the published inputs pinned in research/input-manifest.json."""

import json
from pathlib import Path
import urllib.request
import zipfile

from bootstrap import download_checked

ROOT = Path(__file__).resolve().parents[1]


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "HyperRig-research"})
    with urllib.request.urlopen(req, timeout=90) as response:
        return response.read()


def main():
    locked = json.loads((ROOT / "research/input-manifest.json").read_text(encoding="utf-8"))
    dest = ROOT / "artifacts" / "alpha11"
    dest.mkdir(parents=True, exist_ok=True)
    release_path = dest / "release.json"
    release = json.loads(release_path.read_text(encoding="utf-8") if release_path.exists()
                         else fetch(locked["release"]["api_url"]))
    actual = {a["name"]: a for a in release["assets"]}
    if release["tag_name"] != locked["release"]["tag"]:
        raise ValueError("release tag differs from pinned reference")
    for asset in locked["release"]["assets"]:
        name = asset["name"]
        if actual[name]["digest"] != "sha256:" + asset["sha256"]:
            raise ValueError(f"{name}: release metadata differs from pinned SHA-256")
        p = dest / name
        download_checked(asset["url"], p, asset["sha256"])
        if p.stat().st_size != asset["size"]:
            raise ValueError(f"{name}: size differs from pinned reference")
        if name.endswith(".zip"):
            directory = dest / ("v1" if "-v1-" in name else "v2")
            with zipfile.ZipFile(p) as archive:
                for item in archive.namelist():
                    if not (directory / item).resolve().is_relative_to(directory.resolve()):
                        raise ValueError("archive path traversal")
                archive.extractall(directory)
        print(f"Verified {name}")
    release_path.write_text(json.dumps(release, indent=2) + "\n", encoding="utf-8")
    mini = ROOT / "artifacts" / "tank-mini"
    mini.mkdir(parents=True, exist_ok=True)
    item = locked["tank_mini"]
    download_checked(item["url"], mini / item["name"], item["sha256"])
    (mini / "firmware-provenance.json").write_text(json.dumps(item, indent=2) + "\n", encoding="utf-8")
    print("Verified TANK MINI_009 FWSC")


if __name__ == "__main__":
    main()
