#!/usr/bin/env python3
"""Extract text and images from PDF/PPTX research documents into markdown."""

import datetime
import hashlib
import io
import os
import secrets
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

import fitz  # PyMuPDF
from PIL import Image
from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE_TYPE

from openocr_engine import ocr_image as _ocr_image_path
import marker_extract

# Marker prepass routing (decided in main()).
# Paper-PDFs that classify as text-rich go through marker for body text +
# real markdown structure (headings, lists, tables, LaTeX equations) instead
# of PyMuPDF's flat span-walker. Slide-deck PDFs and scanned PDFs are
# unchanged.
_MARKER_ENABLED = True  # --no-marker turns this off
_MARKER_USE_LLM = True  # --no-llm runs marker locally without Gemini
_MARKER_FORCE = False  # set when --force is passed; busts marker cache


def _ocr_image_bytes(png_bytes: bytes) -> str:
    """OCR a PNG byte buffer via the OpenOCR singleton."""
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        tmp.write(png_bytes)
        tmp.flush()
        path = tmp.name
    try:
        return _ocr_image_path(path)
    finally:
        try:
            os.unlink(path)
        except OSError:
            pass

# The extracted markdown corpus lives at a single hardcoded global location,
# independent of cwd / which project invoked /research. The skill scripts ship
# at ~/.claude/skills/research/tools/ but always write the corpus to
# /mnt/archive4/PAPERS/Prepared/.
OUTPUT_DIR = Path("/mnt/archive4/PAPERS/Prepared")
PROJECT_ROOT = OUTPUT_DIR  # display base for relative_to() in log output
ASSETS_DIR = OUTPUT_DIR / "assets"

