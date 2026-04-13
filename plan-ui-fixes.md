# UI Fix Plan — Anima Isle Frontend
> Source of truth: Figma file `cCVGXRmqJjjUrCYi6fmgm3`
> Based on: `research-ui.md` + Figma MCP design context fetches
> Status: PLAN ONLY — no code modified

**Fetch failures** (nodes no longer in file):
- `31:120` — frosted glass panel (planned from issue brief only)
- `337:2` — header variant (planned from 1:413 + 1:352 comparison)

---

## [P0] Issue 8 — 共感群岛 island selection broken

### PART A — Click detection fix

**Figma spec:** N/A — this is an interaction/code bug, not a visual spec.

**Current state (from code audit):**

The map page template renders children of `.square-map-page__artboard` in this DOM order:

```
1. outline layers (v-for selectionOutlineLayers)     ← z-index: unset
2. ribbon-shell--outline (v-if 'current')             ← z-index: 0, NO pointer-events:none
3. ALL scene layers (v-for sceneLayers)              ← pointer-events: none ✓
4. ribbon-shell (always rendered)                    ← position:absolute, NO pointer-events:none
5. hotspots (v-for hotspotIslands)                   ← z-index: 3, opacity: 0.001
```

Three concrete blockers identified:

**Blocker 1 — `.square-map-page__ribbon-shell` has no `pointer-events: none`.**
The ribbon shell sits at `left: 269rpx; top: 1128rpx; width: 424rpx; height: 463rpx` in the artboard. The 'current' island hotspot occupies `left: 286rpx; top: 1246rpx; width: 322rpx; height: 188rpx`. These two rectangles overlap by ~322×188rpx. Because the ribbon-shell has no `pointer-events: none`, it is a tap absorber competing with the hotspot beneath it for the 'current' island.

**Blocker 2 — Hotspot `opacity: 0.001` is platform-unreliable.**
On some WeChat MiniProgram device/SDK combinations, elements with opacity below `0.01` may be skipped in hit-testing. The standard pattern in WeChat is `opacity: 0` (which DOES receive touch events on WeChat) or using `visibility: visible` + transparent background without opacity. The `0.001` value sits in an undefined behaviour zone.

**Blocker 3 — `.square-map-page__scene` container has no `pointer-events: none`.**
The scene is `position: absolute; inset: 0` covering the full page. Without `pointer-events: none`, every tap that falls on the scene background (between islands) is consumed by the scene container itself and never reaches the page's underlying tap handlers. This is not broken per se (hotspots are inside the scene and still receive taps), but the scene container creates unnecessary capture surface. The artboard and ribbon-shell also have no `pointer-events: none`, creating overlapping capture areas.

**Delta:**

| Element | Current | Required |
|---|---|---|
| `.square-map-page__scene` | no `pointer-events` set | `pointer-events: none` |
| `.square-map-page__artboard` | no `pointer-events` set | `pointer-events: none` |
| `.square-map-page__ribbon-shell` | no `pointer-events` set | `pointer-events: none` |
| `.square-map-page__ribbon-shell--outline` | no `pointer-events` set | `pointer-events: none` |
| `.square-map-page__hotspot` | `opacity: 0.001` | `opacity: 0` |
| `.square-map-page__hotspot` | `pointer-events` unset | `pointer-events: auto` (explicit override) |

**Files to modify:** `frontend/src/modules/square/pages/map/index.vue`

**Changes (scoped SCSS only):**
```scss
// CHANGE: scene container
.square-map-page__scene {
  pointer-events: none;    // ADD
}

// CHANGE: artboard — all its children are decorative or hotspots; 
// hotspots override below
.square-map-page__artboard {
  pointer-events: none;    // ADD
}

// CHANGE: ribbon shells
.square-map-page__ribbon-shell {
  pointer-events: none;    // ADD
}

// CHANGE: hotspot — must RESTORE pointer events after parent disables them
.square-map-page__hotspot {
  opacity: 0;              // WAS: 0.001
  pointer-events: auto;    // ADD (overrides artboard: none)
}
```

**Risk:** Low. `pointer-events: none` on the scene and artboard is safe because the hotspots explicitly override with `pointer-events: auto`. The `opacity: 0` change on WeChat is behaviour-neutral since WeChat receives tap events on opacity:0 elements unlike browsers.

---

### PART B — Selected state glow

**Figma spec (node 465:219):**
- A white-blue glowing island silhouette outline
- The glow SVG bleeds `-11.57%` top/bottom and `-13.24%` left/right beyond its bounding box
- Effect: soft halo of white-blue light tracing the island edge
- Visual weight: clearly visible, not subtle — the glow is the primary selection indicator

**Current state:**

The outline layers ARE rendered in the template when `selectedIslandId` is set, but they have a **critical layering bug**:

The current template DOM order inside `__artboard` is:
```
1. outline layers (v-for selectionOutlineLayers)   ← RENDERED FIRST = bottom of stack
2. ribbon outline
3. ALL scene layers                                 ← RENDERED AFTER = on top of outline!
4. hotspots
```

The outline layers are rendered **beneath** the full scene layers. Because the scene layers are opaque SVG artworks that cover the entire artboard area, the outline glow underneath is fully hidden. It never appears on screen — which is why selection looks broken.

**Delta:**

The outline layers must render **after** all base scene layers, not before. Additionally, the outline requires a stronger visual specification and an `--outline` class modifier that produces a clearly visible glow (not just blur + reduced opacity).

