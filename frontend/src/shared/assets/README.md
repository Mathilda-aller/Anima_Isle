# Asset Template

## Directory Rules

- `modules/<module>/assets/icons/`: SVG icons or small monochrome assets
- `modules/<module>/assets/images/`: regular UI bitmaps, decorations, masks, underlines
- `modules/<module>/assets/illustrations/`: character art, scene art, large expressive visuals
- `modules/<module>/assets/bg/`: page or section backgrounds
- `shared/assets/*`: only for assets reused across multiple modules

## Export Rules From Figma

- Prefer `layer image` for page restoration and cut assets
- Prefer `SVG` for icons
- Use `original source image` only when you need the untouched source for later recropping or external processing

## Naming Rules

- Use `kebab-case` for actual files
- Use semantic names, not Figma layer names like `Rectangle 381`
- Add the role suffix only when it clarifies meaning: `-icon`, `-bg`, `-illustration`
- Keep one asset meaning per file

## Recommended File Names

- Icons: `wechat-login-icon.svg`, `memory-lane-icon.svg`
- Images: `login-switch-underline.png`, `chat-input-glow.png`
- Illustrations: `island-ip-logo.png`, `island-ip-character.png`
- Backgrounds: `auth-dark-global-bg.png`, `chat-home-dark-bg.png`

## Index Template

Each module keeps a single `assets/index.ts`:

```ts
export const MODULE_ASSETS = {
  icons: {},
  images: {},
  illustrations: {},
  bg: {},
} as const;
```

## Import Example

```ts
import { AUTH_ASSETS } from "@/modules/auth/assets";

const logo = AUTH_ASSETS.illustrations.islandIpLogo;
const pageBg = AUTH_ASSETS.bg.darkGlobalBg;
```