SOURCES = [
    {
        "path": "/mnt/archive4/PAPERS/preetham-1999-analytic-daylight.pdf",
        "slug": "preetham-1999-analytic-daylight",
        "type": "pdf",
        "title": "A Practical Analytic Model for Daylight — Preetham, Shirley, Smits 1999 (SIGGRAPH 1999)",
    },
    {
        "path": "/home/midori/Downloads/3484514.pdf",
        "slug": "muller-rideau-2022-double-word-arithmetic",
        "type": "pdf",
        "title": "Formalization of Double-Word Arithmetic, and Comments on \"Tight and Rigorous Error Bounds for Basic Building Blocks of Double-Word Arithmetic\" — Muller & Rideau 2022 (ACM TOMS 48:1 art.9)",
    },
    {
        "path": "/home/midori/Downloads/dekker1971.pdf",
        "slug": "dekker-1971-double-length-arithmetic",
        "type": "pdf",
        "title": "A Floating-Point Technique for Extending the Available Precision — T. J. Dekker 1971 (Numer. Math. 18, 224-242)",
    },
    {
        "path": "/mnt/archive4/PAPERS/engel-2007-cascaded-shadow-maps.pdf",
        "slug": "engel-2007-cascaded-shadow-maps",
        "type": "pdf",
        "title": "Cascaded Shadow Maps — Wolfgang Engel 2007 (ShaderX5 §4.1, Rockstar San Diego)",
    },
    {
        "path": "/home/midori/Downloads/2602.19452v1.pdf",
        "slug": "gao-baidoo-2026-compensated-summation",
        "type": "pdf",
        "title": "Dekker's Floating Point Number System and Compensated Summation Algorithms — Gao & Baidoo 2026",
    },
    {
        "path": "/home/midori/Downloads/df64_qf128.pdf",
        "slug": "thall-2009-extended-precision-gpu",
        "type": "pdf",
        "title": "Extended-Precision Floating-Point Numbers for GPU Computation (df64 / qf128) — Andrew Thall 2009 (Alma College)",
    },
    {
        "path": "/home/midori/Downloads/foster-metaxas-gmip96.pdf",
        "slug": "foster-metaxas-1996-realistic-liquid-animation",
        "type": "pdf",
        "title": "Realistic Animation of Liquids — Foster & Metaxas 1996",
    },
    # PPTX
    {
        "path": "/mnt/archive4/Downloads/slides_public_release.pptx",
        "slug": "bauer-2019-rdr2-atmospherics",
        "type": "pptx",
        "title": "Creating the Atmospheric World of RDR2 — Bauer 2019",
    },
    {
        "path": "/mnt/archive4/Downloads/Frostbite PB and unified volumetrics.pptx",
        "slug": "frostbite-pb-volumetrics",
        "type": "pptx",
        "title": "Frostbite PB and Unified Volumetrics",
    },
    {
        "path": "/mnt/archive4/Downloads/TemporalAA.pptx",
        "slug": "karis-2014-temporal-aa",
        "type": "pptx",
        "title": "High-Quality Temporal Supersampling — Karis 2014",
    },
    # PDF
    {
        "path": "/home/midori/Downloads/Nubis Cubed (Advances 2023).pdf",
        "slug": "nubis-cubed-2023",
        "type": "pdf",
        "title": "Nubis Cubed (Advances 2023)",
    },
    {
        "path": "/home/midori/Downloads/Nubis - Authoring Realtime Volumetric Cloudscapes with the Decima Engine - Final .pdf",
        "slug": "nubis-decima",
        "type": "pdf",
        "title": "Nubis - Authoring Realtime Volumetric Cloudscapes with Decima Engine",
    },
    {
        "path": "/home/midori/Downloads/s2016-pbs-frostbite-sky-clouds-new.pdf",
        "slug": "s2016-frostbite-sky-clouds",
        "type": "pdf",
        "title": "Physically Based Sky, Atmosphere and Cloud Rendering in Frostbite (SIGGRAPH 2016)",
    },
    {
        "path": "/home/midori/Downloads/The Real-time Volumetric Cloudscapes of Horizon - Zero Dawn - ARTR.pdf",
        "slug": "horizon-zd-clouds",
        "type": "pdf",
        "title": "The Real-time Volumetric Cloudscapes of Horizon Zero Dawn",
    },
    # DUPLICATE SKIPPED: The-Real-time-Volumetric-Cloudscapes-of-Horizon-Zero-Dawn.pdf
    # (identical MD5: 5f084c030aa9c2912110259d2851033c)
    {
        "path": "/home/midori/Downloads/egsr2020.pdf",
        "slug": "egsr2020",
        "type": "pdf",
        "title": "EGSR 2020",
    },
    {
        "path": "/home/midori/Downloads/Kuhi_informaatika_2018.pdf",
        "slug": "kuhi-2018",
        "type": "pdf",
        "title": "Kuhi Informaatika 2018",
    },
    {
        "path": "/home/midori/Downloads/Revision 2013 - Real-time Volumetric Rendering Course Notes.pdf",
        "slug": "revision-2013-volumetric",
        "type": "pdf",
        "title": "Revision 2013 - Real-time Volumetric Rendering Course Notes",
    },
    {
        "path": "/home/midori/Downloads/oz_volumes.pdf",
        "slug": "oz-volumes",
        "type": "pdf",
        "title": "Oz Volumes",
    },
    {
        "path": "/home/midori/Downloads/suppl.pdf",
        "slug": "siggraph23-mrpnn-suppl",
        "type": "pdf",
        "title": "Deep Real-time Volumetric Rendering Using Multi-feature Fusion — Supplementary (SIGGRAPH 2023)",
    },
    {
        "path": "/mnt/archive4/Downloads/siggraph15_volsampling.pptx",
        "slug": "siggraph15-volsampling",
        "type": "pptx",
        "title": "A Novel Sampling Algorithm for Fast and Stable Real-Time Volume Rendering (SIGGRAPH 2015)",
    },
    {
        "path": "/mnt/archive4/Downloads/DecimaSiggraph2017-final.pptx",
        "slug": "decima-siggraph2017",
        "type": "pptx",
        "title": "Advances in Lighting and AA — Decima Engine (SIGGRAPH 2017)",
    },
    {
        "path": "/home/midori/Downloads/seed-siggraph21-surfel-gi.pdf",
        "slug": "seed-siggraph21-surfel-gi",
        "type": "pdf",
        "title": "SEED SIGGRAPH 2021 — Surfel GI",
    },
    {
        "path": "/home/midori/Downloads/SIGGRAPH2022-Advances-Lumen-Wright et al.pdf",
        "slug": "siggraph2022-lumen-advances",
        "type": "pdf",
        "title": "Advances in Lumen — SIGGRAPH 2022 (Wright et al.)",
    },
    {
        "path": "/home/midori/Downloads/3675382.pdf",
        "slug": "radiance-caching-on-surface",
        "type": "pdf",
        "title": "Radiance Caching with On-Surface Caches for Real-Time Global Illumination (Tatzgern et al.)",
    },
    {
        "path": "/tmp/research-scherzer/scherzer2010d-paper.pdf",
        "slug": "scherzer-2010-temporal-coherence",
        "type": "pdf",
        "title": "Exploiting Temporal Coherence in Real-Time Rendering (Scherzer, Yang, Mattausch — SIGGRAPH Asia 2010 Course)",
    },
    {
        "path": "/home/midori/Downloads/svgf_preprint.pdf",
        "slug": "schied-2017-svgf",
        "type": "pdf",
        "title": "Spatiotemporal Variance-Guided Filtering (SVGF — Schied et al., HPG 2017)",
    },
    {
        "path": "/home/midori/Downloads/adaptive_temporal_filtering.pdf",
        "slug": "schied-2018-asvgf",
        "type": "pdf",
        "title": "Gradient Estimation for Real-Time Adaptive Temporal Filtering (A-SVGF — Schied et al., HPG 2018)",
    },
    {
        "path": "/home/midori/Downloads/El_Mansouri_Jalal_Rendering_Rainbow_Six.pdf",
        "slug": "el-mansouri-2016-r6-siege",
        "type": "pdf",
        "title": "Rendering 'Rainbow Six | Siege' (El Mansouri — GDC 2016, 4× Checkerboard Reconstruction)",
    },
    {
        "path": "/mnt/archive4/PAPERS/jimenez-2017-cod-taa-upsampling.pdf",
        "slug": "jimenez-2017-cod-taa-upsampling",
        "type": "pdf",
        "title": "Dynamic Temporal Antialiasing and Upsampling in Call of Duty (Jimenez — SIGGRAPH 2017 Advances / Digital Dragons 2018)",
    },
    {
        "path": "/home/midori/Downloads/TheReal-timeVolumetricSuperstormsOfHorizonForbiddenWest_Schneider_Andrew.pdf",
        "slug": "schneider-2022-hfw-superstorms",
        "type": "pdf",
        "title": "The Real-time Volumetric Superstorms of Horizon Forbidden West (Schneider — GDC 2022)",
    },
    {
        "path": "/home/midori/Downloads/SimulatingTropicalWeather_Weick_Colin_Zhou_Emily.pdf",
        "slug": "simulating-tropical-weather-weick-zhou",
        "type": "pdf",
        "title": "Simulating Tropical Weather (Weick, Colin; Zhou, Emily)",
    },
    {
        "path": "/home/midori/Downloads/Report-Sparkles_CS-2024-02.pdf",
        "slug": "report-sparkles-cs-2024",
        "type": "pdf",
        "title": "Sparkles: A Practical Glint Rendering Framework (CS Report 2024-02)",
    },
    {
        "path": "/home/midori/Downloads/siggraph15_sparkly.pdf",
        "slug": "siggraph15-sparkly-slides",
        "type": "pdf",
        "title": "Rendering Glints on High-Resolution Normal-Mapped Specular Surfaces — SIGGRAPH 2015 (Slides)",
    },
    {
        "path": "/home/midori/Downloads/sparkle.pdf",
        "slug": "siggraph15-sparkly-paper",
        "type": "pdf",
        "title": "Rendering Glints on High-Resolution Normal-Mapped Specular Surfaces — SIGGRAPH 2015 (Paper)",
    },
    {
        "path": "/home/midori/Downloads/2856400.2856409.pdf",
        "slug": "zirr-kaplanyan-2016-procedural-multiscale",
        "type": "pdf",
        "title": "Real-time Rendering of Procedural Multiscale Materials (Zirr & Kaplanyan — I3D 2016)",
    },
    {
        "path": "/mnt/archive4/Downloads/bwronski_volumetric_fog_siggraph2014.pptx",
        "slug": "bwronski-2014-volumetric-fog",
        "type": "pptx",
        "title": "Volumetric Fog: Unified, Compute Shader Based Solution to Atmospheric Scattering — Wroński (SIGGRAPH 2014)",
    },
    {
        "path": "/home/midori/Downloads/Fast Flexible Physically-Based Volumetric Light Scattering - Notes.pdf",
        "slug": "fast-flexible-volumetric-light-scattering-notes",
        "type": "pdf",
        "title": "Fast Flexible Physically-Based Volumetric Light Scattering — Course Notes (GDC)",
    },
    {
        "path": "/home/midori/Downloads/2109.13704v2.pdf",
        "slug": "ruijters-volume-rendering-artifacts",
        "type": "pdf",
        "title": "Common Artifacts in Volume Rendering (Ruijters 2021)",
    },
    {
        "path": "/home/midori/Downloads/geomclipmap.pdf",
        "slug": "losasso-hoppe-geomclipmap",
        "type": "pdf",
        "title": "Geometry Clipmaps: Terrain Rendering Using Nested Regular Grids (Losasso & Hoppe)",
    },
    {
        "path": "/home/midori/Downloads/paper-lowres.pdf",
        "slug": "soderlund-2022-sdf-grid-raytracing",
        "type": "pdf",
        "title": "Ray Tracing of Signed Distance Function Grids (Söderlund, Evans, Akenine-Möller — JCGT 2022)",
    },
    {
        "path": "/home/midori/Downloads/SIGGRAPH2007_AlphaTestedMagnification.pdf",
        "slug": "green-2007-sdf-magnification",
        "type": "pdf",
        "title": "Improved Alpha-Tested Magnification for Vector Textures and Special Effects (Green — SIGGRAPH 2007)",
    },
    {
        "path": "/home/midori/Downloads/Clipmap.pdf",
        "slug": "tanner-1998-clipmap",
        "type": "pdf",
        "title": "The Clipmap: A Virtual Mipmap (Tanner, Migdal, Jones — SIGGRAPH 1998)",
    },
    {
        "path": "/home/midori/Downloads/Thesis-1.pdf",
        "slug": "kuehnert-2022",
        "type": "pdf",
        "title": "Methods for Automated Creation and Efficient Visualisation of Large-Scale Terrains based on Real Height-Map Data (Kühnert — TU Chemnitz 2022)",
    },
    {
        "path": "/home/midori/Downloads/aaltonenhaar_siggraph2015_combined_final_footer_220dpi.pdf",
        "slug": "aaltonen-haar-2015-gpu-driven",
        "type": "pdf",
        "title": "GPU-Driven Rendering Pipelines (Haar & Aaltonen — SIGGRAPH 2015)",
    },
    {
        "path": "/home/midori/Downloads/Wihlidal_Graham_OptimizingTheGraphics.pdf",
        "slug": "wihlidal-2016-optimizing-graphics-pipeline",
        "type": "pdf",
        "title": "Optimizing the Graphics Pipeline with Compute (Wihlidal — GDC 2016)",
    },
    {
        "path": "/home/midori/Downloads/p387-fernando.pdf",
        "slug": "fernando-2001-adaptive-shadow-maps",
        "type": "pdf",
        "title": "Adaptive Shadow Maps (Fernando, Fernandez, Bala, Greenberg — SIGGRAPH 2001)",
    },
    {
        "path": "/home/midori/Downloads/johnson05_irregularzbuf.pdf",
        "slug": "johnson-2005-irregular-zbuffer",
        "type": "pdf",
        "title": "The Irregular Z-Buffer: Hardware Acceleration for Irregular Data Structures (Johnson, Lee, Burns, Mark — UT Austin / TOG 2005)",
    },
    {
        "path": "/home/midori/Downloads/Fitted_virtual_shadow_maps.pdf",
        "slug": "giegl-2007-fitted-virtual-shadow-maps",
        "type": "pdf",
        "title": "Fitted Virtual Shadow Maps (Giegl & Wimmer — Vienna University of Technology, 2007)",
    },
    {
        "path": "/home/midori/Downloads/12_CSSM.pdf",
        "slug": "kolic-2013-camera-space-shadow-maps",
        "type": "pdf",
        "title": "Camera Space Shadow Maps for Large Virtual Environments (Kolic & Mihajlovic — University of Zagreb, 2013)",
    },
    {
        "path": "/home/midori/Downloads/clustered_shadows_tvcg.pdf",
        "slug": "olsson-2015-clustered-shadows",
        "type": "pdf",
        "title": "More Efficient Virtual Shadow Maps for Many Lights (Olsson, Billeter, Sintorn, Kämpe et al. — TVCG 2015)",
    },
    {
        "path": "/home/midori/Downloads/Sakmary-Resolution-Matched-Virtual-Shadow-Maps.pdf",
        "slug": "sakmary-resolution-matched-virtual-shadow-maps",
        "type": "pdf",
        "title": "Resolution Matched Virtual Shadow Maps (Sakmary — CTU Prague)",
    },
    {
        "path": "/home/midori/Downloads/premoze04.pdf",
        "slug": "premoze-2004-multiple-scattering",
        "type": "pdf",
        "title": "Practical Rendering of Multiple Scattering Effects in Participating Media — Premoze 2004",
    },
    {
        "path": "/home/midori/Downloads/Predicted Virtual Soft Shadow Maps with High Quality Filtering.pdf",
        "slug": "shen-2011-predicted-virtual-soft-shadow-maps",
        "type": "pdf",
        "title": "Predicted Virtual Soft Shadow Maps with High Quality Filtering (Shen, Guennebaud, Yang, Feng — Eurographics 2011)",
    },
    {
        "path": "/home/midori/Downloads/NRN-TR04.pdf",
        "slug": "narasimhan-2004-analytic-multiple-scattering",
        "type": "pdf",
        "title": "Analytic Rendering of Multiple Scattering in Participating Media — Narasimhan 2004",
    },
    {
        "path": "/home/midori/Downloads/GIEGL-2007-QV1-Preprint.pdf",
        "slug": "giegl-2007-queried-virtual-shadow-maps",
        "type": "pdf",
        "title": "Queried Virtual Shadow Maps (Giegl & Wimmer — Vienna University of Technology, 2007)",
    },
    {
        "path": "/home/midori/Downloads/CG_CGASI-2012-09-0082.R1_Elek.pdf",
        "slug": "elek-2012-screen-space-scattering",
        "type": "pdf",
        "title": "Real-Time Screen-Space Scattering in Homogeneous Environments — Elek 2012",
    },
    {
        "path": "/home/midori/Downloads/Virtual Shadow Maps in Unreal Engine _ Unreal Engine 5.1 Documentation _ Epic Developer Community.pdf",
        "slug": "epic-ue51-virtual-shadow-maps-docs",
        "type": "pdf",
        "title": "Virtual Shadow Maps in Unreal Engine (Epic — UE 5.1 Documentation)",
    },
    {
        "path": "/home/midori/Downloads/aila2004egsr_paper.pdf",
        "slug": "aila-laine-2004-alias-free-shadow-maps",
        "type": "pdf",
        "title": "Alias-Free Shadow Maps (Aila & Laine — Helsinki University of Technology / Eurographics Symposium on Rendering 2004)",
    },
    {
        "path": "/home/midori/Downloads/mwre-1520-0493_1997_125_2265_aotvof_2.0.co_2.pdf",
        "slug": "margolin-1997-vof-cloud-advection",
        "type": "pdf",
        "title": "Application of the Volume-of-Fluid Method to the Advection–Condensation Problem (Margolin, Reisner & Smolarkiewicz — Mon. Wea. Rev. 1997)",
    },
    {
        "path": "/home/midori/Downloads/qt40v513qg.pdf",
        "slug": "lefohn-2007-resolution-matched-shadow-maps",
        "type": "pdf",
        "title": "Resolution Matched Shadow Maps (Lefohn, Sengupta, Owens — UC Davis / TOG 2007)",
    },
    {
        "path": "/home/midori/Downloads/flux_main.pdf",
        "slug": "hirasawa-2021-flux-interpolated-advection",
        "type": "pdf",
        "title": "A Flux-Interpolated Advection Scheme for Fluid Simulation (Hirasawa, Kanai & Ando — CGI 2021)",
    },
    {
        "path": "/home/midori/Downloads/An_Efficient_Alias-free_Shadow_Algorithm_for_Opaqu.pdf",
        "slug": "sintorn-olsson-2008-alias-free-shadow-volumes",
        "type": "pdf",
        "title": "An Efficient Alias-free Shadow Algorithm for Opaque and Transparent Objects using per-triangle Shadow Volumes (Sintorn, Olsson, Assarsson — Chalmers 2008)",
    },
    {
        "path": "/home/midori/Downloads/Lauritzen-SDSM(SIGGRAPH 2010 Advanced RealTime Rendering Course).pdf",
        "slug": "lauritzen-2010-sample-distribution-shadow-maps",
        "type": "pdf",
        "title": "Sample Distribution Shadow Maps (Lauritzen — SIGGRAPH 2010 Advances in Real-Time Rendering Course)",
    },
    {
        "path": "/home/midori/Downloads/avsm_egsr2010_lowres.pdf",
        "slug": "salvi-2010-adaptive-volumetric-shadow-maps",
        "type": "pdf",
        "title": "Adaptive Volumetric Shadow Maps (Salvi, Vidimče, Lauritzen, Lefohn — Intel / EGSR 2010)",
    },
    {
        "path": "/home/midori/Downloads/chen2025dmd.pdf",
        "slug": "chen-2025-dmd-fluid-subspace",
        "type": "pdf",
        "title": "Fast Subspace Fluid Simulation with a Temporally-Aware Basis (Chen et al. — SIGGRAPH 2025)",
    },
    {
        "path": "/home/midori/Downloads/2015-1.pdf",
        "slug": "jin-2015-conservative-semi-lagrangian-ffd",
        "type": "pdf",
        "title": "Improvement of Fast Fluid Dynamics with a Conservative Semi-Lagrangian Scheme (Jin & Chen — HFF 2015)",
    },
    {
        "path": "/home/midori/Downloads/gridFluids_GPU_Gems.pdf",
        "slug": "harris-gpu-gems-ch38-fast-fluid-dynamics",
        "type": "pdf",
        "title": "Fast Fluid Dynamics Simulation on the GPU (Harris — GPU Gems Ch. 38, 2004)",
    },
    {
        "path": "/home/midori/Downloads/fast-fluid-dynamics-on.pdf_recZxLHseys3jxzKm.pdf",
        "slug": "fais-iorio-2011-ffd-scc",
        "type": "pdf",
        "title": "Fast Fluid Dynamics on the Single-chip Cloud Computer (Fais & Iorio — Autodesk Research, 2011)",
    },
    {
        "path": "/home/midori/Downloads/surfaceTracking.pdf",
        "slug": "muller-2009-surface-tracking",
        "type": "pdf",
        "title": "Fast and Robust Tracking of Fluid Surfaces (Müller — SCA 2009)",
    },
    {
        "path": "/home/midori/Downloads/LLDL21.pdf",
        "slug": "lyu-2021-fluid-solid-coupling",
        "type": "pdf",
        "title": "Fast and Versatile Fluid-Solid Coupling for Turbulent Flow Simulation (Lyu, Li, Desbrun, Liu — SIGGRAPH 2021)",
    },
    {
        "path": "/home/midori/Downloads/batty-siggraph2007-variationalcoupling.pdf",
        "slug": "batty-2007-variational-coupling",
        "type": "pdf",
        "title": "A Fast Variational Framework for Accurate Solid-Fluid Coupling (Batty, Bertails, Bridson — SIGGRAPH 2007)",
    },
    {
        "path": "/mnt/archive4/Downloads/2017_Sig_Improved_Culling_final.pptx",
        "slug": "drobot-2017-improved-culling",
        "type": "pptx",
        "title": "Improved Culling for Tiled and Clustered Rendering (Drobot — SIGGRAPH 2017 Advances in Real-Time Rendering)",
    },
    {
        "path": "/home/midori/Downloads/cuntz07gpudt.pdf",
        "slug": "cuntz-kolb-2007-hierarchical-3d-distance-transform",
        "type": "pdf",
        "title": "Fast Hierarchical 3D Distance Transforms on the GPU (Cuntz & Kolb — Eurographics 2007 Short Papers)",
    },
    {
        "path": "/home/midori/Downloads/tr0601-distancetransform.pdf",
        "slug": "cuntz-kolb-2007-tr-3d-distance-transform",
        "type": "pdf",
        "title": "Fast Hierarchical 3D Distance Transforms on the GPU (Cuntz & Kolb — University of Siegen Technical Report, May 15 2007)",
    },
    {
        "path": "/home/midori/Downloads/Improved Moment Shadow Maps for Translucent_Occluders, Soft Shadows and Single Scattering.pdf",
        "slug": "peters-2017-improved-moment-shadow-maps",
        "type": "pdf",
        "title": "Improved Moment Shadow Maps for Translucent Occluders, Soft Shadows and Single Scattering (Peters, Münstermann, Wetzstein, Klein — JCGT Vol. 6 No. 1, 2017)",
    },
    {
        "path": "/home/midori/Downloads/1360612.1360633.pdf",
        "slug": "annen-2008-all-frequency-shadows",
        "type": "pdf",
        "title": "Real-Time, All-Frequency Shadows in Dynamic Scenes (Annen, Dong, Mertens, Bekaert, Seidel, Kautz — ACM TOG / SIGGRAPH 2008)",
    },
    {
        "path": "/home/midori/Downloads/GDC2023_GT7_SKY_RENDERING.pdf",
        "slug": "suzuki-yasutomi-2023-gt7-sky-dome",
        "type": "pdf",
        "title": "Realistic Real-time Sky Dome Rendering in Gran Turismo 7 (Suzuki & Yasutomi — Polyphony Digital, GDC 2023)",
    },
    {
        "path": "/mnt/archive4/PAPERS/crassin-2009-gigavoxels-ray-guided-streaming.pdf",
        "slug": "crassin-2009-gigavoxels-ray-guided-streaming",
        "type": "pdf",
        "title": "GigaVoxels: Ray-Guided Streaming for Efficient and Detailed Voxel Rendering (Crassin, Neyret, Lefebvre, Eisemann — i3D 2009)",
        "slide_deck": False,
    },
    {
        "path": "/mnt/archive4/PAPERS/crassin-2011-gigavoxels-thesis.pdf",
        "slug": "crassin-2011-gigavoxels-thesis",
        "type": "pdf",
        "title": "GigaVoxels: A Voxel-Based Rendering Pipeline for Efficient Exploration of Large and Detailed Scenes (Cyril Crassin — PhD thesis, Université de Grenoble, 2011)",
        "slide_deck": False,
    },
    {
        "path": "/mnt/archive4/PAPERS/amanatides-woo-1987-voxel-traversal.pdf",
        "slug": "amanatides-woo-1987-voxel-traversal",
        "type": "pdf",
        "title": "A Fast Voxel Traversal Algorithm for Ray Tracing (John Amanatides & Andrew Woo — Dept. of Computer Science, University of Toronto, Eurographics '87)",
        # PDF v1.2 has no embedded image objects — Figure 1 is vector PostScript paths.
        # Force slide-deck mode so PyMuPDF rasterises each page, giving the vision pass
        # something to read for the figure + code listings. Filename pattern: pNNN-slide.png.
        "slide_deck": True,
    },
    {
        "path": "/home/midori/Downloads/1730804.1730814.pdf",
        "slug": "laine-karras-2010-sparse-voxel-octrees",
        "type": "pdf",
        "title": "Efficient Sparse Voxel Octrees (Laine & Karras — NVIDIA Research / I3D 2010)",
        "slide_deck": False,
    },
    {
        "path": "/home/midori/Downloads/Young_iastate_0097M_16385.pdf",
        "slug": "young-2017-multilevel-voxel",
        "type": "pdf",
        "title": "Multi-level Voxel Representation for GPU-Accelerated Solid Modeling (Young, MS thesis, Iowa State 2017)",
        "slide_deck": False,
    },
    {
        "path": "/mnt/archive4/PAPERS/gobbetti-marton-2005-far-voxels.pdf",
        "slug": "gobbetti-marton-2005-far-voxels",
        "type": "pdf",
        "title": "Far Voxels: A Multiresolution Framework for Interactive Rendering of Huge Complex 3D Models on Commodity Graphics Platforms (Gobbetti & Marton, SIGGRAPH 2005)",
    },
    {
        "path": "/home/midori/Downloads/1404435.1404438.pdf",
        "slug": "mittring-2008-advanced-virtual-texture-topics",
        "type": "pdf",
        "title": "Advanced Virtual Texture Topics (Martin Mittring — Crytek GmbH; Chapter 2 of \"Advances in Real-Time Rendering in 3D Graphics and Games Course\", N. Tatarchuk ed., SIGGRAPH 2008)",
        "slide_deck": False,
    },
    {
        "path": "/mnt/archive4/PAPERS/blinn-1982-light-reflection-clouds-dusty-surfaces.pdf",
        "slug": "blinn-1982-light-reflection-clouds-dusty-surfaces",
        "type": "pdf",
        "title": "Light Reflection Functions for Simulation of Clouds and Dusty Surfaces (James F. Blinn, JPL/Caltech — Computer Graphics 16:3, July 1982 / SIGGRAPH 1982)",
    },
    {
        "path": "/mnt/archive4/PAPERS/gobbetti-marton-iglesias-guitian-2008-single-pass-gpu-raycasting.pdf",
        "slug": "gobbetti-marton-iglesias-guitian-2008-single-pass-gpu-raycasting",
        "type": "pdf",
        "title": "A single-pass GPU ray casting framework for interactive out-of-core rendering of massive volumetric datasets (Gobbetti, Marton, Iglesias-Guitián — Visual Computer 2008)",
        "slide_deck": False,
    },
    {
        "path": "/mnt/archive4/PAPERS/schwarz-seidel-2010-fast-parallel-voxelization.pdf",
        "slug": "schwarz-seidel-2010-fast-parallel-voxelization",
        "type": "pdf",
        "title": "Fast Parallel Surface and Solid Voxelization on GPUs (Michael Schwarz, Hans-Peter Seidel — SIGGRAPH Asia 2010)",
        "slide_deck": False,
    },
    {
        "path": "/mnt/archive4/PAPERS/eisemann-decoret-2008-single-pass-gpu-solid-voxelization.pdf",
        "slug": "eisemann-decoret-2008-single-pass-gpu-solid-voxelization",
        "type": "pdf",
        "title": "Single-Pass GPU Solid Voxelization for Real-Time Applications (Elmar Eisemann, Xavier Décoret — Graphics Interface 2008)",
        "slide_deck": False,
    },
    {
        "path": "/mnt/archive4/PAPERS/frisken-perry-2002-quadtree-octree-traversal.pdf",
        "slug": "frisken-perry-2002-quadtree-octree-traversal",
        "type": "pdf",
        "title": "Simple and Efficient Traversal Methods for Quadtrees and Octrees (Sarah F. Frisken, Ronald N. Perry — Journal of Graphics Tools, 2002)",
        "slide_deck": False,
    },
    {
        "path": "/mnt/archive4/PAPERS/lefebvre-hoppe-2006-perfect-spatial-hashing.pdf",
        "slug": "lefebvre-hoppe-2006-perfect-spatial-hashing",
        "type": "pdf",
        "title": "Perfect Spatial Hashing (Sylvain Lefebvre, Hugues Hoppe — SIGGRAPH 2006)",
        "slide_deck": False,
    },
    {
        "path": "/mnt/archive4/PAPERS/knoll-2008-octree-volume-rendering-survey.pdf",
        "slug": "knoll-2008-octree-volume-rendering-survey",
        "type": "pdf",
        "title": "A Survey of Octree Volume Rendering Methods (Aaron Knoll — IRTG 1131 / VG 2008 / SCI Institute, 2008)",
        "slide_deck": False,
    },
    {
        "path": "/mnt/archive4/PAPERS/lefebvre-dachsbacher-2007-tiletrees.pdf",
        "slug": "lefebvre-dachsbacher-2007-tiletrees",
        "type": "pdf",
        "title": "TileTrees (Sylvain Lefebvre, Carsten Dachsbacher — I3D 2007)",
        "slide_deck": False,
    },
    {
        "path": "/mnt/archive4/PAPERS/lefohn-2006-glift-gpu-data-structures.pdf",
        "slug": "lefohn-2006-glift-gpu-data-structures",
        "type": "pdf",
        "title": "Glift: Generic, Efficient, Random-Access GPU Data Structures (Aaron E. Lefohn, Shubhabrata Sengupta, Joe Kniss, Richard Strzodka, John D. Owens — ACM TOG 25:1, January 2006)",
        "slide_deck": False,
    },
    {
        "path": "/mnt/archive4/PAPERS/kraus-ertl-2002-adaptive-texture-maps.pdf",
        "slug": "kraus-ertl-2002-adaptive-texture-maps",
        "type": "pdf",
        "title": "Adaptive Texture Maps (Martin Kraus, Thomas Ertl — Graphics Hardware 2002)",
        "slide_deck": False,
    },
    {
        "path": "/mnt/archive4/PAPERS/bouthors-2008-interactive-anisotropic-scattering-clouds.pdf",
        "slug": "bouthors-2008-interactive-anisotropic-scattering-clouds",
        "type": "pdf",
        "title": "Interactive Multiple Anisotropic Scattering in Clouds (Bouthors, Neyret, Holzschuch, Pacanowski, Cani, Lefebvre — I3D 2008)",
        "slide_deck": False,
    },
    {
        "path": "/mnt/archive4/PAPERS/bouthors-neyret-lefebvre-2006-stratiform-clouds.pdf",
        "slug": "bouthors-neyret-lefebvre-2006-stratiform-clouds",
        "type": "pdf",
        "title": "Real-Time Realistic Illumination and Shading of Stratiform Clouds (Bouthors, Neyret, Lefebvre — Eurographics 2006)",
        "slide_deck": False,
    },
    {
        "path": "/mnt/archive4/PAPERS/max-1995-optical-models-direct-volume-rendering.pdf",
        "slug": "max-1995-optical-models-direct-volume-rendering",
        "type": "pdf",
        "title": "Optical Models for Direct Volume Rendering (Nelson Max — IEEE Transactions on Visualization and Computer Graphics 1:2, June 1995)",
        "slide_deck": False,
    },
    {
        "path": "/mnt/archive4/PAPERS/kajiya-vonherzen-1984-ray-tracing-volume-densities.pdf",
        "slug": "kajiya-vonherzen-1984-ray-tracing-volume-densities",
        "type": "pdf",
        "title": "Ray Tracing Volume Densities (James T. Kajiya, Brian P. Von Herzen — Computer Graphics 18:3, July 1984 / SIGGRAPH 1984)",
        "slide_deck": False,
    },
    {
        "path": "/mnt/archive4/PAPERS/tatarchuk-2013-destiny-rendering.pdf",
        "slug": "tatarchuk-2013-destiny-rendering",
        "type": "pdf",
        "title": "Destiny: From Mythic Science Fiction to Rendering in Real Time (Natalya Tatarchuk — Bungie, SIGGRAPH 2013 Advances in Real-Time Rendering)",
        # Creator = "Microsoft® PowerPoint® 2010" → is_slide_deck_pdf auto-fires on "powerpoint"
        # No override needed; left here as documentation of the auto-detect outcome.
    },
    {
        "path": "/mnt/archive4/PAPERS/tatarchuk-2015-applied-graphics-research.pdf",
        "slug": "tatarchuk-2015-applied-graphics-research",
        "type": "pdf",
        "title": "Applied Graphics Research for Video Games (Natalya Tatarchuk — AMD, GDC 2015)",
        # Likely a PowerPoint export; is_slide_deck_pdf will auto-detect via "powerpoint" in Creator.
        # No override needed.
    },
    {
        "path": "/mnt/archive4/PAPERS/yusov-2013-epipolar-sampling-min-max-trees.pdf",
        "slug": "yusov-2013-epipolar-sampling-min-max-trees",
        "type": "pdf",
        "title": "Outdoor Light Scattering Sample (Egor Yusov — Intel, 2013 / Intel Developer Zone); epipolar sampling with 1D min-max mip-tree acceleration for real-time atmospheric scattering",
        # Text-layer PDF; let is_slide_deck_pdf auto-detect. Expected: paper route via marker.
    },
    {
        "path": "/mnt/archive4/PAPERS/jarosz-2008-monte-carlo-light-transport-scattering-media.pdf",
        "slug": "jarosz-2008-monte-carlo-light-transport-scattering-media",
        "type": "pdf",
        "title": "Efficient Monte Carlo Methods for Light Transport in Scattering Media (Wojciech Jarosz — PhD thesis, UCSD, 2008)",
        # Text-layer PhD thesis (~83 MB, 200+ pages). Let is_slide_deck_pdf auto-detect.
        # Expected: paper route via marker with redo_inline_math=True (math-dense: RTE, HG phase
        # function, beam radiance estimate, photon density estimate, Rayleigh/Mie phase functions).
    },
    {
        "path": "/mnt/archive4/PAPERS/toth-umenhoffer-2009-volumetric-lighting-participating-media.pdf",
        "slug": "toth-umenhoffer-2009-volumetric-lighting-participating-media",
        "type": "pdf",
        "title": "Real-Time Volumetric Lighting in Participating Media (Toth & Umenhoffer — Eurographics 2009 Short Papers)",
        # Small text-layer paper (~780 KB). Let is_slide_deck_pdf auto-detect (expected: False).
        # Math content: HG phase function, single-scattering integral along view ray,
        # ray-marching with shadow-map sampling. redo_inline_math=True is the default.
    },
    {
        "path": "/mnt/archive4/PAPERS/bruneton-neyret-2008-precomputed-atmospheric-scattering.pdf",
        "slug": "bruneton-neyret-2008-precomputed-atmospheric-scattering",
        "type": "pdf",
        "title": "Precomputed Atmospheric Scattering (Bruneton & Neyret — EGSR 2008 / JCGT 2008)",
        # Text-layer paper (~2.3 MB, 8 pages). Let is_slide_deck_pdf auto-detect (expected: False).
        # Math content: radiative transfer equation, Rayleigh/Mie phase functions,
        # precomputed 4D scattering tables, single vs multiple scattering.
        # redo_inline_math=True is the default.
    },
    {
        "path": "/mnt/archive4/PAPERS/keinert-2014-enhanced-sphere-tracing.pdf",
        "slug": "keinert-2014-enhanced-sphere-tracing",
        "type": "pdf",
        "title": "Enhanced Sphere Tracing (Keinert et al. — STAG 2014)",
        # Text-layer paper. Let is_slide_deck_pdf auto-detect (expected: False).
        # Math content: sphere tracing acceleration, SDF evaluation, step-size bounds.
        # redo_inline_math=True is the default.
        "slide_deck": False,
    },
    {
        "path": "/mnt/archive4/PAPERS/hart-1995-sphere-tracing.pdf",
        "slug": "hart-1995-sphere-tracing",
        "type": "pdf",
        "title": "Sphere Tracing: A Geometric Method for the Antialiased Ray Tracing of Implicit Surfaces (John C. Hart — The Visual Computer 12, 1996 / earlier 1995 technical report)",
        # Text-layer paper. Let is_slide_deck_pdf auto-detect (expected: False).
        # Math content: implicit surface rendering, Lipschitz bounds, sphere tracing algorithm,
        # antialiasing via unbounding volumes. redo_inline_math=True is the default.
        "slide_deck": False,
    },
    {
        "path": "/mnt/archive4/PAPERS/crassin-2011-voxel-cone-tracing.pdf",
        "slug": "crassin-2011-voxel-cone-tracing",
        "type": "pdf",
        "title": "Interactive Indirect Illumination Using Voxel Cone Tracing (Cyril Crassin, Fabrice Neyret, Miguel Sainz, Simon Green, Elmar Eisemann — SIGGRAPH 2011 / GPU Pro 2)",
        # Text-layer paper (ACM / NVIDIA). Let is_slide_deck_pdf auto-detect (expected: False).
        # Foundational paper for voxel-based global illumination via cone tracing in a sparse
        # voxel octree. Math content: cone-casting integral, mipmapped voxel cone filter,
        # anisotropic GGX, ambient occlusion via cone tracing, diffuse/specular indirect
        # illumination. redo_inline_math=True is the default.
    },
    # ============================================================================
    # Williams 1983 — Pyramidal Parametrics (foundational mipmap / image pyramid)
    # ============================================================================
    {
        "path": "/mnt/archive4/PAPERS/williams-1983-pyramidal-parametrics.pdf",
        "slug": "williams-1983-pyramidal-parametrics",
        "type": "pdf",
        "title": "Pyramidal Parametrics (Lance Williams — Computer Graphics 17:3, July 1983 / SIGGRAPH 1983)",
    },
    {
        "path": "/home/midori/Downloads/SIGGRAPH2022-Advances-NubisEvolved-NoVideos.pdf",
        "slug": "schneider-2022-nubis-evolved",
        "type": "pdf",
        "slide_deck": True,
        "title": "Nubis, Evolved: Real-time Volumetric Clouds for Skies, Environments, and VFX — Andrew Schneider (SIGGRAPH 2022 Advances in Real-Time Rendering in Games)",
    },
    {
        "path": "/mnt/archive4/PAPERS/krause-2025-enshrouded-volumetric-fog.pdf",
        "slug": "krause-2025-enshrouded-volumetric-fog",
        "type": "pdf",
        "slide_deck": True,
        "title": "The Fog is Lifting: Volumetric Rendering Enshrouded — Philip Krause (GDC 2025)",
    },
    # ============================================================================
    # Ulschmid et al. 2026 — NAADF: Globally Illuminated Voxel Worlds Accelerated
    # with Nested Axis-Aligned Distance Fields (EUROGRAPHICS 2026 / CGF 70413)
    # ============================================================================
    {
        "path": "/mnt/archive4/PAPERS/ulschmid-2026-naadf-voxel-gi.pdf",
        "slug": "ulschmid-2026-naadf-voxel-gi",
        "type": "pdf",
        "title": "NAADF: Globally Illuminated Voxel Worlds Accelerated with Nested Axis-Aligned Distance Fields (Ulschmid, Ott, Macho, Wimmer, Ohrhallinger — TU Wien / EUROGRAPHICS 2026 / CGF 10.1111/cgf.70413)",
        # Text-layer CGF paper. Let is_slide_deck_pdf auto-detect (expected: False).
        # Math content: nested axis-aligned distance fields, voxel cone stepping,
        # global illumination integral, ADF hierarchy construction, ray-AABB tests.
        # redo_inline_math=True is the default.
        "slide_deck": False,
    },
    # ============================================================================
    # Kider et al. 2014 — A Framework for the Experimental Comparison of Solar
    # and Skydome Illumination (SIGGRAPH Asia 2014, ACM TOG 33:6 art.180)
    # Cornell Program of Computer Graphics.
    # Measurement-methodology anchor for offline-baked-sky-LUT-authoring research.
    # Dataset used by Bruneton's clear-sky-models harness and GT7 Skysim validation.
    # ============================================================================
    {
        "path": "/mnt/archive4/PAPERS/kider-2014-experimental-comparison-skydome-illumination.pdf",
        "slug": "kider-2014-experimental-comparison-skydome-illumination",
        "type": "pdf",
        "title": "A Framework for the Experimental Comparison of Solar and Skydome Illumination — Kider, Knowlton, Newlin, Li, Greenberg (SIGGRAPH Asia 2014 / ACM TOG 33:6 art.180, Cornell Program of Computer Graphics)",
        # ~12-page paper PDF. Text-layer expected (not scanned). slide_deck=False.
        # Math-heavy: spectral radiometry, camera/spectroradiometer calibration,
        # hemispherical fisheye + spot measurement equations.
        "slide_deck": False,
    },
    # ============================================================================
    # Wilkie et al. 2021 — A Fitted Radiance and Attenuation Model for Realistic
    # Atmospheres (SIGGRAPH 2021, ACM TOG 40:4 art.138)
    # Charles University CGG group. Successor to Hosek-Wilkie 2012 and
    # Wilkie-Hosek 2013. Fitted analytic sky model with aerial perspective
    # attenuation trained against path-traced ground truth. Multi-spectral output.
    # CGG publication page: "Unless compatibility with old codebases is essential,
    # the new model should be used whenever possible."
    # ============================================================================
    {
        "path": "/mnt/archive4/PAPERS/wilkie-2021-fitted-radiance-atmosphere.pdf",
        "slug": "wilkie-2021-fitted-radiance-atmosphere",
        "type": "pdf",
        "title": "A Fitted Radiance and Attenuation Model for Realistic Atmospheres — Wilkie, Vévoda, Bashford-Rogers, Hošek, Iser, Kolářová, Rittig, Křivánek (SIGGRAPH 2021 / ACM TOG 40:4 art.138, Charles University CGG)",
        # ~26 MB paper PDF (large due to high-fidelity full-sky comparison renders).
        # Text-layer expected (not scanned). slide_deck=False.
        # Math-heavy: fitted coefficient parameterisation, radiance + attenuation
        # formulas, solar disc, multi-spectral output, aerial perspective LUT.
        # High equation-substitution risk: rho (particle radius), tau (optical depth),
        # omega (single-scattering albedo), mu (emission cosine), gamma (scattering angle).
        "slide_deck": False,
    },
    # ============================================================================
    # Hošek & Wilkie 2012 — An Analytic Model for Full Spectral Sky-Dome Radiance
    # (SIGGRAPH 2012 / ACM TOG 31:4 art.95, Charles University in Prague)
    # The canonical analytic sky model that succeeded Preetham 1999. Fitted from
    # a path-traced ground-truth dataset; supports 11 wavelengths (spectral), RGB,
    # and CIE XYZ output. 9 coefficients per (turbidity, albedo, sun-elevation)
    # combination. Predecessor of Wilkie 2021 and widely used as a bake source for
    # offline sky LUTs (GT7 Suzuki-Yasutomi 2023, Bruneton clear-sky-models harness).
    # ============================================================================
    {
        "path": "/mnt/archive4/PAPERS/hosek-wilkie-2012-analytic-skydome.pdf",
        "slug": "hosek-wilkie-2012-analytic-skydome",
        "type": "pdf",
        "title": "An Analytic Model for Full Spectral Sky-Dome Radiance — Hošek & Wilkie (SIGGRAPH 2012 / ACM TOG 31:4 art.95, Charles University in Prague)",
        # Text-layer SIGGRAPH paper (~1.3 MB). Let is_slide_deck_pdf auto-detect (expected: False).
        # Math-heavy: 9-coefficient fitted analytic formula, Preetham comparison plots,
        # polar-plot panels per wavelength band, turbidity/albedo parameterisation.
        # High equation-substitution risk: gamma (scattering angle vs transmittance exponent),
        # theta (zenith angle), chi (chi-function in the HW radiance formula),
        # rho (particle radius), tau (optical depth).
        "slide_deck": False,
    },
    # ============================================================================
    # Nishita et al. 1993 — Display of the Earth Taking into Account Atmospheric Scattering
    # SIGGRAPH 1993, Tomoyuki Nishita, Takao Sirai, Katsumi Tadamura, Eihachiro Nakamae.
    # THE foundational atmospheric scattering paper: single-scattering for a planet from
    # space, wavelength-dependent extinction, precomputed scattering tables extended by
    # Bruneton 2008. Cited by Hosek-Wilkie, Bruneton, Hillaire, GT7. Small (~380 KB),
    # Ghostscript-produced — likely re-scan or old TeX vintage like Preetham 1999.
    # Expect old-TeX-vintage math corruption (decimal-points-as-colons, dropped Greek,
    # shattered equations). High equation-substitution risk: sigma (extinction coefficient),
    # lambda (wavelength), theta (scattering angle), tau (optical depth), rho (density).
    # ============================================================================
    {
        "path": "/mnt/archive4/PAPERS/nishita-1993-display-of-earth-atmospheric.pdf",
        "slug": "nishita-1993-display-of-earth-atmospheric",
        "type": "pdf",
        "title": "Display of the Earth Taking into Account Atmospheric Scattering — Nishita, Sirai, Tadamura, Nakamae (SIGGRAPH 1993)",
        "slide_deck": False,
    },
    # ============================================================================
    # Wilkie & Hošek 2013 — Predicting Sky Dome Appearance on Earth-like Extrasolar Worlds
    # SCCG 2013, Alexander Wilkie & Lukáš Hošek (Charles University in Prague).
    # Companion to Hosek-Wilkie 2012 / Wilkie 2021: extends the analytic sky model to
    # alien-sun scenarios (star colour temperatures 3000K–10000K, binary stars).
    # Derives coefficient-scaling rules for re-fitting when illumination spectrum changes
    # substantially. Primary source for offline-baked-sky-LUT authoring under non-solar
    # illumination. 8-page pdfTeX paper; text-layer intact (no OCR issues expected).
    # Math-heavy: spectral scaling rules, coefficient parameterisation, blackbody emission
    # across star temperatures, binary-star superposition. High equation-substitution risk:
    # lambda (wavelength), theta (zenith angle), gamma (scattering angle), tau (optical
    # depth), chi (chi-function in HW radiance formula).
    # ============================================================================
    {
        "path": "/mnt/archive4/PAPERS/wilkie-hosek-2013-extrasolar-sky-dome.pdf",
        "slug": "wilkie-hosek-2013-extrasolar-sky-dome",
        "type": "pdf",
        "title": "Predicting Sky Dome Appearance on Earth-like Extrasolar Worlds — Wilkie & Hošek (SCCG 2013, Charles University in Prague)",
        # 8-page pdfTeX paper (PDF 1.4, pdfTeX-1.40.9). Text-layer expected; not scanned.
        # slide_deck=False confirmed by metadata (creator=LaTeX with hyperref, portrait pages).
        "slide_deck": False,
    },
    {
        "path": "/mnt/archive4/PAPERS/kol-2012-analytical-sky-simulation.pdf",
        "slug": "kol-2012-analytical-sky-simulation",
        "type": "pdf",
        "title": "Analytical Sky Simulation — An Implementation and Analysis of Daytime Skylight Models (Timothy R. Kol, Utrecht University MSc Thesis, 2012)",
        # 41-page master's thesis (PDF 1.4, PDFill PDF Editor 14.0, portrait 612x792 pt).
        # Likely a re-print of a TeX original. Text-layer should be present.
        # slide_deck=False confirmed by portrait geometry and page count.
        "slide_deck": False,
    },
    # ============================================================================
    # Maquignaz 2024 — Towards Physically-Based Sky-Modeling (arXiv 2412.11883v1)
    # Ian J. Maquignaz, Université Laval, 16 December 2024.
    # 12-page figure-dense ACM acmart pdfTeX paper (~33 MB).
    # Introduces "AllSky" DNN/sky-modeling approach for EDR (14 EV) environment maps
    # inclusive of the sun. Argues conventional HDRI is insufficient for outdoor scene
    # relighting. Newest work in offline sky-LUT authoring as of Dec 2024.
    # ============================================================================
    {
        "path": "/mnt/archive4/PAPERS/maquignaz-2024-physically-based-sky-modeling.pdf",
        "slug": "maquignaz-2024-physically-based-sky-modeling",
        "type": "pdf",
        "title": "Towards Physically-Based Sky-Modeling — Ian J. Maquignaz (Université Laval, arXiv 2412.11883v1, December 2024)",
        # 12-page pdfTeX (ACM acmart template). Text-layer expected; not scanned.
        # slide_deck=False confirmed by portrait ACM layout.
        "slide_deck": False,
    },
]


