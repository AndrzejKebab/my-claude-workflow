# OKF Corpus Tag Taxonomy

Every tag in the `tags` field of a corpus document must be drawn from this list. Tags are kebab-case strings; a document may carry both a specific tag (e.g. `virtual-shadow-maps`) and its parent cluster tag (e.g. `shadow-maps`) when both apply. Tags are chosen for the topics a document substantively covers, not merely mentions.

---

## Shadow Maps

- **shadow-maps** — techniques that render depth from a light's viewpoint and compare against it at shade time; the general shadow-map family.
- **virtual-shadow-maps** — shadow maps that decouple virtual resolution from physical texture allocation via a page table, covering UE5 VSM, Giegl FVSM/QVSM, Olsson clustered shadows, Sakmary RMVSM, and Stephano SVSM.
- **cascaded-shadow-maps** — partition the camera frustum into depth slices, each rendered to a separate shadow map; covers CSM, PSSM, and SDSM variants.
- **adaptive-shadow-maps** — hierarchical or demand-driven shadow maps that refine resolution where the receiver requires it (Fernando 2001, Lefohn 2007 RMSM, Shen 2011 PVSSM).
- **moment-shadow-maps** — shadow maps that store statistical moments of the depth distribution to reconstruct penumbrae without per-sample queries (Peters 2017).
- **alias-free-shadow-maps** — shadow maps that project visible eye-space pixels into light space to eliminate sampling-rate mismatch (Aila & Laine 2004, Johnson 2005 IZB, Sintorn 2008 shadow volumes).
- **soft-shadows** — techniques that approximate area-light penumbrae, including PCSS, SMRT, and analytically filtered variants.
- **deep-shadow-maps** — per-texel transmittance curves recording partial occlusion through volumes (Salvi 2010 AVSM, Lokovic-Veach lineage).
- **horizon-mapping** — precomputed per-texel directional visibility used to self-shadow surface detail without rendering depth from the light: a horizon angle tabulated per azimuthal direction, or any compressed stand-in for that function (Max 1988 origin, Rushmeier 2001 capture, Kautz 2000 per-texel ellipse fit, Onoue 2004 curvature correction, Wang 2003 view-dependent displacement, Fritsch 2025 Fourier compression, Snyder-Nowrouzezahrai 2008 height-field self-shadowing). Distinct from **soft-shadows**, which is area-light penumbrae — a horizon-map paper is usually a *hard*-shadow paper, and most of this family predates or sidesteps shadow maps entirely.
## Volumetrics & Participating Media

- **volumetric-fog** — real-time fog computed in a froxel (frustum-aligned voxel) grid, covering Wronski 2014, Hillaire 2015 Frostbite, Feller 2024, Krause 2025, and Wickedengine variants.
- **volumetric-lighting** — rendering of light shafts, god rays, and in-scattering through participating media in real time (Hoobler 2016, Toth 2009, Yusov 2013 epipolar).
- **participating-media** — the physics and rendering of media that scatter and absorb light (Jarosz 2008, Kajiya 1984, Max 1995 optical models, Premoze 2004, Narasimhan 2004).
- **multiple-scattering** — approximations or analytic models for light that scatters more than once inside a medium (Premoze 2004, Narasimhan 2004, Elek 2012 screen-space, Zhong 2023 MRPNN).
- **volume-sampling** — sampling strategies for ray-marching through volumes (Bowles-Wang volsample, siggraph15-volsampling, fast-flexible notes).
- **volume-rendering** — the pipeline for rendering 3D scalar fields: compositing models, ray casting, slab operations, and artifacts (Max 1995, Kajiya 1984, Knoll 2008, Gobbetti 2008, Ruijters 2021).
- **neural-volumetric-rendering** — volumetric rendering augmented by neural networks (Zhong 2023 MRPNN, siggraph23-mrpnn).

## Atmosphere, Sky & Clouds

