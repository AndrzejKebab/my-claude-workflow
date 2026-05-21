#!/usr/bin/env python3
"""Phase 2: PPTX video transcription.

Phase 2 used to run OCR on every referenced image asset, but that role
moved into phase 1 as a body-text fallback (image-only PDFs / slides /
scanned reproductions where there is no native text layer to extract).
Image inclusions inside otherwise-text-rich docs are NEVER OCR'd here —
the vision pass reads them with full visual context and outclasses any
CPU OCR engine; OCR scaffolding alongside an image only narrows what
the vision agent looks at and primes it with mistakes.

What's left for phase 2: extract videos embedded in PPTX decks and
transcribe them with faster-whisper.
"""

import os
import re
import sys
import subprocess
import tempfile
import zipfile
from lxml import etree
from pathlib import Path

# The extracted markdown corpus lives at a single hardcoded global location,
# independent of cwd / which project invoked /research.
OUTPUT_DIR = Path("/mnt/archive4/PAPERS/Prepared")
PROJECT_ROOT = OUTPUT_DIR  # display base for relative_to() in log output
ASSETS_DIR = OUTPUT_DIR / "assets"

# Source files needed for re-rendering pages / extracting videos
SOURCES_BY_SLUG = {
    "rundlett-gustafsson-2025-raytracing-voxels-teardown": {
        "path": "/home/midori/Downloads/Rundlett-Gustafsson-raytracing-voxels-in-teardown-and-beyond.pdf",
        "type": "pdf",
    },
    "preetham-1999-analytic-daylight": {
        "path": "/mnt/archive4/PAPERS/preetham-1999-analytic-daylight.pdf",
        "type": "pdf",
    },
    "muller-rideau-2022-double-word-arithmetic": {
        "path": "/home/midori/Downloads/3484514.pdf",
        "type": "pdf",
    },
    "engel-2007-cascaded-shadow-maps": {
        "path": "/mnt/archive4/PAPERS/engel-2007-cascaded-shadow-maps.pdf",
        "type": "pdf",
    },
    "gao-baidoo-2026-compensated-summation": {
        "path": "/home/midori/Downloads/2602.19452v1.pdf",
        "type": "pdf",
    },
    "thall-2009-extended-precision-gpu": {
        "path": "/home/midori/Downloads/df64_qf128.pdf",
        "type": "pdf",
    },
    "foster-metaxas-1996-realistic-liquid-animation": {
        "path": "/home/midori/Downloads/foster-metaxas-gmip96.pdf",
        "type": "pdf",
    },
    "montoya-2022-teardown-breakdown": {
        "path": "/mnt/archive4/PAPERS/montoya-2022-teardown-breakdown.pdf",
        "type": "pdf",
    },
    "nubis-cubed-2023": {
        "path": "/home/midori/Downloads/Nubis Cubed (Advances 2023).pdf",
        "type": "pdf",
    },
    "horizon-zd-clouds": {
        "path": "/home/midori/Downloads/The Real-time Volumetric Cloudscapes of Horizon - Zero Dawn - ARTR.pdf",
        "type": "pdf",
    },
    "bauer-2019-rdr2-atmospherics": {
        "path": "/mnt/archive4/PAPERS/bauer-2019-rdr2-atmospherics.pptx",
        "type": "pptx",
    },
    "frostbite-pb-volumetrics": {
        "path": "/mnt/archive4/Downloads/Frostbite PB and unified volumetrics.pptx",
        "type": "pptx",
    },
    "karis-2014-temporal-aa": {
        "path": "/mnt/archive4/Downloads/TemporalAA.pptx",
        "type": "pptx",
    },
    "egsr2020": {
        "path": "/home/midori/Downloads/egsr2020.pdf",
        "type": "pdf",
    },
    "s2016-frostbite-sky-clouds": {
        "path": "/home/midori/Downloads/s2016-pbs-frostbite-sky-clouds-new.pdf",
        "type": "pdf",
    },
    "nubis-decima": {
        "path": "/home/midori/Downloads/Nubis - Authoring Realtime Volumetric Cloudscapes with the Decima Engine - Final .pdf",
        "type": "pdf",
    },
    "kuhi-2018": {
        "path": "/home/midori/Downloads/Kuhi_informaatika_2018.pdf",
        "type": "pdf",
    },
    "revision-2013-volumetric": {
        "path": "/home/midori/Downloads/Revision 2013 - Real-time Volumetric Rendering Course Notes.pdf",
        "type": "pdf",
    },
    "oz-volumes": {
        "path": "/home/midori/Downloads/oz_volumes.pdf",
        "type": "pdf",
    },
    "siga21-volume-restir": {
        "path": "/home/midori/Downloads/siga21_volumeReSTIR.pdf",
        "type": "pdf",
    },
    "gjoel-2016-inside-rendering": {
        "path": "/home/midori/Downloads/Gjoel_Svendsen_Rendering_of_Inside.pdf",
        "type": "pdf",
    },
    "fast-flexible-volumetric-light-scattering-notes": {
        "path": "/home/midori/Downloads/Fast Flexible Physically-Based Volumetric Light Scattering - Notes.pdf",
        "type": "pdf",
    },
    "ruijters-volume-rendering-artifacts": {
        "path": "/home/midori/Downloads/2109.13704v2.pdf",
        "type": "pdf",
    },
    "losasso-hoppe-geomclipmap": {
        "path": "/home/midori/Downloads/geomclipmap.pdf",
        "type": "pdf",
    },
    "soderlund-2022-sdf-grid-raytracing": {
        "path": "/home/midori/Downloads/paper-lowres.pdf",
        "type": "pdf",
    },
    "green-2007-sdf-magnification": {
        "path": "/home/midori/Downloads/SIGGRAPH2007_AlphaTestedMagnification.pdf",
        "type": "pdf",
    },
    "tanner-1998-clipmap": {
        "path": "/home/midori/Downloads/Clipmap.pdf",
        "type": "pdf",
    },
    "kuehnert-2022": {
        "path": "/home/midori/Downloads/Thesis-1.pdf",
        "type": "pdf",
    },
    "aaltonen-haar-2015-gpu-driven": {
        "path": "/home/midori/Downloads/aaltonenhaar_siggraph2015_combined_final_footer_220dpi.pdf",
        "type": "pdf",
    },
    "wihlidal-2016-optimizing-graphics-pipeline": {
        "path": "/home/midori/Downloads/Wihlidal_Graham_OptimizingTheGraphics.pdf",
        "type": "pdf",
    },
    "fernando-2001-adaptive-shadow-maps": {
        "path": "/home/midori/Downloads/p387-fernando.pdf",
        "type": "pdf",
    },
    "johnson-2005-irregular-zbuffer": {
        "path": "/home/midori/Downloads/johnson05_irregularzbuf.pdf",
        "type": "pdf",
    },
    "giegl-2007-fitted-virtual-shadow-maps": {
        "path": "/home/midori/Downloads/Fitted_virtual_shadow_maps.pdf",
        "type": "pdf",
    },
    "kolic-2013-camera-space-shadow-maps": {
        "path": "/home/midori/Downloads/12_CSSM.pdf",
        "type": "pdf",
    },
    "olsson-2015-clustered-shadows": {
        "path": "/home/midori/Downloads/clustered_shadows_tvcg.pdf",
        "type": "pdf",
    },
    "sakmary-resolution-matched-virtual-shadow-maps": {
        "path": "/home/midori/Downloads/Sakmary-Resolution-Matched-Virtual-Shadow-Maps.pdf",
        "type": "pdf",
    },
    "premoze-2004-multiple-scattering": {
        "path": "/home/midori/Downloads/premoze04.pdf",
        "type": "pdf",
    },
    "shen-2011-predicted-virtual-soft-shadow-maps": {
        "path": "/home/midori/Downloads/Predicted Virtual Soft Shadow Maps with High Quality Filtering.pdf",
        "type": "pdf",
    },
    "narasimhan-2004-analytic-multiple-scattering": {
        "path": "/home/midori/Downloads/NRN-TR04.pdf",
        "type": "pdf",
    },
    "giegl-2007-queried-virtual-shadow-maps": {
        "path": "/home/midori/Downloads/GIEGL-2007-QV1-Preprint.pdf",
        "type": "pdf",
    },
    "elek-2012-screen-space-scattering": {
        "path": "/home/midori/Downloads/CG_CGASI-2012-09-0082.R1_Elek.pdf",
        "type": "pdf",
    },
    "epic-ue51-virtual-shadow-maps-docs": {
        "path": "/home/midori/Downloads/Virtual Shadow Maps in Unreal Engine _ Unreal Engine 5.1 Documentation _ Epic Developer Community.pdf",
        "type": "pdf",
    },
    "aila-laine-2004-alias-free-shadow-maps": {
        "path": "/home/midori/Downloads/aila2004egsr_paper.pdf",
        "type": "pdf",
    },
    "margolin-1997-vof-cloud-advection": {
        "path": "/home/midori/Downloads/mwre-1520-0493_1997_125_2265_aotvof_2.0.co_2.pdf",
        "type": "pdf",
    },
    "lefohn-2007-resolution-matched-shadow-maps": {
        "path": "/home/midori/Downloads/qt40v513qg.pdf",
        "type": "pdf",
    },
    "hirasawa-2021-flux-interpolated-advection": {
        "path": "/home/midori/Downloads/flux_main.pdf",
        "type": "pdf",
    },
    "sintorn-olsson-2008-alias-free-shadow-volumes": {
        "path": "/home/midori/Downloads/An_Efficient_Alias-free_Shadow_Algorithm_for_Opaqu.pdf",
        "type": "pdf",
    },
    "lauritzen-2010-sample-distribution-shadow-maps": {
        "path": "/home/midori/Downloads/Lauritzen-SDSM(SIGGRAPH 2010 Advanced RealTime Rendering Course).pdf",
        "type": "pdf",
    },
    "salvi-2010-adaptive-volumetric-shadow-maps": {
        "path": "/home/midori/Downloads/avsm_egsr2010_lowres.pdf",
        "type": "pdf",
    },
    "chen-2025-dmd-fluid-subspace": {
        "path": "/home/midori/Downloads/chen2025dmd.pdf",
        "type": "pdf",
    },
    "jin-2015-conservative-semi-lagrangian-ffd": {
        "path": "/home/midori/Downloads/2015-1.pdf",
        "type": "pdf",
    },
    "harris-gpu-gems-ch38-fast-fluid-dynamics": {
        "path": "/home/midori/Downloads/gridFluids_GPU_Gems.pdf",
        "type": "pdf",
    },
    "fais-iorio-2011-ffd-scc": {
        "path": "/home/midori/Downloads/fast-fluid-dynamics-on.pdf_recZxLHseys3jxzKm.pdf",
        "type": "pdf",
    },
    "muller-2009-surface-tracking": {
        "path": "/home/midori/Downloads/surfaceTracking.pdf",
        "type": "pdf",
    },
    "lyu-2021-fluid-solid-coupling": {
        "path": "/home/midori/Downloads/LLDL21.pdf",
        "type": "pdf",
    },
    "batty-2007-variational-coupling": {
        "path": "/home/midori/Downloads/batty-siggraph2007-variationalcoupling.pdf",
        "type": "pdf",
    },
    "drobot-2017-improved-culling": {
        "path": "/mnt/archive4/Downloads/2017_Sig_Improved_Culling_final.pptx",
        "type": "pptx",
    },
    "peters-2017-improved-moment-shadow-maps": {
        "path": "/home/midori/Downloads/Improved Moment Shadow Maps for Translucent_Occluders, Soft Shadows and Single Scattering.pdf",
        "type": "pdf",
    },
    "annen-2008-all-frequency-shadows": {
        "path": "/home/midori/Downloads/1360612.1360633.pdf",
        "type": "pdf",
    },
    "suzuki-yasutomi-2023-gt7-sky-dome": {
        "path": "/home/midori/Downloads/GDC2023_GT7_SKY_RENDERING.pdf",
        "type": "pdf",
    },
    "crassin-2009-gigavoxels-ray-guided-streaming": {
        "path": "/mnt/archive4/PAPERS/crassin-2009-gigavoxels-ray-guided-streaming.pdf",
        "type": "pdf",
    },
    "crassin-2011-gigavoxels-thesis": {
        "path": "/mnt/archive4/PAPERS/crassin-2011-gigavoxels-thesis.pdf",
        "type": "pdf",
    },
    "amanatides-woo-1987-voxel-traversal": {
        "path": "/mnt/archive4/PAPERS/amanatides-woo-1987-voxel-traversal.pdf",
        "type": "pdf",
    },
    "laine-karras-2010-sparse-voxel-octrees": {
        "path": "/home/midori/Downloads/1730804.1730814.pdf",
        "type": "pdf",
    },
    "young-2017-multilevel-voxel": {
        "path": "/home/midori/Downloads/Young_iastate_0097M_16385.pdf",
        "type": "pdf",
    },
    "mittring-2008-advanced-virtual-texture-topics": {
        "path": "/home/midori/Downloads/1404435.1404438.pdf",
        "type": "pdf",
    },
    "gobbetti-marton-2005-far-voxels": {
        "path": "/mnt/archive4/PAPERS/gobbetti-marton-2005-far-voxels.pdf",
        "type": "pdf",
    },
    "blinn-1982-light-reflection-clouds-dusty-surfaces": {
        "path": "/mnt/archive4/PAPERS/blinn-1982-light-reflection-clouds-dusty-surfaces.pdf",
        "type": "pdf",
    },
    "gobbetti-marton-iglesias-guitian-2008-single-pass-gpu-raycasting": {
        "path": "/mnt/archive4/PAPERS/gobbetti-marton-iglesias-guitian-2008-single-pass-gpu-raycasting.pdf",
        "type": "pdf",
    },
    "schwarz-seidel-2010-fast-parallel-voxelization": {
        "path": "/mnt/archive4/PAPERS/schwarz-seidel-2010-fast-parallel-voxelization.pdf",
        "type": "pdf",
    },
    "eisemann-decoret-2008-single-pass-gpu-solid-voxelization": {
        "path": "/mnt/archive4/PAPERS/eisemann-decoret-2008-single-pass-gpu-solid-voxelization.pdf",
        "type": "pdf",
    },
    "frisken-perry-2002-quadtree-octree-traversal": {
        "path": "/mnt/archive4/PAPERS/frisken-perry-2002-quadtree-octree-traversal.pdf",
        "type": "pdf",
    },
    "lefebvre-hoppe-2006-perfect-spatial-hashing": {
        "path": "/mnt/archive4/PAPERS/lefebvre-hoppe-2006-perfect-spatial-hashing.pdf",
        "type": "pdf",
    },
    "knoll-2008-octree-volume-rendering-survey": {
        "path": "/mnt/archive4/PAPERS/knoll-2008-octree-volume-rendering-survey.pdf",
        "type": "pdf",
    },
    "lefebvre-dachsbacher-2007-tiletrees": {
        "path": "/mnt/archive4/PAPERS/lefebvre-dachsbacher-2007-tiletrees.pdf",
        "type": "pdf",
    },
    "lefohn-2006-glift-gpu-data-structures": {
        "path": "/mnt/archive4/PAPERS/lefohn-2006-glift-gpu-data-structures.pdf",
        "type": "pdf",
    },
    "max-1995-optical-models-direct-volume-rendering": {
        "path": "/mnt/archive4/PAPERS/max-1995-optical-models-direct-volume-rendering.pdf",
        "type": "pdf",
    },
    "kajiya-vonherzen-1984-ray-tracing-volume-densities": {
        "path": "/mnt/archive4/PAPERS/kajiya-vonherzen-1984-ray-tracing-volume-densities.pdf",
        "type": "pdf",
    },
    "tatarchuk-2013-destiny-rendering": {
        "path": "/mnt/archive4/PAPERS/tatarchuk-2013-destiny-rendering.pdf",
        "type": "pdf",
    },
    "tatarchuk-2015-applied-graphics-research": {
        "path": "/mnt/archive4/PAPERS/tatarchuk-2015-applied-graphics-research.pdf",
        "type": "pdf",
    },
    "yusov-2013-epipolar-sampling-min-max-trees": {
        "path": "/mnt/archive4/PAPERS/yusov-2013-epipolar-sampling-min-max-trees.pdf",
        "type": "pdf",
    },
    "jarosz-2008-monte-carlo-light-transport-scattering-media": {
        "path": "/mnt/archive4/PAPERS/jarosz-2008-monte-carlo-light-transport-scattering-media.pdf",
        "type": "pdf",
    },
    "toth-umenhoffer-2009-volumetric-lighting-participating-media": {
        "path": "/mnt/archive4/PAPERS/toth-umenhoffer-2009-volumetric-lighting-participating-media.pdf",
        "type": "pdf",
    },
    "bruneton-neyret-2008-precomputed-atmospheric-scattering": {
        "path": "/mnt/archive4/PAPERS/bruneton-neyret-2008-precomputed-atmospheric-scattering.pdf",
        "type": "pdf",
    },
    "keinert-2014-enhanced-sphere-tracing": {
        "path": "/mnt/archive4/PAPERS/keinert-2014-enhanced-sphere-tracing.pdf",
        "type": "pdf",
    },
    "hart-1995-sphere-tracing": {
        "path": "/mnt/archive4/PAPERS/hart-1995-sphere-tracing.pdf",
        "type": "pdf",
    },
    "crassin-2011-voxel-cone-tracing": {
        "path": "/mnt/archive4/PAPERS/crassin-2011-voxel-cone-tracing.pdf",
        "type": "pdf",
    },
    "williams-1983-pyramidal-parametrics": {
        "path": "/mnt/archive4/PAPERS/williams-1983-pyramidal-parametrics.pdf",
        "type": "pdf",
    },
    "ulschmid-2026-naadf-voxel-gi": {
        "path": "/mnt/archive4/PAPERS/ulschmid-2026-naadf-voxel-gi.pdf",
        "type": "pdf",
    },
    "kider-2014-experimental-comparison-skydome-illumination": {
        "path": "/mnt/archive4/PAPERS/kider-2014-experimental-comparison-skydome-illumination.pdf",
        "type": "pdf",
    },
    "wilkie-2021-fitted-radiance-atmosphere": {
        "path": "/mnt/archive4/PAPERS/wilkie-2021-fitted-radiance-atmosphere.pdf",
        "type": "pdf",
    },
    "hosek-wilkie-2012-analytic-skydome": {
        "path": "/mnt/archive4/PAPERS/hosek-wilkie-2012-analytic-skydome.pdf",
        "type": "pdf",
    },
    "nishita-1993-display-of-earth-atmospheric": {
        "path": "/mnt/archive4/PAPERS/nishita-1993-display-of-earth-atmospheric.pdf",
        "type": "pdf",
    },
    "wilkie-hosek-2013-extrasolar-sky-dome": {
        "path": "/mnt/archive4/PAPERS/wilkie-hosek-2013-extrasolar-sky-dome.pdf",
        "type": "pdf",
    },
    "kol-2012-analytical-sky-simulation": {
        "path": "/mnt/archive4/PAPERS/kol-2012-analytical-sky-simulation.pdf",
        "type": "pdf",
    },
    "maquignaz-2024-physically-based-sky-modeling": {
        "path": "/mnt/archive4/PAPERS/maquignaz-2024-physically-based-sky-modeling.pdf",
        "type": "pdf",
    },
    "fang-2025-aokana-voxel-rendering": {
        "path": "/home/midori/Downloads/3728299.pdf",
        "type": "pdf",
    },
    "braley-2010-prediction-buffer-traversal": {
        "path": "/mnt/archive4/PAPERS/braley-2010-prediction-buffer-traversal.pdf",
        "type": "pdf",
    },
    "molenaar-eisemann-2024-svdag-editing": {
        "path": "/mnt/archive4/PAPERS/molenaar-eisemann-2024-svdag-editing.pdf",
        "type": "pdf",
    },
    "wang-2026-llm-long-context-degradation": {
        "path": "/tmp/research-arxiv-2601-15300/2601.15300v1.pdf",
        "type": "pdf",
    },
}


