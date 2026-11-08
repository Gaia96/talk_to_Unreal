using UnrealBuildTool;

public class ColorCubeChatTarget : TargetRules
{
	public ColorCubeChatTarget(TargetInfo Target) : base(Target)
	{
		DefaultBuildSettings = BuildSettingsVersion.Latest;
		IncludeOrderVersion = EngineIncludeOrderVersion.Latest;
		Type = TargetType.Game;
		ExtraModuleNames.Add("ColorCubeChat");
	}
}
