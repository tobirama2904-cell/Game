#pragma once
#include "CoreMinimal.h"
#include "GameFramework/SaveGame.h"
#include "SignalSaveGame.generated.h"

UCLASS()
class AFTERSIGNAL_API USignalSaveGame : public USaveGame
{
    GENERATED_BODY()
public:
    UPROPERTY() int32 ChapterStep = 0;
    UPROPERTY() bool bMedicineCollected = false;
    UPROPERTY() bool bSignalSent = false;
    UPROPERTY() int32 BroadcastChoice = 0;
    UPROPERTY() float Health = 100.f;
    UPROPERTY() int32 Ammo = 6;
    UPROPERTY() int32 ReserveAmmo = 18;
    UPROPERTY() int32 Bandages = 2;
    UPROPERTY() int32 Supplies = 0;
    UPROPERTY() bool bBleeding = false;
    UPROPERTY() bool bLegInjured = false;
    UPROPERTY() int32 Stones = 3;
    UPROPERTY() FVector Position = FVector(0.f, 2600.f, 140.f);
    UPROPERTY() TArray<int32> CollectedPickups;
};
