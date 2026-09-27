#pragma once
#include "CoreMinimal.h"
#include "GameFramework/HUD.h"
#include "SignalHUD.generated.h"

UCLASS()
class AFTERSIGNAL_API ASignalHUD : public AHUD
{
    GENERATED_BODY()
public:
    virtual void DrawHUD() override;
};