@dataclass
class ImageData:
    data: bytes
    ext: str


@dataclass
class PageData:
    number: int
    heading: str | None = None
    text: str = ""
    images: list[ImageData] = field(default_factory=list)
    slide_image: ImageData | None = None  # full-page render for slide-deck PDFs / PPTX
    is_figure_bearing: bool = True  # paper-mode only: False for pure-prose pages.
    # When False, the page is still rendered + embedded for reference (math
    # equations, citation context, etc.) but is OUT OF SCOPE for the vision
    # pass. Filename suffix becomes `-text` instead of `-page`, which is the
    # signal the vision agent uses to skip.
    notes: str | None = None
    video_markers: list[str] = field(default_factory=list)


@dataclass
class Document:
    slug: str
    title: str
    source_path: str
    doc_type: str  # "pdf" / "pptx" / "slides-pdf" / "slides-pptx"
    page_count: int
    file_size_mb: float
    pages: list[PageData] = field(default_factory=list)
    is_slide_deck: bool = False  # one rendered image per page, no per-figure cutouts


SLIDE_DECK_KEYWORDS = (
    "powerpoint",
    "keynote",
    "google slides",
    "googleslides",
    "beamer",
    "pptx",
    "presentation",
    "impress",
)


def is_slide_deck_pdf(doc: fitz.Document) -> bool:
    """Heuristic: does this PDF look like a slide-deck export?

    A slide deck wants per-page rendering for vision pass — embedded image
    extraction would cut individual visual elements (chart chrome + plot,
    photo + frame, etc.) into useless pieces. Triggers if:
      - creator/producer/title metadata mentions PowerPoint / Keynote /
        Google Slides / Beamer / Impress, OR
      - all pages are landscape AND aspect ratio is one of the standard
        slide ratios (4:3 ≈ 1.33, 16:10 ≈ 1.6, 16:9 ≈ 1.78) AND there are
        at least 3 pages (single landscape pages can be posters / figures).
    """
    meta = doc.metadata or {}
    haystack = " ".join(
        (meta.get(k) or "").lower() for k in ("creator", "producer", "title", "subject")
    )
    if any(kw in haystack for kw in SLIDE_DECK_KEYWORDS):
        return True

    page_count = len(doc)
    if page_count < 3:
        return False

    landscape = 0
    slide_ratio = 0
    for i in range(page_count):
        rect = doc[i].rect  # respects rotation
        w, h = rect.width, rect.height
        if w <= 0 or h <= 0:
            continue
        if w > h:
            landscape += 1
        ratio = max(w, h) / min(w, h)
        # 4:3 = 1.333, 16:10 = 1.6, 16:9 = 1.778 — accept anywhere in 1.25..1.85
        if 1.25 <= ratio <= 1.85:
            slide_ratio += 1

    return landscape == page_count and slide_ratio == page_count