**Files to modify:** `frontend/src/modules/square/pages/map/index.vue`

**Changes:**

1. **Reorder template**: Move outline layer rendering to AFTER the `v-for sceneLayers` block and AFTER `ribbon-shell`, so they sit visually on top of the scene.

```html
<!-- BEFORE (broken order): -->
<image v-for="outline layers" />       ← buried under scene
<view ribbon-shell--outline />
<image v-for="sceneLayers" />          ← covers outline
<view ribbon-shell />
<view v-for="hotspots" />

<!-- AFTER (fixed order): -->
<image v-for="sceneLayers" />          ← base scene first
<view ribbon-shell />                  ← ribbon over scene
<image v-for="outline layers" />       ← GLOW ON TOP of scene ✓
<view ribbon-shell--outline />         ← ribbon outline on top ✓
<view v-for="hotspots" />              ← hotspots last (transparent tap targets)
```

2. **Strengthen the outline glow visual** — current values from `selectedOutlineStyle`:
   - `opacity: islandConfig.value.outlineOpacity` (range: 0.82–0.96)
   - `filter: blur(islandConfig.value.outlineBlur)` (range: "16rpx"–"22rpx")

   These values are already reasonable. The fix above (reordering) should make the glow visible. After reordering, verify blur amounts are sufficient; adjust per-island in `ISLAND_CONFIGS` if needed.

3. **Interaction behaviour**: The current `selectIsland()` logic is correct:
   - First tap on island A → `selectedIslandId = A` (sets selection, renders glow)
   - Second tap on same island A → navigates to island detail
   - Tap on island B while A selected → `selectedIslandId = B` (switches selection)
   
   No logic changes needed — the interaction model is already correctly implemented.

4. **Add CSS transition** for the glow appearing on first tap. The `--outline` layers have `transition: opacity 180ms ease, filter 180ms ease` already. No change needed.

**Risk:** Medium. Reordering DOM elements is a safe SCSS-free change, but must be verified visually on device. The ribbon outline for 'current' island depends on `v-if="selectedIslandId === 'current'"` — verify the condition still reads correctly after the reorder.

---

### PART C — Island detail page visual

**Figma spec (nodes 465:219, 20:174):**
**Scene composition:**
- Active island: highlighted (full brightness, no filter)
- All other islands/background: significantly darkened — `filter: brightness(0.34) saturate(0.78)` in current code matches the intent
- Dim mask: should be a simple dark semi-transparent overlay, NOT the night gradient
- Active island outline glow: same as Part B — the selected island's outline SVG layers should render with blur+opacity on top of the scene

**Tag bubbles (node 20:174 — `tag_bubbel_selected`):**

Figma spec:
```
border-radius:   100px (fully pill / ≈200rpx in rpx)
box-shadow:      0 0 24px rgba(255, 255, 255, 0.25)   ← outer glow
background:      radial-gradient from bottom-left corner:
                   rgba(141, 234, 255, 0.24) at 19.87%
                 → rgba(198, 244, 255, 0.62) at 59.94%
                 → rgba(255, 255, 255, 1.0) at 100%
font:            HYShuSongEr, 12px (≈24rpx), white, tracking 0.5px
text-shadow:     0 0 4px rgba(255, 255, 255, 0.37)
```

Current `IslandTagChip` state:
```scss
.island-tag-chip {
  border-radius: 999rpx;           // close but too large a value; 200rpx preferred
  box-shadow: 0 0 8rpx rgba(255, 255, 255, 0.5);   // WRONG: too tight (8rpx vs 24px)
  background: rgba(255, 255, 255, 0.03);           // WRONG: plain translucent vs radial gradient
}
.island-tag-chip__label {
  font-size: 22rpx;                // WRONG: should be 24rpx (≈12px × 2)
  color: var(--anima-text-dim);    // WRONG: should be #ffffff (pure white)
}
```

**Tag counts per island size (already in island configs — verify):**
- small islands (pebble, sprout, azure): 2–3 `tagSlots` ✓ (pebble=2, sprout=3, azure=3)
- medium islands (ember, lagoon, mist): 3–4 `tagSlots` ✓ (ember=3, lagoon=4, mist=4)
- large island (current): 5 `tagSlots` ✓
- No overflow possible since `islandBubbles` maps slots 1:1 to `tagSlots.length`

**Dim mask:**
```scss
// CURRENT (wrong — uses gradient not overlay):
.square-island-page__dim-mask {
  background: var(--anima-night-gradient);
  opacity: 0.76;
}

// REQUIRED (plain dark overlay):
.square-island-page__dim-mask {
  background: rgba(5, 11, 24, 0.72);   // straight dark overlay
  opacity: 1;                           // no double-opacity
}
```

**Entry animation (camera push-in):**
Currently the artboard transform (`sceneTransform`) is applied statically with no animation. To feel like a camera push-in, add a CSS transition on the artboard transform that fires on page load.
**NOTE RESOLVED — Animation trigger:** `nextTick` is unreliable for triggering CSS transitions in UniApp. Use `setTimeout(fn, 50)` instead. The script change is:
- Add `const sceneReady = ref(false)` 
- In `onLoad`, after data loads: `setTimeout(() => { sceneReady.value = true }, 50)`
- `sceneTransform` computed: when `!sceneReady`, return identity `"translate(0,0) scale(1)"`; otherwise return the real transform
- The CSS `transition` on `__artboard` then plays the push-in automatically

