# Memory index

- [voxelworld foundations spec](voxelworld-foundations-spec.md) — locked core decisions (C++ core, URP, 24 km², brush-entity model, 60 Hz dig+paint) and journal pointers
- [steamdeck transient drops](steamdeck-transient-drops.md) — the Deck naps off-network then returns on the same IP; one failed ssh probe is not "offline"
- [astroneer terrain talk does not exist](astroneer-terrain-talk-does-not-exist.md) — searched exhaustively; only a Twitch interview exists, and it says nothing about materials
- [no sabotage arms, TDD instead](no-sabotage-arms-tdd-instead.md) — arms/biters prohibited, write the test red first; graphics ships before it gets gated
- [port verbatim, don't re-derive](port-verbatim-dont-rederive.md) — copy bevy_voxel_world line by line; re-deriving its intent is what produced the overengineering
- [calibrate instruments before trusting](calibrate-instruments-before-trusting.md) — five metrics measured themselves in one session; every gate needs a known-answer case asserted first