def _page_has_figure(page: fitz.Page, drawings_threshold: int = 12) -> bool:
    """Triage: does this paper-mode page carry a figure worth rendering?

    Vision pass is expensive — a 200-page thesis with figures only on 60% of
    pages should not produce 200 page renders. We render only pages that
    plausibly carry a figure / diagram / plot / table. The heuristic accepts:

      - Any embedded raster image (`page.get_images(full=True)` non-empty).
        Even one embedded image means the page has a real figure worth a
        vision pass.
      - "Many" vector drawings (`len(page.get_drawings()) >= drawings_threshold`).
        Vector flowcharts / cone diagrams / cache-architecture diagrams appear
        as dozens of stroke / fill operations rather than embedded rasters,
        and the threshold is set above what running text + page chrome /
        underline marks typically produce.

    The heuristic intentionally errs on the side of including pages: a small
    over-render is cheap, missing a figure costs a vision-pass blind spot.
    """
    if page.get_images(full=True):
        return True
    try:
        drawings = page.get_drawings()
    except Exception:
        drawings = []
    return len(drawings) >= drawings_threshold


def _classify_paper_pdf(doc: fitz.Document, sample: int = 10, min_chars: int = 50) -> str:
    """Decide whether a non-slide-deck PDF is text-rich or scanned.

    Marker (and PyMuPDF span-walking) both rely on a usable text layer.
    Scanned papers without OCR text layers must keep the existing OCR
    fallback path. Sample up to `sample` pages and count those with at
    least `min_chars` of native text. Majority decides.
    """
    n = min(sample, len(doc))
    if n == 0:
        return "scanned"
    rich = 0
    for i in range(n):
        if len(doc[i].get_text("text").strip()) >= min_chars:
            rich += 1
    return "text-paper" if rich * 2 >= n else "scanned"


