"""Create the cloud handoff's native input, pose and desktop acceptance assets via MCP."""
import unreal
from pathlib import Path
import json

assert unreal.EditorLevelLibrary.get_game_world() is None
tools=unreal.AssetToolsHelpers.get_asset_tools()
sub=unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
lib=unreal.SubobjectDataBlueprintFunctionLibrary
folder='/VRSharp/Tests'

def save(obj):
    assert unreal.EditorAssetLibrary.save_loaded_asset(obj, only_if_is_dirty=False)

def create(name,cls,factory):
    path=folder+'/'+name
    return unreal.load_asset(path) if unreal.EditorAssetLibrary.does_asset_exist(path) else tools.create_asset(name,folder,cls,factory)

def blueprint(name,parent):
    f=unreal.BlueprintFactory();f.set_editor_property('parent_class',parent)
    return create(name,unreal.Blueprint,f)

def parts(bp):
    result={}
    for h in sub.k2_gather_subobject_data_for_blueprint(bp):
        d=lib.get_data(h);o=lib.get_object_for_blueprint(d,bp) or lib.get_object(d)
        if isinstance(o,unreal.ActorComponent):result[o.get_name().split('_GEN_VARIABLE')[0]]=o
    return result

def action(name,boolean=False):
    a=create(name,unreal.InputAction,unreal.InputAction_Factory())
    a.set_editor_property('value_type',unreal.InputActionValueType.BOOLEAN if boolean else unreal.InputActionValueType.AXIS3D)
    save(a);return a

def input_key(name):
    k=unreal.Key()
    k.import_text(name)
    return k

