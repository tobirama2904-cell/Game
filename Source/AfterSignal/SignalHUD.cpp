#include "SignalHUD.h"
#include "SignalCharacter.h"
#include "SignalCompanion.h"
#include "SignalInteractable.h"
#include "Engine/Canvas.h"
#include "Engine/Engine.h"
#include "EngineUtils.h"
#include "GameFramework/PlayerController.h"

void ASignalHUD::DrawHUD()
{
    Super::DrawHUD();
    if (!Canvas || !PlayerOwner) return;
    const ASignalCharacter* Player = Cast<ASignalCharacter>(PlayerOwner->GetPawn());
    if (!Player) return;
    const float Scale = FMath::Clamp(Canvas->SizeY / 900.f, .7f, 1.6f);
    const FLinearColor Text(.9f,.9f,.8f,1.f);
    const FLinearColor Accent(.86f,.71f,.47f,1.f);
    const FLinearColor Danger(.9f,.25f,.2f,1.f);
    UFont* Font = GEngine ? GEngine->GetSmallFont() : nullptr;
    if (!Font) return;
    DrawText(TEXT("AFTER THE SIGNAL  /  OREGON, 2041"), Accent, 24.f*Scale, 20.f*Scale, Font, Scale);
    DrawText(Player->GetObjective(), Text, 24.f*Scale, 50.f*Scale, Font, Scale);
    if (Player->ChapterStep == 3)
        DrawText(Player->GetEndingText(), Accent, 24.f*Scale, 77.f*Scale, Font, Scale);
    const float Bottom = Canvas->SizeY - 125.f*Scale;
    DrawText(FString::Printf(TEXT("HEALTH %d   STAMINA %d   AMMO %d / %d   BANDAGES %d   STONES %d   SUPPLIES %d"),
        FMath::RoundToInt(Player->Health), FMath::RoundToInt(Player->Stamina), Player->Ammo, Player->ReserveAmmo, Player->Bandages, Player->Stones, Player->Supplies),
        Player->Health < 30.f ? Danger : Text, 24.f*Scale, Bottom, Font, Scale);
    DrawText(TEXT("WASD MOVE  SHIFT RUN  CTRL CROUCH  LMB FIRE  R RELOAD  H BANDAGE  Q STONE  F ETHAN WAIT/FOLLOW  E USE  F5 SAVE"),
        Text, 24.f*Scale, Bottom + 27.f*Scale, Font, Scale);
    if (Player->bBleeding || Player->bLegInjured)
        DrawText(Player->bBleeding ? TEXT("BLEEDING - USE A BANDAGE [H]") : TEXT("LEG INJURED - MOVEMENT SLOWED"),
            Danger, 24.f*Scale, Bottom - 28.f*Scale, Font, Scale);
    DrawText(TEXT("+"), Text, Canvas->SizeX*.5f-4.f*Scale, Canvas->SizeY*.5f-9.f*Scale, Font, Scale);
    if (Player->IsStoryLineVisible())
        DrawText(Player->GetStoryLine(), Accent, 24.f*Scale, Canvas->SizeY*.79f, Font, Scale);
    const ASignalInteractable* Nearby = nullptr;
    float Best = FMath::Square(230.f);
    for (TActorIterator<ASignalInteractable> It(GetWorld()); It; ++It)
    {
        const float Dist = FVector::DistSquared(Player->GetActorLocation(), It->GetActorLocation());
        if (Dist < Best && It->CanUse(Player)) { Best = Dist; Nearby = *It; }
    }
    if (Nearby) DrawText(FString::Printf(TEXT("[E] %s"), *Nearby->GetPrompt()), Accent,
        Canvas->SizeX*.5f-110.f*Scale, Canvas->SizeY*.7f, Font, Scale);
}