def extract_pdf(source: dict, scale: float = 2.0, paper_scale: float = 2.5) -> Document:
    """Extract PDF.

    BOTH slide-deck and paper PDFs render full pages for the vision pass.
    Paper PDFs render only figure-bearing pages (per `_page_has_figure`)
    so a 200-page paper does not produce 200 PNGs; pages of pure body text
    are skipped because their text-layer extraction is already canonical
    and a vision pass on running prose adds no value.

    Asset filename pattern:
      - Slide-deck PDFs (and PPTX):  `sNNN-slide.png`  (one per page)
      - Paper PDFs:                  `pNNN-page.png`   (one per figure-bearing page)

    Embedded-image cutout extraction (`pNNN-figXX.png`) is intentionally
    REMOVED. PDF figures are typically PostScript / vector composites — a
    single authored figure (e.g. cone-tracing diagram, octree pyramid,
    cache architecture) decomposes into 5-40 separate xref entries, and
    each cutout is a meaningless fragment. The vision agent describing
    those fragments must lean on text-layer prose anchoring rather than
    on the visual itself, which defeats the point of a vision pass. Render
    the page as the reader saw it; the figure boundary is preserved.

    `paper_scale` defaults higher than `scale` because papers tend to pack
    smaller-detail figures (sub-panel labels, axis tick marks, equation
    glyphs) into the page than slide decks do, and the vision agent needs
    the extra resolution to read them.
    """
    path = source["path"]
    file_size = os.path.getsize(path) / (1024 * 1024)
    doc = fitz.open(path)

    forced = source.get("slide_deck")
    slide_deck = forced if forced is not None else is_slide_deck_pdf(doc)

    # Marker prepass for text-rich paper-PDFs only. Slide-decks render as
    # full-page images (their text layer is auxiliary, the visual is canonical),
    # and scanned PDFs lack the text layer marker depends on — those still
    # route through the legacy PyMuPDF span-walker + OpenOCR fallback.
    use_marker = (
        _MARKER_ENABLED
        and not slide_deck
        and _classify_paper_pdf(doc) == "text-paper"
    )
    marker_pages: dict[int, str] = {}
    if use_marker:
        cache_dir = ASSETS_DIR / source["slug"]
        try:
            result = marker_extract.convert_pdf(
                path,
                cache_dir=cache_dir,
                use_llm=_MARKER_USE_LLM,
                force=_MARKER_FORCE,
            )
            marker_pages = result.pages
            cache_note = " [cached]" if result.used_cache else ""
            model_note = (
                f" [{result.llm_provider}/{result.llm_model}"
                + (" +redo_inline_math" if result.redo_inline_math else "")
                + "]"
                if result.used_llm and not result.used_cache
                else ""
            )
            llm_note = (
                f" [llm: {result.llm_request_count} req / {result.llm_token_count} tok]"
                if result.used_llm and not result.used_cache
                else ""
            )
            print(f"  marker: {len(marker_pages)} pages{cache_note}{model_note}{llm_note}")
        except Exception as exc:
            print(f"  marker FAILED ({exc!r}); falling back to PyMuPDF span-walker")
            use_marker = False

    document = Document(
        slug=source["slug"],
        title=source["title"],
        source_path=path,
        doc_type="slides-pdf" if slide_deck else "pdf",
        page_count=len(doc),
        file_size_mb=round(file_size, 1),
        is_slide_deck=slide_deck,
    )

    for page_idx in range(len(doc)):
        page = doc[page_idx]
        page_data = PageData(number=page_idx + 1)

        if use_marker:
            # Marker path: per-page markdown body straight from the prepass.
            # First markdown heading on the page is the section anchor
            # (replaces the old font-size>14 heuristic, which produces noise
            # on PDFs whose body font happens to be ~15pt).
            md_body = marker_pages.get(page_idx, "")
            page_data.text = md_body
            page_data.heading = marker_extract.first_heading(md_body)
        else:
            # Legacy path: PyMuPDF text-dict span walker. Used for slide-decks
            # (text layer is auxiliary), scanned paper PDFs (handled together
            # with the OCR fallback below), and when --no-marker is passed.
            text_dict = page.get_text("dict")
            all_text_parts = []
            heading_candidate = None

            for block in text_dict.get("blocks", []):
                if block["type"] != 0:  # text block
                    continue
                for line in block.get("lines", []):
                    line_text = ""
                    max_font_size = 0
                    for span in line.get("spans", []):
                        line_text += span["text"]
                        max_font_size = max(max_font_size, span["size"])
                    line_text = line_text.strip()
                    if not line_text:
                        continue
                    all_text_parts.append(line_text)
                    if heading_candidate is None and max_font_size > 14:
                        heading_candidate = line_text

            page_data.text = "\n".join(all_text_parts)
            page_data.heading = heading_candidate

        if slide_deck:
            # Slide-deck mode: render every page once.
            pix = page.get_pixmap(matrix=fitz.Matrix(scale, scale))
            page_data.slide_image = ImageData(data=pix.tobytes("png"), ext="png")
        else:
            # Paper mode: render EVERY page so the markdown carries a visual
            # reference for every body-text page (math-dense prose, citation
            # context, etc.). The figure-bearing/text split is preserved as a
            # `is_figure_bearing` flag — the markdown emitter chooses the file
            # suffix from it (`-page` for figure-bearing, `-text` for prose),
            # and the vision agent uses the suffix to scope its work to real
            # diagrams. Skipping the render entirely for prose pages was the
            # old behaviour — it left math-bearing prose pages unverifiable
            # against marker's LLM cleanup output (which routinely produces
            # KaTeX-incompatible LaTeX). Visual reference is cheap; missing it
            # costs the ability to spot-check marker fidelity.
            page_data.is_figure_bearing = _page_has_figure(page)
            pix = page.get_pixmap(matrix=fitz.Matrix(paper_scale, paper_scale))
            png_bytes = pix.tobytes("png")
            page_rot = page.rotation  # 0 / 90 / 180 / 270
            if page_rot:
                # PIL.rotate is counter-clockwise; PDF rotation is clockwise.
                img = Image.open(io.BytesIO(png_bytes))
                img = img.rotate(-page_rot, expand=True)
                buf = io.BytesIO()
                img.save(buf, format="PNG")
                png_bytes = buf.getvalue()
            page_data.slide_image = ImageData(data=png_bytes, ext="png")

        # Body-text OCR fallback: when the page has no native text layer
        # (typical of scanned PDFs and image-only slides exported as
        # raster), OCR the page's own image asset and use the result as
        # the page body. Skipped on the marker path — marker has already
        # decided what text the page carries, and an empty marker page is
        # a deliberate "figure-only with captions, vision pass takes it
        # from here" signal, not a missing text layer. This is the ONLY
        # path on which OCR enters the canonical document body — image
        # inclusions inside a text-rich doc are NEVER OCR'd here. The
        # vision pass reads images directly with full visual context and
        # outclasses any CPU OCR engine; OCR
        # scaffolding alongside an image only narrows what the vision
        # agent looks at and primes it with mistakes.
        if not use_marker and len(page_data.text.strip()) < 20:
            target_bytes = None
            if page_data.slide_image is not None:
                target_bytes = page_data.slide_image.data
            elif page_data.images:
                # Largest embedded image is the full-page scan in scanned
                # PDFs and the only-image-on-page in image-only slide
                # exports.
                target_bytes = max((im.data for im in page_data.images), key=len)
            if target_bytes is not None:
                ocr_text = _ocr_image_bytes(target_bytes)
                if ocr_text:
                    page_data.text = ocr_text

        document.pages.append(page_data)

    doc.close()
    return document


