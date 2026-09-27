#pragma once
#include "CoreMinimal.h"
#include "GameFramework/Character.h"
#include "SignalEnemy.generated.h"

class ASignalCharacter;
class UStaticMeshComponent;

UCLASS()
class AFTERSIGNAL_API ASignalEnemy : public ACharacter
{
    GENERATED_BODY()
public:
    ASignalEnemy();
    virtual void BeginPlay() override;
    virtual void Tick(float DeltaTime) override;
    UFUNCTION(BlueprintCallable, Category="Enemy") void ReceiveShot(float Damage);
    static void BroadcastNoise(UWorld* World, const FVector& Position, float Radius);
    void HearNoise(const FVector& Position);
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Enemy") bool bRunner = false;
    UPROPERTY(VisibleAnywhere) TObjectPtr<UStaticMeshComponent> PlaceholderBody;
    UPROPERTY(VisibleAnywhere) TObjectPtr<UStaticMeshComponent> PlaceholderHead;
    UPROPERTY(BlueprintReadOnly, Category="Enemy") float Health = 90.f;
    UPROPERTY(BlueprintReadOnly, Category="Enemy") bool bAlerted = false;
private:
    FVector Home;
    FVector Interest;
    float Memory = 0.f;
    float AttackCooldown = 0.f;
    float WanderPhase = 0.f;
};
