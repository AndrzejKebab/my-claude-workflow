# Project Memory

## Weather Biome
- `CelestialBeamFog` disabled when using `WeatherCelestialStage` (both occupy Stage=Weather)

## Perf target
- **Steam Deck 60 FPS minimum** — anchors every cost/scope call: `project_deck_60fps_target.md`
- Default presets start Medium/Low — players opt UP, never start lagged: `feedback_conservative_default_quality.md`

## Atmospherics direction
- Volumetric fog samples the same Hillaire 2020 AP 3D LUT clouds sample — no separate fog integrator: `project_volumetric_fog_direction.md`
- NC23 voxelised cloud lighting NOT pursued — unshippable on Deck (2026-04-24); classical Nubis/HZD cone-march stays: `project_nc23_ambient_vs_sun_voxel.md`
- CPU alloc follow-ups (FloatingOrigin, CloudPresetInterpolator) deferred from 2026-04-13: `project_cpu_alloc_followups.md`
- Fog volume noise erosion at froxel-scale doesn't produce powdery edges — needs raymarch-level integration like clouds (followup): `project_fog_noise_erosion_followup.md`
- FogMap painting tool — in-editor brush for the Bauer slide 20 RGB profile encoding (followup): `project_fog_map_painting_followup.md`
- RealtimeGIPass clipmap is LINEAR — outer cascades vary probe density in fixed entries, not extent: `project_realtime_gi_linear_clipmap.md`
- Cloud disocclusion: slow hemi-oct cloudmap on history-reject (WE pattern) — prototype before alternatives: `project_disocclusion_cloudmap_fallback.md`
- Block-mode Pass-1 write-gate landed 2026-05-07 (speculative — reasoned-not-observed; safe to revert): `project_cloud_ghosting_dissipation_followup.md`
- Sky pixels (cloudDepth ≥ farPlane) need direction-only motion vectors + sky-only AABB clip + sky-state upsample gating — HDRP 17 three-stage canon, not in Schneider PDFs: `feedback_skybox_farplane_history_fallback.md`
- Cloud-trace depth uses HDRP projective inverse-z (`saturate(near/depth)`) in [0,1] R16_SFloat — sky=encoded 0, 35km hard cap, NEVER raw `_ProjectionParams.z`: `feedback_cloud_depth_encoding.md`
- Cloud SM is RG16F + 768²/6 mips fixed; G stores integrated optical depth `-log(transmittance)`, receiver applies `belowSlabT = exp(-G)` (analytical-from-ESM was wrong polarity): `feedback_cloud_shadow_below_slab_analytical.md`
- Fog authoring split across 2 components: `FogMaterialVolume` (renamed from `FogVolume`) + `FogMap` (texture-shape with painting tooling); shadow volume is unconditional cascade+cloudSM+terrainSM, no per-volume override (FogShadowVolume deleted 2026-05-04): `feedback_fog_volume_architecture.md`
- God rays = Bauer slide 62; transmittance-weighted shadow accumulation along ray modulates AMBIENT inscatter only — direct stays per-step shadowed (no double-attenuation): `feedback_godrays_canonical.md`
- VolumetricFogCommon globals are plain file-scope (NOT cbuffer) → every compute consumer needs `SetComputeVectorParam`/`FloatParam` per-dispatch — `_VolumetricFog_AlbedoTint` missing-binding caused 11-stage shadow-fog debugging session: `feedback_volumetric_fog_uniforms_compute_audit.md`
- Compute shadow sampling: read URP `Shadows.hlsl` and write explicit-LOD compute-safe variant (Vulkan rejects implicit-LOD `Texture2D.Sample`); rely on URP globals via builder `AllowGlobalState*`/`UseTexture` — never `Shader.GetGlobalTexture` + `SetComputeTextureParam`: `feedback_compute_shadow_sampling_canon.md`
- Terrain SM is camera-anchored RG16F (R=LS depth, G=raw ray length); tier 128–512 (Medium=256); softness derives consumer-side via `HeightfieldShadowSoftness(rayLen, _HFPenumbraScale)`: `feedback_terrain_shadow_camera_anchored.md`
- HeightfieldTerrainController has NO FloatingOriginAnchor — terrain content lives at (goPos + Origin) in Unity-world; any matrix from terrainTf needs Translate(±Origin) compensation: `feedback_heightfield_terrain_no_fo_anchor.md`
- FO event subscription across heightfields↔VT asmdefs uses an upstream bridge (VT can't ref heightfields — circular); bridge in heightfields forwards Origin.Shifted to RWVTManager.ActiveHandles: `feedback_fo_cross_asmdef_bridge.md`
- Fog material volumes = Bauer 2019 slide 44 cluster grid + Drobot 2017 z-binning, **hard 32 cap (structural — single uint tile bitmask)**; unified buffer + 3 accumulators in inner loop, blended Add→Alpha→Particle at exit: `project_fog_volumes_zbin_canon.md`
- "Fog should look like a cloud" = sharp outer SILHOUETTE (Enshrouded sl.20 voxel-SDF), NOT inside-the-volume noise — current detail erosion only carves interior; silhouette is a different feature: `project_fog_volume_cloud_silhouette.md`
- Source 2 (cloud-density-as-fog inside Fog Detail) self-shadow fix = altitude LUT gating cloud SM contribution by sample-point altitude vs cloud band, deferred for V6+: `project_cloud_altitude_lut_for_self_shadow.md`
- Det/Frx density mismatch (Det reads MaterialA.a/dt_slab, Frx reads Hillaire-baked SLV) dissolves naturally when V3 voxel field lands — both consumers share sparse-VT atlas as single density source: `project_v3_voxel_field_resolves_density_mismatch.md`
- V3 voxel work begins with foundational GPU library (voxel primitives, sphere-tracing, sparse-VT, jump-flood SDF, raymarcher) with thorough test coverage BEFORE atmospherics integration: `project_voxel_engine_foundational_work.md`
- Fog volumes lose ~50% density at horizon line — pre-existing physics-correct behaviour (geometric clipping by scene depth + premult-alpha contrast against varying background), not a Phase 4/4.5/5 regression. V3 voxel field naturally improves via dense authored σ_t: `project_fog_volume_horizon_discontinuity_pre_existing.md`
- Atmospheric compositor sources sky directly — Unity skybox pass skipped on game cameras, RenderSettings.skybox MATERIAL retained for IBL/probe bakes. Resolves fog-vs-bright-sky horizon contrast canonically (HDRP volumetric sky+fog + Schneider 2023 sl.49 pattern). Transparent integration deferred: `project_compositor_as_sky_source.md`
- **Enshrouded canon hierarchy**: Krause 2025 (`krause-2025-*.md`) ships; Feller 2024 GPC (`feller-2024-*.md`) is postmortem of unshipped exploration. Where they conflict (e.g. density-erosion vs noise-position-offset), Krause wins: `reference_enshrouded_canon_hierarchy.md`

## Workflow
- Sub-agent briefs must explicitly serialize unity-cli test invocations (5s sleep, never `&` parallel): `feedback_no_parallel_unity_cli_tests_in_agent.md`
- Never use isolated worktrees for sub-agents — they need the live editor on the main checkout: `feedback_no_worktrees.md`
- Dead-simple sequential git: no worktrees, no parallel agents, no proactive branching, prior work just stays on disk: `feedback_git_simple_sequential.md`
- `execute @docs/.../handoff.md` = run it yourself in main session, don't dispatch a sub-agent: `feedback_run_handoffs_yourself.md`
- Commits are checkpoints, not curated history; in `/delegate` mode commits are delegated to a sub-agent to keep diffs out of orchestrator context: `feedback_commits_as_checkpoints.md`
- `/delegate` checkpoint commit agent = `git add -A .` + commit, submodules first then root, NEVER stash/selective-stage/revert (fix baked into delegate SKILL.md): `feedback_delegate_checkpoint_commit.md`
- Pasted images live at `~/.claude/image-cache/<session-uuid>/<N>.png` where N = "image N" index — resolve to absolute paths before citing in shared files: `reference_claude_code_image_cache.md`

## Research / design discipline
- HDRP 17 is the canonical TA reference — cross-check all cloud TA against it: `feedback_hdrp_canonical_ta_reference.md`
- Anchor to canonical research (NC23, HZD, FB, Hillaire, Kühnert); no "adapted" variants: `feedback_research_canonical_anchor.md`
- Never read PDFs from ~/Downloads — all research is `docs/research/*.md`: `feedback_no_pdfs_use_research_md.md`
- `extract_research.py --only=<slug>` clobbers `docs/research/index.md` — restore from git after: `feedback_research_index_clobber.md`
- `extract_research.py --force` overwrites refined `<slug>.md` in place with no backup — destroyed Pass-3-refined lefebvre-hoppe doc; never pass --force without explicit per-slug authorization: `feedback_no_force_extract_research.md`
- Verify research-md slides have BOTH bullets and speaker notes before drawing canon — incomplete exports drop bullets, masking structural facts: `feedback_research_md_check_bullets.md`
- /research Pass 2.5 (`tools/validate_research.py`) catches LaTeX/Mermaid syntax errors marker emits (misplaced `&` in `\begin{split}`, undefined macros like `\ddy`) — runs between vision and refine, refiner brief MUST cite the sidecar: `project_research_pass25_validation.md`
- `extract_research.py` paper-mode skips page renders for pages with 0 images AND <12 vector drawings (pure-prose pages); body text preserved in marker.md, only `pNNN-page.png` is absent — by design, not a bug: `project_extract_research_page_skip.md`
- Never force CPU marker via `CUDA_VISIBLE_DEVICES=""` — CPU inference takes literal hours on long papers; accept the PyMuPDF fall-through and let vision pass recover from page renders: `feedback_no_cpu_marker_fallback.md`
- /research Pass 3 refiner must be dispatched on `claude-opus-4-7[1M]` (`model: opus` + 1M-context note in brief) — overrides the skill's stale `claude-opus-4-6` pin: `feedback_research_refiner_model.md`
- Nubis-lineage primitives (HG, beer-powder, in-scatter, cone-march) = `canonical-replace` not `deviation-cut`; silver-lining = keep-as-art-control: `feedback_nubis_lineage_vs_deviation.md`
- No legacy/backcompat: `feedback_no_legacy.md`
- Disregard Enviro entirely — never cite as reference, target, or coexist-with: `feedback_disregard_enviro.md`
- GPU compression (BCn/ASTC) routes by per-resource graphics format — never a `*Enabled` boolean: `feedback_no_compression_boolean_route_by_format.md`

## URP / render graph
- No scene refs in ScriptableRendererFeatures — use UniversalLightData/UniversalCameraData via frameData: `feedback_no_scene_refs_in_features.md`
- Sky/atmosphere/fog decoupled from CelestialTimeSystem — read sun from frame context; celestial drives only via main light: `feedback_sky_decoupled_from_celestial.md`
- Sky publishes to URP ambient (RenderSettings.ambient*, customReflectionTexture); private globals on top, not instead: `feedback_sky_publishes_urp_ambient.md`
- Extract sun from `UniversalLightData.visibleLights[mainLightIndex]` — never RenderSettings.sun / FindObjectsByType: `feedback_sun_from_universallight_data.md`
- **UNIVERSAL RULE**: `Shader.SetGlobal*` NEVER binds to compute (not a Vulkan quirk — API contract on every platform). Always `cmd.SetCompute*Param` per-dispatch + `cmd.DispatchCompute` (NEVER `cs.Dispatch`): `feedback_compute_bindings_universal_rule.md`
- Compute scalar/vector uniforms: `SetComputeFloat/VectorParam` per-dispatch (corollary of universal rule): `feedback_compute_needs_explicit_params.md`
- `_PhysicalSky_SunColor/SunDirection/MoonColor/MoonDirection` MUST be bound via `SetComputeVectorParam` on every fog/cloud/AP compute kernel: `feedback_physical_sky_compute_bindings.md`
- Scattering/AP LUTs use `R16G16B16A16_SFloat`, not B10G11R11 (rounds to zero): `feedback_lut_precision.md`
- `Blitter.BlitTexture` does NOT update `_BlitTexture_TexelSize`; read `input.positionCS.xy`: `feedback_blitter_texel_size.md`
- Camera-anchored bounded SDFs publish origin from LAST rebake, not current-frame camera: `feedback_sdf_publish_baked_origin.md`
- RenderGraph design (transient vs external, TextureHandle lifecycle, pass sharing, compute, Blitter): `feedback_rendergraph_design.md`
- Shaders via `Shader.Find` + serialized manifest on feature, NOT Resources.Load: `feedback_resources_load_shaders.md`
- Package ScriptableObject assets at fixed Resources paths — `[InitializeOnLoad]` bootstrap, not `[CreateAssetMenu]`: `feedback_auto_bootstrap_assets.md`
- Atmospherics ship manifest = hidden serialized field on render feature, never Resources/: `feedback_manifest_on_feature_not_resources.md`
- URP depth handle selection is config-dependent (forward/deferred × priming on/off); format-detect, never blanket "use activeDepthTexture" — see `docs/unity/rendergraph/depth-targets.md`: `feedback_active_depth_not_depth_texture.md`

## HLSL / shaders
- `#pragma once` in HLSL, not `#ifndef` guards: `feedback_pragma_once.md`
- Better Shaders instanceID: `v.instanceID` + `#if UNITY_ANY_INSTANCING_ENABLED`: `feedback_better_shaders_instanceid.md`
- `Tooltip()` prohibits punctuation: `feedback_tooltip_no_punctuation.md`
- `isnan()` optimized away under fast-math — finite sentinel (1e30) + threshold: `feedback_hlsl_no_isnan_cutout.md`
- Don't re-declare `sampler_LinearClamp` in package headers — URP GlobalSamplers.hlsl already declares it; collision = "Kernel at index (0) is invalid" on Vulkan: `feedback_urp_sampler_linearclamp_collision.md`
- Shader property type conflict requires Unity restart, not cache clear: `feedback_shader_property_conflict.md`

## ShaderGraph
- Never redeclare SG properties in custom HLSL (auto-declared)
- Hybrid Per Instance: `UNITY_ACCESS_HYBRID_INSTANCED_PROP(name, float_type)` — always `float`/`float4x4`, never `half`
- `float4x4` DOTS property: C# columns = HLSL rows (no transpose)
- `SHADERPASS_FORWARD` triggers SH/lightmap/fog — use `SHADERPASS_SPRITEFORWARD` for non-sprite
- `DepthNormalsOnlyPass.hlsl` requires `_NORMAL_DROPOFF_TS` — write custom pass
- `ZTest Off` = Disabled = no depth writes — use `ZTest Always` + `ZWrite On`
- `CorePragmas.Forward` includes `InstancingOptions(RenderingLayer)` — use `CorePragmas.Instanced` for simpler

## Cloud / fog specifics
- CB+TAA cloud variance envelope: trace-sourced at HALF-RES stride (canon §7.1) — never history-sourced, never trace-res stride: `feedback_cb_taa_envelope_per_pixel.md`
- Cloud Pass 1 history sample: bilinear with linear-clamp sampler (canon §6.2) — Catmull-Rom forbidden (border halo from negative lobes; smooth radiance gets no sharpening benefit): `feedback_pass1_history_sample_bilinear.md`
- Cloud Pass 2 upsample: bilinear when 2×2 cloud-depth range <1 km, nearest-depth otherwise (canon §11.2) — never Catmull-Rom: `feedback_catmull_rom_edge_halo.md`
- Cloud blur under camera motion = §9.2 motion-scaled history dilution (Karis 2014 sl.45): `accumulationFactor *= 1 - 0.5*saturate(reprojShift/0.05)` — NOT a sharper kernel: `feedback_motion_scaled_history_dilution.md`
- Shadow/occlusion upsample without TAA: UE bilinear + nearest-depth pick — no bilinear across depth edges, no Catmull-Rom, no stochastic: `feedback_shadow_upsample_sharp_edges.md`
- Cloud TAA problems doc (edge-fade, checkerboard ridging, static-camera scrub lag): `docs/clouds-ta-problematic.md`
- Quality tiers hold raymarch steps constant — vary subres/acc only (fog): `feedback_quality_tiers_fixed_steps.md`
- Cloud accumulation capped at 16 (canon §9 N/(N+1)), not a tier knob — artistic dial is `_TemporalBlendFactor`: `feedback_cloud_accumulation_floor.md`
- Block modes need a deterministic per-pixel cloud-front-vs-hi occlusion gate in composite — CB modes accidentally survive via 2×2-trace-block kernel diversity, block modes don't; gate is load-bearing: `feedback_cloud_block_mode_occlusion_gate.md`
- Visual blend modes are artistic, not a perf tier axis — never `[QualityLocked]`: `feedback_fog_shadow_blend_is_art.md`
- No per-instance tracking in composited SDF shaders — use world-space data: `feedback_no_instance_tracking.md`

## BC compression
- BC encoder tests = PSNR ≥35 dB roundtrip + mean-colour cross-slot isolation; not SSIM: `feedback_bc_test_approach.md`

## Floating Origin / VT
- FO ↔ RWVT: sample via `content = world - Origin` / `worldY = contentY + Origin.y` — wrong sign works at Origin=0 and breaks on teleport: `feedback_fo_world_to_vt_content_space.md`
- VT seams fixed by atlas border padding, never trilinear — Kühnert §4.5.4: `feedback_vt_border_padding.md`
- RWVT tests in the package, not project — package must be independently testable: `feedback_rwvt_tests_in_package.md`
- HeightfieldTerrainController VT layer slots reserved unconditionally — `(mask & (1<<li))` indexing in StampCompositor/fulfiller partition silently corrupts on manifest-timing drift in builds: `feedback_vt_layer_indices_unconditional.md`

## Burst / DOTS
- `[BurstCompile]` only on entry points — helpers auto-compile from Burst context and CAN return structs by value: `feedback_burst_entrypoints_only.md`
- Burst jobs for CPU work; `Schedule().Complete()` for iteration/marshalling: `feedback_burst_jobs_cpu_work.md`
- Burst errors only surface in editor — `unity-cli console --filter error`: `feedback_burst_verification.md`
- Spatial tags = strict per-tag KDTree layers, no match-all/wildcard: `feedback_no_match_all_tags.md`
- Shapes immutable — pass `worldPos` separately: `feedback_shapes_immutable.md`
- `UnityEngine.Object` null check: `if (obj)`, not `== null` (destroyed = non-null): `feedback_unity_object_null_check.md`
- Use NativeCollections for perf-critical systems, not managed: `feedback_native_collections.md`

## Unity.Mathematics
- Pitfalls: `float4x4 *` is componentwise (use `mul`), `log` is natural, PerlinNoise ≠ cnoise, `CorrelatedColorTemperatureToRGB` absent: `feedback_math_pitfalls.md`
- Pass `float3`/`float4x4` directly to Unity APIs; implicit conversion works except `SetVector` (wrap in `float4(...)`): `feedback_implicit_conversion_at_api_boundary.md`
- `using static math` name collisions — rename locals (min/max/lerp become free funcs): `feedback_using_static_name_collisions.md`
- Serialized field types follow code — `float3` fields for modernised code, accept .asset breakage: `feedback_serialized_types_follow_code.md`
- Mesh pipelines: `NativeArray<float3>/<ushort>` end-to-end, never `Vector3[]`/`int[]`: `feedback_no_managed_vertex_arrays.md`

## Tests / debugging
- Script defaults don't override serialized .asset values — check serialized before tuning: `feedback_defaults_vs_serialized.md`
- Don't flag Unity's zero/false default on new serialized fields in existing assets — expected, silent: `feedback_unity_serialization_defaults.md`
- Perceptual artefact fixes (streak/flicker/ghost): verify manually, no mechanism tests: `feedback_perceptual_fixes_verify_manual.md`
- E2E tests in PlayMode assemblies (no EnterPlayMode/ExitPlayMode needed): `feedback_enterplaymode_editmode.md`
- E2E uses the real public API — no mocks, no parallel reimplementation: `feedback_e2e_test_substance.md`
- E2E goes through full lifecycle (JsScriptRequest → fulfillment → __componentInit → __tickComponents) — no RegisterImmediate shortcuts: `feedback_test_real_paths.md`
- Only E2E tests — no trivial assertions on constants/sizes: `feedback_only_e2e_tests.md`
- Don't delete tests during infrastructure migrations — rework them: `feedback_dont_nuke_tests.md`
- Never delete test artifacts (TestScreenshots/, logs): `feedback_dont_delete_test_artifacts.md`
- All visually-asserting tests must save PNGs to TestScreenshots/ even on PASS — manual verification: `feedback_visual_tests_write_screenshots.md`
- Never sleep-poll for test results — run foreground: `feedback_no_sleep_polling.md`
- No concurrent unity-cli tests; full suite only on big refactors / when asked: `feedback_unity_cli_tests.md`
- Sleep 5s between sequential unity-cli test runs: `feedback_sleep_between_tests.md`
- Scope grep/find to Packages/<pkg> or Assets/_Project/Scripts — never project-wide: `feedback_search_scope.md`
- Package tests ship a one-command entry point (run-quick.sh beside tests): `feedback_package_tests_one_command.md`
- No `delayCall` — use long unity-cli `--timeout` (delayCall needs editor focus): `feedback_no_delaycall.md`
- Profile results: per-frame stats only (mean/median/p90/p95/min/max), not total ms: `feedback_profile_per_frame_stats.md`

## Unity editor workflow
- Kill + relaunch Unity after recompiling native .so/.dll: `feedback_relaunch_after_native.md`
- unity-cli fail → read `Editor.log` tail before assuming crash: `feedback_check_editor_log.md`
- Safe-mode popup blocks startup if compile errors exist: `feedback_unity_safe_mode_popup.md`
- Never care about .meta files — Unity auto-manages: `feedback_no_meta_care.md`
- Never edit Unity assets (.asset/.prefab/.unity) directly — prompt user: `feedback_no_edit_unity_assets.md`
- Never chase GUIDs / scene refs / orphan-script cleanup — Unity auto-updates, just flag for manual update: `feedback_no_guid_or_scene_ref_chasing.md`

## QuickJS / unity.js
- JsGameCodegen: `dotnet build` after editing JsGameCodegen~ before relaunching Unity: `feedback_codegen_dotnet_build.md`
- `JS_IsArray` P/Invoke returns 0 for arrays from `JS_GetPropertyStr` — don't gate: `feedback_js_isarray_broken.md`
- **CRITICAL**: `JS_Eval` buffer must be null-terminated: `GetBytes(code + '\0')`, `len = bytes.Length - 1`
- `JS_SetPropertyStr` consumes the value — do NOT free after setting
- `UpdateBurstContext` before any tick — `GetEntityFromIdBurst` silently fails otherwise: `feedback_tick_burst_context.md`
- Use `QJS.ToManagedString`/`QJS.GetStringProperty` — no raw ToCString chains: `feedback_qjs_string_helpers.md`

## MicroSplat
- Never reimplement MicroSplat sampling — call SurfImpl, write harness around it: `feedback_no_reimplement_microsplat.md`
- `_Base.shader` is codegen — edit `MicroSplatHeightfieldModule.cs`: `feedback_microsplat_base_codegen.md`
- URP6P3 shader deleted — only `.surfshader` matters; Better Shaders regenerates: `feedback_urp6p3_deleted.md`

## Windows VM build
- SSH build pipeline, drive mapping, prerequisites, Deck deploy via Proton: `reference_windows_vm_build.md`

## References
- com.bovinelabs.core for Burst-compatible NativeContainers & ISystem patterns (copy, don't depend): `reference_bovinelabs_core.md`
- Two-phase HiZ canon = Aaltonen-Haar SIGGRAPH 2015 pp.51-54 (NOT Wihlidal GDC 2016 — that's GCN compute triangle/cluster culling): `project_two_phase_hiz_canon.md`
- Cuntz & Kolb 2007 FHA-vs-JFA — canonical perf/accuracy comparison for hierarchical 3D DT vs Jump Flooding; relevant to Phase 5 V3 voxel SDF (`Volumetrics*JFA*.compute` + `Phase5_AtlasSDFTraceTest.cs`): `reference_cuntz_kolb_2007_fha_vs_jfa.md`
- Unity GPU BCn via compute + CopyTexture format reinterpret (aras-p/UnityGPUTexCompression): `reference_unity_gpu_bcn_compression.md`
- float2/float3/float4 constructor patterns: `reference_float_constructors.md`
- Kill + relaunch Unity when editor hangs: `reference_unity_relaunch.md`
- unity-cli test defaults to EditMode — run both modes separately: `reference_unity_cli_test_modes.md`
- TDZ bug repro (domain reload → play mode → default not initialized): `reference_tdz_repro.md`
- Atmospherics ship manifest — package-scoped variant whitelist (auto-bootstrapped + auto-populated from #pragma scan): `reference_atmospherics_ship_manifest.md`
- Hot reload re-init design question (should start() re-run on reload?): `project_hot_reload_reinit.md`
- SharpToolsMCP installed at `~/_dev/SharpToolsMCP`, registered as `sharptools` in user-scope `~/.claude.json`; update via `~/_dev/SharpToolsMCP/update.sh`: `reference_sharptools_mcp.md`

## Project state
- Domain reload disabled on play mode transition since project creation: `project_domain_reload_disabled.md`
- PlayMode bridge crash: codegen'd bridges crash on structural changes — blocks full PlayMode suite: `project_playmode_bridge_crash.md`
- RWVT page table → clipped quadtree StructuredBuffer (Kühnert §4.5): `project_chunked_clipmap.md`
- AVT multi-instance VT (Wave 9+): `RWVTHandle` becomes N-instance-capable. "Slab" is project jargon, NOT a VT primitive. `*Slab*` types in VT package = wrong: `project_avt_slabs_framework.md`
