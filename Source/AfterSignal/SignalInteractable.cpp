#include "SignalInteractable.h"
#include "SignalCharacter.h"
#include "Components/SphereComponent.h"
#include "Components/StaticMeshComponent.h"
#include "UObject/ConstructorHelpers.h"

ASignalInteractable::ASignalInteractable()
{
    Trigger = CreateDefaultSubobject<USphereComponent>(TEXT("InteractionTrigger"));
    RootComponent = Trigger;
    Trigger->InitSphereRadius(110.f);
    Trigger->SetCollisionResponseToAllChannels(ECR_Ignore);
    Trigger->SetCollisionResponseToChannel(ECC_WorldDynamic, ECR_Overlap);
    Trigger->SetCollisionObjectType(ECC_WorldDynamic);
    Mesh = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("PickupMesh"));
    Mesh->SetupAttachment(RootComponent);
    Mesh->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    static ConstructorHelpers::FObjectFinder<UStaticMesh> Cube(TEXT("/Engine/BasicShapes/Cube.Cube"));
    if (Cube.Succeeded()) Mesh->SetStaticMesh(Cube.Object);
    Mesh->SetRelativeScale3D(FVector(.35f, .35f, .3f));
}
void ASignalInteractable::Use(ASignalCharacter* Player)
{
    if (!Player) return;
    switch (Kind)
    {
    case ESignalPickup::Ammo: Player->ReserveAmmo += 8; break;
    case ESignalPickup::Bandage: ++Player->Bandages; break;
    case ESignalPickup::Supplies: ++Player->Bandages; break;
    case ESignalPickup::Note: if (Player->ChapterStep != 0) return; Player->AdvanceStory(); break;
    case ESignalPickup::Medicine: if (!Player->CollectMedicine()) return; break;
    case ESignalPickup::Tower: if (Player->ChapterStep != 2) return; Player->SendSignal(); break;
    }
    Destroy();
}
