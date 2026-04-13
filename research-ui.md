# UI Architecture Research — Anima Isle Frontend

> Scope: `frontend/src/uni.scss`, `frontend/src/App.vue`, `frontend/src/main.ts`,
> `frontend/src/pages.json`, `frontend/src/shared/**`, `frontend/src/modules/square/**`
> Date: 2026-04-11

---

## 1. Project Root Layout

```
frontend/
  src/
    App.vue               # App shell — lifecycle hooks only, imports theme
    main.ts               # App factory — Pinia, uview-plus, vant CSS
    uni.scss              # uni-app boilerplate SCSS variables + uview-plus imports
    pages.json            # Route manifest + global nav style
    shared/
      assets/             # Barrel-exported static assets (bg, icons, illustrations)
      components/         # Reusable UI primitives
      constants/          # Routes, storage keys
      styles/             # theme.scss — the only real global CSS
      types/              # Shared TypeScript types
      utils/              # Navigation helpers
    modules/
      square/             # The Square / Map feature module
        api/              # HTTP calls
        assets/           # SVG scene layers + PNG avatars
        components/       # Module-local components
        constants/        # Island configs, scene layer data
        pages/            # map/, island/, publish/
        store/            # Pinia store
        types/            # TypeScript types
```

---

## 2. Global Styles

### 2.1 Theme Entry Point

`frontend/src/shared/styles/theme.scss` is the single authoritative stylesheet.
It is loaded in **two places**:

| Location | Mechanism |
|---|---|
| `main.ts` line 7 | `import "./shared/styles/theme.scss"` (programmatic, applied globally) |
| `App.vue` `<style>` block | `@import "./shared/styles/theme.scss"` (Vue SFC style) |

**This is a duplicate import.** CSS custom property declarations will be emitted twice, which is harmless but redundant and can cause confusion.

### 2.2 Global Background

The background is set at three levels simultaneously:

1. `pages.json` `globalStyle.backgroundColor: "#0a0a1a"` — controls native nav bar area background on WeChat MiniProgram / App targets.
2. `pages.json` `globalStyle.navigationBarBackgroundColor: "#0a0a1a"` — native navigation bar colour.
3. `theme.scss`: `page, body { background-color: var(--bg-deep); }` where `--bg-deep: #0a0a1a` — covers the web/H5 target.

### 2.3 CSS Custom Property System (`--anima-*`)

All design tokens live in a single `:root {}` block in `theme.scss`. There are two parallel namespaces:

**Generic tokens** (used by both custom and uview-plus code):
```
--bg-deep: #0a0a1a
--bg-panel: rgba(255, 255, 255, 0.06)
--text-primary: #ffffff
--text-secondary: #9db0cc
--brand-primary: #2b63f1
--brand-success: #1f9d55
--danger: #ff7a7a
```

**Project-specific `--anima-*` tokens** (used exclusively by custom components):