def _find_libreoffice() -> str | None:
    """Locate a LibreOffice CLI binary. Returns None if not installed."""
    import shutil

    for name in ("soffice", "libreoffice", "lowriter"):
        which = shutil.which(name)
        if which:
            return which
    # Common Linux/Mac install locations
    for candidate in (
        "/usr/bin/libreoffice",
        "/usr/bin/soffice",
        "/usr/lib/libreoffice/program/soffice",
        "/Applications/LibreOffice.app/Contents/MacOS/soffice",
    ):
        if os.path.exists(candidate):
            return candidate
    return None


def _pptx_to_pdf(pptx_path: str, out_dir: str) -> str:
    """Convert PPTX to PDF via LibreOffice headless. Returns path to the PDF.

    Raises RuntimeError if LibreOffice is unavailable. Install via:
        Arch:    pacman -S libreoffice-fresh
        Debian:  apt install libreoffice
        macOS:   brew install --cask libreoffice
    """
    import subprocess

    soffice = _find_libreoffice()
    if not soffice:
        raise RuntimeError(
            "LibreOffice not found on PATH. PPTX → slide-image rendering "
            "requires `soffice` / `libreoffice` (headless conversion to PDF). "
            "Install: pacman -S libreoffice-fresh (Arch) / "
            "apt install libreoffice (Debian) / "
            "brew install --cask libreoffice (macOS). "
            "See SKILL.md → 'PPTX rendering dependency' section."
        )
    pptx_name = Path(pptx_path).stem
    out_pdf = os.path.join(out_dir, f"{pptx_name}.pdf")
    if os.path.exists(out_pdf):
        return out_pdf
    subprocess.run(
        [soffice, "--headless", "--convert-to", "pdf", "--outdir", out_dir, pptx_path],
        check=True,
        capture_output=True,
    )
    if not os.path.exists(out_pdf):
        raise RuntimeError(
            f"LibreOffice ran but did not produce {out_pdf}. "
            f"Check that `{pptx_path}` is a valid PPTX file."
        )
    return out_pdf


