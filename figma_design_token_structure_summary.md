# Anima Isle Figma Design Token Structure Summary

Source file: `https://www.figma.com/design/cCVGXRmqJjjUrCYi6fmgm3/Untitled?m=dev`
Analysis date: 2026-03-03

## 1. Scope and method
This summary is based on sampled nodes from key sections (`聊天舱`, `登录/首页`, `reference`, day/night home frames) using Figma MCP `get_variable_defs` and `get_design_context`.

Note: current MCP output exposes variable names + resolved values/effects on nodes, but does not fully expose explicit collection IDs/names in this file context. So collection boundaries below are inferred from naming/usage patterns.

## 2. Observed token layers

### A. Theme / mode layer (day vs night)
Likely top-level theme collections by mode:
- Day-oriented tokens:
  - `day_version` -> `#FFFFFF` (as observed)
  - `day_shoe` -> `#feecc2`
  - `text_day` -> `#6a7282`
  - `Color2` -> `#99a1af`
  - `Linear`, `Radial` (gradient variables, observed as gradient-type placeholders)
- Night-oriented tokens:
  - `text_last` -> `#e6f8ff99`
  - `icon` -> `#adafc8`
  - `按键` -> `#ffffff99`
  - also relies on gradient variables: `ip渐变1`, `渐变3`

### B. Effect layer (visual effects / glow / depth)
Effect tokens are separated and reused across text/IP/input contexts:
- `ip_day_effects`
- `ip_day_effects_inner`
- `111` (drop shadow)
- `text_light` (text glow)
- `message_input` (stronger glow)

### C. Component-oriented layer
Component-level variables seem to consume theme/effect tokens:
- IP component: `ip渐变1`, `渐变3`, plus day effect tokens
- Input/button/text components: `icon`, `按键`, `text_last`, `text_day`, `Color2`

## 3. Connection points between variable collections

## CP-1: Theme collection -> Semantic text/icon collection
- Day frames bind `text_day`, `Color2`.
- Night frames bind `text_last`, `icon`, `按键`.
- This is the primary mode switch connection point for readable UI content.

## CP-2: Theme collection -> IP visual collection
- IP-related nodes consistently bind gradient variables (`ip渐变1`, `渐变3`) in night contexts.
- Day IP nodes bind `Linear`/`Radial` + `ip_day_effects*`.
- This indicates the IP element is a cross-collection bridge: gradient collection + effect collection jointly define final look.

## CP-3: Effect collection -> Semantic/component collection
- `text_light` and `message_input` are effect tokens attached to semantic UI regions (headline text, input).
- `111` appears as generic glow/drop-shadow token and likely acts as shared surface-depth effect.

## CP-4: Shared semantic token reused across sections
- `icon` (`#adafc8`) appears repeatedly in multiple sections (`聊天舱`, `登录/首页`, subcomponents).
- Suggests a shared semantic/icon collection consumed by multiple page collections.

## 4. Practical token architecture (inferred)
Recommended representation of current structure:

1. `Primitives` collection
- raw color stops, opacity variants, shadow primitives

2. `Theme` collection (modes: `day`, `night`)
- background, foreground, readability, atmosphere
- examples: `text_day`, `text_last`, `按键`, `Color2`

3. `Effects` collection
- glow, inner-shadow, depth
- examples: `ip_day_effects`, `text_light`, `message_input`

4. `Component` collection
- IP, input, buttons, icon containers
- variables reference theme/effect tokens (`ip渐变1`, `渐变3`, etc.)

Connection graph (logical):
`Primitives -> Theme(day/night) -> Semantic UI / Component tokens -> Frame instances`
`Primitives -> Effects -> Semantic UI / Component tokens -> Frame instances`

## 5. Risks and cleanup opportunities
- Inconsistent naming language and meaning (`111`, Chinese + English mixed, `Color2` too generic).
- Gradient variables (`Linear`, `Radial`, `ip渐变1`, `渐变3`) are not self-descriptive; ownership is unclear.
- Some sections return `{}` (no variable bindings), implying hard-coded styles still exist.