| Category | Tokens |
|---|---|
| Night gradient | `--anima-night-gradient` |
| Surfaces | `--anima-surface-overlay`, `--anima-surface-panel`, `--anima-surface-card`, `--anima-surface-water`, `--anima-surface-water-lines`, `--anima-surface-field`, `--anima-surface-field-strong`, `--anima-surface-input` |
| Text | `--anima-text-main`, `--anima-text-strong`, `--anima-text-muted`, `--anima-text-soft`, `--anima-text-dim`, `--anima-text-float`, `--anima-text-placeholder`, `--anima-text-error` |
| Lines | `--anima-line-soft`, `--anima-line-strong`, `--anima-line-focus`, `--anima-line-field`, `--anima-line-code-button` |
| Shadows | `--anima-shadow-soft`, `--anima-shadow-inner`, `--anima-shadow-field`, `--anima-shadow-field-soft`, `--anima-shadow-field-focus`, `--anima-shadow-title` |
| Buttons | `--anima-button-primary`, `--anima-button-secondary`, `--anima-button-disabled` (a raw `0.6`, not a color) |
| Glows / radial gradients | `--anima-glow-auth`, `--anima-glow-chat`, `--anima-glow-cabin-halo`, `--anima-glow-stage-core`, `--anima-glow-stage-outer`, `--anima-glow-stage-mist`, `--anima-glow-stage-shadow` |
| Resident (profile) surfaces | `--anima-resident-surface`, `--anima-resident-surface-strong`, `--anima-resident-line`, `--anima-resident-line-strong`, `--anima-resident-shadow`, `--anima-resident-tag`, `--anima-resident-scene-mask` |
| Border-radius | `--anima-radius-pill: 100rpx`, `--anima-radius-lg: 20rpx`, `--anima-radius-md: 12rpx`, `--anima-radius-sm: 10rpx` |
| Spacing | `--anima-space-xs: 8rpx`, `--anima-space-sm: 12rpx`, `--anima-space-md: 16rpx`, `--anima-space-lg: 24rpx`, `--anima-space-xl: 42rpx` |
| Font sizes | `--anima-font-title: 50rpx`, `--anima-font-subtitle: 30rpx`, `--anima-font-body: 28rpx` |
| Typography | `--anima-font-display: "STSong", "Noto Serif SC", serif` |

### 2.4 Colour Palette

The entire project is a single dark "night sky ocean" theme. There is no light mode.

| Role | Value |
|---|---|
| Page background | `#0a0a1a` |
| Night sky gradient | `#072743 → #2c417a → #3f4376` (top-to-bottom) |
| Primary text | `#e6f8ff` (ice white-blue) |
| Muted text | `#d1d5dc` |
| Brand blue | `#2b63f1` / button `#5f88ff` |
| Glow accent | `rgba(116, 212, 234, …)` — cyan-teal, used in all radial glows and halos |
| Danger | `#ff7a7a` |
| All surfaces | Semi-transparent whites/blacks — no opaque mid-tones |

### 2.5 The `uni.scss` File

This is the **uni-app boilerplate** file, not a project stylesheet. Its purpose:

- Defines `$uni-*` SCSS variables (colors, sizes, radii, spacing) — these are the uni-app framework's default tokens.
- These variables are **not used** by any custom component in this project. The project uses `--anima-*` CSS custom properties instead.
- At the bottom, it imports `uview-plus/theme.scss` and `uview-plus/index.scss` — this is what actually matters: it bootstraps the uview-plus component library styles.

**Notable bug in boilerplate:**
```scss
$uni-font-size-lg: 16;   // Missing "px" unit — should be 16px
```

---

## 3. Fonts

### 3.1 Declaration

There is **one font family** declared for the design system:
```
--anima-font-display: "STSong", "Noto Serif SC", serif
```

This is a Chinese serif typeface stack:
- **STSong** — a CJK serif bundled natively with macOS, iOS, and some Android devices.
- **Noto Serif SC** — a Google Fonts fallback for devices without STSong.
- **serif** — generic fallback.

### 3.2 No `@font-face` Rules

There are **no `@font-face` declarations** anywhere in the codebase. The font stack relies entirely on system fonts being present on the device. Noto Serif SC is listed as a fallback but is not loaded via any `<link rel="stylesheet">` or `@import url()` — it will only render on devices that have it pre-installed.

### 3.3 Vant CSS

`main.ts` imports `vant/lib/index.css` — this brings Vant Mobile UI library styles into scope, including its own font stacks. This may conflict or override base font styles.

### 3.4 uview-plus

uview-plus styles are included via `uni.scss` → `uview-plus/theme.scss` + `uview-plus/index.scss`. These bring their own font defaults.

---

## 4. Component Patterns

### 4.1 Composition API (universal)

Every component uses `<script setup lang="ts">`. No Options API is present.

