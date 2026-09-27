using UnrealBuildTool;

public class AfterSignal : ModuleRules
{
    public AfterSignal(ReadOnlyTargetRules Target) : base(Target)
    {
        PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;
        PublicDependencyModuleNames.AddRange(new [] { "Core", "CoreUObject", "Engine", "InputCore" });
    }
}
