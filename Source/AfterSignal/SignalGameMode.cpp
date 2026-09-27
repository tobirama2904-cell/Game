#include "SignalGameMode.h"
#include "SignalCharacter.h"
#include "SignalHUD.h"
#include "Kismet/GameplayStatics.h"
#include "SignalEnemy.h"
#include "SignalInteractable.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMeshActor.h"
#include "Engine/DirectionalLight.h"
#include "Engine/SkyLight.h"
#include "Components/DirectionalLightComponent.h"
#include "Components/SkyLightComponent.h"
#include "Engine/World.h"
#include "Materials/MaterialInterface.h"
#include "GameFramework/PlayerController.h"
#include "UObject/ConstructorHelpers.h"

ASignalGameMode::ASignalGameMode()
{
    DefaultPawnClass = ASignalCharacter::StaticClass();
    HUDClass = ASignalHUD::StaticClass();
    static ConstructorHelpers::FObjectFinder<UStaticMesh> Cube(TEXT("/Engine/BasicShapes/Cube.Cube"));
    static ConstructorHelpers::FObjectFinder<UStaticMesh> Cone(TEXT("/Engine/BasicShapes/Cone.Cone"));
    static ConstructorHelpers::FObjectFinder<UStaticMesh> Cylinder(TEXT("/Engine/BasicShapes/Cylinder.Cylinder"));
    if (Cube.Succeeded()) CubeMesh = Cube.Object;
    if (Cone.Succeeded()) ConeMesh = Cone.Object;
    if (Cylinder.Succeeded()) CylinderMesh = Cylinder.Object;
    // Optional editor-generated content. If not imported, fall back to engine materials.
    ForestMaterial = LoadObject<UMaterialInterface>(nullptr, TEXT("/Game/Materials/M_ForestGround.M_ForestGround"));
    RoadMaterial = LoadObject<UMaterialInterface>(nullptr, TEXT("/Game/Materials/M_RoadAsphalt.M_RoadAsphalt"));
    ConcreteMaterial = LoadObject<UMaterialInterface>(nullptr, TEXT("/Game/Materials/M_Concrete.M_Concrete"));
}
void ASignalGameMode::BeginPlay()
{
    Super::BeginPlay();
    BuildWorld();
    // Entry is an engine map: no authored .umap is required to start this prototype.
    if (!UGameplayStatics::DoesSaveGameExist(TEXT("AfterSignal"), 0))
        if (APawn* Player = GetWorld()->GetFirstPlayerController() ? GetWorld()->GetFirstPlayerController()->GetPawn() : nullptr)
            Player->SetActorLocation(FVector(0.f, 2600.f, 140.f));
}
void ASignalGameMode::Block(FVector Location, FVector Size, UStaticMesh* Mesh, bool bCollision, UMaterialInterface* Material)
{
    if (!Mesh || !GetWorld()) return;
    AStaticMeshActor* Piece = GetWorld()->SpawnActor<AStaticMeshActor>(Location, FRotator::ZeroRotator);
    if (!Piece) return;
    Piece->GetStaticMeshComponent()->SetMobility(EComponentMobility::Movable);
    Piece->GetStaticMeshComponent()->SetStaticMesh(Mesh);
    if (Material) Piece->GetStaticMeshComponent()->SetMaterial(0, Material);
    Piece->SetActorScale3D(Size / 100.f);
    Piece->GetStaticMeshComponent()->SetCollisionEnabled(bCollision ? ECollisionEnabled::QueryAndPhysics : ECollisionEnabled::NoCollision);
}
void ASignalGameMode::BuildWorld()
{
    UWorld* World = GetWorld();
    if (!World) return;
    World->SpawnActor<ADirectionalLight>(FVector(-4500.f, -4500.f, 7000.f), FRotator(-45.f, -25.f, 0.f));
    World->SpawnActor<ASkyLight>(FVector(0.f, 0.f, 700.f), FRotator::ZeroRotator);
    Block(FVector(0.f, -4500.f, -65.f), FVector(23000.f, 26000.f, 120.f), CubeMesh, true, ForestMaterial);
    Block(FVector(0.f, -4000.f, 2.f), FVector(700.f, 21000.f, 6.f), CubeMesh, true, RoadMaterial);
    for (int32 I = 0; I < 110; ++I)
    {
        const float X = FMath::FRandRange(-10500.f, 10500.f);
        const float Y = FMath::FRandRange(-15000.f, 7000.f);
        if (FMath::Abs(X) < 1000.f || FVector2D::Distance(FVector2D(X,Y), FVector2D(-3100.f,-2500.f)) < 1600.f || FVector2D::Distance(FVector2D(X,Y), FVector2D(2500.f,-6400.f)) < 1600.f) continue;
        const float H = FMath::FRandRange(380.f, 750.f);
        Block(FVector(X,Y,H*.32f), FVector(42.f,42.f,H*.64f), CylinderMesh, false);
        for (int32 J=0; J<3; ++J) Block(FVector(X,Y,H*(.53f + J*.17f)), FVector(280.f-J*38.f,280.f-J*38.f,230.f), ConeMesh, false);
    }
    for (const FVector& P : TArray<FVector>{ FVector(-3100.f,-2500.f,0.f), FVector(2500.f,-6400.f,0.f), FVector(-1900.f,-9000.f,0.f) })
    {
        Block(P + FVector(0.f,0.f,22.f), FVector(1300.f,1000.f,44.f), CubeMesh, true, ConcreteMaterial);
        Block(P + FVector(-650.f,0.f,205.f), FVector(35.f,1000.f,365.f), CubeMesh, true, ConcreteMaterial);
        Block(P + FVector(0.f,-500.f,205.f), FVector(1300.f,35.f,365.f), CubeMesh, true, ConcreteMaterial);
        Block(P + FVector(0.f,0.f,420.f), FVector(900.f,800.f,30.f), CubeMesh);
    }
    for (int32 I=0; I<4; ++I)
    {
        const float X=(I%2 ? -320.f : 320.f), Y=(I/2 ? -11900.f : -11300.f);
        Block(FVector(X,Y,1200.f), FVector(35.f,35.f,2400.f), CylinderMesh);
    }
    for (int32 I=0; I<5; ++I) Block(FVector(0.f,-11600.f,I*470.f+120.f), FVector(670.f,30.f,25.f), CubeMesh, false);
    struct FPickup { FVector Position; ESignalPickup Kind; };
    const FPickup Pickups[] = {
        {FVector(-3100.f,-2500.f,95.f), ESignalPickup::Note},
        {FVector(2500.f,-6400.f,95.f), ESignalPickup::Medicine},
        {FVector(0.f,-11600.f,95.f), ESignalPickup::Tower},
        {FVector(600.f,400.f,95.f), ESignalPickup::Ammo},
        {FVector(-3400.f,-1900.f,95.f), ESignalPickup::Bandage},
        {FVector(-1800.f,-9000.f,95.f), ESignalPickup::Supplies}
    };
    for (int32 I = 0; I < static_cast<int32>(UE_ARRAY_COUNT(Pickups)); ++I)
        if (ASignalInteractable* Item = World->SpawnActor<ASignalInteractable>(Pickups[I].Position, FRotator::ZeroRotator))
        { Item->Kind = Pickups[I].Kind; Item->PickupId = I; }
    const FVector EnemyPositions[] = {FVector(-900.f,-500.f,140.f),FVector(900.f,-1500.f,140.f),FVector(-2600.f,-3200.f,140.f),FVector(1200.f,-4500.f,140.f),FVector(2800.f,-4800.f,140.f),FVector(-900.f,-8300.f,140.f),FVector(800.f,-10600.f,140.f)};
    for (int32 I=0; I<static_cast<int32>(UE_ARRAY_COUNT(EnemyPositions)); ++I)
        if (ASignalEnemy* Enemy = World->SpawnActor<ASignalEnemy>(EnemyPositions[I], FRotator::ZeroRotator)) Enemy->bRunner = I%3 == 0;
}
