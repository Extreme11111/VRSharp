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

- 2026-10-31 (Work cloud session, first increment): Created and independently read back enabled automation `6ae60129215c81918d455b846281d49d`, timezone `Asia/Shanghai`, `RRULE:FREQ=HOURLY;INTERVAL=2`, DTSTART `2026-10-31T14:54:33Z` (22:54:33 Shanghai). Scheduler returned no next-run timestamp and no recorded run result; scheduling is enabled, but future worker execution is not yet demonstrated. This supersedes the earlier local scheduler-creation failure, not its historical record.
- Session permission evidence: GitHub connector reports login `Extreme11111`; main read and topic-branch creation succeeded. Command-line public clone, all 556 tracked LFS downloads and `git lfs fsck` succeeded. Git push dry-run and an actual unique LFS object upload attempt failed because this session has no command-line Git credential. Connector write/PR operations are a separate channel; LFS upload authorization remains BLOCKED, and no probe branch was created. Do not infer authorization from Actions. No credentials were exported or checks disabled; this increment changes text only.
- First bounded regression fix: `StepFingerContactTarget` previously propagated NaN weights and interpreted negative-infinite distance as deep penetration. Recover a non-finite weight from its finite counterpart (both invalid => open pose), hold current pose for invalid distance, and retain positive infinity as the existing no-contact sentinel. Normal finite contact behavior and serialized/Blueprint APIs are unchanged.
- Validation: .NET SDK 9.0.320 available in this session after provisioning. Both production-linked standalone projects passed via `Tools/cloud/run-checks.sh`, including new invalid weight/distance/timestep/radius and clamping cases. The added suite fails against unchanged main (`invalid distance holds current pose`) and passes with the fix. `Tools/cloud/check-environment.sh` and `git diff --check` passed. These compile only the standalone mathematical helper, NOT the full gameplay assembly. UE compilation, generated Glue, PIE and headset testing were not available and remain pending.
- Next: inspect this increment's PR checks/review before another PR; prioritize reproducible P0 traversal/hand-follow cases and P1 grab lifecycle issues. For runtime acceptance, test both hands on real colliders at 30/60/90/120 Hz (deep/shallow contact, separation, release/re-grab); confirm finite animation weights and unchanged ordinary contact response. LFS asset writes require cloud Git/LFS credentials supplied through supported environment configuration before attempting binary changes.
