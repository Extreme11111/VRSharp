# VRSharp development instructions

This repository is the VRSharp Unreal Engine plugin, not a complete UE project. Read README.md and the implementation notes under Docs before changing behavior. The current baseline uses UE 5.7, UnrealSharp 0.1 and .NET 9. Do not upgrade the engine/runtime or rewrite the framework as an incidental cleanup.

## Product priorities

Keep physical VR interaction usable first. Prioritize reproducible bugs and regression coverage in physics locomotion, frame-rate-independent tracking, local grab selection and finger contact. Then improve configurable Grabbable behavior, authored/dynamic hand poses, desktop input fallback and a portable plugin setup. Treat sliding grips, multi-hand behavior and networking as explicit features with acceptance criteria; do not add speculative subsystems just to satisfy a vague idea of industry standards.

One Grabbable component remains the primary authoring entry point. Related options belong in its configuration or reusable pose/data assets. Keep helper components internal where practical. Preserve existing Blueprint-visible names, serialized properties and collision profile semantics unless a migration is provided.

## Validation and claims

Use small, coherent changes. Add meaningful tests for changed algorithms, boundary cases and failure paths. Run both standalone math projects with .NET 9. These tests link production math but do not compile the complete UnrealSharp gameplay assembly.

Do not claim UE compilation, PIE behavior, Blueprint correctness, visual quality, frame-rate budgets or headset usability from math tests or source inspection alone. A full gameplay build needs a compatible host UE/UnrealSharp environment and generated Glue. Native assets must be edited and saved with UE/Blender tooling, not fabricated byte edits. If that environment is missing, keep affected engine/asset behavior explicitly pending validation.

Follow the current local API and engine bindings. Preserve readable UTF-8 Chinese. Avoid per-tick allocation and broad reflection workarounds when an existing native binding works. Never introduce a compile-failing intermediate source save into a running UnrealSharp editor.

## Git and scheduled work

At the start of each unattended run, fetch main, inspect open improvement PRs, CI and Docs/Continuous-Improvement.md. Handle failed checks and relevant review feedback before starting another change. Finish one bounded useful increment and record what was tested and what remains unverified. Use a topic branch and a reviewable PR for unattended changes; do not force push main, rewrite history, auto-merge unvalidated changes or overwrite a person's active edits. Avoid duplicate PRs for the same work.

Binary Unreal/Blender/FBX assets use Git LFS. Keep .gitattributes in effect. Never bypass LFS because a credential or network request failed. Do not run history migration, disable checks, or embed credentials in scripts, remotes, logs or commits. Repository permissions, LFS authorization and network access are separate checks.
