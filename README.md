# nosut's Dalamud plugins

A custom plugin repository for [Dalamud](https://github.com/goatcorp/Dalamud),
the FFXIV plugin framework used by XIVLauncher.

## Add the repository

1. In game, type `/xlsettings` and open the **Experimental** tab.
2. Under **Custom Plugin Repositories**, paste this URL, click **+**, then
   **Save and Close**:

   ```
   https://raw.githubusercontent.com/nosut/DalamudPlugins/main/repo.json
   ```

3. Type `/xlplugins`, search for the plugin, and click **Install**. Updates
   arrive through Dalamud like any other plugin.

## Plugins

| Plugin | What it does |
| --- | --- |
| Achievement Browser | Every achievement in the game's own category tree, with search and filters that work across all categories, reward and earned-status filters, and pinned achievements with progress in a small tracker window. Open it with `/ach`. |
| FlagShare | Shows your party's map flags as named pins on the map and minimap, and in a `/flags` window, so nobody has to paste `<flag>` in chat. Everyone in the party needs FlagShare, and you all enter the same relay host in its settings. Same-world parties only. |

## Publishing (maintainer)

Bump `<Version>` in the plugin's `.csproj`, then from a clone of this repo:

```
python scripts/publish.py --project <path to the plugin's .csproj>
```

It builds Release x64, uploads the zip as release `<InternalName>-<version>`,
and updates and pushes `repo.json`. Tests: `cd scripts && python -m unittest`.

This repository holds only release builds and the plugin list. Plugins here
are personal projects, offered as is.
