# VRSharpLab 场景与 VR 测试交付

地图已保存至 `/VRSharp/Maps/VRSharpLab`。以用户提供的实验室参考图为依据，制作了中央空容器、环形平台、双侧楼梯、二层廊道、观察区、机械臂区、控制台、服务器、设备柜、推车和桌面小物件。

## 模块与源文件

- 208 个独立美术零件网格，1803 个美术实例；另有行走辅助坡道和二层转角连接件。
- UE 美术资源：`/VRSharp/Lab/Meshes`、`Materials`、`Textures`；辅助碰撞资源：`/VRSharp/Lab/Collision`。
- Blender 源文件：`ArtSource/VRSharpLab/VRSharpLab_HardSurface.blend`。包含独立零件库和按装配体组织的场景层级。
- FBX 零件、装配表与 UE 运动轴/行程准备数据：`ArtSource/VRSharpLab/Exports`、`lab_manifest.json`、`lab_unreal_parts.json`。清单为有效资源列表，目录里可能保留早期导出文件。
- 抽屉、把手、柜门、显示器、椅子部件、机械臂关节、夹爪、玻璃、容器装甲板和 48 块平台盖板保持独立；装饰螺栓归属于所属零件。

## 重叠面修复

底座承重环和外沿改为一个连续封闭截面，避免同高顶面相交。盖板保留为独立模块。窗框、门框、柜体、格栅等固定零件内部的穿插外壳经过精确布尔清理，保留装配体之间的独立关系，并重新导出、导入 UE。

`Saved/Tests/Lab-Coplanar.json` 的当前结果为零处同向、正面积的共面重叠；该扫描范围是单个源零件内部，不是任意场景实例组合的数学证明。`Lab-Geometry.json` 检查未发现反向封闭壳或完全重复面。UE 实例位置和旋转与清单一致，抽屉带动把手的层级检查通过。

## 当前碰撞

- 地面下有连续承重层，避免地砖接缝成为漏空。
- 固定门框、窗框和主要家具框架采用准确表面碰撞，避免单个凸包封住门洞或桌下空间。
- 玻璃、中央平台、护栏、设备和家具保留实体碰撞。
- 双侧楼梯有仅阻挡 VRPlayer 的隐藏连续坡面；VRHand 忽略辅助坡面，仍触碰可见台阶几何。
- 二层后侧转角补了连接板；玩家出生点在前方通道，避开桌子。
- 旧演示内容移至 `OriginalDemo_Archived`，隐藏并关闭碰撞；原地图备份位于 `/Game/VRSharpLab_Backups/VRSharpLab_BeforeArt_20261017`。

`Lab-VRCollisionChecks.json` 中的 10 项检查通过，包含出生点、双侧楼梯中段、平台坡道、二层转角、玻璃阻挡及辅助坡面对手部的忽略。另行检查门框中心可穿过、立柱能阻挡。未代替 Quest 3 硬件测试；优先测试楼梯、转角、玻璃和平台边缘。

当前新设备按场景碰撞配置，尚未接入抓取、开合或机械臂控制逻辑。复杂表面碰撞用于当前静态框架；将来需要模拟整个家具或设备时，应配套设计简单复合碰撞和物理约束。

## 画面与重建

当前编辑器会话启用了 TAA 预览；原项目配置文件中关闭抗锯齿的设置未修改。PC VR 与 Quest 独立运行的性能尚未做硬件测量。UE 实际渲染位于 `Saved/Tests/LabScreenshots`。

重建美术的脚本顺序：`build_lab_models.py` → `check_lab_coplanar.py` → `union_lab_contacts.py` → 再次检查 → `organize_lab_blender.py`。精确接缝清理只在同一固定零件内部操作，不合并柜门、抽屉等可动部件。UE 脚本通过现有本地 MCP 连接执行；未使用 Computer Use，也未重启编辑器。