## 6. Refactor suggestions for stable handoff to code
1. Rename semantic tokens with explicit roles, e.g.:
- `text_day` -> `text/primary/day`
- `text_last` -> `text/primary/night`
- `按键` -> `text/button/night`
- `Color2` -> `text/secondary/day`

2. Normalize effect naming:
- `111` -> `effect/surface/glow-sm`
- `message_input` -> `effect/input/glow-lg`
- `text_light` -> `effect/text/glow-sm`

3. Establish explicit collection contracts:
- `core/primitives`
- `theme/mode`
- `effect/system`
- `component/ip`, `component/input`, `component/nav`

4. Ensure all production frames bind variables (remove remaining hard-coded color/effect values).

## 7. Standard naming (day/night only)
Naming rule:
- `category/role/state/mode`
- `category` examples: `text`, `icon`, `surface`, `effect`, `component`
- `state` default to `default` when no interaction state exists
- `mode` only keeps `day` and `night`

Proposed migration from currently observed variables:

| Current name | Value (observed) | Proposed standard token |
|---|---|---|
| `text_day` | `#6A7282` | `text/primary/default/day` |
| `text_last` | `#E6F8FF 60%` | `text/primary/default/night` |
| `textday_first` | `#363B44` | `text/emphasis/default/day` |
| `Color2` | `#99A1AF` | `text/secondary/default/day` |
| `icon` | `#ADAFC8` | `icon/primary/default/night` |
| `icon2` | `#889599` | `icon/primary/default/day` |
| `dash` | `#FFFFFF 60%` | `text/button/default/night` |
| `按键` | `#FFFFFF99` | `text/button/default/night` (merge with `dash`) |
| `day_shoe` | `#FEECC2` | `surface/ip-glow/default/day` |
| `ip渐变1` | gradient | `component/ip/gradient/outer/night` |
| `渐变3` | gradient | `component/ip/gradient/inner/night` |
| `Linear` | gradient | `component/ip/gradient/outer/day` |
| `Radial` | gradient | `component/ip/gradient/inner/day` |
| `ip_day_effects` | effect set | `effect/ip/outer/day` |
| `ip_day_effects_inner` | effect set | `effect/ip/inner/day` |
| `text_light` | drop shadow | `effect/text/glow/default/night` |
| `message_input` | drop shadow | `effect/input/glow/default/night` |
| `111` | drop shadow | `effect/surface/glow/default/night` |

Notes:
- `dash` and `按键` are semantically overlapping in night mode; keep one canonical token.
- Keep Chinese naming out of final production token names to simplify code export and linting.
- Keep gradient/effect tokens in component/effect categories, not in text/icon categories.

## 8. Practical optimization and refactor method
1. Freeze current variables and export a backup snapshot.
2. Create new collections:
- `sys/color` (day/night modes)
- `sys/effect` (day/night modes)
- `comp/ip` (day/night modes)
- `comp/input` (day/night modes)
3. Add canonical tokens first (new names above), without deleting old tokens.
4. Convert old tokens to alias-only bridge tokens:
- old token aliases new token for one migration cycle.
- example: `text_day -> text/primary/default/day`.
5. Refit top-level frames in priority:
- `登录/首页` -> `聊天舱` -> `共感地图`.
6. Replace direct hex/effect values with tokens in all production frames.
7. Run visual regression (day/night) on key screens:
- home, chat idle, chat recording, chat response, login.
8. Remove deprecated tokens only after all bindings are migrated and verified.

Execution checklist:
- No hard-coded colors/effects in production frames.
- No ambiguous names (`111`, `Color2`, `渐变3`, `ip渐变1`) left.
- Every token includes explicit `day` or `night` mode.
- Token export to frontend keeps 1:1 name mapping.

## 9. Key takeaway
The file already follows a mostly correct token direction: mode-aware theme tokens + reusable effect tokens + component bindings. The main gap is not visual capability, but token governance: naming clarity, explicit collection boundaries, and complete variable coverage across all frames.
