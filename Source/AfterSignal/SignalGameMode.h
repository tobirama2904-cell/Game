#pragma once
#include "CoreMinimal.h"
#include "GameFramework/GameModeBase.h"
#include "SignalGameMode.generated.h"

class UStaticMesh;
class UMaterialInterface;

UCLASS()
class AFTERSIGNAL_API ASignalGameMode : public AGameModeBase
{
    GENERATED_BODY()
public:
    ASignalGameMode();
    virtual void BeginPlay() override;
private:
    UPROPERTY() TObjectPtr<UStaticMesh> CubeMesh;
    UPROPERTY() TObjectPtr<UStaticMesh> ConeMesh;
    UPROPERTY() TObjectPtr<UStaticMesh> CylinderMesh;
    UPROPERTY() TObjectPtr<UMaterialInterface> ForestMaterial;
    UPROPERTY() TObjectPtr<UMaterialInterface> RoadMaterial;
    UPROPERTY() TObjectPtr<UMaterialInterface> ConcreteMaterial;
    void Block(FVector Location, FVector Size, UStaticMesh* Mesh, bool bCollision = true, UMaterialInterface* Material = nullptr);
    void BuildWorld();
};