def extract_pptx_videos(pptx_path: str, slug: str) -> dict[str, Path]:
    """Extract all video files from PPTX, return {media_name: output_path}."""
    slug_assets = ASSETS_DIR / slug
    slug_assets.mkdir(parents=True, exist_ok=True)

    extracted = {}
    zf = zipfile.ZipFile(pptx_path)
    for name in zf.namelist():
        if not name.startswith("ppt/media/media"):
            continue
        basename = name.split("/")[-1]
        out_path = slug_assets / basename
        with open(out_path, "wb") as f:
            f.write(zf.read(name))
        extracted[basename] = out_path
    zf.close()
    return extracted


def get_slide_video_map(pptx_path: str) -> dict[int, list[str]]:
    """Map slide numbers to their embedded video filenames."""
    zf = zipfile.ZipFile(pptx_path)
    slide_videos = {}
    for name in sorted(zf.namelist()):
        if not (name.startswith("ppt/slides/_rels/") and name.endswith(".rels")):
            continue
        content = zf.read(name)
        root = etree.fromstring(content)
        videos = []
        for rel in root:
            target = rel.get("Target", "")
            if "media/media" in target:
                videos.append(target.split("/")[-1])
        if videos:
            # slide1.xml.rels -> slide number 1
            slide_name = name.replace("ppt/slides/_rels/", "").replace(".xml.rels", "")
            slide_num = int(re.search(r"(\d+)", slide_name).group(1))
            # Deduplicate
            slide_videos[slide_num] = list(dict.fromkeys(videos))
    zf.close()
    return slide_videos


