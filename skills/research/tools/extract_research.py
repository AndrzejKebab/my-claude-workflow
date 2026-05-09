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

# Resolve output dir from the *invocation cwd*, not the script location.
# The skill scripts ship at ~/.claude/skills/research/tools/ but write to the
# project's docs/research/. The agent runs the script from the project root.
PROJECT_ROOT = Path(os.environ.get("RESEARCH_PROJECT_ROOT", os.getcwd())).resolve()
OUTPUT_DIR = PROJECT_ROOT / "docs" / "research"
ASSETS_DIR = OUTPUT_DIR / "assets"

SOURCES = [
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


def extract_pdf(source: dict, scale: float = 2.0) -> Document:
    """Extract PDF.

    For slide-deck PDFs (detected via metadata + aspect ratio), each page is
    rendered as a single PNG (`pNNN-slide.png`) — no per-figure cutout
    extraction, since slide-deck PDFs decompose visuals into many small
    embedded image objects that lose meaning when separated.

    For regular PDFs (papers, technical reports), embedded images are
    extracted as figures and saved as `pNNN-figXX.png`.
    """
    path = source["path"]
    file_size = os.path.getsize(path) / (1024 * 1024)
    doc = fitz.open(path)

    forced = source.get("slide_deck")
    slide_deck = forced if forced is not None else is_slide_deck_pdf(doc)

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

        # Extract text with structure (for both modes — text layer is independent of imagery)
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
            # Slide-deck mode: render the whole page once. No per-figure cutouts.
            pix = page.get_pixmap(matrix=fitz.Matrix(scale, scale))
            page_data.slide_image = ImageData(data=pix.tobytes("png"), ext="png")
        else:
            # Paper mode: extract embedded images as figures.
            # Honour the page's display rotation — PDF stores rotation as a
            # display-time hint (clockwise degrees) and the underlying image
            # bytes are unrotated. Without this, scanner-produced PDFs (which
            # commonly tag rotation=180) extract upside-down.
            image_list = page.get_images(full=True)
            page_rot = page.rotation  # 0 / 90 / 180 / 270
            for img_info in image_list:
                xref = img_info[0]
                try:
                    pix = fitz.Pixmap(doc, xref)
                    if pix.width < 32 or pix.height < 32:
                        continue
                    if pix.n > 4 or pix.n == 4:
                        pix = fitz.Pixmap(fitz.csRGB, pix)
                    png_bytes = pix.tobytes("png")
                    if page_rot:
                        # PIL.rotate is counter-clockwise; PDF rotation is clockwise.
                        img = Image.open(io.BytesIO(png_bytes))
                        img = img.rotate(-page_rot, expand=True)
                        buf = io.BytesIO()
                        img.save(buf, format="PNG")
                        png_bytes = buf.getvalue()
                    page_data.images.append(ImageData(data=png_bytes, ext="png"))
                except Exception:
                    continue

        # Body-text OCR fallback: when the page has no native text layer
        # (typical of scanned PDFs and image-only slides exported as
        # raster), OCR the page's own image asset and use the result as
        # the page body. This is the ONLY path on which OCR enters the
        # canonical document body — image inclusions inside a text-rich
        # doc are NEVER OCR'd here. The vision pass reads images directly
        # with full visual context and outclasses any CPU OCR engine; OCR
        # scaffolding alongside an image only narrows what the vision
        # agent looks at and primes it with mistakes.
        if len(page_data.text.strip()) < 20:
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

        # Slide-deck mode: ONE rendered slide image per page.
        if page.slide_image is not None:
            slide_name = f"{prefix}{page.number:03d}-slide.{page.slide_image.ext}"
            slide_path = slug_assets / slide_name
            slide_path.write_bytes(page.slide_image.data)
            total_images += 1
            rel_path = f"assets/{doc.slug}/{slide_name}"
            lines.append(f"![{slide_name}]({rel_path})")
            lines.append("")

        # Paper mode: per-figure cutouts
        for fig_idx, img in enumerate(page.images):
            fig_name = f"{prefix}{page.number:03d}-fig{fig_idx + 1:02d}.{img.ext}"
            fig_path = slug_assets / fig_name
            fig_path.write_bytes(img.data)
            total_images += 1
            rel_path = f"assets/{doc.slug}/{fig_name}"
            lines.append(f"![{fig_name}]({rel_path})")
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

    Historically this rewrote `docs/research/index.md` from scratch, which wiped
    every entry that wasn't part of the current run (memory: feedback_research_index_clobber.md).
    The canonical index is now agent-curated; this function only writes to
    `index_extracted_pending.md` so a human / orchestrator can copy the new rows
    into the real index and delete the stub.
    """
    lines = [
        "<!-- Auto-generated suggested rows from tools/extract_research.py.",
        "     Merge the rows you want into docs/research/index.md by hand,",
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