```vue
<script setup lang="ts">
import { computed, ref } from "vue";

const props = withDefaults(defineProps<{ label: string; avatarSrc?: string }>(), {
  avatarSrc: "",
});
</script>
```

### 4.2 BEM Naming Convention

CSS class names follow strict BEM: `block__element--modifier`. The block is always page-scoped or component-scoped:

```
square-map-page
square-map-page__topbar
square-map-page__topbar-spacer
square-map-page__layer--outline
night-ip
night-ip__head--back
night-ip--animated
island-tag-chip
island-tag-chip__avatar-shell
```

Every component uses `<style scoped lang="scss">` — there are no unscoped style blocks in component files.

### 4.3 Slots

Only `StageViewportShell` uses a `<slot />`:
```vue
<template>
  <view class="stage-viewport-shell">
    <view class="stage-viewport-shell__viewport" :style="{ maxWidth: viewportMaxWidth }">
      <DarkBackgroundLayer :texture-opacity="textureOpacity" />
      <slot />
    </view>
  </view>
</template>
```
No named slots are used anywhere.

### 4.4 Props Pattern

All components use TypeScript generic props with `withDefaults`:
```ts
withDefaults(defineProps<{ textureOpacity?: number }>(), { textureOpacity: 0.3 })
```

### 4.5 Asset Imports

Assets are never referenced by path strings inside components. They go through typed barrel files:

```ts
// shared/assets/index.ts
import darkBg from "./bg/dark-bg.png";
export const SHARED_ASSETS = { bg: { darkBg }, icons: { ... } } as const;
```

Components then use `SHARED_ASSETS.icons.exit`, `SQUARE_ASSETS.icons.mistIslandBase`, etc. This is consistently applied across both `shared` and module-level assets.

### 4.6 Deep Selectors

`island/index.vue` uses Vue's `:deep()` combinator to override child component styles from the parent:
```scss
.square-island-page__bubble--highlighted :deep(.island-tag-chip) {
  box-shadow: 0 0 8rpx rgba(255, 255, 255, 0.55), ...;
}
```

### 4.7 `hover-class` Pattern

Interactive elements use UniApp's `hover-class` attribute for tap feedback instead of CSS `:hover` or `:active`:
```vue
<view hover-class="tap-hover" @click="goBack">
<view hover-class="publish-page__bubble--hover" @click="...">
```

The `tap-hover` class is defined inline in `publish/index.vue`:
```scss
.tap-hover { opacity: 0.82; transform: translateY(-2rpx); }
```

---

## 5. Layout System

### 5.1 rpx Is Universal