```scss
// ADD to .square-island-page__artboard:
.square-island-page__artboard {
  transition: transform 520ms cubic-bezier(0.22, 1, 0.36, 1);
  will-change: transform;
}
```

In the `<script setup>`, apply transform with a micro-delay after mount so the transition plays:
- On `onLoad`, set a `sceneReady` ref to `false` initially (no transform)
- After a `nextTick`, set `sceneReady = true` to trigger the transition

**Files to modify:**
- `frontend/src/modules/square/pages/island/index.vue`
- `frontend/src/modules/square/components/IslandTagChip.vue`

**Changes — `IslandTagChip.vue`:**
```scss
.island-tag-chip {
  border-radius: 200rpx;                    // WAS: 999rpx
  box-shadow: 0 0 48rpx rgba(255, 255, 255, 0.25);  // WAS: 8rpx 0.5 → 48rpx 0.25 (rpx = 24px×2)
  // NOTE RESOLVED: Figma matrix gradient origin is bottom-left → circle at 20% 80%
  background: radial-gradient(
    circle at 20% 80%,
    rgba(141, 234, 255, 0.24) 0%,
    rgba(198, 244, 255, 0.62) 60%,
    rgba(255, 255, 255, 1.0) 100%
  );                                         // WAS: rgba(255,255,255,0.03)
}


.island-tag-chip__label {
  font-size: 24rpx;                          // WAS: 22rpx
  color: #ffffff;                            // WAS: var(--anima-text-dim)
}
```

**Changes — `island/index.vue` scoped SCSS:**
```scss
.square-island-page__dim-mask {
  background: rgba(5, 11, 24, 0.72);        // WAS: var(--anima-night-gradient)
  opacity: 1;                               // WAS: 0.76
}

.square-island-page__artboard {
  transition: transform 520ms cubic-bezier(0.22, 1, 0.36, 1);   // ADD
  will-change: transform;                    // ADD
}
```

**Changes — `island/index.vue` layout rule compliance:**

The `__bubble` elements are `position: absolute; z-index: 4` over the `__viewport`. The `tagSlots` coordinates are artboard-relative rpx values (the positions are meaningful only within the 750×1624rpx artboard coordinate space). The layout rule says no new absolute positioning outside decoration — these bubbles ARE overlaying a specific artboard position (not arbitrary layout), so they stay absolute. No change needed for the bubbles' position strategy, but **convert the page's non-scene content (hero title, subtitle, transport message, topbar) to use a proper flex column layout** rather than relying on `position: relative; margin-top: X` stacking.

```scss
// ADD: a flex wrapper for the above-scene content
.square-island-page__header-content {
  position: relative;
  z-index: 3;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 0 32rpx;
}
```

This avoids separate `margin-top` on each text element. The scene then follows as a sibling block.

**Risk:** Medium. The `IslandTagChip` change affects all uses of the component across the app — verify no other page uses this component with different styling expectations. The dim mask change alters the visual significantly; the opacity of `0.72` may need tweaking after visual review.

---

## [P1] Issue 1 — Global background ripple (dark-bg.png)

**Figma spec:** No specific node — the issue brief describes the ripple as "barely visible."

**Current state:**

`DarkBackgroundLayer.vue` renders `dark-bg.png` with:
- `opacity: textureOpacity` (default `0.3`, passed from `StageViewportShell`)
- CSS `filter: saturate(0.9) brightness(0.82)` — further dims the texture
- No `mix-blend-mode`

`StageViewportShell` is used only by `publish/index.vue`. The `map/index.vue` and `island/index.vue` use `--anima-night-gradient` directly with **no texture layer at all**.

Combined effective opacity: `0.3 × 0.82 brightness` ≈ effectively ~24% visibility with desaturation. The texture is nearly invisible.

**Delta:**

| Property | Current | Required |
|---|---|---|
| `textureOpacity` default | `0.3` | `0.55` |
| `filter` on texture image | `saturate(0.9) brightness(0.82)` | `saturate(1.0) brightness(0.95)` |
| `mix-blend-mode` | not set | `overlay` |
| Presence on map + island pages | not present | add `DarkBackgroundLayer` |

**Files to modify:**
- `frontend/src/shared/components/DarkBackgroundLayer.vue`
- `frontend/src/shared/components/StageViewportShell.vue` (default prop)
- `frontend/src/modules/square/pages/map/index.vue`
- `frontend/src/modules/square/pages/island/index.vue`

**Changes — `DarkBackgroundLayer.vue`:**
```scss
.dark-background-layer__texture {
  filter: saturate(1.0) brightness(0.95);    // WAS: saturate(0.9) brightness(0.82)
  mix-blend-mode: overlay;                   // ADD
}
```

**Changes — `StageViewportShell.vue`:**
```ts
withDefaults(defineProps<{ viewportMaxWidth?: string; textureOpacity?: number }>(), {
  viewportMaxWidth: "820rpx",
  textureOpacity: 0.55,    // WAS: 0.3
})
```

**Changes — `map/index.vue` and `island/index.vue`:**
Add `<DarkBackgroundLayer :texture-opacity="0.55" />` as the first child of `square-map-page` and `square-island-page` respectively. Import `DarkBackgroundLayer` from `@/shared/components/DarkBackgroundLayer.vue`.

