# UE交接：模拟手指输入

分支 cloud/manual-finger-input；AVRSharpHand.SetFingerInput(thumb,index,grasp) 位于 Script/ManagedVRSharp/Core/VRSharpHand.cs。三个轴为0..1；非有限样本保留前值；正在抓取时返回false并不覆盖接触反馈。此入口目前只支持空手，不代表已实现抓握期间扳机姿势混合或完整PC/OpenXR适配器。

UE5.7/UnrealSharp0.1宿主生成Glue并编译。在/VRSharp/Maps/VRSharpDemo测试副本，通过临时UMG三滑条或OpenXR轴值每帧调用每手SetFingerInput；使用该入口时不要同时驱动原Touched/Clicked动画回调，否则同帧后写入者覆盖前者。姿态跟随可使用现有UpdateTracking，抓放使用TryGrab/Release，输入映射需本地建立，未修改原资产。

验收：0/.5/1连续输入平滑驱动对应拇指/食指/三指；越界钳制；NaN/Infinity不污染目标；抓取时调用返回false且接触动画继续；释放后可重新驱动。左右手分别测试，保存蓝图重开确认节点可用。正常旧输入绑定应保持。UE编译、蓝图、PIE和头显均待执行；独立测试仅覆盖数值归一化。