- **atmospheric-scattering** — physically-based single- and multi-scattering models for planetary atmospheres (Nishita 1993, Bruneton 2008 precomputed, Hillaire 2020, Wilkie 2021 fitted).
- **sky-models** — analytic or precomputed sky dome radiance models (Preetham 1999, Hosek-Wilkie 2012, Wilkie 2013, Kol 2012, Maquignaz 2024, Kider 2014, Suzuki 2023).
- **clouds** — rendering and simulation of clouds at real-time rates, including Nubis (Schneider), HZD, Bauer RDR2, Hillaire Frostbite, Bouthors, and Hogfeldt clouds.
- **cloud-simulation** — physical simulation of cloud dynamics: advection–condensation, VOF interface reconstruction, and meteorological coupling (Margolin 1997, Weick-Zhou 2021 FC6, simulating-tropical-weather).
- **weather-simulation** — numerical weather prediction and physics-based atmospheric dynamics coupled to a rendering pipeline (Weick-Zhou 2021 FC6, Schneider 2022 Nubis evolved/superstorms).

## Fluid Simulation

- **fluid-simulation** — grid-based Navier-Stokes fluid solvers for graphics: Stam Stable Fluids, Foster-Metaxas MAC, Harris GPU Gems, Jin 2015 CSL, Fais 2011 SCC, Chen 2025 DMD, Lyu 2021 coupling.
- **semi-lagrangian-advection** — the back-tracing advection scheme used in Stam-style solvers; also its conservative variants (Jin 2015, Hirasawa 2021).
- **fluid-solid-coupling** — algorithms for two-way or one-way interaction between fluids and rigid/deformable solids (Batty 2007, Lyu 2021, Müller 2009 surface tracking).
- **fluid-surface-tracking** — methods for evolving free surfaces in fluid simulations: marker chains, level sets, VOF (Müller 2009, Foster-Metaxas 1996, Margolin 1997).
## Cellular Automata & Falling Sand

- **falling-sand** — particle simulation games and engines based on per-pixel update rules for granular materials (Purho Noita 2019, Bittker Sandspiel, Jackson, Winter, Dyar, Marf, Shiffman, nivmiz, jasondiesel, zicore).
- **cellular-automata** — discrete computational models where cells update from neighborhood state; the theoretical basis for falling-sand and particle sim (Fates 2014, Devlin-Schuster 2020, Conway).
- **granular-simulation** — simulation of sand, powder, and granular materials including probabilistic and physically-based CA variants (Devlin-Schuster 2020, repo-* engines).

## Voxels & Sparse Data Structures

- **voxels** — 3D grid-based representations of geometry or fields; the broad voxel cluster.
- **sparse-voxel-octrees** — hierarchical, memory-efficient voxel representations using octrees (Laine-Karras 2010 SVO, Crassin 2009 GigaVoxels, Crassin 2011 thesis/GigaVoxels, Gobbetti 2005 Far Voxels, Knoll 2008 survey, Molenaar 2024 SVDAG).
- **voxel-cone-tracing** — indirect illumination computed by tracing cones through a sparse voxel mip-hierarchy (Crassin 2011 VCT).
- **voxelization** — converting meshes or scenes to voxel grids on the GPU (Schwarz-Seidel 2010, Eisemann-Decoret 2008, Young 2017 multilevel).
- **voxel-traversal** — algorithms for stepping through voxel grids along rays (Amanatides-Woo 1987, Braley 2010 prediction buffer, Frisken-Perry 2002).
- **voxel-gi** — global illumination computed from a voxel scene representation (Crassin 2011 VCT, Ulschmid 2026 NAADF, Fang 2025 Aokana).
- **signed-distance-fields** — scalar fields encoding distance to a surface, used for rendering, collision, and soft-shadow approximation (Hart 1995, Keinert 2014, Green 2007, Cuntz-Kolb 2007, Soderlund 2022).
- **sphere-tracing** — ray-marching through a signed-distance field by advancing the ray by the field value at each step (Hart 1995, Keinert 2014).

## Global Illumination & Radiance Caching

- **global-illumination** — algorithms that account for indirect light bounces (Veach 1997 path sampling, Wright 2021/2022 Lumen, Kolesik 2024 Enshrouded GI, siggraph2022-lumen).
- **radiance-caching** — storing and reusing radiance probes or records at surface or world-space positions to accelerate indirect illumination (Wright 2021, Tatzgern 2024, radiance-caching-on-surface).
- **surfel-gi** — global illumination using surface elements (surfels) as radiance caches covering a scene (SEED 2021, seed-siggraph21).
- **radiance-cascades** — a hierarchical interval-based probe structure for real-time indirect illumination (Freeman 2025 holographic cascades, Osborne-Sannikov 2024 non-LTE).
- **lumen** — Unreal Engine's dynamic global illumination system based on surface caching, SDFs, and radiance caching (Wright 2021/2022, siggraph2022-lumen).
- **restir** — reservoir-based spatiotemporal importance resampling for real-time light sampling (Lin 2021 Volume ReSTIR).