This is a **background decoration layer** so `position: absolute` is permitted by the layout rules.

**Risk:** Low on publish page (props change only). Medium on map/island pages — the texture image on top of the gradient changes the overall feel. The `mix-blend-mode: overlay` means the texture will affect both dark and light parts of the gradient differently. Review carefully on device — if overlay is too intense, fall back to `mix-blend-mode: soft-light`.

---

## [P1] Issue 2 — IP character glow and page halo

**Figma spec (four nodes):**

| Node | Page context | Shape | Gradient | Blur | Size |
|---|---|---|---|---|---|
| `1:665` | login / register | pill (fully circular) | `rgba(116,212,234,0.55) → rgba(90,166,183,0.535) → rgba(65,120,132,0.52)` at 0%, 12.74%, 25.48% | 64px (128rpx) | 347px ≈ 694rpx |
| `35:40` | chat home | raster ellipse PNG (large semi-circle glow at screen bottom) | N/A — image asset | N/A | fills screen width |
| `1:229` | chat active / IP glow | pill | `rgba(116,212,234,1.0) → rgba(90,166,183,1.0) → rgba(65,120,132,1.0)` fully opaque | 64px (128rpx) | 272px ≈ 544rpx |
| `1:58` | thinking / generating | pill | `rgba(116,212,234,0.36) → rgba(160,214,214,0.68) → rgba(203,215,194,1.0)` (warm greenish) | 64px (128rpx) | 386px ≈ 772rpx |

The node `35:40` renders as a raster image (`Ellipse14` — a PNG of a large circular glow). The others are pure CSS radial gradients with 64px blur.

**Mapping to `--anima-*` tokens in `theme.scss`:**

| Token | Used for | Matches Figma? |
|---|---|---|
| `--anima-glow-auth` | login/register | Partially: stops are 0.55/0.42/0 vs Figma 0.55/0.535/0.52 (fade is too fast) |
| `--anima-glow-chat` | chat active | Partially: stops are 0.85/0.48/0 at 0/32/70% vs Figma 1.0/1.0/1.0 at 0/12.74/25.48% (much weaker) |
| `--anima-glow-cabin-halo` | cabin (matches `1:229` spec) | ✓ matches `1:229` |
| None | generating / thinking | `1:58` has no corresponding token |

**Delta — `theme.scss` token corrections:**

```scss
// WAS:
--anima-glow-auth: radial-gradient(circle, rgba(116,212,234,0.55) 0%, rgba(90,166,183,0.42) 26%, rgba(65,120,132,0) 66%);

// REQUIRED (matches 1:665):
--anima-glow-auth: radial-gradient(circle, rgba(116,212,234,0.55) 0%, rgba(90,166,183,0.535) 12.74%, rgba(65,120,132,0.52) 25.48%, rgba(65,120,132,0) 100%);
```

```scss
// WAS:
--anima-glow-chat: radial-gradient(circle, rgba(116,212,234,0.85) 0%, rgba(90,166,183,0.48) 32%, rgba(65,120,132,0) 70%);

// REQUIRED (matches 1:229 — this is the IP glow, fully saturated core):
--anima-glow-ip-core: radial-gradient(circle, rgba(116,212,234,1.0) 0%, rgba(90,166,183,1.0) 12.74%, rgba(65,120,132,0) 25.48%);
// NOTE: 1:229 is 272px wide; --anima-glow-cabin-halo already matches this exactly
// --anima-glow-chat is a DIFFERENT use (chat page ambient, not IP core glow) — keep separately
```

```scss
// ADD new token for generating/thinking state (matches 1:58):
--anima-glow-generating: radial-gradient(circle, rgba(116,212,234,0.36) 0%, rgba(160,214,214,0.68) 12.74%, rgba(203,215,194,1.0) 25.48%, rgba(203,215,194,0) 100%);
```

**Per-page implementation spec:**

| Page | Halo to use | Size | Position | Blend mode |
|---|---|---|---|---|
| login / register | `--anima-glow-auth` | 694rpx × 694rpx | Centered horizontally, bottom ~40% of viewport | `mix-blend-mode: screen` |
| chat home | node `35:40` PNG image | 100% viewport width | `position: absolute; bottom: 0; left: 0; right: 0` | `mix-blend-mode: screen` |
| chat active (IP visible) | `--anima-glow-cabin-halo` | 544rpx × 544rpx | Centered on IP character | `mix-blend-mode: screen` |
| generating / thinking | `--anima-glow-generating` | 772rpx × 772rpx | Centered horizontally, centered vertically | `mix-blend-mode: screen` |

**Implementation pattern (shared across pages):**

Each halo is a `position: absolute; pointer-events: none` decoration view behind the IP character:

```vue
<view class="page-halo" />
```

```scss
.page-halo {
  position: absolute;       // decoration layer — permitted by layout rules
  pointer-events: none;
  border-radius: 50%;
  background: var(--anima-glow-auth);  // swap per page
  filter: blur(128rpx);    // 64px × 2 = 128rpx
  mix-blend-mode: screen;
  // size and position per table above
}
```

**Files to modify:**
- `frontend/src/shared/styles/theme.scss` (token corrections + new token)
- `frontend/src/modules/auth/pages/login/index.vue` (read before implementing)
- `frontend/src/modules/auth/pages/register/index.vue` (read before implementing)
- `frontend/src/modules/chat/pages/home/index.vue` (read before implementing)
- `frontend/src/modules/chat/pages/cabin/index.vue` (read before implementing)
- `frontend/src/modules/chat/pages/generating/index.vue` (read before implementing)
- `frontend/src/shared/assets/index.ts` (add `35:40` ellipse PNG if not already present)

