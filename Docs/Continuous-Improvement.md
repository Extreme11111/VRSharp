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

- 2026-11-02: Implemented per-hand component lookup in Grabbable; hand spring and finger contact now use that lookup rather than the first hand's shared GrabbedComponent cache. Preserved existing public property. Added Docs/LocalUEHandover.md with multi-component, release-order and invalid-component acceptance cases. SDK9.0.320 provisioned under workspace/toolchains (not /tmp); both standalone math projects passed in an isolated remote-branch worktree. These unchanged mathematical suites do not validate the new Unreal dictionary/component path; full gameplay build, PIE, headset and runtime regression remain pending. Connector identity Extreme11111 confirmed; Git branch reads and API writes passed. LFS upload remains separately blocked/unverified; no binary changes. No existing PR feedback required action.
