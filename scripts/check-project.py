"""Offline structural checks; not an Unreal build or in-engine test."""
import json
from pathlib import Path

root = Path(__file__).resolve().parent.parent
project = json.loads((root / 'AfterSignal.uproject').read_text())
assert project['EngineAssociation'] == '5.4'
assert project['Modules'][0]['Name'] == 'AfterSignal'
assert any(p['Name'] == 'PythonScriptPlugin' for p in project['Plugins'])

maps = ['ForestGround', 'RoadAsphalt', 'Concrete']
world = (root / 'Source/AfterSignal/SignalGameMode.cpp').read_text()
importer = (root / 'scripts/import_materials.py').read_text()
for name in maps:
    assert (root / f'Content/SourceTextures/{name}.jpg').is_file(), name
    assert (root / f'Content/SourceTextures/{name}.jpg').stat().st_size > 1000, name
    assert f'/Game/Materials/M_{name}.M_{name}' in world, name
    assert f"'{name}', 'M_{name}'" in importer, name
for name in ['SignalGameMode', 'SignalCharacter', 'SignalEnemy', 'SignalHUD',
             'SignalInteractable', 'SignalSaveGame']:
    for suffix in ('.h', '.cpp'):
        path = root / f'Source/AfterSignal/{name}{suffix}'
        assert path.exists(), path
        if suffix == '.cpp':
            text = path.read_text()
            assert text.count('{') == text.count('}'), path
print('Structural checks passed. Unreal compilation and Android packaging NOT tested.')