**Risk:** Medium. These pages were not read during research — must read each file before touching. The `mix-blend-mode: screen` on the halo only works correctly on dark backgrounds; verify that none of these pages have light elements near the halo position.

---

## [P2] Issue 3 — 成为屿民 page

**Figma spec:**

| Node | Role | Spec |
|---|---|---|
| `31:59` | Background hero image | `height: 113.64%` (overflows container), `top: -0.02%`. Full-bleed island/night sky AI photo. |
| `31:61` | Gradient overlay on image | `linear-gradient(to top, #354278 12.5%, rgba(78,94,162,0.62) 59.135%, rgba(108,130,225,0) 100%)` |
| `32:120` | Frosted glass panel | Node not in file — spec from brief: more transparent, lighter, text must not overflow |
| `33:178` | Resident ticket card | `inset: [-5.11%_-10.85%_-6.57%_-10.85%]` — image bleeds beyond container. Must be centered. |

**Current state:** Not read during research. Must read `frontend/src/modules/auth/pages/resident/index.vue` before implementing.

**Delta (from Figma data):**

**31:59 → 31:61 gradient transition:**

The background image sits at 113.64% height, slightly overflowing. The gradient overlay (`31:61`) blends the bottom of the image into the page background:

```scss
// ADD: gradient overlay layer on top of the hero image
.resident-page__image-gradient {
  position: absolute;          // decoration layer — permitted
  inset: 0;
  pointer-events: none;
  background: linear-gradient(
    to top,
    #354278 12.5%,
    rgba(78, 94, 162, 0.62) 59.135%,
    rgba(108, 130, 225, 0) 100%
  );
}
```

**32:120 frosted glass panel:**
  It should be more transparent, ligher.

```scss
.resident-page__glass-panel {
  background: rgba(255, 255, 255, 0.05);     // more transparent than current
  backdrop-filter: blur(20rpx);
  border: 1rpx solid rgba(255, 255, 255, 0.12);
  border-radius: 24rpx;
  padding: 32rpx 40rpx;                      // internal padding to prevent text overflow
  overflow: hidden;                          // hard clip at panel edge
}
// Text inside must use white-space: normal and have explicit max-width
```

**33:178 ticket card:**

The ticket image `inset: [-5.11%_-10.85%_-6.57%_-10.85%]` means the image asset includes a shadow/halo bleed of ~5–11% on all sides. The **visual content** of the card is inside those bleeds. Implementation:

```scss
// Container: centered, no overflow
.resident-page__ticket-shell {
  display: flex;
  justify-content: center;
  align-items: center;
  width: 100%;
  padding: 0 40rpx;
}

// Inner wrapper: the "logical" card size
.resident-page__ticket {
  position: relative;
  width: 100%;
  max-width: 620rpx;
  aspect-ratio: 620 / 340;     // adjust to match card proportions
}

// The image bleeds beyond the logical bounds — use negative margin
.resident-page__ticket-image {
  position: absolute;          // decoration layer — permitted
  inset: -5.11% -10.85% -6.57% -10.85%;
  width: calc(100% + 21.7%);   // compensate for horizontal bleed
  height: calc(100% + 11.68%); // compensate for vertical bleed
}
```

Text content inside the ticket must be layered above the image (`z-index: 1`), with `padding` matching the visible card interior (inside the bleed zone).

**Layout rule compliance:** The gradient and ticket image use `position: absolute` as decoration layers — permitted. The ticket shell and glass panel use flexbox for centering — compliant.

**Files to modify:**
- `frontend/src/modules/auth/pages/resident/index.vue` (read first)
- `frontend/src/modules/auth/pages/resident-ticket/index.vue` (read first — may contain ticket card too)


---

## [P2] Issue 4 — 船票 detail page
**NOTE RESOLVED — Corner mismatch diagnosis:** Must read `ticket/pages/detail/index.vue` first to determine which case applies:
- **Case A** (wrapper `border-radius` conflicts with notch image) → remove `border-radius` from wrapper, keep image free
- **Case B** (image clipping/mode wrong) → fix `mode` attribute to `scaleToFill` or `aspectFill`; ensure wrapper has `overflow: hidden` only if needed
Decision is made at read-time during implementation.

**Figma spec:**

| Node | Role | Spec |
|---|---|---|
| `1:424` | Ticket card body | Rounded top (all 4 corners same radius), flat sides with notch cutouts at mid-height. Bleed: `inset: [-5.11%_-10.85%_-6.57%_-10.85%]` same as `33:178`. Taller aspect ratio (portrait). |
| `1:404` | Halo behind ticket | `rgba(116,212,234,0.54) → rgba(90,166,183,0.705) → rgba(65,120,132,0.87)` at 0/12.74/25.48%. 272px × 272px. blur: 64px. Positioned behind the ticket card. |

**Current state:** Not read during research. Must read `frontend/src/modules/ticket/pages/detail/index.vue` before implementing.

**Delta:**

**Bottom corner radius mismatch:**

From the screenshot of `1:424`: the ticket has four uniformly rounded corners at top (all same radius, approximately `20rpx`), and the bottom edge has **notched cutouts** (semicircular negative space cut from the left and right sides at approximately 50% height). This is a boarding-pass ticket shape. The notches are part of the background image asset, not CSS `border-radius`.

