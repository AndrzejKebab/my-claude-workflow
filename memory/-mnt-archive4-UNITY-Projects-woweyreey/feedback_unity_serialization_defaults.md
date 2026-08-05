---
name: Don't flag Unity serialization defaults on new fields
description: When adding a new serialized field (bool/float/int/enum) to a type with existing .asset/.prefab/.unity instances, don't warn about defaults — user knows and it's never an issue.
type: feedback
originSessionId: 54fcb518-eed1-4c6d-a6e3-73f6941176ce
---
Do not treat Unity's "new field defaults to zero/false on existing assets" behaviour as a caveat worth raising.

**Why:** The user is deeply familiar with Unity serialization and treats zero/false defaults on pre-existing assets as expected, not as a footgun. Flagging it every time adds noise without informing.

**How to apply:** When adding a new `public bool`/`float`/`int`/`enum` field to a `Serializable` type (CloudSettings, similar presets, ScriptableObjects, MonoBehaviour inspector fields), just land the change. Don't mention that existing `.asset` files will show the default value until re-saved, don't suggest ticking a checkbox first — the user will handle the asset-side toggles on their own when testing.

Only mention it if the default value is load-bearing for *correctness* (e.g. a new field whose zero value would crash or produce silently-wrong behaviour that isn't obvious from visual inspection). Pure artistic / opt-in behaviour toggles: silent.
