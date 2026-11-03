# Continuous improvement / 持续推进

Repository: https://github.com/Extreme11111/VRSharp

Requested cadence: every two hours, cloud execution, Asia/Shanghai. The actual schedule and cloud permission validation must be confirmed by the task scheduler; this file is durable working context, not proof that a schedule exists.

## 每次运行

1. 从远端读取当前 main、已有改进 PR、CI 结果和最新人工反馈；先处理阻塞问题，避免同一任务重复开 PR。
2. 选一个可完成、可验证的小增量，写清问题、预期行为与验收依据，再实施。提交到主题分支并创建/更新 PR，更新本文件的进展记录。
3. 至少运行两个独立数学检查。涉及 UnrealSharp/蓝图/资源的修改还需相应的 UE 编译、PIE 或实机验证；没有工具时明确标记未验证，不能用模型推理冒充运行证据。
4. 仅在有实际改动、明确发现、失败或需要用户处理时报告；无变化时不重复发布进度。不要无限重试同一个权限问题。

## 优先级

- P0：不平地面/台阶的物理移动、手部跟随与抓取可用性。已有移动实现尚缺完整的真实通行验证，先补充可复现用例，避免盲目继续扩展。
- P1：抓取目标筛选、接触回弹、无效引用/切换目标/多人或多手状态一致性与回归测试。
- P2：单个 Grabbable 的配置化设计、预设姿势与扳机等动态姿势混合、PC 模拟和 OpenXR 输入兼容性。
- P3：性能测量、插件迁移/打包、可维护文档与示例。联网功能需明确权威端、所有权和同步边界后再做。

实验室的动态光照闪烁尚未解决。此前将局部灯改成硬阴影的方案已按用户要求撤回，不应在无人值守运行中反复应用同一方案或声称问题已解决。

## Cloud prerequisites

A cloud task does not inherit the local editor, Git Credential Manager login, generated Glue or headset. Its own environment must have repository read/write access, Git LFS, .NET 9 and appropriate network access. Permit the GitHub/LFS URLs in the published cloud environment's official network controls; never work around a denial by exporting local credentials. See [OpenAI cloud environments](https://learn.chatgpt.com/docs/environments/cloud-environments).

Run `bash Tools/cloud/check-environment.sh`. For LFS proof, download the repository's tracked assets and use `git lfs fsck`; upload permission requires an actual successful LFS upload in that same cloud identity, not just a successful GitHub API query. GitHub PR/contents access through a connector is not itself a Git/LFS credential.

## Validation available in this repository

`Tools/cloud/check-environment.sh` checks the checkout, tools and local LFS objects. `Tools/cloud/run-checks.sh` runs production-linked standalone math checks. GitHub Actions runs those checks on pull requests and main commits, with an LFS-enabled checkout. It is validation infrastructure, not the two-hour AI work scheduler.

## Progress

- 2026-10-31: Added LFS tracking, cloud environment checks, CI and durable unattended-work guidance. Cloud scheduling/identity tests must be recorded separately when completed.

- 2026-10-31: Local authenticated Git/LFS upload passed (556 objects, about 114 MB). GitHub Actions run 41211244151 passed Linux LFS checkout and both .NET checks. Creating the requested Work Cloud task returned cloudflare_challenge twice; no task ID or two-hour schedule was created. Browser login showed no verification prompt. Do not mark the cloud schedule active until the service can create and read it back. A separate trusted-main Actions job probes its own branch/LFS upload/download permissions; this validates the Actions identity, not a future Codex/Work identity.

- 2026-10-31 verification update: GitHub Actions run 41211738115 succeeded, including cloud-repository-access (branch push, new LFS object upload, independent clone/download and byte comparison; probe branch removed). A separate fresh local clone also completed git lfs pull and git lfs fsck. A later Work Cloud creation request returned a queued client identifier, but no usable cloud conversation ID or schedule has been confirmed. This remains pending; Actions access does not prove the queued Work Cloud identity.

- 2026-11-03: Added Blueprint-callable SetFingerInput for empty-hand analog targets, with production-linked finite/clamped normalization checks (40 combinations). Rejects manual writes while grabbing to preserve existing contact feedback. Both math suites and input checks passed against 729f4a1 in isolated checkout using workspace .NET9. Initial helper create hit a transient GitHub rule timeout; repaired missing file and reran successful build, rather than claiming the intermediate failed run passed. Adapter mappings and animation validation remain local UE handoff; this is not full OpenXR/PC support or grabbed-trigger pose blending. No binaries changed, LFS upload identity remains unverified. Existing PR CI green/no feedback; separate feature PR.

- 2026-11-03: Expanded production-linked input regressions to 56 sample/prior combinations, sequential valid/invalid adapter samples, and both-invalid initial-state recovery. Both math projects and expanded input suite passed at 4dacd9f in isolated cloud checkout; LFS fsck passed, connector identity Extreme11111 confirmed. No gameplay change or new PR. UE bindings/animation/PIE/headset remain untested, and local/Actions LFS checks do not prove session upload authorization.

- 2026-11-03 输入所有权更新（5db78bd）：成功SetFingerInput后，旧Touched/Clicked/Released动画回调不再覆盖外部目标；新增BlueprintCallable ClearFingerInput，在适配器断开、UI关闭或切换回旧输入时调用。空手清零目标；抓取中仅解除外部所有权，保留接触姿势。不主动释放物体，也不自动检测设备断开。此规则取代此前“同帧后写入者覆盖”的接线警告。待UE验收：外部输入后触发全部旧动画事件，目标应保持；Clear后空手张开且旧输入事件恢复；抓取中Clear不改变接触姿势；连续Clear幂等；左右手所有权独立。完整UE编译/PIE/头显与此状态切换路径未验证，数值测试不能替代。