def has_audio(video_path: str) -> bool:
    """Check if a video file has an audio track."""
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-select_streams", "a",
             "-show_entries", "stream=codec_type", "-of", "csv=p=0", video_path],
            capture_output=True, text=True, timeout=10,
        )
        return "audio" in result.stdout
    except Exception:
        return False


def get_duration(video_path: str) -> float:
    """Get video duration in seconds."""
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "csv=p=0", video_path],
            capture_output=True, text=True, timeout=10,
        )
        return float(result.stdout.strip())
    except Exception:
        return 0.0


def extract_audio(video_path: str, audio_path: str) -> bool:
    """Extract audio from video to WAV for whisper."""
    try:
        subprocess.run(
            ["ffmpeg", "-i", video_path, "-vn", "-acodec", "pcm_s16le",
             "-ar", "16000", "-ac", "1", "-y", audio_path],
            capture_output=True, timeout=60,
        )
        return os.path.exists(audio_path) and os.path.getsize(audio_path) > 1000
    except Exception:
        return False


def transcribe_audio(audio_path: str) -> str:
    """Transcribe audio using faster-whisper."""
    try:
        model = transcribe_audio._model
        segments, info = model.transcribe(audio_path, language="en", beam_size=5)
        text = " ".join(seg.text.strip() for seg in segments)
        return text.strip()
    except Exception as e:
        print(f"    Whisper error: {e}")
        return ""