def extract_pptx(source: dict, scale: float = 2.0) -> Document:
    """Extract PPTX as a slide deck.

    PPTX is always treated as a slide deck — every slide rendered as a single
    PNG via LibreOffice → PDF → PyMuPDF rasterisation. Per-shape image
    extraction is NEVER used: it cuts visual elements into useless fragments
    (chart chrome split from plot, photo split from frame, etc.) and the
    relative geometry is lost. Speaker notes and slide title are still pulled
    from python-pptx for text content.
    """
    path = source["path"]
    file_size = os.path.getsize(path) / (1024 * 1024)
    prs = Presentation(path)

    document = Document(
        slug=source["slug"],
        title=source["title"],
        source_path=path,
        doc_type="slides-pptx",
        page_count=len(prs.slides),
        file_size_mb=round(file_size, 1),
        is_slide_deck=True,
    )

    # Render each slide via LibreOffice → PDF → PyMuPDF
    tmp_dir = tempfile.mkdtemp(prefix="research-pptx-render-")
    pdf_path = _pptx_to_pdf(path, tmp_dir)
    pdf_doc = fitz.open(pdf_path)

    for slide_idx, slide in enumerate(prs.slides):
        page_data = PageData(number=slide_idx + 1)
        text_parts = []
        title_text = None

        for shape in slide.shapes:
            if shape.has_text_frame:
                try:
                    if shape.is_placeholder and shape.placeholder_format.idx == 0:
                        title_text = shape.text_frame.text.strip()
                except (ValueError, AttributeError):
                    pass
                text = shape.text_frame.text.strip()
                if text:
                    text_parts.append(text)

            if shape.shape_type == MSO_SHAPE_TYPE.MEDIA:
                try:
                    name = shape.name or f"video_{slide_idx}"
                    page_data.video_markers.append(name)
                except Exception:
                    pass

        page_data.text = "\n".join(text_parts)
        page_data.heading = title_text

        try:
            if slide.has_notes_slide and slide.notes_slide.notes_text_frame:
                notes = slide.notes_slide.notes_text_frame.text.strip()
                if notes:
                    page_data.notes = notes
        except Exception:
            pass

        # Render the corresponding PDF page (PPTX → PDF preserves slide order 1:1)
        if slide_idx < len(pdf_doc):
            pix = pdf_doc[slide_idx].get_pixmap(matrix=fitz.Matrix(scale, scale))
            page_data.slide_image = ImageData(data=pix.tobytes("png"), ext="png")

        document.pages.append(page_data)

    pdf_doc.close()
    return document


