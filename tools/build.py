"""Builds the registry site in docs/ from packages.json.

For each package version it downloads the vendor's tarball once (cached in .cache/), reads its package.json and
checksums, and writes the npm metadata Unity's Package Manager reads. The tarballs themselves are never hosted here:
each version's dist.tarball points at the vendor's own download.

Usage: python tools/build.py
"""
import base64
import hashlib
import json
import os
import sys
import tarfile
import urllib.request
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = os.path.join(ROOT, "docs")
CACHE = os.path.join(ROOT, ".cache")


def load_json(path, default=None):
    if not os.path.exists(path):
        return default
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def write_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")


def download(url, path):
    if os.path.exists(path):
        return
    os.makedirs(os.path.dirname(path), exist_ok=True)
    print(f"  downloading {url}")
    partial = path + ".partial"
    with urllib.request.urlopen(url) as response, open(partial, "wb") as out:
        while chunk := response.read(1 << 20):
            out.write(chunk)
    os.replace(partial, path)


def read_manifest(tarball):
    with tarfile.open(tarball, "r:gz") as archive:
        return json.load(archive.extractfile("package/package.json"))


def checksums(path):
    sha1, sha512 = hashlib.sha1(), hashlib.sha512()
    with open(path, "rb") as f:
        while chunk := f.read(1 << 20):
            sha1.update(chunk)
            sha512.update(chunk)
    return sha1.hexdigest(), "sha512-" + base64.b64encode(sha512.digest()).decode()


def version_key(version):
    return tuple(int(part) if part.isdigit() else part for part in version.replace("-", ".").split("."))


def main():
    config = load_json(os.path.join(ROOT, "packages.json"))
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")
    search = []

    for name, versions in config["packages"].items():
        print(name)
        # Keep each version's publish time from the last build, so rebuilding changes nothing.
        previous = load_json(os.path.join(SITE, name), {})
        times = previous.get("time", {})
        packument = {"_id": name, "name": name, "dist-tags": {}, "versions": {}, "time": {}}

        for version in sorted(versions, key=version_key):
            url = config["source"].format(name=name, version=version)
            tarball = os.path.join(CACHE, f"{name}-{version}.tgz")
            download(url, tarball)

            manifest = read_manifest(tarball)
            if manifest.get("name") != name or manifest.get("version") != version:
                sys.exit(f"{url} holds {manifest.get('name')}@{manifest.get('version')}, not {name}@{version}")

            shasum, integrity = checksums(tarball)
            manifest["_id"] = f"{name}@{version}"
            manifest["dist"] = {"tarball": url, "shasum": shasum, "integrity": integrity}
            packument["versions"][version] = manifest
            packument["time"][version] = times.get(version, now)

        latest = max(packument["versions"], key=version_key)
        info = packument["versions"][latest]
        packument["dist-tags"]["latest"] = latest
        for field in ("description", "displayName", "keywords", "author"):
            if field in info:
                packument[field] = info[field]
        packument["time"]["created"] = times.get("created", min(packument["time"].values()))
        packument["time"]["modified"] = max(v for k, v in packument["time"].items() if k != "created")

        write_json(os.path.join(SITE, name), packument)
        search.append({"package": {
            "name": name,
            "version": latest,
            "displayName": info.get("displayName", name),
            "description": info.get("description", ""),
            "keywords": info.get("keywords", []),
            "author": info.get("author", {}),
            "date": packument["time"][latest],
        }})

    write_json(os.path.join(SITE, "-", "v1", "search"), {"objects": search, "total": len(search), "time": now})
    write_json(os.path.join(SITE, "-", "all"), {"_updated": 0, **{o["package"]["name"]: o["package"] for o in search}})
    open(os.path.join(SITE, ".nojekyll"), "w").close()
    print(f"Wrote {len(search)} packages to {SITE}")


if __name__ == "__main__":
    main()
