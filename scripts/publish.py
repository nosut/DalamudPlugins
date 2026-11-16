"""Publish a Dalamud plugin to this custom repository (nosut/DalamudPlugins).

    python scripts/publish.py --project <path to the plugin's .csproj>

Builds the plugin (Release, x64), uploads its DalamudPackager zip as
<InternalName>.zip on a GitHub release named <InternalName>-<AssemblyVersion>,
then updates repo.json in this clone and pushes it. Only the zip and manifest
become public, never source. Refuses to run if the release already exists
(bump <Version> in the .csproj first) or if the build output is stale.
"""

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

DIST = Path(__file__).resolve().parent.parent
DIST_REPO = "nosut/DalamudPlugins"

# Manifest keys copied into the repo.json entry as-is.
MANIFEST_KEYS = [
    "Author", "Name", "InternalName", "AssemblyVersion", "Description", "Punchline",
    "ApplicableVersion", "Tags", "CategoryTags", "DalamudApiLevel",
    "LoadRequiredState", "LoadSync", "CanUnloadAsync", "LoadPriority", "AcceptsFeedback",
]


def repo_entry(manifest, dist_repo, now):
    """The repo.json entry for this manifest, pointing at its versioned release zip.

    RepoUrl always points at the public repo: plugin sources may be private.
    """
    entry = {k: manifest[k] for k in MANIFEST_KEYS if k in manifest}
    tag = f"{manifest['InternalName']}-{manifest['AssemblyVersion']}"
    url = f"https://github.com/{dist_repo}/releases/download/{tag}/{manifest['InternalName']}.zip"
    entry.update({
        "RepoUrl": f"https://github.com/{dist_repo}",
        "DownloadLinkInstall": url,
        "DownloadLinkUpdate": url,
        "DownloadLinkTesting": url,
        "LastUpdate": int(now),
        "IsHide": False,
        "IsTestingExclusive": False,
    })
    return entry


def merge_entry(entries, entry):
    """Replace the plugin's entry (by InternalName) or add it; sorted by InternalName."""
    kept = [e for e in entries if e.get("InternalName") != entry["InternalName"]]
    kept.append(entry)
    return sorted(kept, key=lambda e: e["InternalName"])


def project_version(csproj_text):
    """The <Version> from a .csproj, or None."""
    match = re.search(r"<Version>\s*([^<\s]+)\s*</Version>", csproj_text)
    return match.group(1) if match else None


def package_paths(csproj):
    """(output dir, manifest json, packaged zip) for a Dalamud.NET.Sdk project built Release x64."""
    name = csproj.stem
    out = csproj.parent / "bin" / "x64" / "Release"
    return out, out / f"{name}.json", out / name / "latest.zip"


def run(*args, cwd=None, capture=False):
    print("+", " ".join(str(a) for a in args))
    result = subprocess.run([str(a) for a in args], cwd=cwd, check=True, text=True,
                            capture_output=capture)
    return result.stdout if capture else None


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--project", required=True, type=Path, help="the plugin's .csproj")
    args = parser.parse_args()
    project = args.project.resolve()
    if project.suffix != ".csproj" or not project.exists():
        sys.exit(f"{project} is not a .csproj")

    if run("git", "status", "--porcelain", cwd=DIST, capture=True).strip():
        sys.exit(f"{DIST} has uncommitted changes; commit or stash them first")
    run("git", "pull", "--ff-only", cwd=DIST)

    run("dotnet", "build", project, "-c", "Release", "-p:Platform=x64", "-nologo", "-v", "q")
    out, manifest_path, package = package_paths(project)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    expected = project_version(project.read_text(encoding="utf-8"))
    if manifest["AssemblyVersion"] != expected:
        sys.exit(f"built manifest says {manifest['AssemblyVersion']} but {project.name} says {expected}; "
                 "the build output is stale, nothing was published")
    if not package.exists():
        sys.exit(f"missing {package}; did DalamudPackager run?")

    name = manifest["InternalName"]
    tag = f"{name}-{manifest['AssemblyVersion']}"
    existing = subprocess.run(["gh", "release", "view", tag, "--repo", DIST_REPO],
                              capture_output=True, text=True)
    if existing.returncode == 0:
        sys.exit(f"release {tag} already exists; bump <Version> in {project.name}")

    with tempfile.TemporaryDirectory() as tmp:
        asset = Path(tmp) / f"{name}.zip"
        shutil.copyfile(package, asset)
        run("gh", "release", "create", tag, asset, "--repo", DIST_REPO,
            "--title", f"{manifest['Name']} {manifest['AssemblyVersion']}",
            "--notes", f"{manifest['Name']} {manifest['AssemblyVersion']}. Install through the custom repository; see README.")

    repo_json = DIST / "repo.json"
    entries = json.loads(repo_json.read_text(encoding="utf-8")) if repo_json.exists() else []
    entries = merge_entry(entries, repo_entry(manifest, DIST_REPO, time.time()))
    repo_json.write_text(json.dumps(entries, indent=2) + "\n", encoding="utf-8", newline="\n")

    run("git", "add", "repo.json", cwd=DIST)
    run("git", "-c", "user.name=nosut", "-c", "user.email=nosut@users.noreply.github.com",
        "commit", "-m", f"Publish {manifest['Name']} {manifest['AssemblyVersion']}", cwd=DIST)
    run("git", "push", cwd=DIST)
    print(f"Published {tag}.")


if __name__ == "__main__":
    main()
