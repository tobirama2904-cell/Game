# Unreal Engine 5 edition — actual status

This is a **new UE5 C++ project**, not a wrapper around the web build. It does not include third-party Marketplace/Fab packs. It is a small standalone code prototype; the earlier browser version remains in `src/` as historical work, but does not run inside UE5.

## Requirements

* Unreal Engine **5.4** editor with C++ toolchain and generated project files (Windows: Visual Studio 2022 with Game development with C++; Linux: compatible clang toolchain and UE5 installed).
* The engine is not included in this Git repository. This sandbox has no UnrealEditor, UnrealBuildTool or access to the private EpicGames/UnrealEngine repository; compilation and in-engine testing **have not been performed here**. The `AfterSignal.uproject` should be opened and built on a machine with UE 5.4; errors may need fixing against that installed UE version.
* For Android packaging: install the UE-recommended Android SDK/NDK/JDK **matching your UE installation**, configure Android Platform SDK in Unreal, supply your signing key, cook/package for Android ARM64, and **test on an actual POCO F4**. No APK is provided.

## What is authored in C++

* `ASignalGameMode` spawns the starting road, ruins, tower, forest, enemies, pickups and basic lighting using built-in primitive meshes. The default engine Entry map is used instead of a binary `.umap`.
* `ASignalCharacter` implements third-person camera, locomotion, sprint and stamina, crouch, hitscan pistol, reload, bandages, interaction and story state.
* `ASignalEnemy` implements distance/stance-based detection, response to gunshot noise, memory, investigation, chase, damage and death. Movement currently uses direct swept motion, not a navigation mesh or tactical pathfinding.
* `ASignalInteractable` implements a simple three-step sequence: find radio note, collect clinic medicine, use tower; extra ammunition/bandages. There is no dialogue/cutscene system in this UE version yet.

## Why the graphics aren't PS5-quality yet

The project currently uses **engine primitives as placeholders**. High-end visual quality requires original or appropriately licensed scanned terrain/structures, authored hero characters with skeletons and animations, material authoring, cinematic lighting, facial performances, level art, VFX, audio, UI, optimization and validation. None of those are magically supplied by changing engines. Desktop Lumen/Nanite settings in `DefaultEngine.ini` are a starting configuration, **not** a proof of achievable fidelity or mobile support. Android requires distinct reduced-quality profiles and profiling. Assets should be licensed and provenance documented before importing; don't import The Last of Us assets or copy its scenes/story.

## Next verifiable production gate

1. Build this UE5 C++ project in the editor, resolve any version-specific compile issues, and play the three-step episode.
2. Replace temporary capsule/mesh characters with properly licensed skeletal meshes and animation blueprints; import a cohesive vegetation/building kit and PBR materials.
3. Set up a distinct mobile scalability profile, landscape touch controls and HUD, and package ARM64 APK; measure FPS/memory/temperature on POCO F4.
4. Only publish an APK to GitHub Releases once it actually exists and is install-tested. Keep binary build outputs out of Git.

## Recent source additions (still not compiled in Unreal)

The UE5 branch now includes a `Canvas` HUD with objectives, health/stamina/ammunition and an interaction prompt; short **text-only** story lines; and a `USaveGame` slot for chapter, location, inventory and collected pickups (F5 manual save; item pickup auto-save). These are code-level features, not voice acting or cinematics. To capture real Unreal screenshots, launch this project in UE 5.4 and use the editor's viewport screenshot or `HighResShot 1920x1080` during play. Never label screenshots from the legacy web build as Unreal screenshots.

## Additional code and build entry point

Recent source work adds bleeding, leg injury, bandage treatment, stone distraction (`Q`), on-screen injury status, and saved injury/stone counts. A synopsis and sample scene beats are in [STORY.md](STORY.md), but most of those scenes are **not** in the game. On a Linux host with a licensed UE 5.4 installation and matching Android SDK/NDK/JDK, `UE_ROOT=/path/to/UnrealEngine ANDROID_HOME=/path/to/sdk JAVA_HOME=/path/to/jdk scripts/package-android.sh` invokes the real Unreal `BuildCookRun` and rejects an empty/missing APK. This command cannot run in the current sandbox because the prerequisites are absent. Desktop and Android builds must both be tested before publishing screenshots or APKs.

## Textures actually used by the UE world

The three locally authored maps in `Content/SourceTextures/` are **source JPEG files**, not Unreal `.uasset` files. In a UE 5.4 editor with Python Editor Script Plugin, run `UnrealEditor AfterSignal.uproject -unattended -ExecutePythonScript=scripts/import_materials.py`. The script imports textures, creates and saves `/Game/Materials/M_ForestGround`, `M_RoadAsphalt`, `M_Concrete`, and sets UV tiling. The C++ world loads those material assets at startup and applies them to terrain/road/ruins; if they have not been imported, the scene falls back to default UE materials. These files do not change placeholder characters into scanned or photorealistic assets. `python3 scripts/check-project.py` checks paths/JSON/source structure **offline only**; it does not compile UE.

## Companion milestone (source only)

`ASignalCompanion` now spawns Ethan near Mara, follows from behind/side, mirrors crouching, and supports `F` wait/follow. It avoids broadcasting noise, and teleports to a floor-tested position if separated too far; it does **not** have navigation around buildings, combat aid, spoken lines or a finished skeletal model. This code must be compiled and playtested in UE5 before being called functional on a device.

## Detection, companion aid and tower choice (source, not runtime verified)

Enemy sight now requires range, a forward view cone and a visibility line trace; noise from shots, stones and moving footsteps instead gives a timed last-known location. Ethan can spend **one** emergency bandage on a nearby bleeding Mara (no repeated free healing). At the relay, `E` sends an open distress call or `G` uses a private channel; the decision and its short ending text are saved. This is a **small choice at the end of one short episode**, not the promised branching AAA campaign. `python3 scripts/test-story-contracts.py` checks that input, save fields and stage gates are wired consistently, but cannot verify UE compilation, behavior, rendering or Android performance.