Current suspected issue: the bottom `border-radius` of the ticket container might be applying to the wrapper element, visually clashing with the notched image underneath.

Fix approach:
- The ticket card must use the image asset for its full visual shape
- The wrapper element should have NO `border-radius` — only the image defines the shape
- Text content inside must clear the notched zone with appropriate padding

**Ticket position offset:**

Not determinable without reading the current code. Plan: read the file, find the ticket's `margin`, `padding`, or `top` value, and cross-reference with the Figma vertical position of the ticket within the page frame.

**Halo implementation (1:404):**

This halo does not exist in the current code (confirmed from research — `--anima-glow-auth` etc. are defined in theme.scss but no halo element exists on the ticket detail page).

```scss
// ADD to ticket detail page
.ticket-detail-page__halo {
  position: absolute;          // decoration layer — permitted
  pointer-events: none;
  border-radius: 50%;
  width: 544rpx;               // 272px × 2
  height: 544rpx;
  background: radial-gradient(
    circle,
    rgba(116, 212, 234, 0.54) 0%,
    rgba(90, 166, 183, 0.705) 12.74%,
    rgba(65, 120, 132, 0.87) 25.48%,
    rgba(65, 120, 132, 0) 100%
  );
  filter: blur(128rpx);
  mix-blend-mode: screen;
  // Position: centered horizontally, ~35% from top of page
  left: 50%;
  top: 35%;
  transform: translate(-50%, -50%);
}
```

Add the `--anima-glow-ticket` token to `theme.scss`:
```scss
--anima-glow-ticket: radial-gradient(circle,
  rgba(116, 212, 234, 0.54) 0%,
  rgba(90, 166, 183, 0.705) 12.74%,
  rgba(65, 120, 132, 0.87) 25.48%,
  rgba(65, 120, 132, 0) 100%
);
```

**Layout rule compliance:** Halo is a decoration layer (absolute OK). Ticket content area should use flexbox column for internal layout. The image bleed uses absolute inset — decoration layer (OK).

**Files to modify:**
- `frontend/src/modules/ticket/pages/detail/index.vue` (read first)
- `frontend/src/shared/styles/theme.scss` (add `--anima-glow-ticket`)

**Risk:** Medium. The ticket shape (notches) is baked into the image asset. If the image is rendered as a plain `<image>` inside a container with border-radius, the fix is to remove CSS border-radius from the wrapper. If the notches are implemented as CSS, that's more complex — read the file first.

---

## [P3] Issue 5 — 记忆航线 continuity
**NOTE RESOLVED — Asset URLs expire in 7 days.** Figma MCP asset URLs are temporary. During implementation: download both SVGs via `curl` immediately from the MCP-provided URLs and write them to `frontend/src/modules/ticket/assets/icons/` before the URLs expire. Do not reference the Figma URLs in production code.

**Figma spec (node 41:103 — Component1):**

Four variants of a curved dashed path SVG:
- **Vector 24**: ~312.5 × 270rpx → `imgProperty1Vector24`
- **Vector 25**: ~311 × 273.5rpx → `imgProperty1Vector25`
- **Variant3**: same dimensions as Vector 25 (uses same image)
- **Variant4**: same dimensions as Vector 24

Screenshot shows: a **white dashed S-curve** on dark background. The path enters from the top-right, curves left, then right, exiting at bottom-right. This is the connector/route path between ticket items in the timeline list.

The two variants (Vector 24 vs Vector 25) likely mirror or reverse the S-curve so that alternating tickets use left/right winding paths, creating a continuous flowing route.

**Current state:** Not read during research. Must read `frontend/src/modules/ticket/pages/list/index.vue` before implementing.

**Delta:**

The timeline currently lacks the continuous dashed path connector between ticket cards. Plan:

1. Read the ticket list page to understand the current rendering structure (v-for over tickets, how items are laid out)

2. Between each pair of adjacent ticket items, insert a connector element:
```vue
<!-- Between ticket[n] and ticket[n+1] -->
<view class="ticket-list__connector">
  <image 
    class="ticket-list__connector-path"
    :src="n % 2 === 0 ? TICKET_ASSETS.path.vector25 : TICKET_ASSETS.path.vector24"
    mode="aspectFit"
  />
</view>
```

3. CSS for the connector:
```scss
.ticket-list__connector {
  display: flex;
  justify-content: center;
  align-items: center;
  width: 100%;
  height: 548rpx;      // 273.5rpx × 2 (rpx conversion of 273.5px)
  pointer-events: none;
}

.ticket-list__connector-path {
  width: 622rpx;       // 311px × 2
  height: 548rpx;
  opacity: 0.7;
}
```

4. The S-curve variants alternate: even index → Vector 25, odd index → Vector 24 (or vice versa). Visually this makes consecutive paths flow continuously.

5. **Add the path SVGs to TICKET_ASSETS**: The images currently exist only in the Figma MCP response (as URLs). They need to be downloaded and committed as static assets in `frontend/src/modules/ticket/assets/`.

**Layout rule compliance:** The connector is a flex-centered decoration element within the list flow — uses flexbox (compliant). The image inside is natural-flow content.

