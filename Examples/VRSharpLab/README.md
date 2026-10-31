# VRSharpLab host configuration

`DefaultEngine.ini` is a snapshot of the host project used to develop the bundled laboratory. It includes startup maps, renderer settings, collision profiles/channels, platform settings, and physics substepping. It is a reference, not an automatically loaded plugin configuration.

Review the relevant sections and merge them into your host project. Do not overwrite a project's entire DefaultEngine.ini, especially when it already uses custom collision channels or has different target hardware. Rendering settings here target the desktop lab/PC VR workflow and are not a standalone Quest Android performance preset.
