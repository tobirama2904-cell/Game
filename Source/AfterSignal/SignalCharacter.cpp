#include "SignalCharacter.h"
#include "SignalEnemy.h"
#include "SignalCompanion.h"
#include "SignalInteractable.h"
#include "SignalSaveGame.h"
#include "Kismet/GameplayStatics.h"
#include "EngineUtils.h"
#include "Camera/CameraComponent.h"
#include "GameFramework/SpringArmComponent.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "Components/CapsuleComponent.h"
#include "Components/InputComponent.h"
#include "Components/StaticMeshComponent.h"
#include "UObject/ConstructorHelpers.h"
#include "Engine/World.h"
#include "TimerManager.h"

ASignalCharacter::ASignalCharacter()
{
    PrimaryActorTick.bCanEverTick = true;
    GetCapsuleComponent()->InitCapsuleSize(42.f, 96.f);
    bUseControllerRotationYaw = false;
    GetCharacterMovement()->bOrientRotationToMovement = true;
    GetCharacterMovement()->RotationRate = FRotator(0.f, 560.f, 0.f);
    GetCharacterMovement()->MaxWalkSpeed = 340.f;
    GetCharacterMovement()->GetNavAgentPropertiesRef().bCanCrouch = true;
    SpringArm = CreateDefaultSubobject<USpringArmComponent>(TEXT("CameraBoom"));
    SpringArm->SetupAttachment(RootComponent);
    SpringArm->TargetArmLength = 340.f;
    SpringArm->SocketOffset = FVector(0.f, 60.f, 70.f);
    SpringArm->bUsePawnControlRotation = true;
    FollowCamera = CreateDefaultSubobject<UCameraComponent>(TEXT("FollowCamera"));
    FollowCamera->SetupAttachment(SpringArm, USpringArmComponent::SocketName);
    FollowCamera->bUsePawnControlRotation = false;
    // Clearly labelled fallback geometry. Replace with original licensed skeletal meshes.
    static ConstructorHelpers::FObjectFinder<UStaticMesh> Cylinder(TEXT("/Engine/BasicShapes/Cylinder.Cylinder"));
    static ConstructorHelpers::FObjectFinder<UStaticMesh> Sphere(TEXT("/Engine/BasicShapes/Sphere.Sphere"));
    PlaceholderBody = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("PlaceholderBody"));
    PlaceholderBody->SetupAttachment(RootComponent);
    PlaceholderBody->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    PlaceholderBody->SetRelativeScale3D(FVector(.55f, .34f, .85f));
    if (Cylinder.Succeeded()) PlaceholderBody->SetStaticMesh(Cylinder.Object);
    PlaceholderHead = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("PlaceholderHead"));
    PlaceholderHead->SetupAttachment(RootComponent);
    PlaceholderHead->SetRelativeLocation(FVector(0.f, 0.f, 70.f));
    PlaceholderHead->SetRelativeScale3D(FVector(.27f));
    PlaceholderHead->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    if (Sphere.Succeeded()) PlaceholderHead->SetStaticMesh(Sphere.Object);
}
void ASignalCharacter::BeginPlay() { Super::BeginPlay(); LoadProgress(); LastStoryChangeTime = GetWorld()->GetTimeSeconds(); }
void ASignalCharacter::Tick(float DeltaTime)
{
    Super::Tick(DeltaTime);
    if (bBleeding && Health > 0.f)
    {
        Health = FMath::Max(0.f, Health - 2.5f * DeltaTime);
        if (Health <= 0.f) GetCharacterMovement()->DisableMovement();
    }
    const bool bRunning = bSprinting && Stamina > 1.f && !bStealthCrouch && GetVelocity().SizeSquared2D() > 100.f;
    Stamina = FMath::Clamp(Stamina + (bRunning ? -24.f : 14.f) * DeltaTime, 0.f, 100.f);
    GetCharacterMovement()->MaxWalkSpeed = bStealthCrouch ? 160.f : (bLegInjured ? 190.f : (bRunning ? 570.f : 340.f));
}
void ASignalCharacter::SetupPlayerInputComponent(UInputComponent* Input)
{
    Super::SetupPlayerInputComponent(Input);
    Input->BindAxis("MoveForward", this, &ASignalCharacter::MoveForward);
    Input->BindAxis("MoveRight", this, &ASignalCharacter::MoveRight);
    Input->BindAxis("Turn", this, &APawn::AddControllerYawInput);
    Input->BindAxis("LookUp", this, &APawn::AddControllerPitchInput);
    Input->BindAction("Sprint", IE_Pressed, this, &ASignalCharacter::StartSprint);
    Input->BindAction("Sprint", IE_Released, this, &ASignalCharacter::StopSprint);
    Input->BindAction("Crouch", IE_Pressed, this, &ASignalCharacter::ToggleCrouch);
    Input->BindAction("Fire", IE_Pressed, this, &ASignalCharacter::Fire);
    Input->BindAction("Reload", IE_Pressed, this, &ASignalCharacter::Reload);
    Input->BindAction("Heal", IE_Pressed, this, &ASignalCharacter::Heal);
    Input->BindAction("Interact", IE_Pressed, this, &ASignalCharacter::Interact);
    Input->BindAction("Save", IE_Pressed, this, &ASignalCharacter::SaveProgress);
    Input->BindAction("Distract", IE_Pressed, this, &ASignalCharacter::ThrowStone);
    Input->BindAction("CompanionWait", IE_Pressed, this, &ASignalCharacter::ToggleCompanionWait);
}
void ASignalCharacter::MoveForward(float Value)
{
    if (Controller && Value != 0.f) AddMovementInput(FRotationMatrix(FRotator(0.f, Controller->GetControlRotation().Yaw, 0.f)).GetUnitAxis(EAxis::X), Value);
}
void ASignalCharacter::MoveRight(float Value)
{
    if (Controller && Value != 0.f) AddMovementInput(FRotationMatrix(FRotator(0.f, Controller->GetControlRotation().Yaw, 0.f)).GetUnitAxis(EAxis::Y), Value);
}
void ASignalCharacter::StartSprint() { bSprinting = true; }
void ASignalCharacter::StopSprint() { bSprinting = false; }
void ASignalCharacter::ToggleCrouch() { bStealthCrouch = !bStealthCrouch; if (bStealthCrouch) Crouch(); else UnCrouch(); }
void ASignalCharacter::TakeSurvivalDamage(float Amount)
{
    if (!IsAlive()) return;
    Health = FMath::Clamp(Health - Amount, 0.f, 100.f);
    // Repeat injuries have lasting consequences until treated.
    if (Amount >= 12.f) bBleeding = true;
    if (Amount >= 18.f) bLegInjured = true;
    if (!IsAlive()) GetCharacterMovement()->DisableMovement();
}
void ASignalCharacter::ThrowStone()
{
    if (!GetWorld() || Stones <= 0 || !IsAlive()) return;
    --Stones;
    const FVector Start = FollowCamera->GetComponentLocation();
    const FVector End = Start + FollowCamera->GetForwardVector() * 1800.f;
    FHitResult Hit;
    FCollisionQueryParams Query(SCENE_QUERY_STAT(SignalThrownStone), true, this);
    const FVector NoisePosition = GetWorld()->LineTraceSingleByChannel(Hit, Start, End, ECC_Visibility, Query) ? Hit.ImpactPoint : End;
    ASignalEnemy::BroadcastNoise(GetWorld(), NoisePosition, 900.f);
}
void ASignalCharacter::Fire()
{
    if (Ammo < 1 || !GetWorld() || GetWorld()->GetTimerManager().IsTimerActive(ReloadTimer) || GetWorld()->GetTimeSeconds() - LastShotTime < .35f || !IsAlive()) return;
    LastShotTime = GetWorld()->GetTimeSeconds(); --Ammo;
    const FVector Start = FollowCamera->GetComponentLocation();
    const FVector End = Start + FollowCamera->GetForwardVector() * 4500.f;
    FHitResult Hit;
    FCollisionQueryParams Query(SCENE_QUERY_STAT(SignalShot), true, this);
    if (GetWorld()->LineTraceSingleByChannel(Hit, Start, End, ECC_Visibility, Query))
        if (ASignalEnemy* Enemy = Cast<ASignalEnemy>(Hit.GetActor())) Enemy->ReceiveShot(Hit.BoneName == FName("head") ? 90.f : 45.f);
    ASignalEnemy::BroadcastNoise(GetWorld(), GetActorLocation(), 1900.f);
}
void ASignalCharacter::Reload()
{
    if (!GetWorld() || Ammo >= 6 || ReserveAmmo < 1 || GetWorld()->GetTimerManager().IsTimerActive(ReloadTimer)) return;
    GetWorld()->GetTimerManager().SetTimer(ReloadTimer, [this]()
    {
        const int32 Count = FMath::Min(6 - Ammo, ReserveAmmo);
        Ammo += Count; ReserveAmmo -= Count;
    }, 1.3f, false);
}
void ASignalCharacter::Heal()
{
    if (Bandages <= 0 || !IsAlive() || (Health >= 100.f && !bBleeding && !bLegInjured)) return;
    --Bandages;
    Health = FMath::Min(100.f, Health + 45.f);
    bBleeding = false;
    bLegInjured = false;
    SaveProgress();
}
void ASignalCharacter::Interact()
{
    if (!GetWorld()) return;
    TArray<FOverlapResult> Hits;
    FCollisionObjectQueryParams Objects; Objects.AddObjectTypesToQuery(ECC_WorldDynamic);
    FCollisionQueryParams Query(SCENE_QUERY_STAT(SignalInteract), false, this);
    GetWorld()->OverlapMultiByObjectType(Hits, GetActorLocation(), FQuat::Identity, Objects, FCollisionShape::MakeSphere(230.f), Query);
    ASignalInteractable* Closest = nullptr;
    float Best = 230.f * 230.f;
    for (const FOverlapResult& Result : Hits)
    {
        if (ASignalInteractable* Item = Cast<ASignalInteractable>(Result.GetActor()))
        {
            if (!Item->CanUse(this)) continue;
            const float Distance = FVector::DistSquared(GetActorLocation(), Item->GetActorLocation());
            if (Distance < Best) { Best = Distance; Closest = Item; }
        }
    }
    if (Closest) Closest->Use(this);
}
void ASignalCharacter::AdvanceStory() { if (ChapterStep == 0) { ChapterStep = 1; LastStoryChangeTime = GetWorld()->GetTimeSeconds(); OnStoryChanged.Broadcast(); } }
bool ASignalCharacter::CollectMedicine() { if (ChapterStep != 1) return false; bMedicineCollected = true; ChapterStep = 2; LastStoryChangeTime = GetWorld()->GetTimeSeconds(); OnStoryChanged.Broadcast(); return true; }
void ASignalCharacter::SendSignal() { if (ChapterStep == 2 && bMedicineCollected) { bSignalSent = true; ChapterStep = 3; LastStoryChangeTime = GetWorld()->GetTimeSeconds(); OnStoryChanged.Broadcast(); } }

