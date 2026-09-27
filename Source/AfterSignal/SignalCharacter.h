#pragma once
#include "CoreMinimal.h"
#include "GameFramework/Character.h"
#include "TimerManager.h"
#include "SignalCharacter.generated.h"

class USpringArmComponent;
class UCameraComponent;
class USkeletalMeshComponent;
class UStaticMeshComponent;

DECLARE_DYNAMIC_MULTICAST_DELEGATE(FOnSignalStoryChanged);

UCLASS()
class AFTERSIGNAL_API ASignalCharacter : public ACharacter
{
    GENERATED_BODY()
public:
    ASignalCharacter();
    virtual void BeginPlay() override;
    virtual void Tick(float DeltaTime) override;
    virtual void SetupPlayerInputComponent(UInputComponent* PlayerInputComponent) override;
    UFUNCTION(BlueprintCallable, Category="Survival") void TakeSurvivalDamage(float Amount);
    UFUNCTION(BlueprintCallable, Category="Survival") bool CollectMedicine();
    UPROPERTY(BlueprintReadOnly, Category="Survival") float Health = 100.f;
    UPROPERTY(BlueprintReadOnly, Category="Survival") float Stamina = 100.f;
    UPROPERTY(BlueprintReadOnly, Category="Survival") int32 Ammo = 6;
    UPROPERTY(BlueprintReadOnly, Category="Survival") int32 ReserveAmmo = 18;
    UPROPERTY(BlueprintReadOnly, Category="Survival") int32 Bandages = 2;
    UPROPERTY(BlueprintReadOnly, Category="Story") int32 ChapterStep = 0;
    UPROPERTY(BlueprintReadOnly, Category="Story") bool bMedicineCollected = false;
    UPROPERTY(BlueprintReadOnly, Category="Story") bool bSignalSent = false;
    UPROPERTY(BlueprintAssignable, Category="Story") FOnSignalStoryChanged OnStoryChanged;
    UFUNCTION(BlueprintPure, Category="Survival") bool IsCrouchedForStealth() const { return bStealthCrouch; }
    UFUNCTION(BlueprintPure, Category="Survival") bool IsAlive() const { return Health > 0.f; }
    UFUNCTION(BlueprintPure, Category="Survival") bool IsSprinting() const { return bSprinting; }
    UFUNCTION(BlueprintCallable, Category="Save") void SaveProgress();
    UFUNCTION(BlueprintCallable, Category="Save") void LoadProgress();
    void MarkPickupCollected(int32 PickupId);
    UFUNCTION(BlueprintPure, Category="Story") FString GetStoryLine() const;
    UFUNCTION(BlueprintPure, Category="Story") bool IsStoryLineVisible() const;
    void AdvanceStory();
    void SendSignal();
protected:
    UPROPERTY(VisibleAnywhere) TObjectPtr<USpringArmComponent> SpringArm;
    UPROPERTY(VisibleAnywhere) TObjectPtr<UCameraComponent> FollowCamera;
    UPROPERTY(VisibleAnywhere) TObjectPtr<UStaticMeshComponent> PlaceholderBody;
    UPROPERTY(VisibleAnywhere) TObjectPtr<UStaticMeshComponent> PlaceholderHead;
    void MoveForward(float Value);
    void MoveRight(float Value);
    void StartSprint();
    void StopSprint();
    void ToggleCrouch();
    void Fire();
    void Reload();
    void Heal();
    void Interact();
    bool bSprinting = false;
    bool bStealthCrouch = false;
    float LastShotTime = -10.f;
    FTimerHandle ReloadTimer;
    TArray<int32> CollectedPickups;
    float LastStoryChangeTime = -100.f;
};
