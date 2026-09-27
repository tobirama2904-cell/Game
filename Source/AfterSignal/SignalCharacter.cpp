#include "SignalCharacter.h"
#include "SignalEnemy.h"
#include "SignalInteractable.h"
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
void ASignalCharacter::BeginPlay() { Super::BeginPlay(); }
void ASignalCharacter::Tick(float DeltaTime)
{
    Super::Tick(DeltaTime);
    const bool bRunning = bSprinting && Stamina > 1.f && !bStealthCrouch && GetVelocity().SizeSquared2D() > 100.f;
    Stamina = FMath::Clamp(Stamina + (bRunning ? -24.f : 14.f) * DeltaTime, 0.f, 100.f);
    GetCharacterMovement()->MaxWalkSpeed = bStealthCrouch ? 160.f : (bRunning ? 570.f : 340.f);
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
void ASignalCharacter::TakeSurvivalDamage(float Amount) { Health = FMath::Clamp(Health - Amount, 0.f, 100.f); if (Health <= 0.f) GetCharacterMovement()->DisableMovement(); }
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
void ASignalCharacter::Heal() { if (Bandages && Health < 100.f && IsAlive()) { --Bandages; Health = FMath::Min(100.f, Health + 45.f); } }
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
        if (ASignalInteractable* Item = Cast<ASignalInteractable>(Result.GetActor()))
        {
            const float Distance = FVector::DistSquared(GetActorLocation(), Item->GetActorLocation());
            if (Distance < Best) { Best = Distance; Closest = Item; }
        }
    if (Closest) Closest->Use(this);
}
void ASignalCharacter::AdvanceStory() { if (ChapterStep == 0) { ChapterStep = 1; OnStoryChanged.Broadcast(); } }
bool ASignalCharacter::CollectMedicine() { if (ChapterStep != 1) return false; bMedicineCollected = true; ChapterStep = 2; OnStoryChanged.Broadcast(); return true; }
void ASignalCharacter::SendSignal() { if (ChapterStep == 2 && bMedicineCollected) { bSignalSent = true; ChapterStep = 3; OnStoryChanged.Broadcast(); } }
