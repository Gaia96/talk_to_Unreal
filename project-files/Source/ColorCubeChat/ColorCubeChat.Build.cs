using UnrealBuildTool;

public class ColorCubeChat : ModuleRules
{
	public ColorCubeChat(ReadOnlyTargetRules Target) : base(Target)
	{
		PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;
		PublicDependencyModuleNames.Add("Core");
	}
}