## Temporal Methods

- **temporal-anti-aliasing** — temporal accumulation and filtering to reduce aliasing using per-pixel history (Karis 2014, Jimenez 2017 CoD, de Carpentier 2017 Decima, Scherzer 2010/2012).
- **temporal-upsampling** — using temporal history frames to reconstruct higher resolution output (Jimenez 2017, cbr-ta-upsampling).
- **reprojection** — warping a previous frame's pixel data into the current frame using motion vectors or depth reprojection (Nehab 2007 reverse reprojection, Scherzer 2010/2012).
- **temporal-coherence** — exploiting frame-to-frame coherence in rendering to amortise cost (Scherzer 2010/2012 survey, Yang 2009 amortised supersampling, Mueller 2021 TASA).

## Culling & Visibility

- **frustum-culling** — testing objects against the camera frustum planes to skip invisible work (view-frustum-culling, frustum-culling-turning-the-crank, frustum-culling-in-stingray, practical-dynamic-visibility-for-games).
- **occlusion-culling** — testing objects against a depth representation to skip work hidden behind other geometry (Hasselgren 2016 masked SW occlusion, Brands 2024, Vale 2017 HZD visibility, practical-dynamic-visibility).
- **hierarchical-z-buffer** — a mip-hierarchy of depth values used for fast occlusion and shadow tests (Hasselgren 2016, Aaltonen-Haar 2015, Sintorn 2008).
- **gpu-driven-rendering** — pipelines where the GPU generates draw calls and performs culling without CPU intervention (Aaltonen-Haar 2015, Wihlidal 2016, Drobot 2017, drazhevskyi, Lazarek 2025).

## Virtual Texturing & Terrain

- **virtual-texturing** — decoupling a logical high-resolution texture from physical GPU memory via a page table (Barrett 2008 SVT, Mittring 2008 advanced VT, Chen 2015 adaptive VT, Kraus-Ertl 2002).
- **clipmaps** — a mip-hierarchy that keeps only the high-resolution region near the viewer resident, toroidal-updating as the camera moves (Tanner 1998, Losasso-Hoppe 2004 geometry clipmaps).
- **terrain-rendering** — GPU techniques for rendering large-scale terrain: clipmaps, geometry clipmaps, LOD (Losasso-Hoppe 2004, Widmark 2012 BF3, Kuehnert 2022, Keb 2023 Frostbite).
- **procedural-generation** — algorithmic creation of geometry or content at runtime (Zirr-Kaplanyan 2016 procedural multiscale, van Muijden 2017 HZD vegetation placement, Keb 2023 Frostbite terrain, Sanders 2017 HZD vegetation).

## Procedural Noise Functions

- **procedural-noise** — parent cluster tag for coherent pseudo-random noise functions used as a primitive for procedural content (Perlin 2002 Noise Hardware, Gustavson 2005 simplex noise demystified, KdotJPG 2022 Perlin Problem series).
- **gradient-noise** — noise built by interpolating pseudo-random gradients assigned to a lattice, the family covering classic Perlin noise, Simplex, and OpenSimplex variants (Perlin 2002, Gustavson 2005, KdotJPG 2022).
- **perlin-noise** — the original square/hypercubic-lattice gradient noise and its axis-alignment artifacts (Perlin 2002 Noise Hardware, KdotJPG 2022 square noise).
- **simplex-noise** — gradient noise evaluated on a simplectic (triangular/tetrahedral) lattice instead of a hypercubic one, including Simplex, OpenSimplex, OpenSimplex2, and OpenSimplex2S (Gustavson 2005, KdotJPG 2022).
- **noise-hardware** — dedicated silicon or GPU-native evaluation of noise functions, and the design constraints that come with fixing an algorithm in hardware (Perlin 2002).
- **domain-rotation** — transforming input coordinates (typically via an added and rescaled dimension) before sampling a noise function, to cancel a lattice's visible directional bias (KdotJPG 2022 domain rotation).

## Denoising & Filtering

- **denoising** — filtering noisy rendered images using temporal or spatial filters (Schied 2017 SVGF, Schied 2018 ASVGF, Mueller 2021 TASA).
- **spatiotemporal-filtering** — filters that combine spatial neighborhood samples with temporal history (Schied 2017 SVGF, Schied 2018 ASVGF).

