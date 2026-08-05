# VoxelQuest Project Memory

## Successful Revival Build (2026-02-04)

Built on: CachyOS (Linux 6.18.7-2), GCC 15.2.1, CMake 4.2.3

### Key Fixes Applied

1. **CMake/Hunter Updates**
   - Updated `cmake_minimum_required` to 3.15
   - Updated Hunter to v0.26.6
   - Set `CMAKE_POLICY_VERSION_MINIMUM=3.5` env var for Hunter compatibility
   - Use system GLFW on Linux to avoid building X11

2. **POSIX Socket Compatibility** (gamenetwork.cpp/h)
   - Added POSIX socket includes and compatibility macros
   - Platform guards for WSADATA/SOCKET types

3. **GCC 15 Strictness Fixes**
   - Added missing includes: `<cmath>`, `<cstring>`, `<cfloat>`, `<string>`, `<sys/time.h>`
   - Fixed rvalue address errors (Stringify() calls in settings.cpp, gameorg.cpp, cache.cpp)
   - Fixed goto crossing initialization (gamelogic.cpp, gameworld.cpp) with scope blocks
   - Fixed extra class qualification in settings.h
   - Added M_PI guard in constants.h
   - Renamed shadowed `glInfo` member in dynbuffer.h

4. **OpenGL Loader Migration**
   - Replaced GLEW with glbinding initialization in initGlew.cpp
   - Created imgui_gl_glbinding.h wrapper for imgui backends

5. **Windows-Only Code Guards**
   - Wrapped wglSwapIntervalEXT in `#ifdef _WIN32`

### Build Command
```bash
mkdir -p build && cd build
CMAKE_POLICY_VERSION_MINIMUM=3.5 cmake ..
cmake --build .
```
