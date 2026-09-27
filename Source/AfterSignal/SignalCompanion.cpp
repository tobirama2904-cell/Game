#include "SignalCompanion.h"
#include "SignalCharacter.h"
#include "Components/CapsuleComponent.h"
#include "Components/StaticMeshComponent.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "Kismet/GameplayStatics.h"
#include "UObject/ConstructorHelpers.h"

ASignalCompanion::ASignalCompanion()
{
    PrimaryActorTick.bCanEverTick = true;
    GetCapsuleComponent()->InitCapsuleSize(38.f, 88.f);
    GetCharacterMovement()->MaxWalkSpeed = 400.f;
    GetCharacterMovement()->GetNavAgentPropertiesRef().bCanCrouch = true;
    static ConstructorHelpers::FObjectFinder<UStaticMesh> Cylinder(TEXT("/Engine/BasicShapes/Cylinder.Cylinder"));
    static ConstructorHelpers::FObjectFinder<UStaticMesh> Sphere(TEXT("/Engine/BasicShapes/Sphere.Sphere"));
    Body = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("PlaceholderBody"));
    Body->SetupAttachment(RootComponent);
    Body->SetRelativeScale3D(FVector(.48f,.33f,.72f));
    Body->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    if (Cylinder.Succeeded()) Body->SetStaticMesh(Cylinder.Object);
    Head = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("PlaceholderHead"));
    Head->SetupAttachment(RootComponent);
    Head->SetRelativeLocation(FVector(0.f,0.f,62.f));
    Head->SetRelativeScale3D(FVector(.24f));
    Head->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    if (Sphere.Succeeded()) Head->SetStaticMesh(Sphere.Object);
}
void ASignalCompanion::BeginPlay()
{
    Super::BeginPlay();
    if (!Leader) Leader = Cast<ASignalCharacter>(UGameplayStatics::GetPlayerCharacter(this, 0));
}
void ASignalCompanion::SetLeader(ASignalCharacter* NewLeader) { Leader = NewLeader; }
void ASignalCompanion::ToggleWait() { if (IsAlive()) bWaiting = !bWaiting; }
void ASignalCompanion::ReceiveDamage(float Amount)
{
    if (!IsAlive()) return;
    Health = FMath::Max(0.f, Health - FMath::Max(0.f, Amount));
    if (!IsAlive())
    {
        GetCharacterMovement()->DisableMovement();
        GetCapsuleComponent()->SetCollisionEnabled(ECollisionEnabled::NoCollision);
        SetActorTickEnabled(false);
    }
}
void ASignalCompanion::Tick(float DeltaTime)
{
    Super::Tick(DeltaTime);
    if (!IsAlive() || bWaiting || !IsValid(Leader) || !Leader->IsAlive()) return;
    // Desired place is behind and to the side; crouch is mirrored and emits no noise.
    const FVector Forward = Leader->GetActorForwardVector();
    const FVector Side = FVector::CrossProduct(FVector::UpVector, Forward);
    const FVector Goal = Leader->GetActorLocation() - Forward*190.f + Side*135.f;
    const FVector Delta = Goal - GetActorLocation();
    const float Distance = Delta.Size2D();
    if (Leader->IsCrouchedForStealth() && !bIsCrouched) Crouch();
    else if (!Leader->IsCrouchedForStealth() && bIsCrouched) UnCrouch();
    if (Distance < 95.f) return;
    // Recover from separation. The sweep movement alone cannot pathfind around buildings.
    if (Distance > 2400.f)
    {
        FHitResult Floor;
        FCollisionQueryParams Query(SCENE_QUERY_STAT(CompanionRecovery), false, this);
        const FVector Start = Goal + FVector(0.f,0.f,350.f);
        const FVector End = Goal - FVector(0.f,0.f,400.f);
        if (GetWorld()->LineTraceSingleByChannel(Floor, Start, End, ECC_Visibility, Query))
            SetActorLocation(Floor.ImpactPoint + FVector(0.f,0.f,GetCapsuleComponent()->GetScaledCapsuleHalfHeight()), false, nullptr, ETeleportType::TeleportPhysics);
        return;
    }
    GetCharacterMovement()->MaxWalkSpeed = Leader->IsCrouchedForStealth() ? 150.f : 420.f;
    AddMovementInput(Delta.GetSafeNormal2D());
}
