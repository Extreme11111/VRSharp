"""Configure reusable production desktop input on the existing VRSharpPlayer Blueprint."""
import unreal
assert unreal.EditorLevelLibrary.get_game_world() is None
tools=unreal.AssetToolsHelpers.get_asset_tools()
folder='/VRSharp/Input/Desktop'
mapping_names={'Move':'Move','Look':'Look','LeftGrip':'LeftGrip','RightGrip':'RightGrip','LeftTrigger':'LeftTrigger','RightTrigger':'RightTrigger','ActiveTrigger':'Trigger','SwitchHand':'SwitchHand','HandMove':'HandMove','HandRotate':'HandRotate','ToggleGrip':'ToggleGrip','Fingers':'Fingers'}
with unreal.ScopedEditorTransaction('Configure automatic desktop fallback for VRSharpPlayer'):
    actions={}
    for field,suffix in mapping_names.items():
        path=folder+'/IA_'+field
        actions[field]=unreal.load_asset(path) if unreal.EditorAssetLibrary.does_asset_exist(path) else unreal.EditorAssetLibrary.duplicate_asset('/VRSharp/Tests/IA_Desktop'+suffix,path)
        assert unreal.EditorAssetLibrary.save_loaded_asset(actions[field],only_if_is_dirty=False)
    ctxpath=folder+'/IMC_VRSharpDesktop'
    ctx=unreal.load_asset(ctxpath) if unreal.EditorAssetLibrary.does_asset_exist(ctxpath) else tools.create_asset('IMC_VRSharpDesktop',folder,unreal.InputMappingContext,unreal.InputMappingContext_Factory())
    source=unreal.load_asset('/VRSharp/Tests/IMC_VRSharpDesktop')
    rows=[]
    by_source={unreal.load_asset('/VRSharp/Tests/IA_Desktop'+suffix):actions[field] for field,suffix in mapping_names.items()}
    for row in source.get_editor_property('default_key_mappings').get_editor_property('mappings'):
        old=row.get_editor_property('action')
        if old not in by_source:continue
        mods=[]
        for mod in row.get_editor_property('modifiers'):
            # Instanced modifiers must belong to this new context when saved/cooked.
            copied=unreal.new_object(mod.get_class(),outer=ctx)
            if isinstance(mod,unreal.InputModifierNegate):
                pass  # Source negates use the native all-axis defaults.
            elif isinstance(mod,unreal.InputModifierScalar):copied.set_editor_property('scalar',mod.get_editor_property('scalar'))
            elif isinstance(mod,unreal.InputModifierSwizzleAxis):copied.set_editor_property('order',mod.get_editor_property('order'))
            mods.append(copied)
        rows.append(unreal.EnhancedActionKeyMapping(action=by_source[old],key=row.get_editor_property('key'),modifiers=mods))
    ctx.set_editor_property('default_key_mappings',unreal.InputMappingContextMappingData(mappings=rows))
    unreal.EditorAssetLibrary.save_loaded_asset(ctx,only_if_is_dirty=False)
    f=unreal.DataAssetFactory();f.set_editor_property('data_asset_class',unreal.load_class(None,'/Script/UnrealSharp.VRSharpDesktopInputSettings_C'))
    spath=folder+'/DA_DesktopInput'
    settings=unreal.load_asset(spath) if unreal.EditorAssetLibrary.does_asset_exist(spath) else tools.create_asset('DA_DesktopInput',folder,unreal.DataAsset,f)
    settings.set_editor_property('MappingContext',ctx)
    for name,action in actions.items():settings.set_editor_property(name,action)
    unreal.EditorAssetLibrary.save_loaded_asset(settings,only_if_is_dirty=False)
    bp=unreal.load_asset('/VRSharp/Blueprints/BP_VRSharpPlayer')
    sub=unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem);lib=unreal.SubobjectDataBlueprintFunctionLibrary
    matched=set()
    for h in sub.k2_gather_subobject_data_for_blueprint(bp):
        data=lib.get_data(h);o=lib.get_object_for_blueprint(data,bp) or lib.get_object(data)
        if o and o.get_class()==unreal.load_class(None,'/Script/UnrealSharp.VRSharpDesktopInput_C'):
            o.set_editor_property('Settings',settings)
            matched.add(o.get_path_name())
    assert matched,'Default DesktopInput component was not generated on VRSharpPlayer'
    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    unreal.EditorAssetLibrary.save_loaded_asset(bp,only_if_is_dirty=False)
    cdo=unreal.get_default_object(bp.generated_class())
    print('MODE',cdo.get_editor_property('ControlMode'),'COMPONENT',matched)
    print('Configured production PC actions',len(actions),'mappings',len(rows))
