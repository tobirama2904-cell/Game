#pragma once
#include "CoreMinimal.h"
#include "GameFramework/Character.h"
#include "SignalCompanion.generated.h"

class ASignalCharacter;
class UStaticMeshComponent;

/** Ethan follows Mara without producing enemy noise. This is a placeholder actor,
 * not a finished skeletal character or navigation-based companion. */
UCLASS()
class AFTERSIGNAL_API ASignalCompanion : public ACharacter
{
    GENERATED_BODY()
public:
    ASignalCompanion();
    virtual void BeginPlay() override;
    virtual void Tick(float DeltaTime) override;
    void SetLeader(ASignalCharacter* NewLeader);
    void ToggleWait();
    UFUNCTION(BlueprintPure, Category="Companion") bool IsWaiting() const { return bWaiting; }
    UFUNCTION(BlueprintPure, Category="Companion") bool IsAlive() const { return Health > 0.f; }
    UFUNCTION(BlueprintCallable, Category="Companion") void ReceiveDamage(float Amount);
    UPROPERTY(BlueprintReadOnly, Category="Companion") float Health = 100.f;
private:
    UPROPERTY() TObjectPtr<ASignalCharacter> Leader;
    UPROPERTY(VisibleAnywhere) TObjectPtr<UStaticMeshComponent> Body;
    UPROPERTY(VisibleAnywhere) TObjectPtr<UStaticMeshComponent> Head;
    bool bWaiting = false;
};
