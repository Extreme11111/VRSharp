# Runtime acceptance / 运行验收

Status: NOT RUN. This checklist is a reproducible host-editor handoff, not runtime evidence. Baseline: UE 5.7, UnrealSharp 0.1, .NET 9. Use a disposable host project with plugin collision profiles merged, generated Glue and both hand Blueprints. Do not change the lab lighting workaround.

## Record for every run

Record commit SHA, UE/UnrealSharp build, map, headset/runtime (or desktop simulation), physics substep settings, actual frame times, collider dimensions and collision profiles. Keep independent math checks, full gameplay build, PIE and headset results in separate columns. Mark missing evidence pending. Capture video and logs for failures; record exact input sequence and transforms before/after. Desktop simulation cannot establish tracked-hand comfort.

## P0 traversal matrix

Use simple blocking collision in a temporary test map. Measure the configured body capsule radius R and document the actual dimensions; do not save temporary fixtures into production maps.

| Case | Fixture / input | Acceptance |
|---|---|---|
| Flat baseline | Walk forward/back/sideways for 10 seconds, stop for 5 | No persistent unintended drift or capsule penetration; record stop displacement |
| Step boundaries | Steps of 0.1R, 0.25R, 0.5R, R; approach head-on and diagonally | Record actual supported height; no claim that every height must pass; blocked steps must not launch or trap player |
| Uneven floor | Alternating low slabs and gaps narrower than capsule diameter | No persistent oscillation, falling through blocking surfaces or unrecoverable wedging |
| Slope transitions | Flat to 10/20/30 degree ramps and back | Record supported slope; stable stop and controllable reversal; blocked slopes must fail safely |
| Wall/ceiling | Walk into wall; physically crouch/stand under low ceiling | No tunneling; head/body collision behavior and recovery recorded independently |
| Tracking movement | Stationary input, room-scale head motion/crouch, then locomotion | Preserve intended camera/body relation; no cumulative offset after returning to origin |

Repeat at actual 30/60/90/120 Hz where supported, with identical substep settings. A frame cap is not proof of achieved timing. Record failures and supported limits rather than adjusting acceptance after the result.

## Hands and contact

Test left and right hands independently and together. On simple convex colliders: shallow contact, deep contact, separation, release/re-grab, grip while target moves out of range, target destruction and switching objects. Capture displayed pose weights and finite/bounded state. Deep contact should open, shallow contact hold, separation reclose; nearby valid targets should remain locally selectable. Include hand inside collision, large objects with distant actor origins, and a non-grabbable object in the forward ray. Repeat at the frame rates above; preserve mirrored-hand setup. Complex collision nearest-point fallback needs its own record and must not be reported as exact nearest-surface selection.

## Results template

| Commit / case | Math | Gameplay build | PIE | Headset | Evidence / failure / next action |
|---|---|---|---|---|---|
| Pending | Pending | Pending | Pending | Pending | No runtime execution recorded |
