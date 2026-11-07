"""Build native four-sample pose playback assets without changing the existing hand AnimBP."""
import unreal
assert unreal.EditorLevelLibrary.get_game_world() is None
tools=unreal.AssetToolsHelpers.get_asset_tools()
base='/VRSharp/Characters/MannequinsXR/Animations/'
idle=unreal.load_asset(base+'A_MannequinsXR_Idle_Right')
grip=unreal.load_asset(base+'A_MannequinsXR_Grasp_Right')
pressed=unreal.load_asset(base+'SK_MannequinsXR_Close_Right')
def value(cls,**fields):
    obj=cls()
    for name,v in fields.items():obj.set_editor_property(name,v)
    return obj
with unreal.ScopedEditorTransaction('Configure reusable native grip and pressed animation playback'):
    path='/VRSharp/Tests/BS_ToolGrip'
    if unreal.EditorAssetLibrary.does_asset_exist(path):blend=unreal.load_asset(path)
    else:
        factory=unreal.BlendSpaceFactoryNew();factory.set_editor_property('target_skeleton',idle.get_editor_property('skeleton'))
        blend=tools.create_asset('BS_ToolGrip','/VRSharp/Tests',unreal.BlendSpace,factory)
    axes=list(blend.get_editor_property('blend_parameters'))
    for i,name in enumerate(['Trigger','PoseWeight']):axes[i]=value(unreal.BlendParameter,display_name=name,min=0,max=1,grid_num=4)
    blend.set_editor_property('blend_parameters',axes)
    blend.set_editor_property('sample_data',[
        value(unreal.BlendSample,animation=idle,sample_value=unreal.Vector(0,0,0),use_single_frame_for_blending=True,frame_index_to_sample=0),
        value(unreal.BlendSample,animation=idle,sample_value=unreal.Vector(1,0,0),use_single_frame_for_blending=True,frame_index_to_sample=0),
        value(unreal.BlendSample,animation=grip,sample_value=unreal.Vector(0,1,0),use_single_frame_for_blending=True,frame_index_to_sample=0),
        value(unreal.BlendSample,animation=pressed,sample_value=unreal.Vector(1,1,0),use_single_frame_for_blending=True,frame_index_to_sample=0)])
    blend.set_editor_property('target_weight_interpolation_speed_per_sec',0)
    blend.set_editor_property('notify_trigger_mode',unreal.NotifyTriggerMode.NONE)
    assert unreal.EditorAssetLibrary.save_loaded_asset(blend,only_if_is_dirty=False)
    for side in ['Left','Right']:
        p=unreal.load_asset('/VRSharp/Tests/DA_ToolGrip_'+side)
        p.set_editor_property('GripAnimation',grip);p.set_editor_property('PressedAnimation',pressed);p.set_editor_property('PoseBlendSpace',blend)
        assert unreal.EditorAssetLibrary.save_loaded_asset(p,only_if_is_dirty=False)
print('Saved BS_ToolGrip and connected both reusable clip presets')
