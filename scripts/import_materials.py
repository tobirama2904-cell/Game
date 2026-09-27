"""Run inside UE 5.4 editor with PythonScriptPlugin (not system Python).

Example: UnrealEditor AfterSignal.uproject -unattended -ExecutePythonScript=scripts/import_materials.py
Imports this project's authored JPEG source maps into /Game/Textures and creates
three UE material assets used by the procedural world. Requires an actual editor.
"""
import os
import unreal

project_dir = unreal.Paths.project_dir()
root = os.path.join(project_dir, 'Content', 'SourceTextures')
textures = [('ForestGround', 'M_ForestGround', 0.92, 36.0, 40.0),
            ('RoadAsphalt', 'M_RoadAsphalt', 0.86, 1.0, 38.0),
            ('Concrete', 'M_Concrete', 0.91, 2.0, 2.0)]
asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
editor_assets = unreal.EditorAssetLibrary

for texture_name, material_name, roughness, u_tiles, v_tiles in textures:
    source = os.path.join(root, texture_name + '.jpg')
    if not os.path.isfile(source):
        raise FileNotFoundError(source)
    task = unreal.AssetImportTask()
    task.set_editor_property('filename', source)
    task.set_editor_property('destination_path', '/Game/Textures')
    task.set_editor_property('destination_name', 'T_' + texture_name)
    task.set_editor_property('automated', True)
    task.set_editor_property('replace_existing', True)
    task.set_editor_property('save', True)
    asset_tools.import_asset_tasks([task])
    texture = editor_assets.load_asset('/Game/Textures/T_' + texture_name)
    if not texture:
        raise RuntimeError('Failed to import ' + source)
    material_path = '/Game/Materials/' + material_name
    material = editor_assets.load_asset(material_path)
    if not material:
        material = asset_tools.create_asset(material_name, '/Game/Materials',
                                            unreal.Material, unreal.MaterialFactoryNew())
    if not material:
        raise RuntimeError('Failed to create ' + material_path)
    # Replace nodes instead of accumulating duplicate nodes on re-runs.
    unreal.MaterialEditingLibrary.delete_all_material_expressions(material)
    sample = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionTextureSample, -430, 0)
    sample.set_editor_property('texture', texture)
    uv = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionTextureCoordinate, -630, 0)
    uv.set_editor_property('u_tiling', u_tiles)
    uv.set_editor_property('v_tiling', v_tiles)
    unreal.MaterialEditingLibrary.connect_material_expressions(uv, '', sample, 'Coordinates')
    unreal.MaterialEditingLibrary.connect_material_property(
        sample, 'RGB', unreal.MaterialProperty.MP_BASE_COLOR)
    rough = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionConstant, -420, 220)
    rough.set_editor_property('r', roughness)
    unreal.MaterialEditingLibrary.connect_material_property(
        rough, '', unreal.MaterialProperty.MP_ROUGHNESS)
    unreal.MaterialEditingLibrary.recompile_material(material)
    if not editor_assets.save_loaded_asset(material):
        raise RuntimeError('Failed to save ' + material_path)
    unreal.log('AfterSignal imported ' + material_path)

unreal.log('AfterSignal: material import completed')