## Perceptual Quality & Just-Noticeable-Difference

- **perceptual-quality** — objective metrics that predict human-perceived visual quality of rendered images and 3D meshes, validated against subjective opinion scores (Lavoué-Cheng-Basu 2013 mesh MVQ, Cheng-Boulanger 2005/2006 JND, Xie 2023 multimodal JND).
- **just-noticeable-difference** — modeling the JND threshold below which a visual change is imperceptible, via Weber's-law lookup or learned multimodal predictors, used to bound distortion or allocate resources (Cheng-Boulanger 2005/2006, Xie 2023 hmJND-Net).

## Light Transport Theory

- **light-transport** — the mathematical foundation of light propagation: rendering equation, path integrals, Monte Carlo (Veach 1997, Jarosz 2008, Kajiya 1984).
- **monte-carlo-rendering** — stochastic integration of the rendering equation via path tracing and importance sampling (Veach 1997, Jarosz 2008, Lin 2021 ReSTIR).
- **physically-based-rendering** — rendering grounded in energy-conserving BRDFs and physical light units (Hoffman 2015, tatarchuk-2015-applied-graphics-research).

## Lens Effects & Compositing

- **lens-flare** — optical artifacts of camera lenses: physically-based models and real-time rendering (Hullin 2011, Keshmirian 2008, Lee 2013, Tang 2011, herur-raman-2024).
- **sparkle** — specular highlight glints from multi-flake surfaces (Wang-Bowles 2016, Bowles 2015, siggraph15-sparkly, Fan-Baranoski 2024 survey, report-sparkles-cs-2024).
- **compositing** — alpha compositing and the over operator for combining rendered layers (Porter-Duff 1984).

## GPU Architecture & Compute

- **gpu-architecture** — GPU hardware design and pipeline, shader model capabilities, and compute models (Lefohn 2006 Glift, Wihlidal 2016, gdc24-arm-mobile-raytracing).
- **gpu-data-structures** — generic programmable data structures on GPU: sparse arrays, virtual pages, indirect buffers (Lefohn 2006 Glift, Lefebvre-Dachsbacher 2007 TileTrees, Lefebvre-Hoppe 2006 spatial hashing).
- **spatial-hashing** — mapping spatial coordinates to hash table entries for fast nearest-neighbor and point queries (Lefebvre-Hoppe 2006 perfect spatial hashing).
- **mesh-shaders** — the meshlet-based GPU rendering pipeline replacing fixed vertex/geometry stages, used for GPU-driven culling and VSM (Sakmary 2025, Lazarek 2025).
- **graphics-api-design** — low-level graphics API and driver design: pipeline-state-object (PSO) surface, resource binding models, command buffer submission, and GPU synchronization/barrier models across DirectX 12, Vulkan, and Metal (aaltonen-2025 no-graphics-api, aaltonen-2026 reducing-api-complexity).

## Game Engine Architecture

- **game-engine-architecture** — parent cluster tag for the high-level structural design of a game engine or app framework itself — its core abstractions, module boundaries, and the tradeoffs behind them — as distinct from any single rendering/simulation technique it ships (Bevy 0.19 release notes, Anderson 2026 Bevy sixth birthday).
- **entity-component-system** — a data-oriented architecture that separates entity identity, component data storage, and system logic operating over component queries, instead of object-oriented inheritance hierarchies (Bevy ECS).
- **scene-authoring** — declarative formats and workflows for defining and composing entity/component hierarchies as reusable, templated scene data rather than imperative spawn code (Bevy BSN / Bevy Scene Notation).

## Floating-Point Arithmetic & Numerical Precision

- **floating-point-arithmetic** — the IEEE 754 number system, rounding, and error analysis (Dekker 1971, Anderson 1967, Tomasulo 1967, Gao-Baidoo 2026).
- **extended-precision** — double-word and quad-precision representations that extend GPU float precision without hardware changes (Dekker 1971, Thall 2009, Muller-Rideau 2022, Gao-Baidoo 2026).
- **large-world-coordinates** — techniques for maintaining floating-point precision in game worlds spanning tens of kilometres (dekeersmaecker-2024 UE5.4, Thall 2009 df64).
- **numerical-methods** — discretization, iterative solvers, and convergence in simulation and rendering contexts.

## Production / Game Rendering