with unreal.ScopedEditorTransaction('Configure VRSharp cloud handoff native assets'):
    actions={}
    for n in ['Move','Look','HandMove','Grip','SwitchHand','Trigger','LeftGrip','RightGrip','LeftTrigger','RightTrigger','HandRotate','ToggleGrip','Fingers','CaptureCheckpoint','RestoreCheckpoint']:
        actions[n]=action('IA_Desktop'+n,n in ['Grip','SwitchHand','LeftGrip','RightGrip','ToggleGrip','CaptureCheckpoint','RestoreCheckpoint'])
    context=create('IMC_VRSharpDesktop',unreal.InputMappingContext,unreal.InputMappingContext_Factory())
    rows=[]
    def key(n,k,axis=0,negative=False,gain=1):
        modifiers=[]
        if negative:
            modifiers.append(unreal.new_object(unreal.InputModifierNegate,outer=context))
        if gain!=1:
            m=unreal.new_object(unreal.InputModifierScalar,outer=context);m.set_editor_property('scalar',unreal.Vector(gain,gain,gain));modifiers.append(m)
        if axis:
            m=unreal.new_object(unreal.InputModifierSwizzleAxis,outer=context)
            m.set_editor_property('order',unreal.InputAxisSwizzle.YXZ if axis==1 else unreal.InputAxisSwizzle.ZYX);modifiers.append(m)
        rows.append(unreal.EnhancedActionKeyMapping(action=actions[n],key=input_key(k),modifiers=modifiers))
    for n,keys in [('Move',[('W',0,False),('S',0,True),('D',1,False),('A',1,True),('E',2,False),('Q',2,True)]),
                   ('HandMove',[('I',0,False),('K',0,True),('L',1,False),('J',1,True),('U',2,False),('O',2,True)]),
                   ('HandRotate',[('R',0,False),('F',0,True),('T',1,False),('G',1,True),('Y',2,False),('H',2,True)])]:
        for k,axis,neg in keys:key(n,k,axis,neg)
    key('Look','MouseX',gain=.70);key('Look','MouseY',1,False,.70)
    for n,k in [('Grip','MiddleMouseButton'),('LeftGrip','LeftMouseButton'),('RightGrip','RightMouseButton'),('SwitchHand','Tab'),('ToggleGrip','P'),('Trigger','LeftShift'),('LeftTrigger','V'),('RightTrigger','B'),('CaptureCheckpoint','F5'),('RestoreCheckpoint','F9')]:key(n,k)
    for k,axis in [('Z',0),('X',1),('C',2)]:key('Fingers',k,axis)
    context.set_editor_property('default_key_mappings',unreal.InputMappingContextMappingData(mappings=rows));save(context)

    pawn=blueprint('BP_DesktopTestPawn',unreal.load_class(None,'/Script/UnrealSharp.VRSharpDesktopTestPawn_C'))
    cdo=unreal.get_default_object(pawn.generated_class())
    for n,a in actions.items():cdo.set_editor_property('Desktop'+n,a)
    cdo.set_editor_property('DesktopMappingContext',context)
    for side in ['Left','Right']:cdo.set_editor_property(side+'HandClass',unreal.load_asset('/VRSharp/Blueprints/BP_VRSharpHand'+side).generated_class())
    components=parts(pawn)
    components['Camera'].set_editor_property('lock_to_hmd',False)
    for side,y in [('Left',-20),('Right',20)]:
        components[side+'Target'].set_editor_property('relative_location',unreal.Vector(42,y,-15))
        components[side+'Target'].set_editor_property('relative_rotation',unreal.Rotator(pitch=0,yaw=-90,roll=90))
    tick=cdo.get_editor_property('primary_actor_tick');tick.set_editor_property('tick_group',unreal.TickingGroup.TG_PRE_PHYSICS);cdo.set_editor_property('primary_actor_tick',tick)
    unreal.BlueprintEditorLibrary.compile_blueprint(pawn);save(pawn)

    presets={}
    for side in ['Left','Right']:
        f=unreal.DataAssetFactory();f.set_editor_property('data_asset_class',unreal.load_class(None,'/Script/UnrealSharp.VRSharpHandPosePreset_C'))
        preset=create('DA_ToolGrip_'+side,unreal.DataAsset,f)
        for n,v in {'EnterBlendSeconds':.1,'ExitBlendSeconds':.15,'AnimationKey':'ToolGrip','UseFingerWeights':True,'UseTriggerBlend':True,'ThumbWeight':.7,'IndexWeight':.25,'GraspWeight':.85,'TriggerIndexWeight':.9}.items():preset.set_editor_property(n,v)
        save(preset);presets[side]=preset

    flashlight=blueprint('BP_VRSharpFlashlight',unreal.load_class(None,'/Script/UnrealSharp.VRSharpFlashlight_C'))
    p=parts(flashlight)
    body=p['Body'];body.set_editor_property('static_mesh',unreal.load_asset('/Engine/BasicShapes/Cylinder'))
    body.set_editor_property('relative_scale3d',unreal.Vector(.07,.07,.22));body.set_mobility(unreal.ComponentMobility.MOVABLE)
    body.set_collision_profile_name('PhysicsActor')
    bi=body.get_editor_property('body_instance');bi.set_editor_property('simulate_physics',True);bi.set_editor_property('override_mass',True);bi.set_editor_property('mass_in_kg_override',.35);body.set_editor_property('body_instance',bi)
    lamp=p['Lamp'];lamp.set_mobility(unreal.ComponentMobility.MOVABLE);lamp.set_editor_property('relative_location',unreal.Vector(0,0,52));lamp.set_editor_property('relative_rotation',unreal.Rotator(pitch=90));lamp.set_editor_property('intensity',5000);lamp.set_editor_property('attenuation_radius',1800);lamp.set_editor_property('visible',False)
    grab=p['Grab']
    for n,v in {'RequireExplicitGrabPose':True,'TriggerPressThreshold':.75,'TriggerReleaseThreshold':.55}.items():grab.set_editor_property(n,v)
    for side,y in [('Left',-23),('Right',23)]:
        pose=p[side+'Grip'];pose.set_editor_property('AnimationPreset',presets[side]);pose.set_editor_property('ExclusiveToOneHand',True)
        pose.set_editor_property('TargetComponent',body)
        pose.set_editor_property('DisableRightHand' if side=='Left' else 'DisableLeftHand',True)
        pose.set_editor_property('relative_location',unreal.Vector(0,y,0))
        pose.set_editor_property('relative_rotation',unreal.Rotator(pitch=0,yaw=0 if side=='Left' else 180,roll=0))
    unreal.BlueprintEditorLibrary.compile_blueprint(flashlight);save(flashlight)

    mode=blueprint('BP_DesktopTestGameMode',unreal.GameModeBase)
    unreal.get_default_object(mode.generated_class()).set_editor_property('default_pawn_class',pawn.generated_class())
    unreal.BlueprintEditorLibrary.compile_blueprint(mode);save(mode)

    xr=unreal.load_asset('/VRSharp/Input/VRSharpInputContext')
    data=xr.get_editor_property('default_key_mappings');mappings=list(data.get_editor_property('mappings'))
    for side in ['Left','Right']:
        a=action('IA_TriggerAnalog_'+side)
        mappings=[m for m in mappings if m.get_editor_property('action')!=a]
        mappings.append(unreal.EnhancedActionKeyMapping(action=a,key=input_key('OculusTouch_'+side+'_Trigger_Axis')))
        bp=unreal.load_asset('/VRSharp/Blueprints/BP_VRSharpHand'+side)
        unreal.get_default_object(bp.generated_class()).set_editor_property('AnalogTriggerAction',a)
        unreal.BlueprintEditorLibrary.compile_blueprint(bp);save(bp)
    xr.set_editor_property('default_key_mappings',unreal.InputMappingContextMappingData(mappings=mappings));save(xr)

print('CREATED',folder,len(rows),'desktop mappings; presets, flashlight, GameMode and analog XR actions saved')