def write_markdown(doc: Document):
    slug_assets = ASSETS_DIR / doc.slug
    slug_assets.mkdir(parents=True, exist_ok=True)

    # Page label: PPTX and slide-deck PDFs both use "Slide". Regular PDFs use "Page".
    page_label = "Slide" if doc.is_slide_deck else "Page"
    prefix = "s" if doc.is_slide_deck else "p"
    # Render-asset suffix: slide-decks render every page as a "slide";
    # paper PDFs render only figure-bearing pages as a "page".
    render_suffix = "slide" if doc.is_slide_deck else "page"
    filename = Path(doc.source_path).name

    lines = [
        "---",
        f"source: {doc.source_path}",
        f"type: {doc.doc_type}",
        f"pages: {doc.page_count}",
        f"slide_deck: {str(doc.is_slide_deck).lower()}",
        "extracted: 2026-04-16",
        f"slug: {doc.slug}",
        "---",
        "",
        f"# {doc.title}",
        "",
        f"> Source: `{filename}` ({doc.page_count} {page_label.lower()}s, {doc.file_size_mb} MB)",
        "",
    ]

    total_images = 0

    for page in doc.pages:
        heading_suffix = f" -- {page.heading}" if page.heading else ""
        lines.append(f"## {page_label} {page.number}{heading_suffix}")
        lines.append("")

        if page.text.strip():
            lines.append(page.text.strip())
            lines.append("")

        # Render the full page (slide-deck: every page; paper-mode: every page
        # too, but with a filename suffix that signals vision-pass scope). The
        # vision agent treats `-page` as in scope and `-text` as out of scope
        # (pure-prose pages, embedded only as a visual reference for math /
        # citation context). Per-figure-cutout extraction was removed because
        # PDF figures are vector composites that PyMuPDF over-segments into
        # meaningless fragments — see SKILL.md "Vision pass MUST run on
        # full-page renders" for the reasoning.
        if page.slide_image is not None:
            if doc.is_slide_deck:
                page_suffix = render_suffix  # always "slide"
            else:
                page_suffix = "page" if page.is_figure_bearing else "text"
            asset_name = f"{prefix}{page.number:03d}-{page_suffix}.{page.slide_image.ext}"
            asset_path = slug_assets / asset_name
            asset_path.write_bytes(page.slide_image.data)
            total_images += 1
            rel_path = f"assets/{doc.slug}/{asset_name}"
            if not doc.is_slide_deck and not page.is_figure_bearing:
                # Reference-only embed: tell the vision agent (and any future
                # pass) explicitly that this page is out of scope for visual
                # description. Cheaper signal than scanning the filename later.
                lines.append("<!-- vision-skip: text-only page (embedded for "
                             "reference / math equation visual) -->")
            lines.append(f"![{asset_name}]({rel_path})")
            lines.append("")

        # Speaker notes (PPTX)
        if page.notes:
            lines.append(f"> **Speaker Notes:** {page.notes}")
            lines.append("")

        # Video markers
        for vid in page.video_markers:
            lines.append(f"<!-- VIDEO: {vid} - TRANSCRIPTION-PENDING -->")
            lines.append("")

        # No OCR-PENDING marker. Phase 2 runs OpenOCR unconditionally on every
        # page render and inserts a delimited `**OCR (auto):**` block; the
        # vision-pass agent integrates it with native text + image content.

    md_path = OUTPUT_DIR / f"{doc.slug}.md"
    force = "--force" in sys.argv
    if md_path.exists() and not force:
        # Randomised suffix so concurrent agents extracting the same slug don't
        # clobber each other's regen sidecar.
        stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        suffix = secrets.token_hex(3)
        regen_path = OUTPUT_DIR / f"{doc.slug}.regen-{stamp}-{suffix}.md"
        regen_path.write_text("\n".join(lines), encoding="utf-8")
        print(
            f"  EXISTS, wrote regenerated draft alongside: {regen_path.relative_to(PROJECT_ROOT)} "
            f"({doc.page_count} pages, {total_images} images)"
        )
        print(f"  (pass --force to overwrite {md_path.relative_to(PROJECT_ROOT)} in place)")
    else:
        md_path.write_text("\n".join(lines), encoding="utf-8")
        print(f"  -> {md_path.relative_to(PROJECT_ROOT)} ({doc.page_count} pages, {total_images} images)")
    return total_images


def write_index(results: list[tuple[dict, int]]):
    """Write a *suggested-rows* side file (NOT index.md) for the agent to merge by hand.

    Historically this rewrote `/mnt/archive4/PAPERS/Prepared/index.md` from scratch, which wiped
    every entry that wasn't part of the current run (memory: feedback_research_index_clobber.md).
    The canonical index is now agent-curated; this function only writes to
    `index_extracted_pending.md` so a human / orchestrator can copy the new rows
    into the real index and delete the stub.
    """
    lines = [
        "<!-- Auto-generated suggested rows from tools/extract_research.py.",
        "     Merge the rows you want into /mnt/archive4/PAPERS/Prepared/index.md by hand,",
        "     then delete this file. NEVER let any tool overwrite index.md. -->",
        "",
        "| Document | Pages | Type | Images |",
        "|----------|-------|------|--------|",
    ]

    for source, img_count in results:
        slug = source["slug"]
        title = source["title"]
        doc_type = source["type"].upper()
        # Re-count from source for page count
        if source["type"] == "pdf":
            doc = fitz.open(source["path"])
            pages = len(doc)
            doc.close()
        else:
            prs = Presentation(source["path"])
            pages = len(prs.slides)

        lines.append(f"| [{title}]({slug}.md) | {pages} | {doc_type} | {img_count} |")

    # Randomised suffix so concurrent agents (or re-runs against the same slug)
    # don't clobber each other's pending sidecar. Each pending file represents
    # one extraction run and is meant to be merged into index.md then deleted.
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    suffix = secrets.token_hex(3)
    pending_path = OUTPUT_DIR / f"index_extracted_pending-{stamp}-{suffix}.md"
    pending_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"  -> {pending_path.relative_to(PROJECT_ROOT)}  (merge into index.md by hand, then delete)")


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    force = "--force" in sys.argv
    only_slugs = set()
    for arg in sys.argv[1:]:
        if arg.startswith("--only="):
            only_slugs.update(arg.split("=", 1)[1].split(","))

    # Marker prepass routing flags (see _MARKER_ENABLED / _MARKER_USE_LLM
    # at module top). `--no-marker` reverts text-paper PDFs to the legacy
    # PyMuPDF span-walker; `--no-llm` runs marker locally without Gemini
    # (no API key needed, lower quality on tables / equations / form fields).
    global _MARKER_ENABLED, _MARKER_USE_LLM, _MARKER_FORCE
    if "--no-marker" in sys.argv:
        _MARKER_ENABLED = False
    if "--no-llm" in sys.argv:
        _MARKER_USE_LLM = False
    if "--force" in sys.argv:
        _MARKER_FORCE = True

    results = []
    for source in SOURCES:
        path = source["path"]
        if not os.path.exists(path):
            print(f"SKIP (not found): {path}")
            continue

        if only_slugs and source["slug"] not in only_slugs:
            continue

        md_path = OUTPUT_DIR / f"{source['slug']}.md"
        # Per-slug existence is now handled inside write_markdown(): if the .md
        # already exists and --force is not passed, it writes a .md.regen sidecar
        # instead of overwriting the (possibly heavily-refined) live extraction.
        # We still skip the full re-extraction in bulk mode (no --only) because
        # there's no point regenerating identical scaffolding 100× per run.
        if md_path.exists() and not force and not only_slugs:
            print(f"SKIP (exists, pass --only=SLUG --force to refresh): {source['slug']}")
            assets_dir = ASSETS_DIR / source["slug"]
            img_count = len(list(assets_dir.glob("*"))) if assets_dir.exists() else 0
            results.append((source, img_count))
            continue

        print(f"Extracting: {source['title']}...")
        if source["type"] == "pdf":
            doc = extract_pdf(source)
        else:
            doc = extract_pptx(source)

        img_count = write_markdown(doc)
        results.append((source, img_count))

    print("\nWriting index...")
    write_index(results)
    print("Done.")


if __name__ == "__main__":
    main()