**Files to modify:**
- `frontend/src/modules/ticket/pages/list/index.vue` (read first)
- `frontend/src/modules/ticket/assets/index.ts` (add path SVG imports)
- `frontend/src/modules/ticket/assets/paths/` (add Vector24.svg and Vector25.svg files)

**Risk:** Low-Medium. Visual continuity depends on ticket card dimensions and spacing — the connector height (548rpx) must match the gap between cards. Read the list page first to verify card dimensions.

---

## [P3] Issue 6 — Header consistency
**NOTE RESOLVED — Implementation order:** P0 fully complete → P1 → P2 → P3. Within each issue, read all files first, then write code. No cross-issue parallel edits.

**Figma spec:**

| Node | Page | Structure | Key measurements |
|---|---|---|---|
| `1:413` | 我的船票 (ticket list) | `flex; justify-content: space-between; align-items: center; padding: 0 32rpx` | Left: empty spacer 48rpx, Center: "我的船票" HYShuSongEr 24px≈48rpx white text-shadow, Right: share icon 24px≈48rpx |
| `1:352` | 记忆航线 (ticket viewer/detail) | Same flex structure, same `padding: 0 32rpx` | Left: X/close icon 24px≈48rpx, Center: "二零二六年·春" HYShuSongEr **12px≈24rpx** `#d1d5dc`, Right: share icon 24px≈48rpx |
| `337:2` | (unavailable) | — | — |

**Measurements extracted from Figma Tailwind output:**
- `px-[15.999px]` ≈ `px: 16px` = `32rpx` on both headers
- Icon buttons: `size-[23.993px]` ≈ `24px` = `48rpx`
- Header height implied by content: `35px line-height` = `70rpx` + safe area

