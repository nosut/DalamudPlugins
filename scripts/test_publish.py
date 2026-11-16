import unittest

from pathlib import Path

from publish import repo_entry, merge_entry, project_version, package_paths

MANIFEST = {
    "Author": "nosut", "Name": "FlagShare", "InternalName": "FlagShare",
    "AssemblyVersion": "0.1.1.0", "Description": "d", "Punchline": "p",
    "ApplicableVersion": "any", "RepoUrl": "https://github.com/nosut/DalamudPlugins",
    "CategoryTags": ["utility"], "DalamudApiLevel": 15, "LoadPriority": 0,
}


class PublishTests(unittest.TestCase):
    def test_entry_links_to_versioned_release_zip(self):
        e = repo_entry(MANIFEST, "nosut/DalamudPlugins", now=1700000000)
        url = "https://github.com/nosut/DalamudPlugins/releases/download/FlagShare-0.1.1.0/FlagShare.zip"
        self.assertEqual(e["DownloadLinkInstall"], url)
        self.assertEqual(e["DownloadLinkUpdate"], url)
        self.assertEqual(e["DownloadLinkTesting"], url)
        self.assertEqual(e["LastUpdate"], 1700000000)
        self.assertEqual(e["AssemblyVersion"], "0.1.1.0")
        self.assertEqual(e["DalamudApiLevel"], 15)

    def test_entry_repo_url_points_at_public_repo(self):
        private = dict(MANIFEST, RepoUrl="https://github.com/nosut/AchievementBrowser")
        e = repo_entry(private, "nosut/DalamudPlugins", now=0)
        self.assertEqual(e["RepoUrl"], "https://github.com/nosut/DalamudPlugins")

    def test_package_paths_follow_project_folder(self):
        out, manifest, package = package_paths(Path("C:/src/Foo/Foo/Foo.csproj"))
        self.assertEqual(out, Path("C:/src/Foo/Foo/bin/x64/Release"))
        self.assertEqual(manifest, out / "Foo.json")
        self.assertEqual(package, out / "Foo" / "latest.zip")

    def test_merge_replaces_same_plugin_and_keeps_others(self):
        other = {"InternalName": "Other", "AssemblyVersion": "1.0.0.0"}
        old = {"InternalName": "FlagShare", "AssemblyVersion": "0.1.0.0"}
        new = {"InternalName": "FlagShare", "AssemblyVersion": "0.1.1.0"}
        merged = merge_entry([other, old], new)
        self.assertEqual(merged, [new, other])

    def test_merge_appends_new_plugin_sorted(self):
        merged = merge_entry([{"InternalName": "Zeta"}], {"InternalName": "Alpha"})
        self.assertEqual([e["InternalName"] for e in merged], ["Alpha", "Zeta"])

    def test_project_version_reads_csproj(self):
        text = "<Project><PropertyGroup><Version>0.1.1.0</Version></PropertyGroup></Project>"
        self.assertEqual(project_version(text), "0.1.1.0")

    def test_project_version_missing_returns_none(self):
        self.assertIsNone(project_version("<Project></Project>"))


if __name__ == "__main__":
    unittest.main()