- **production-rendering** — retrospectives and case studies from shipped titles (Bauer 2019 RDR2, Schneider Nubis series, Gjoel 2016 Inside, el-mansouri 2016 R6, tatarchuk 2013 Destiny, de-carpentier 2017 Decima, tatarchuk-2015, Lazarek 2025 Doom).
- **mobile-rendering** — rendering techniques targeting mobile GPUs: tile-based architectures, bandwidth limits, hybrid ray tracing (gdc24-arm-mobile-raytracing).
- **instanced-rendering** — submitting many instances of the same mesh in a single draw call for CPU/GPU efficiency (Persson 2012 merge-instancing, aaltonen-haar-2015-gpu-driven).

## Geometry Processing & Discrete Differential Geometry

- **geometry-processing** — algorithms operating on triangle meshes and other surface representations as the object of study rather than as render input: parameterization, remeshing, smoothing, field design, discrete operators (Liu 2026 Phong-Rodrigues, Knöppel 2013, Stein 2020).
- **discrete-differential-geometry** — discretizations of differential-geometric structure on meshes: connections, covariant derivatives, holonomy and curvature, Hodge/connection Laplacians, DEC and Whitney/Crouzeix-Raviart element families (Liu 2026, Hirani 2003 DEC, de Goes 2016 course).
- **vector-fields** — representation, interpolation, smoothing and singularity handling of tangent vector-, frame- and N-RoSy fields on surfaces (Liu 2026, Vaxman 2016 survey, Knöppel 2013, Azencot 2015 operator approach).
- **finite-element-method** — basis-function discretizations that assemble mass and stiffness matrices per element by quadrature, and the energies built from them (Liu 2026, Stein 2020, Gatica 2014).

## CS Theory & Systems

- **memory-allocation** — dynamic storage allocation algorithms: fragmentation, free-list strategies, garbage collection (Johnstone-Wilson 1998, Wilson 1995).
- **concurrent-systems** — lock-free and wait-free synchronization, distributed consistency, and hardware ordering (Herlihy 1991, Lamport 1976/1978/1984).
- **compiler-theory** — code generation, SSA form, and compiler optimisations (Braun 2013, Millikin v8, Dybvig 1990, Knuth 1974, Ansari 2016, Vattani 2015).
- **data-structures-theory** — foundational data structure papers: persistent search trees, OBDDs, chazelle filtering search (Bryant 1986, Sarnak-Tarjan 1986, Chazelle 1986).
- **signal-processing** — audio and digital signal processing techniques applied to synthesis or rendering (Brandt 2001 hard sync aliasing, Williams 1983 mipmaps).

## Gameplay AI

- **gameplay-ai** — parent cluster tag for game-specific NPC decision-making and sensory systems, distinct from general AI/ML research (Souza 2020 Behavior Trees).
- **behavior-trees** — hierarchical, node-based AI decision structures that select and run child tasks/composites by reading shared state from a Blackboard (Souza 2020).
- **environment-query-system** — Unreal Engine's EQS: generates a set of candidate points or actors and scores them against context-aware tests to drive spatial AI decisions (Souza 2020).
- **ai-perception** — simulated sensory systems (sight, hearing, and other senses) that feed stimulus events into an NPC's decision-making layer (Souza 2020).

## Pathfinding & Navigation

- **pathfinding** — parent cluster tag for algorithms that compute a route through an environment for a game agent or robot, distinct from the decision-making layer that decides where to go (Cui-Harabor-Grastien 2017 Polyanya).
- **navigation-mesh** — pathfinding over a navmesh: a runtime representation of traversable space as a set of convex (or otherwise structured) polygons, as opposed to a fixed-resolution grid (Cui-Harabor-Grastien 2017 Polyanya).

## Character Animation & Rigging

