# Lumen 稳定性调整（2026-10-23）

已通过 MCP 在当前 VRSharpLab 编辑器应用，并写入 Config/DefaultEngine.ini。无需重启。修改前配置备份：Saved/RepairBackup/Lumen-20261023/DefaultEngine.ini。

原工程关闭了抗锯齿（r.AntiAliasingMethod=0），GI 与反射时域滤波本来已开启。现在选择 TAA（2），TAA.Quality=2；GI 历史累积从 10 调至 16，反射从 12 调至 16，并开启反射 RadianceCache 复用。时域和双边滤波显式保持开启，ClearHistoryEveryFrame=0。没有增加 GI/反射射线数、阴影采样数、渲染分辨率，也没有改变硬件光追模式、灯光强度或材质。

核对本机 UE 5.7 源码后确认 r.PostProcessAAQuality 已不存在，未把该旧变量写入最终配置。原查询返回 0 不能解释为质量为零；实际根因证据是 AntiAliasingMethod=0。

固定 Lab_PreviewCamera，使用原生编辑器截图、32 个截图渲染帧并等待截图任务完成后再切换配置。结果：Saved/Tests/Lumen-Fixed-Before.png、Lumen-Fixed-After.png。已目视核对：金属地面颗粒与细杆锯齿明显减少，仍可能有残余噪点；静态截图不能证明运动中所有闪烁都消失。截图临时延迟设置已恢复至原值 4。

记录了两段 GPU CSV，均值约 13 ms，但期间发生后台限帧和用户视角移动，不能作为严格性能对照，不据此宣称帧率提升或零性能损耗。数据见 Saved/Tests/Lumen-Performance-20261023.json。需要在实际 VR 双眼分辨率下确认预算，以及快速转头时的 TAA 清晰度/拖影。增加历史累积会稍微降低光照变化响应速度；本次仅小幅提高，未采用极大历史长度。

参考：[Epic UE 5.7 Lumen Performance Guide](https://dev.epicgames.com/documentation/en-us/unreal-engine/lumen-performance-guide-for-unreal-engine?application_version=5.7)。参数实际名称、默认值、作用均同时核对本机 UE 5.7 Renderer 源码。

## 继续修复：随时间跳动的亮暗点

固定 SceneCapture2D（960×540），每组预热 40 帧，之后隔帧导出 8 张；对固定地面区域（X=200..649，Y=350..519）计算亮度随时间的标准差。关掉反射、GI、AO 都基本不改善；关掉阴影明显改善。第二轮进一步隔离了 VSM/SMRT 局部灯光软阴影：

- 当前配置基线：平均时域标准差 0.012438（亮度范围 0..1）。
- 关闭自适应射线数：0.012718，没有改善。
- 固定 16 条射线：0.010592，改善有限且增加采样。
- 保留 VSM 阴影，局部灯光 SMRT RayCountLocal=0：0.002248，波动下降约 81.9%。

最终只增加 r.Shadow.Virtual.SMRT.RayCountLocal=0，当前编辑器已生效并写入 DefaultEngine.ini。该项关闭局部灯的随机软半影追踪，仍保留局部灯硬阴影、Lumen GI/反射、AO 和原阴影质量。代价是局部灯阴影边缘变硬；不是提高 Lumen 采样数，也不是关闭阴影。源码核对 UE5.7 VirtualShadowMapArray.cpp 的相关 CVar，以及实际 A/B 图像确认。

首轮 no_ao 排在 no_shadows 之后的结果可能受到状态历史影响，因此不采用它作 AO 结论；第二轮先测试 AO，确认其无显著作用。临时测试捕获 Actor 已删除，临时关掉的 GI、反射、阴影和 AO 均已恢复；后台限帧偏好也已恢复。测试原始图及数据：Saved/Tests/LumenTemporal、LumenTemporalVSM。该数值是固定低分辨率离屏视角的亮度波动，不代表 VR 头显中全部闪烁下降同等比例，也不是 GPU 帧耗测量。

用户实测确认闪烁仍在，已撤回以上硬阴影方案：当前 RayCountLocal 恢复 8，删除配置中的覆盖项。上述离屏测试不足以定位用户实际视口闪烁来源，不作为问题已解决的结论。上一轮 TAA/Lumen 配置保留。
