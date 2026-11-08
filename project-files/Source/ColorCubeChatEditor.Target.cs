using UnrealBuildTool;

public class ColorCubeChatEditorTarget : TargetRules
{
	public ColorCubeChatEditorTarget(TargetInfo Target) : base(Target)
	{
		DefaultBuildSettings = BuildSettingsVersion.Latest;
		IncludeOrderVersion = EngineIncludeOrderVersion.Latest;
		Type = TargetType.Editor;
		ExtraModuleNames.Add("ColorCubeChat");
	}
}
