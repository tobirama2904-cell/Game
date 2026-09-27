"""Static consistency tests only: not UE build, APK, playtest, or runtime AI test."""
from pathlib import Path
root = Path(__file__).resolve().parent.parent
src = root / 'Source/AfterSignal'
char_h = (src/'SignalCharacter.h').read_text()
char_cpp = (src/'SignalCharacter.cpp').read_text()
save_h = (src/'SignalSaveGame.h').read_text()
input_ini = (root/'Config/DefaultInput.ini').read_text()
interact = (src/'SignalInteractable.cpp').read_text()
enemy = (src/'SignalEnemy.cpp').read_text()
companion = (src/'SignalCompanion.cpp').read_text()
for name, key in [('Fire','LeftMouseButton'),('Interact','E'),('Distract','Q'),
                  ('PrivateSignal','G'),('CompanionWait','F')]:
    assert f'ActionName="{name}",Key={key}' in input_ini
    assert f'BindAction("{name}"' in char_cpp
for field in ('BroadcastChoice','Supplies','Stones','bBleeding','bLegInjured'):
    assert field in save_h and field in char_h
    assert f'Save->{field} = {field};' in char_cpp
    assert f'Save->{field}' in char_cpp.split('void ASignalCharacter::LoadProgress()')[1]
assert 'case ESignalPickup::Supplies: ++Player->Supplies;' in interact
assert 'case ESignalPickup::Medicine: return Player->ChapterStep == 1;' in interact
assert 'case ESignalPickup::Tower: return Player->ChapterStep == 2;' in interact
assert 'CompleteBroadcast(1)' in char_cpp and 'CompleteBroadcast(2)' in char_cpp
assert 'GetEndingText()' in char_cpp
assert 'CanSeePlayer' in enemy and 'ECC_Visibility' in enemy
assert 'GetActorForwardVector()' in enemy and 'BroadcastNoise' in enemy
assert 'EmergencyBandages > 0' in companion and 'bWaiting' in companion
print('Static gameplay contracts passed; no Unreal runtime assertions made.')