- **character-animation** — parent cluster tag for techniques that drive character motion, deformation, and expression, covering both runtime animation (locomotion, blending) and the rigs that make it possible (Clavet 2016 motion matching, Pagoria 2026 facial rigs, Cooper-VanAllen 2026, Nilsson-Cooper 2026, Falconer 2026 crowds).
- **control-rig** — Unreal Engine's node-graph rig-evaluation system for building forward/inverse-kinematics and deformation logic as a reusable, inspectable graph rather than hand-scripted animation (Pagoria 2026, Cooper-VanAllen 2026, Nilsson-Cooper 2026).
- **procedural-rigging** — generating skeleton hierarchies and rig structure algorithmically from a node graph or parametric description rather than hand-placing joints (Cooper-VanAllen 2026 Dataflow-to-Control-Rig).
- **facial-rigging** — deformation systems, morph targets, and blend-shape pipelines purpose-built for expressive facial animation (Pagoria 2026).
- **cloth-simulation** — garment authoring, physical simulation, and import pipelines for real-time simulated clothing on characters (Raichstat-Deloe 2026 CLO/Marvelous Designer to Dataflow cloth assets).
- **character-crowd-rendering** — rendering large populations of visually diverse, skinned characters at scale via per-instance attribute variation rather than a unique draw per character (Falconer 2026 MetaHuman crowds).
- **motion-matching** — a brute-force per-frame nearest-pose search over a flat motion-capture database, driven by a cost function over current pose and future trajectory, replacing hand-authored state machines and blend trees for locomotion (Clavet 2016).

## Audio & Procedural Music Systems

- **procedural-audio** — parent cluster tag for sound generated or arranged algorithmically at runtime from gameplay state, rather than played back from fixed audio files (Dörfler 2023, Hart 2025).
- **metasounds** — Unreal Engine's node-graph real-time audio synthesis and DSP system, used to build custom sound-generation, mixing, and signal-processing graphs (Dörfler 2023, Hart 2025, O'Neal 2026 Audio Insights signal-flow debugging).
- **generative-music** — algorithmic composition techniques — layered stem randomization, procedural chord/melody generation — that produce indefinite, non-repeating musical output (Dörfler 2023, Hart 2025).
- **audio-scheduling** — sample-accurate, tempo-quantized scheduling of audio events against a musical clock, so triggered sounds land on the beat/bar grid instead of playing immediately (Unreal's Quartz Clock) (Dörfler 2023, Hart 2025).
- **audio-profiling** — tools and workflows for diagnosing real-time audio-mix issues: voice counts, virtualization/loop culling, modulation state, submix loudness (O'Neal 2026).

## Performance Profiling & Frame Pacing

- **performance-profiling** — parent cluster tag for measuring and diagnosing runtime performance bottlenecks with engine-native or platform profiling tools (Epic 2026 Frame Timing & Latency, Oztalay 2026 60fps, Arnbjörnsson-Oztalay 2026 Profiling with Pirates, Neelakantan 2026 mobile optimization).
- **frame-pacing** — the synchronization contract between the Game/Render/RHI/GPU pipeline stages, and the trade-off between input latency and hitch resiliency it creates (Epic 2026 Frame Timing & Latency).
- **input-latency** — the delay chain from input sampling to displayed photon, and the cvars/techniques used to measure and reduce it (Epic 2026 Frame Timing & Latency).
- **cpu-profiling** — measuring and reducing CPU-side bottlenecks: game-thread cost, UObject counts, garbage collection, and Slate/UI overhead (Arnbjörnsson-Oztalay 2026, Oztalay 2026).

## Game Design Theory & Process

- **game-design-theory** — parent cluster tag for formal frameworks and analytical models that treat game design itself as an object of study, distinct from techniques for building or shipping a game (Hunicke-LeBlanc-Zubek 2004 MDA, Costikyan 2002 critical vocabulary, Meier 2010 psychology of game design, Blow 2007 Design Reboot).
- **design-process** — practices, documentation formats, and workflows for the day-to-day practice of designing games: idea generation, communicating intent to a team, iterating on a design (Librande 2010 one-page designs, Tyroller 2025 Steam hook).
- **player-psychology** — design reasoning grounded in how players perceive fairness, difficulty, and drama rather than strict mathematical or historical accuracy (Meier 2010 psychology of game design).
- **design-criticism** — critical or philosophical argument about what makes game design meaningful versus exploitative, and critiques of inherited industry convention (Blow 2007 Design Reboot, Costikyan 2002 critical vocabulary).

## Point Cloud & Photogrammetry Pipelines

- **photogrammetry** — reconstructing 3D geometry and texture from photographs via structure-from-motion / multi-view stereo capture (Andersson 2025 cave capture, Merchant 2026 as one of the source formats it streams).
- **point-cloud-streaming** — out-of-core streaming and level-of-detail selection for massive point-cloud datasets, e.g. Potree/Entwine-style octrees, inside a real-time engine (Merchant 2026).
- **digital-twin** — large-scale, real-world-accurate 3D reconstructions of physical spaces built for real-time engine visualization (Merchant 2026 campus-scale digital twin).
