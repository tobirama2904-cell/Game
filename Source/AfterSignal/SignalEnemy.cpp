#include "SignalEnemy.h"
#include "SignalCharacter.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "Components/CapsuleComponent.h"
#include "Components/StaticMeshComponent.h"
#include "UObject/ConstructorHelpers.h"
#include "Kismet/GameplayStatics.h"
#include "Engine/World.h"
#include "EngineUtils.h"

ASignalEnemy::ASignalEnemy()
{
    PrimaryActorTick.bCanEverTick = true;
    GetCharacterMovement()->MaxWalkSpeed = 175.f;
    static ConstructorHelpers::FObjectFinder<UStaticMesh> Cylinder(TEXT("/Engine/BasicShapes/Cylinder.Cylinder"));
    static ConstructorHelpers::FObjectFinder<UStaticMesh> Sphere(TEXT("/Engine/BasicShapes/Sphere.Sphere"));
    PlaceholderBody = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("PlaceholderBody"));
    PlaceholderBody->SetupAttachment(RootComponent);
    PlaceholderBody->SetRelativeScale3D(FVector(.51f, .32f, .82f));
    PlaceholderBody->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    if (Cylinder.Succeeded()) PlaceholderBody->SetStaticMesh(Cylinder.Object);
    PlaceholderHead = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("PlaceholderHead"));
    PlaceholderHead->SetupAttachment(RootComponent);
    PlaceholderHead->SetRelativeLocation(FVector(0.f, 0.f, 70.f));
    PlaceholderHead->SetRelativeScale3D(FVector(.26f));
    PlaceholderHead->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    if (Sphere.Succeeded()) PlaceholderHead->SetStaticMesh(Sphere.Object);
}
void ASignalEnemy::BeginPlay()
{
    Super::BeginPlay(); Home = GetActorLocation(); Interest = Home;
    WanderPhase = FMath::FRandRange(0.f, 6.28f);
}
void ASignalEnemy::HearNoise(const FVector& Position) { Interest = Position; Memory = 5.f; bAlerted = true; }
void ASignalEnemy::BroadcastNoise(UWorld* World, const FVector& Position, float Radius)
{
    if (!World) return;
    for (TActorIterator<ASignalEnemy> It(World); It; ++It)
        if ((*It)->Health > 0.f && FVector::DistSquared2D((*It)->GetActorLocation(), Position) < FMath::Square(Radius)) (*It)->HearNoise(Position);
}
void ASignalEnemy::ReceiveShot(float Damage)
{
    if (Health <= 0.f) return;
    Health = FMath::Max(0.f, Health - Damage);
    if (Health <= 0.f)
    {
        GetCharacterMovement()->DisableMovement();
        SetActorTickEnabled(false);
        GetCapsuleComponent()->SetCollisionEnabled(ECollisionEnabled::NoCollision);
        SetLifeSpan(40.f);
    }
    else if (ASignalCharacter* Player = Cast<ASignalCharacter>(UGameplayStatics::GetPlayerCharacter(this, 0))) HearNoise(Player->GetActorLocation());
}
void ASignalEnemy::Tick(float DeltaTime)
{
    Super::Tick(DeltaTime);
    if (Health <= 0.f) return;
    ASignalCharacter* Player = Cast<ASignalCharacter>(UGameplayStatics::GetPlayerCharacter(this, 0));
    if (!Player || !Player->IsAlive()) return;
    const float Distance = FVector::Dist2D(GetActorLocation(), Player->GetActorLocation());
    const float DetectRadius = Player->IsCrouchedForStealth() ? 520.f : Player->IsSprinting() ? 1600.f : 950.f;
    if (Distance < DetectRadius) HearNoise(Player->GetActorLocation());
    Memory = FMath::Max(0.f, Memory - DeltaTime);
    if (Memory <= 0.f) { bAlerted = false; Interest = Home + FVector(FMath::Sin(GetWorld()->GetTimeSeconds()*.25f + WanderPhase)*260.f, FMath::Cos(GetWorld()->GetTimeSeconds()*.25f + WanderPhase)*260.f, 0.f); }
    else if (Distance < DetectRadius * 1.3f) Interest = Player->GetActorLocation();
    const FVector Offset = Interest - GetActorLocation();
    if (Offset.SizeSquared2D() > FMath::Square(110.f))
    {
        const FVector Direction = Offset.GetSafeNormal2D();
        const float Speed = bAlerted ? (bRunner ? 420.f : 290.f) : 110.f;
        FHitResult Hit;
        SetActorLocation(GetActorLocation() + Direction * Speed * DeltaTime, true, &Hit);
        SetActorRotation(Direction.Rotation());
    }
    GetCharacterMovement()->MaxWalkSpeed = bAlerted ? (bRunner ? 420.f : 290.f) : 110.f;
    AttackCooldown = FMath::Max(0.f, AttackCooldown - DeltaTime);
    if (Distance < 145.f && AttackCooldown <= 0.f) { Player->TakeSurvivalDamage(bRunner ? 18.f : 12.f); AttackCooldown = 1.25f; }
}