def load_whisper_model():
    """Load faster-whisper model once."""
    try:
        from faster_whisper import WhisperModel
        print("Loading faster-whisper model (base)...")
        model = WhisperModel("base", device="cpu", compute_type="int8")
        transcribe_audio._model = model
        return True
    except ImportError:
        print("WARNING: faster-whisper not installed, skipping video transcription")
        return False
    except Exception as e:
        print(f"WARNING: whisper load failed: {e}")
        return False


def process_videos(only_slugs: set[str] | None = None):
    """Extract videos, transcribe audio, update markdown."""
    print("\n=== Phase 2b: Video Extraction & Transcription ===\n")

    whisper_available = load_whisper_model()
    video_count = 0
    transcript_count = 0

    for md_file in sorted(OUTPUT_DIR.glob("*.md")):
        slug = md_file.stem
        if only_slugs and slug not in only_slugs:
            continue
        source = SOURCES_BY_SLUG.get(slug)
        if not source or source["type"] != "pptx":
            continue

        content = md_file.read_text(encoding="utf-8")
        if "VIDEO:" not in content:
            continue

        print(f"Processing videos: {slug}...")

        # Extract all videos from PPTX
        video_files = extract_pptx_videos(source["path"], slug)
        print(f"  Extracted {len(video_files)} video files")

        # Get slide-to-video mapping
        slide_map = get_slide_video_map(source["path"])

        # Build a lookup: video_name -> list of slide numbers
        video_to_slides = {}
        for slide_num, vids in slide_map.items():
            for vid in vids:
                video_to_slides.setdefault(vid, []).append(slide_num)

        # Transcribe each unique video
        transcripts = {}
        for vid_name, vid_path in sorted(video_files.items()):
            vid_path_str = str(vid_path)
            duration = get_duration(vid_path_str)
            has_aud = has_audio(vid_path_str)

            print(f"  {vid_name}: {duration:.1f}s, audio={'yes' if has_aud else 'no'}")

            if has_aud and whisper_available:
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                    wav_path = tmp.name
                if extract_audio(vid_path_str, wav_path):
                    text = transcribe_audio(wav_path)
                    if text:
                        transcripts[vid_name] = text
                        transcript_count += 1
                        print(f"    Transcribed: {len(text)} chars")
                    os.unlink(wav_path)
                else:
                    if os.path.exists(wav_path):
                        os.unlink(wav_path)

        # Update markdown: replace VIDEO markers with video links + transcripts
        lines = content.split("\n")
        new_lines = []
        # Find the slide number context for each VIDEO marker
        current_slide = None
        seen_videos_on_slide = {}

        for line in lines:
            m = re.match(r"## Slide (\d+)", line)
            if m:
                current_slide = int(m.group(1))
                seen_videos_on_slide[current_slide] = 0

            video_match = re.search(r"<!-- VIDEO: (.+?) - TRANSCRIPTION-PENDING -->", line)
            if not video_match:
                new_lines.append(line)
                continue

            shape_name = video_match.group(1)
            video_count += 1

            # Find which video file this corresponds to
            vid_filename = None
            if current_slide and current_slide in slide_map:
                slide_vids = slide_map[current_slide]
                idx = seen_videos_on_slide.get(current_slide, 0)
                if idx < len(slide_vids):
                    vid_filename = slide_vids[idx]
                    seen_videos_on_slide[current_slide] = idx + 1

            if vid_filename and vid_filename in video_files:
                rel_path = f"assets/{slug}/{vid_filename}"
                duration = get_duration(str(video_files[vid_filename]))
                new_lines.append(f"**Video:** [{vid_filename}]({rel_path}) ({duration:.1f}s)")
                new_lines.append("")

                if vid_filename in transcripts:
                    new_lines.append(f"> **Transcript:** {transcripts[vid_filename]}")
                    new_lines.append("")
                elif not has_audio(str(video_files[vid_filename])):
                    new_lines.append(f"> *Silent video (no audio track)*")
                    new_lines.append("")
            else:
                # Can't resolve video file — keep a simpler marker
                new_lines.append(f"**Video:** {shape_name} *(embedded, not resolved)*")
                new_lines.append("")

        md_file.write_text("\n".join(new_lines), encoding="utf-8")

    print(f"\nVideos: {video_count} markers processed, {transcript_count} transcribed")
    return video_count, transcript_count


def report_pending_markers():
    """Print the count of unresolved phase-2 markers across all per-slug docs."""
    video_remaining = 0
    for md_file in OUTPUT_DIR.glob("*.md"):
        # Skip non-slug bookkeeping files and per-slug regen sidecars — neither
        # is a canonical extraction, and counting their markers double-counts.
        if md_file.name.startswith("index"):
            continue
        if ".regen-" in md_file.name:
            continue
        text = md_file.read_text(encoding="utf-8")
        video_remaining += text.count("TRANSCRIPTION-PENDING")

    print(f"  Phase 2 marker counts: TRANSCRIPTION-PENDING={video_remaining}")


def main():
    only_slugs: set[str] | None = None
    for arg in sys.argv[1:]:
        if arg.startswith("--only="):
            slugs = {s.strip() for s in arg.split("=", 1)[1].split(",") if s.strip()}
            only_slugs = slugs if slugs else None

    process_videos(only_slugs)
    report_pending_markers()
    print("\nPhase 2 complete.")


if __name__ == "__main__":
    main()