void ASignalCharacter::MarkPickupCollected(int32 PickupId)
{
    CollectedPickups.AddUnique(PickupId);
}
void ASignalCharacter::SaveProgress()
{
    if (!GetWorld() || !IsAlive()) return;
    USignalSaveGame* Save = Cast<USignalSaveGame>(UGameplayStatics::CreateSaveGameObject(USignalSaveGame::StaticClass()));
    if (!Save) return;
    Save->ChapterStep = ChapterStep;
    Save->bMedicineCollected = bMedicineCollected;
    Save->bSignalSent = bSignalSent;
    Save->Health = Health;
    Save->Ammo = Ammo;
    Save->ReserveAmmo = ReserveAmmo;
    Save->Bandages = Bandages;
    Save->bBleeding = bBleeding;
    Save->bLegInjured = bLegInjured;
    Save->Stones = Stones;
    Save->Position = GetActorLocation();
    Save->CollectedPickups = CollectedPickups;
    UGameplayStatics::SaveGameToSlot(Save, TEXT("AfterSignal"), 0);
}
void ASignalCharacter::LoadProgress()
{
    if (!GetWorld() || !UGameplayStatics::DoesSaveGameExist(TEXT("AfterSignal"), 0)) return;
    USignalSaveGame* Save = Cast<USignalSaveGame>(UGameplayStatics::LoadGameFromSlot(TEXT("AfterSignal"), 0));
    if (!Save) return;
    ChapterStep = FMath::Clamp(Save->ChapterStep, 0, 3);
    bMedicineCollected = Save->bMedicineCollected;
    bSignalSent = Save->bSignalSent;
    Health = FMath::Clamp(Save->Health, 1.f, 100.f);
    Ammo = FMath::Clamp(Save->Ammo, 0, 6);
    ReserveAmmo = FMath::Max(0, Save->ReserveAmmo);
    Bandages = FMath::Max(0, Save->Bandages);
    bBleeding = Save->bBleeding;
    bLegInjured = Save->bLegInjured;
    Stones = FMath::Max(0, Save->Stones);
    CollectedPickups = Save->CollectedPickups;
    SetActorLocation(Save->Position, false, nullptr, ETeleportType::TeleportPhysics);
    // GameMode spawns the world at BeginPlay; defer removal until spawned items exist.
    FTimerHandle RemoveHandle;
    GetWorldTimerManager().SetTimer(RemoveHandle, [this]()
    {
        if (!IsValid(this)) return;
        TArray<ASignalInteractable*> ToRemove;
        for (TActorIterator<ASignalInteractable> It(GetWorld()); It; ++It)
            if (CollectedPickups.Contains(It->PickupId)) ToRemove.Add(*It);
        for (ASignalInteractable* Item : ToRemove) if (IsValid(Item)) Item->Destroy();
    }, .1f, false);
    OnStoryChanged.Broadcast();
}

FString ASignalCharacter::GetStoryLine() const
{
    switch (ChapterStep)
    {
    case 0: return TEXT("ETHAN: Do you think anyone is still listening?  MARA: Then let's give them something to hear.");
    case 1: return TEXT("MARA: The operator left medicine in the clinic. Ethan, stay close. I'm coming back.");
    case 2: return TEXT("ETHAN: You found it?  MARA: We still have to get the transmitter working.");
    default: return TEXT("MARA: If you hear me, we're still here.  RADIO: Black Point. We see your light.");
    }
}
bool ASignalCharacter::IsStoryLineVisible() const
{
    return GetWorld() && GetWorld()->GetTimeSeconds() - LastStoryChangeTime < (ChapterStep == 3 ? 18.f : 11.f);
}

void ASignalCharacter::SetCompanion(ASignalCompanion* NewCompanion)
{
    Companion = NewCompanion;
    if (IsValid(Companion)) Companion->SetLeader(this);
}
void ASignalCharacter::ToggleCompanionWait()
{
    if (IsValid(Companion)) Companion->ToggleWait();
}