**All dimensions use rpx** — padding, margin, width, height, font sizes, border-radius, shadow offsets, translate values. There are almost no `px` values in component styles (the only `px` values are in `uni.scss`'s boilerplate SCSS variables which are unused by the app).

### 5.2 The 750rpx Canonical Width

The entire scene system is designed around a **750rpx artboard**. This is the standard UniApp/WeChat MiniProgram baseline (equivalent to a 375px logical screen at 2× density).

Artboard dimensions appear consistently across pages:
```scss
/* map/index.vue */
.square-map-page__artboard { width: 750rpx; height: 1624rpx; }

/* island/index.vue */
.square-island-page__viewport { width: 750rpx; }
.square-island-page__artboard { width: 750rpx; height: 1624rpx; }
```

The inner content is always centered with `margin: 0 auto` and a max-width cap:
- `square-map-page__inner`: `max-width: 750rpx`
- `StageViewportShell`: `max-width` prop (default `820rpx`)

### 5.3 Absolute Positioning Dominant for Scene Elements

All island art, scene layers, and tag bubble positions are `position: absolute` with precise rpx coordinates. There is no CSS Grid. Flexbox is only used for UI chrome (topbars, action buttons, chips).

```scss
.square-map-page__artboard {
  position: absolute;
  top: 0;
  left: 50%;
  width: 750rpx;
  height: 1624rpx;
  transform: translateX(-50%);
}
```

Island configs encode the exact position of each scene layer as inline style objects:
```ts
style: { left: "244rpx", top: "1168rpx", width: "456rpx", height: "390rpx" }
```

### 5.4 `publish/index.vue` — Percentage + Aspect-Ratio Layout

The publish page departs from the rpx-absolute pattern and uses a more sophisticated layout:
```scss
.publish-page__artboard {
  width: min(100%, calc((100vh - env(safe-area-inset-top) - ...) * 402 / 874));
  max-width: 804rpx;
  aspect-ratio: 402 / 874;
}
```

Child elements within the artboard use percentage positioning (`left: 26.55%`, `top: 21.51%`), adapting to the artboard's actual rendered size. This makes the publish page genuinely resolution-independent, unlike the scene pages which are fixed to 750rpx.

### 5.5 `NightIp.vue` — Percentage-Based Compositing

The character mascot component uses percentage-based positions and sizes for all sub-elements, allowing it to scale cleanly regardless of the container width:
```scss
.night-ip__head--back { left: 8.47%; width: 82.96%; height: 71.17%; }
.night-ip__face       { left: 22.38%; top: 29.2%; width: 53.17%; }
```
This is a deliberate pattern for scalable multi-layer image compositing.

### 5.6 Aspect-Ratio Placeholder Pattern

`NightIp.vue` uses the "padding-top ratio box" technique to reserve space:
```scss
.night-ip__ratio { width: 100%; padding-top: 63.31%; }
```
The actual image layers are then positioned absolutely over this spacer.

### 5.7 Safe Area Handling

Safe areas are handled with `calc()` and `env()`:
```scss
padding: calc(48rpx + env(safe-area-inset-top)) 8rpx env(safe-area-inset-bottom);
padding: calc(92rpx + env(safe-area-inset-top)) 22rpx 0;
padding-top: env(safe-area-inset-top);
padding-bottom: env(safe-area-inset-bottom);
```
Applied consistently in page components that use `navigationStyle: "custom"`.

---

## 6. Responsive Approach

- **No media queries** anywhere in the codebase.
- **No breakpoints** defined.
- This is a mobile-first, effectively mobile-only application (UniApp targeting WeChat MiniProgram / iOS / Android).
- Responsiveness is achieved purely via **rpx scaling** — the uni-app runtime translates rpx to device pixels proportionally based on the 750rpx baseline.
- The scene art (750rpx × 1624rpx artboard) has a fixed logical size and is simply clipped by the viewport on smaller screens or centered on wider ones.
- The publish page is the sole exception: it uses `min()`, `aspect-ratio`, and `%` for true fluid scaling.

---

## 7. Pages and Navigation

### 7.1 Route Manifest (`pages.json`)

All routes use the module-based path convention:
```
modules/{module}/pages/{page}/index
```

| Route | Navigation Style |
|---|---|
| `modules/auth/pages/login` | System nav bar |
| `modules/auth/pages/register` | System nav bar |
| `modules/auth/pages/resident` | **Custom** (no nav bar) |
| `modules/auth/pages/resident-ticket` | **Custom** |
| `modules/auth/pages/style` | System nav bar |
| `modules/chat/pages/home` | System nav bar |
| `modules/chat/pages/cabin` | **Custom** |
| `modules/chat/pages/voice` | **Custom** |
| `modules/chat/pages/generating` | **Custom** |
| `modules/ticket/pages/list` | System nav bar |
| `modules/ticket/pages/detail` | System nav bar |
| `modules/ticket/pages/viewer` | **Custom** |
| `modules/square/pages/map` | System nav bar |
| `modules/square/pages/island` | **Custom** |
| `modules/square/pages/publish` | System nav bar |
| `modules/user/pages/aid` | **Custom** |

Most immersive/scenic pages use `navigationStyle: "custom"` (fullscreen, no native bar).

### 7.2 Global Navigation Style

```json
"globalStyle": {
  "navigationBarTextStyle": "white",
  "navigationBarTitleText": "Anima Isle",
  "navigationBarBackgroundColor": "#0a0a1a",
  "backgroundColor": "#0a0a1a"
}
```

### 7.3 Navigation Utilities

`shared/utils/navigation.ts` provides two helpers:
- `toLogin()` — uses `uni.reLaunch` (clears stack), with guard against double-navigation.
- `toChatHome()` — uses `uni.reLaunch` to the chat home.

Page-level navigation uses `uni.navigateTo`, `uni.navigateBack`, `uni.reLaunch`, and `uni.redirectTo` directly. No router abstraction layer exists.

### 7.4 easycom Configuration

```json
"easycom": {
  "autoscan": true,
  "custom": { "^u-(.*)": "uview-plus/components/u-$1/u-$1.vue" }
}
```

uview-plus components (`<u-button>`, `<u-input>`, etc.) auto-resolve without explicit imports.

---

## 8. Square Module Deep Dive

### 8.1 Module Structure

```
modules/square/
  api/square.ts           — 4 API functions: suggestTags, publishTicket, fetchIslandMap, interactWithCard
  assets/index.ts         — 24 SVG scene layer assets + 2 PNG images
  components/IslandTagChip.vue  — Tag bubble with optional avatar
  constants/islands.ts    — All island configs, scene layer data, type definitions
  pages/
    map/index.vue         — Overhead map view with island hotspots
    island/index.vue      — Zoomed-in island view with tag bubbles
    publish/index.vue     — Tag selection + publish flow
  store/square.ts         — Pinia store: suggestedTags, selectedTags, mapStars
  types/square.ts         — MapStarDTO, CardPublishRequest, SquareState
```

### 8.2 Island Configuration System

All island layout data lives in `constants/islands.ts`. Each island is a `IslandConfig` object with:

| Field | Type | Purpose |
|---|---|---|
| `id` | `IslandId` | Visual/frontend identifier |
| `name` | `string` | Chinese display name |
| `backendIslandKey` | `string` | Backend enum key (MIST, WIND, etc.) |
| `englishDisplayName` | `string` | English label shown in UI |
| `hotspotStyle` | `SceneStyle` | rpx position + size for tap area on map |
| `outlineLayerKeys` | `string[]` | Which scene layers glow on hover |
| `focusLayerKeys` | `string[]` | Which scene layers show on island detail |
| `outlineBlur` | `string` | CSS blur amount for outline glow |
| `outlineOpacity` | `string` | Opacity of outline glow |
| `focusScale` / `focusTranslateX/Y` | `number` / `string` | CSS transform for the zoomed-in camera |
| `focusSceneHeight` | `string` | Height of the scene container on island page |
| `tagSlots` | `IslandBubbleSlot[]` | Positions for tag bubbles on island page |
| `mockTags` | `string[]` | Default tags when no user data available |

Seven islands are defined: `current` (心流湾), `mist` (雾岛), `ember` (暖屿), `lagoon` (澄湾), `azure` (澈岛), `sprout` (芽岛), `pebble` (微光礁).

### 8.3 Scene Layer System

`SCENE_LAYERS` is a flat array of 21 layer objects, each with:
- `key`: unique string identifier
- `src`: resolved asset import
- `style`: `{ left, top, width, height }` in rpx as strings
- `islandId?`: optional link to which island "owns" this layer

Pages filter this array to get the layers they need. The map page renders all 21 layers; the island page renders the relevant subset for the focused island.

### 8.4 Bubble Layout Algorithm

`publish/index.vue` contains a client-side randomized layout algorithm for tag bubbles:
- 5 size buckets (108–186rpx), randomly shuffled
- 60 placement attempts per bubble using overlap rejection
- Positions stored as `% of container` (left, top 12–88%)
- Font size derived from bubble diameter: `≥170rpx → 24rpx`, `≥145rpx → 22rpx`, else `20rpx`

### 8.5 State Management

`useSquareStore` (Pinia):
- `suggestedTags: string[]` — AI-suggested tags from backend
- `selectedTags: string[]` — user-chosen tags (max 5)
- `mapStars: MapStarDTO[]` — star positions for the map (fetched but unused in current UI)
- `currentIsland: string` — defaults to `"ISLAND_1"` (mismatch: `IslandId` values are words like `"mist"`, not `"ISLAND_1"`)

Cross-store dependency: `island/index.vue` imports both `useSquareStore` and `useTicketStore`.

---

## 9. Shared Components Reference

### `StageViewportShell`

A page wrapper that:
1. Applies `--anima-night-gradient` as the full-screen background
2. Centers content with `max-width: 820rpx` (configurable via `viewportMaxWidth` prop)
3. Renders `DarkBackgroundLayer` (texture image) behind `<slot />`

Used by: `publish/index.vue`

### `DarkBackgroundLayer`

Renders `dark-bg.png` at 123.88% width offset by `-15.67%` left and `-1.26%` top, with `filter: saturate(0.9) brightness(0.82)`. Accepts `textureOpacity` prop (default `0.3`). Absolutely positioned, `pointer-events: none`.

### `NightIp`

Multi-layer animated character mascot. Layers: back head SVG, front head SVG, face vector SVG, two eye ellipse SVGs. Animated via `@keyframes night-ip-breathe` (4.2s, vertical float + scale). Animation controllable via `animated` prop.

### `IslandTagChip`

A pill-shaped tag component with optional avatar. Styles: `border-radius: 999rpx`, `box-shadow: 0 0 8rpx rgba(255,255,255,0.5)`, `background: rgba(255,255,255,0.03)`. Font is `--anima-font-display`, `22rpx`.

---

## 10. Third-Party Dependencies

| Library | Usage |
|---|---|
| `uview-plus` | UI component library (initialized in `main.ts`, auto-resolved via easycom) |
| `vant` | `vant/lib/index.css` imported in `main.ts` — styles only, no components imported in read files |
| `pinia` | State management |
| `@dcloudio/uni-app` | Lifecycle hooks (`onLaunch`, `onShow`, `onHide`, `onLoad`) |

---

## 11. Known Inconsistencies

### 11.1 Double Import of `theme.scss`
`theme.scss` is imported in both `main.ts` (line 7) and `App.vue`'s `<style>` block. This results in all `:root` CSS custom properties being emitted twice in the output. Harmless but redundant.

### 11.2 Two Parallel CSS Variable Systems
- `uni.scss`: `$uni-*` SCSS variables (only used internally by uview-plus, not by project code)
- `theme.scss`: `--anima-*` CSS custom properties (used exclusively by all project components)

No project component references any `$uni-*` variable. These two systems never interact.

### 11.3 Missing Unit in Boilerplate
`uni.scss` line 44: `$uni-font-size-lg: 16;` — missing `px` unit. This is an upstream boilerplate bug. Not used in the project.

### 11.4 `azure` Island Uses `sprout-island-body` Layer Key
In `islands.ts`, the `azure` island config references:
```ts
outlineLayerKeys: ["sprout-island-body"],
focusLayerKeys: ["sprout-island-body"],
```
The `sprout-island-body` scene layer key actually represents what is visually the azure/cloud island. This naming conflict (`azure` config → `sprout-island-body` key) will confuse anyone maintaining the scene layers.

### 11.5 Duplicate Asset Key in `SHARED_ASSETS`
`shared/assets/index.ts`:
```ts
ipNight: ipDark,   // alias
ipDark,            // original
```
Both `ipNight` and `ipDark` point to the same `ip-dark.svg` file. One of them is redundant.

### 11.6 Cross-Module Asset Imports in `publish/index.vue`
`publish/index.vue` imports assets from two other modules:
```ts
import { CHAT_ASSETS } from "@/modules/chat/assets";     // for ticketRerollRefresh icon
import { TICKET_ASSETS } from "@/modules/ticket/assets"; // for publish icon
```
This breaks module encapsulation — the square module depends on chat and ticket asset internals.

### 11.7 Topbar Padding Inconsistency
- `map/index.vue` inner: `padding: calc(48rpx + env(safe-area-inset-top)) 8rpx ...`
- `island/index.vue` topbar: `padding: calc(92rpx + env(safe-area-inset-top)) 22rpx 0`

The base offset differs (48rpx vs 92rpx), and the two pages apply the safe-area padding at different layout levels (container vs topbar element).

### 11.8 `--anima-button-disabled` Is Not a Color
```css
--anima-button-disabled: 0.6;
```
This token holds a raw unitless number used as `opacity: var(--anima-button-disabled)`. This is an unusual convention — most design systems would name this `--anima-opacity-disabled` or similar, and the opacity of `0.6` conflicts with the separate `$uni-opacity-disabled: 0.3` in `uni.scss`.

### 11.9 `rpx` Inside CSS Custom Properties in `:root`
`theme.scss` contains rpx values inside `:root` custom properties:
```css
--anima-space-xs: 8rpx;
--anima-shadow-soft: 0 0 40rpx rgba(255, 255, 255, 0.08);
--anima-surface-water-lines: repeating-linear-gradient(0deg, rgba(…) 0 4rpx, … 4rpx 18rpx);
```
rpx is not a standard CSS unit — it is a uni-app extension. In H5 (browser) output, the uni-app compiler transforms `rpx` to `rem` or `vw` in component stylesheets. However, custom property values inside `:root {}` may not be transformed by the compiler, causing rendering failures on the H5 target. This is potentially platform-specific breakage.

### 11.10 `currentIsland` Default Mismatch in Pinia Store
`square.ts` store:
```ts
currentIsland: "ISLAND_1",
```
The valid `IslandId` values are `"current" | "mist" | "ember" | "lagoon" | "azure" | "sprout" | "pebble"`. `"ISLAND_1"` is not a valid island ID and would not match any `ISLAND_CONFIGS` key. The `fetchMap` action overwrites this with backend keys (e.g., `"MIST"`, `"WIND"`), which are also not `IslandId` values — they are `backendIslandKey` strings. The `currentIsland` field appears to mix two different ID spaces.

### 11.11 `publish/index.vue` Layout vs. Map/Island Layout Mismatch
The publish page uses a fundamentally different layout strategy than the other two square pages:
- map/island: 750rpx fixed artboard + absolute rpx coordinates
- publish: `min(100%, aspect-ratio-calc)` + `%` percentage positioning

These approaches are incompatible if any code is ever shared between them. A future developer would need to understand both conventions separately.

---

## 12. Summary Reference Card

| Aspect | Value |
|---|---|
| Framework | Vue 3 + UniApp (Composition API, `<script setup>`) |
| Styling | SCSS, scoped per component, global theme in `theme.scss` |
| Design unit | **rpx** (750rpx = full screen width baseline) |
| Artboard size | 750 × 1624 rpx |
| Global background | `#0a0a1a` (near-black) |
| Color theme | Single dark night-ocean theme, no light mode |
| Primary font | STSong / Noto Serif SC (system fonts only, no @font-face) |
| Component style | BEM (`block__element--modifier`), all scoped |
| Layout method | Absolute rpx for scenes; flexbox for UI chrome |
| Safe area | `env(safe-area-inset-*)` with `calc()` |
| Responsive | rpx scaling only; no media queries |
| State | Pinia; `useSquareStore`, cross-references `useTicketStore` |
| Asset loading | Barrel exports (`SHARED_ASSETS`, `SQUARE_ASSETS`) |
| Navigation | Direct `uni.*` calls; `ROUTES` constant map |
| UI libraries | uview-plus (components) + Vant (CSS only) |
