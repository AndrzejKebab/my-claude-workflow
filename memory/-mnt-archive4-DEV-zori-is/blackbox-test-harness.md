---
name: blackbox-test-harness
description: "zori.is — all Rust CA tests drive the headless Simulation; partitions are config, gravity is eased"
metadata: 
  node_type: memory
  type: project
  originSessionId: 86b27887-66d1-4fcd-9884-31d082163037
---

zori.is CA tests are end-to-end black-box (no `World::step*`/`step_banded`/`integrate_range`/internals, no bespoke `SimParams`). Drive `crate::ca::simulation::Simulation` (the headless, scriptable falling-sand sim): control signals in (paint/fill/spawn_particle/stroke/shake/set_tilt/set_weather + registry `set_scalar`/`set_bool`), the shared per-tick conductor `TickDirector::prepare_tick` (`ca/tick_director.rs`, also used by the live browser `Ca` in `ca/driver.rs`) + the production banded executor `World::step_banded_schedule`, pixel/material metrics out (material_at/count_material/packed_grid/sand_centroid/airborne).

Names landed via the domain rename (commit on api-haus/particle-fix): `Simulation` (was CaApp, `ca/simulation.rs`), `TickDirector` (was CaCore, `ca/tick_director.rs`, returns `PreparedTick`). Tests are flat in `src/ca/world/`: `sim_fixture.rs` (helpers), `flow_tests.rs`, `gravity_tests.rs`, `weather_tests.rs`, `particle_tests.rs`, `scheduling_tests.rs`, `determinism_tests.rs` (jitter + band-equivalence).

Non-obvious conventions (`sim_fixture.rs`):
- `pure_ca(w,h,seed)` pins `gravity.response=1, damping=0` so the *eased* gravity vector equals its target immediately and stays constant — this is how you reproduce a fixed `params.gravity`. `set_gravity`/`set_gravity_dir` aim it via strength + device tilt (there is no "set gravity vector" API; the real app only eases).
- Partitions/schedules are first-class config: `ca.scheduling_mode` 0 jitter, 1 two-offset, 2 jit+2off, 3 gold, 4 aligned; band count via `Simulation::set_band_count`; `ca.dda_travel`. Band-equivalence tests run the same scenario at band 1 vs N and compare `packed_grid()`.
- Weather/phase tests enable weather and `set_weather(WeatherSample{..})` (the Scene→sim path), then set `phase.*` rates; weather-on enables default phase rates (snow melts at 15C unless you zero them).
- Pre-existing-failing cure-gates (lattice/seam artifact not fixed) are kept as measurement (scorecard output), not red asserts.

Rule is codified in `~/.claude/CLAUDE.md`: never write unit tests; all tests end-to-end black box; feature gates are app config. See [[handoff-not-supervised-dispatch]].