**Current state (from research-ui.md inconsistency #7):**

| Page | Top padding (current) |
|---|---|
| `map/index.vue` `__inner` | `calc(48rpx + env(safe-area-inset-top)) 8rpx` |
| `island/index.vue` `__topbar` | `calc(92rpx + env(safe-area-inset-top)) 22rpx 0` |

Additional inconsistency: the map and island pages apply safe-area at different layout levels (container padding vs topbar element padding). Headers in other modules (auth, ticket, chat) have not been read — must read each before touching.

**Delta (universal header spec):**

Define a shared header CSS pattern. All pages with a visible topbar should conform to:

```scss
// Shared header pattern (copy into each page's scoped styles)
.{page}__topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: calc(env(safe-area-inset-top) + 88rpx) 32rpx 0;
  // 88rpx ≈ standard status bar + navigation zone on non-custom pages
  // For custom nav (fullscreen) pages: use calc(env(safe-area-inset-top) + 44rpx)
  position: relative;
  z-index: 3;
}

.{page}__topbar-btn {
  width: 48rpx;
  height: 48rpx;
  flex: 0 0 48rpx;
  display: flex;
  align-items: center;
  justify-content: center;
}

.{page}__topbar-title {
  font-family: var(--anima-font-display);
  font-size: 48rpx;      // 1:413 variant (we the ticket list title)
  line-height: 70rpx;
  color: var(--anima-text-main);
  text-shadow: var(--anima-shadow-title);
  letter-spacing: 1rpx;
  text-align: center;
}

.{page}__topbar-subtitle {
  font-family: var(--anima-font-display);
  font-size: 24rpx;      // 1:352 variant (subdued, e.g. date string)
  line-height: 58rpx;
  color: var(--anima-text-muted);
  letter-spacing: 1rpx;
  text-align: center;
}
```

**Note on inconsistency from research-ui.md:** The `square-map-page__inner` applies `calc(48rpx + env(safe-area-inset-top))` as padding-top, then the `__topbar` inside adds a further `44rpx` top padding. The total is `48 + 44 = 92rpx` above the safe area. The `square-island-page__topbar` directly applies `calc(92rpx + env(safe-area-inset-top))`. These happen to match numerically but use different approaches. Standardise: apply safe-area + base offset in the topbar element directly (as island page does), not in the container.

**Files to modify** (after reading each):
- `frontend/src/modules/square/pages/map/index.vue`
- `frontend/src/modules/square/pages/island/index.vue`
- `frontend/src/modules/ticket/pages/list/index.vue`
- `frontend/src/modules/ticket/pages/detail/index.vue`
- `frontend/src/modules/ticket/pages/viewer/index.vue`
- `frontend/src/modules/auth/pages/resident/index.vue`
- Any other page with a custom topbar

**Risk:** Low per file, Medium in aggregate. Changing top padding on every page affects scrollable content positions. Test each page's content starting position after changes.

---

## [P3] Issue 7 — Button borders

**Figma spec (node 33:174 — "加入社群" button):**

```
container:      border-radius: 15px (= 30rpx)
                overflow: hidden
                background: rgba(0, 0, 0, 0) — transparent container
                (border/fill likely provided by parent frame stroke)
text:           HYShuSongEr, 16px (= 32rpx)
                color: #e6f8ff
                text-shadow: 0 0 4px rgba(255,255,255,0.5)
                tracking: 0.5px (= 1rpx)
                line-height: 28px (= 56rpx)
```

The button container is transparent in Figma (`rgba(0,0,0,0)`) — the visual border and glass effect come from the parent frame. In code, the border and background must be applied on the button element itself.

**Current state (from publish page — already closest to spec):**
```scss
.publish-page__publish-action {
  border: 1rpx solid rgba(255, 255, 255, 0.6);
  border-radius: 30rpx;             // matches Figma ✓
  background: linear-gradient(90deg, rgba(21,31,53,0.78) 0%, rgba(50,71,128,0.12) 52%, rgba(21,31,53,0.78) 100%);
  box-shadow: inset 0 0 20rpx rgba(255, 255, 255, 0.1);
}
```

Other button contexts (auth pages, resident page — not read yet) may have different styling.

**Delta — target button spec:**

```scss
// To be added to theme.scss as a reusable token set, NOT a utility class
// (each page applies via its own BEM class referencing these values)

// Border:
border: 1rpx solid rgba(255, 255, 255, 0.26);
// WAS on publish: rgba(255,255,255,0.6) — too bright; Figma button 33:174 is subtle

// Background:
background: linear-gradient(
  135deg,
  rgba(10, 18, 48, 0.82) 0%,
  rgba(30, 51, 95, 0.38) 50%,
  rgba(10, 18, 48, 0.82) 100%
);

// Inner glow:
box-shadow: inset 0 0 32rpx rgba(255, 255, 255, 0.08),
            0 0 0 1rpx rgba(255, 255, 255, 0.08);

// Border radius:
border-radius: 30rpx;    // matches Figma 15px × 2 ✓

// Text:
font-family: var(--anima-font-display);
font-size: 32rpx;        // 16px × 2
color: var(--anima-text-main);   // #e6f8ff
text-shadow: 0 0 8rpx rgba(255, 255, 255, 0.5);   // 4px × 2
letter-spacing: 1rpx;
```

Add to `theme.scss`:
```scss
// Button border token
--anima-button-border: 1rpx solid rgba(255, 255, 255, 0.26);
--anima-button-bg: linear-gradient(135deg, rgba(10,18,48,0.82) 0%, rgba(30,51,95,0.38) 50%, rgba(10,18,48,0.82) 100%);
--anima-button-glow: inset 0 0 32rpx rgba(255,255,255,0.08), 0 0 0 1rpx rgba(255,255,255,0.08);
```

**Files to modify:**
- `frontend/src/shared/styles/theme.scss` (add button tokens)
- `frontend/src/modules/square/pages/publish/index.vue` (update to new spec)
- `frontend/src/modules/auth/pages/resident/index.vue` (read first)
- Any other page with a primary CTA button (read before touching)

**Risk:** Low. Token-only change in theme.scss; then each page's BEM class is updated independently. The `publish-page__publish-action` border opacity changes from `0.6` → `0.26` — this is a significant visual difference (subtler). Verify against full page screenshot.

---

## Shared Notes Across All Issues

### Files to read before any implementation
These modules were not read during research and must be read before modifying:
- `frontend/src/modules/auth/pages/login/index.vue`
- `frontend/src/modules/auth/pages/register/index.vue`
- `frontend/src/modules/auth/pages/resident/index.vue`
- `frontend/src/modules/auth/pages/resident-ticket/index.vue`
- `frontend/src/modules/auth/pages/style/index.vue`
- `frontend/src/modules/chat/pages/home/index.vue`
- `frontend/src/modules/chat/pages/cabin/index.vue`
- `frontend/src/modules/chat/pages/generating/index.vue`
- `frontend/src/modules/ticket/pages/list/index.vue`
- `frontend/src/modules/ticket/pages/detail/index.vue`
- `frontend/src/modules/ticket/pages/viewer/index.vue`
- `frontend/src/modules/user/pages/aid/index.vue`
- `frontend/src/infrastructure/http/` (referenced in App.vue and stores)

### Layout rule compliance summary

| Fix | New absolute? | Compliant? |
|---|---|---|
| P0-A: pointer-events on scene layers | No new elements | ✓ |
| P0-B: Template reorder for outline glow | No new elements | ✓ |
| P0-C: Dim mask background change | No new elements | ✓ |
| P0-C: IslandTagChip style update | No new elements | ✓ |
| P0-C: Flex wrapper for header content | Uses flex column | ✓ |
| P1: DarkBackgroundLayer on map/island | Decoration layer | ✓ (permitted) |
| P2: Page halo (all pages) | Decoration layer | ✓ (permitted) |
| P2: Gradient overlay on resident image | Decoration layer | ✓ (permitted) |
| P2: Glass panel | Flexbox, no absolute | ✓ |
| P2: Ticket shell (centering) | Flex centering | ✓ |
| P2: Ticket image bleed | Decoration layer | ✓ (permitted) |
| P4: Halo behind ticket | Decoration layer | ✓ (permitted) |
| P5: Timeline connector | Flex in list flow | ✓ |
| P6: Header standardization | Existing flex cleanup | ✓ |
| P7: Button token additions | No structural change | ✓ |

### `rpx` in CSS custom properties (known risk from research-ui.md inconsistency #9)

The plan does NOT introduce additional `rpx` values inside `:root {}` CSS custom properties. New tokens added to `theme.scss` that contain length values (e.g. `--anima-button-glow`) use `rpx` inline — this is consistent with the existing pattern and the risk is already accepted in the codebase.

### `HYShuSongEr` font

The Figma spec calls for `HYShuSongEr:S` (a commercial Chinese serif font) as the font-family in all text elements. The current codebase uses `--anima-font-display: "STSong", "Noto Serif SC", serif`. This discrepancy is NOT addressed in this plan — adding a commercial font requires licensing discussion. The current font stack is an acceptable fallback. Flag to the design team.
