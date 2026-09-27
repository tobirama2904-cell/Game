#pragma once
#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "SignalInteractable.generated.h"

class UStaticMeshComponent;
class USphereComponent;
class ASignalCharacter;

UENUM(BlueprintType)
enum class ESignalPickup : uint8 { Ammo, Bandage, Supplies, Note, Medicine, Tower };

UCLASS()
class AFTERSIGNAL_API ASignalInteractable : public AActor
{
    GENERATED_BODY()
public:
    ASignalInteractable();
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Survival") ESignalPickup Kind = ESignalPickup::Supplies;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly) TObjectPtr<USphereComponent> Trigger;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly) TObjectPtr<UStaticMeshComponent> Mesh;
    UFUNCTION(BlueprintCallable, Category="Survival") void Use(ASignalCharacter* Player);
};
