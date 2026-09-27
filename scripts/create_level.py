"""Run in UnrealEditor 5.4 after import_materials.py, never in system Python.

Creates a real project-owned map for cooking. GameMode constructs the playable
prototype in BeginPlay; this empty map is intentional, not a painted level.
"""
import unreal

level = '/Game/Maps/RelayRoad'
if not unreal.EditorAssetLibrary.does_asset_exist(level):
    if not unreal.EditorLevelLibrary.new_level(level):
        raise RuntimeError('Could not create ' + level)
    unreal.log('Created ' + level)
else:
    unreal.log('Already exists: ' + level)
if not unreal.EditorAssetLibrary.does_asset_exist(level):
    raise RuntimeError('Level was not saved: ' + level)
