import { SQUARE_ASSETS } from "@/modules/square/assets";

export type IslandId = "mist" | "ember" | "lagoon" | "azure" | "sprout" | "pebble" | "current";

export type SceneStyle = Record<string, string>;

export type IslandBubbleSlot = {
  left: string;
  top: string;
  width: string;
  highlighted?: boolean;
};

export type IslandConfig = {
  id: IslandId;
  name: string;
  backendIslandKey: string;
  englishDisplayName: string;
  futureChineseDisplayName?: string;
  hotspotStyle: SceneStyle;
  outlineLayerKeys: string[];
  focusLayerKeys: string[];
  outlineBlur: string;
  outlineOpacity: string;
  focusScale: number;
  focusTranslateX: string;
  focusTranslateY: string;  
  focusSceneHeight: string;
  tagSlots: IslandBubbleSlot[];
  mockTags: string[];
};

export type SceneLayer = {
  key: string;
  src: string;
  style: SceneStyle;
  islandId?: IslandId;
};

export const ISLAND_IDS: IslandId[] = ["current", "mist", "ember", "lagoon", "azure", "sprout", "pebble"];
export const DEFAULT_ISLAND_ID: IslandId = "mist";

export const ISLAND_CONFIGS: Record<IslandId, IslandConfig> = {
  current: {
    id: "current",
    name: "心流湾",
    backendIslandKey: "WIND",
    englishDisplayName: "WIND",
    futureChineseDisplayName: "",
    hotspotStyle: { left: "286rpx", top: "1246rpx", width: "322rpx", height: "188rpx" },
    outlineLayerKeys: ["ribbon-core"],
    focusLayerKeys: ["ribbon-core"],
    outlineBlur: "22rpx",
    outlineOpacity: "0.82",
    focusScale: 1.34,
    focusTranslateX: "-272rpx",
    focusTranslateY: "-1368rpx",
    focusSceneHeight: "800rpx",
    tagSlots: [
      { left: "308rpx", top: "302rpx", width: "186rpx", highlighted: true },
      { left: "410rpx", top: "392rpx", width: "172rpx" },
      { left: "244rpx", top: "462rpx", width: "208rpx" },
      { left: "182rpx", top: "534rpx", width: "194rpx" },
      { left: "374rpx", top: "614rpx", width: "192rpx" },
    ],
    mockTags: ["#想沉淀", "#慢一点", "#给自己留白", "#想找回节奏", "#今晚先靠岸"],
  },
  mist: {
    id: "mist",
    name: "雾岛",
    backendIslandKey: "MIST",
    englishDisplayName: "MIST",
    futureChineseDisplayName: "",
    hotspotStyle: { left: "52rpx", top: "196rpx", width: "366rpx", height: "410rpx" },
    outlineLayerKeys: ["mist-island-base"],
    focusLayerKeys: ["mist-island-base", "mist-island-mid", "mist-island-core", "mist-island-tail"],
    outlineBlur: "20rpx",
    outlineOpacity: "0.84",
    focusScale: 1.56,
    focusTranslateX: "62rpx",
    focusTranslateY: "-218rpx",
    focusSceneHeight: "1200rpx",
    tagSlots: [
      { left: "366rpx", top: "336rpx", width: "200rpx" },
      { left: "496rpx", top: "473rpx", width: "210rpx", highlighted: true },
      { left: "258rpx", top: "612rpx", width: "184rpx" },
      { left: "204rpx", top: "802rpx", width: "172rpx" },
    ],
    mockTags: ["#期末周破防", "#游戏连跪中", "#想躺平", "#失恋"],
  },
  ember: {
    id: "ember",
    name: "暖屿",
    backendIslandKey: "THUNDER",
    englishDisplayName: "THUNDER",
    futureChineseDisplayName: "",
    hotspotStyle: { left: "344rpx", top: "598rpx", width: "334rpx", height: "185rpx" },
    outlineLayerKeys: ["ember-island-base"],
    focusLayerKeys: ["ember-island-base", "ember-island-mid", "ember-island-core"],
    outlineBlur: "18rpx",
    outlineOpacity: "0.9",
    focusScale: 1.74,
    focusTranslateX: "-508rpx",
    focusTranslateY: "-755rpx",
    focusSceneHeight: "1160rpx",
    tagSlots: [
      { left: "190rpx", top: "334rpx", width: "186rpx", highlighted: true },
      { left: "360rpx", top: "430rpx", width: "184rpx" },
      { left: "190rpx", top: "526rpx", width: "198rpx" },
    ],
    mockTags: ["#想被安慰", "#想晒太阳", "#需要一点热量"],
  },
  lagoon: {
    id: "lagoon",
    name: "澄湾",
    backendIslandKey: "RAIN",
    englishDisplayName: "RAIN",
    futureChineseDisplayName: "",
    hotspotStyle: { left: "92rpx", top: "902rpx", width: "337rpx", height: "377rpx" },
    outlineLayerKeys: ["lagoon-island-base"],
    focusLayerKeys: ["lagoon-island-base", "lagoon-island-mid", "lagoon-island-core"],
    outlineBlur: "18rpx",
    outlineOpacity: "0.86",
    focusScale: 1.54,
    focusTranslateX: "48rpx",
    focusTranslateY: "-1140rpx",
    focusSceneHeight: "1160rpx",
    tagSlots: [
      { left: "294rpx", top: "530rpx", width: "164rpx" },
      { left: "514rpx", top: "626rpx", width: "178rpx", highlighted: true },
      { left: "364rpx", top: "720rpx", width: "194rpx" },
      { left: "362rpx", top: "380rpx", width: "174rpx" },
    ],
    mockTags: ["#想呼吸", "#适合发呆", "#先停靠一下", "#想被风吹一下"],
  },
  azure: {
    id: "azure",
    name: "澈岛",
    backendIslandKey: "CLOUD",
    englishDisplayName: "CLOUD",
    futureChineseDisplayName: "",
    hotspotStyle: { left: "454rpx", top: "954rpx", width: "144rpx", height: "214rpx" },
    outlineLayerKeys: ["sprout-island-body"],
    focusLayerKeys: ["sprout-island-body"],
    outlineBlur: "16rpx",
    outlineOpacity: "0.92",
    focusScale: 1.98,
    focusTranslateX: "-666rpx",
    focusTranslateY: "-1631rpx",
    focusSceneHeight: "1160rpx",
    tagSlots: [
      { left: "246rpx", top: "256rpx", width: "178rpx", highlighted: true },
      { left: "330rpx", top: "428rpx", width: "182rpx" },
      { left: "252rpx", top: "606rpx", width: "166rpx" },
    ],
    mockTags: ["#想逃离杂音", "#想慢慢清醒", "#想去海边"],
  },
  sprout: {
    id: "sprout",
    name: "芽岛",
    backendIslandKey: "LIGHT",
    englishDisplayName: "LIGHT",
    futureChineseDisplayName: "",
    hotspotStyle: { left: "548rpx", top: "814rpx", width: "96rpx", height: "132rpx" },
    outlineLayerKeys: ["sprout-island-glow"],
    focusLayerKeys: ["sprout-island-glow", "sprout-island-core"],
    outlineBlur: "16rpx",
    outlineOpacity: "0.96",
    focusScale: 2.38,
    focusTranslateX: "-1063rpx",
    focusTranslateY: "-1644rpx",
    focusSceneHeight: "1140rpx",
    tagSlots: [
      { left: "306rpx", top: "302rpx", width: "154rpx", highlighted: true },
      { left: "326rpx", top: "438rpx", width: "162rpx" },
    ],
    mockTags: ["#想重启", "#想恢复生机", "#有一点盼头"],
  },
  pebble: {
    id: "pebble",
    name: "微光礁",
    backendIslandKey: "SNOW",
    englishDisplayName: "SNOW",
    futureChineseDisplayName: "",
    hotspotStyle: { left: "52rpx", top: "1230rpx", width: "132rpx", height: "160rpx" },
    outlineLayerKeys: ["pebble-island-base"],
    focusLayerKeys: ["pebble-island-base", "pebble-island-mid", "pebble-island-core"],
    outlineBlur: "18rpx",
    outlineOpacity: "0.92",
    focusScale: 3.42,
    focusTranslateX: "18rpx",
    focusTranslateY: "-3820rpx",
    focusSceneHeight: "1120rpx",
    tagSlots: [
      { left: "376rpx", top: "632rpx", width: "192rpx", highlighted: true },
      { left: "228rpx", top: "752rpx", width: "194rpx" },
    ],
    mockTags: ["#想缩成一团", "#想暂时安静"],
  },
};

const BACKEND_ISLAND_TO_VISUAL_ID: Record<string, IslandId> = Object.values(ISLAND_CONFIGS).reduce<Record<string, IslandId>>(
  (result, island) => {
    result[island.backendIslandKey] = island.id;
    return result;
  },
  {},
);

export function getIslandIdByBackendKey(backendIslandKey: string | null | undefined): IslandId {
  if (!backendIslandKey) {
    return DEFAULT_ISLAND_ID;
  }

  return BACKEND_ISLAND_TO_VISUAL_ID[backendIslandKey.toUpperCase()] ?? DEFAULT_ISLAND_ID;
}

export const SCENE_LAYERS: SceneLayer[] = [
  {
    key: "center-current-glow",
    src: SQUARE_ASSETS.icons.centerCurrentGlow,
    style: { left: "244rpx", top: "1168rpx", width: "456rpx", height: "390rpx" },
  },
  {
    key: "center-current-outline",
    src: SQUARE_ASSETS.icons.centerCurrentOutline,
    style: { left: "-130rpx", top: "271rpx", width: "643rpx", height: "1042rpx" },
  },
  {
    key: "ribbon-core",
    islandId: "current",
    src: SQUARE_ASSETS.icons.ribbonCore,
    style: { left: "334rpx", top: "1244rpx", width: "298rpx", height: "241rpx" },
  },
  {
    key: "center-current-trail",
    src: SQUARE_ASSETS.icons.centerCurrentTrail,
    style: { left: "327rpx", top: "572rpx", width: "388rpx", height: "625rpx" },
  },
  {
    key: "ember-island-base",
    islandId: "ember",
    src: SQUARE_ASSETS.icons.emberIslandBase,
    style: { left: "354rpx", top: "621rpx", width: "307rpx", height: "154rpx" },
  },
  {
    key: "ember-island-mid",
    src: SQUARE_ASSETS.icons.emberIslandMid,
    style: { left: "366rpx", top: "625rpx", width: "250rpx", height: "125rpx" },
  },
  {
    key: "ember-island-core",
    src: SQUARE_ASSETS.icons.emberIslandCore,
    style: { left: "398rpx", top: "650rpx", width: "168rpx", height: "84rpx" },
  },
  {
    key: "lagoon-island-base",
    islandId: "lagoon",
    src: SQUARE_ASSETS.icons.lagoonIslandBase,
    style: { left: "101rpx", top: "911rpx", width: "320rpx", height: "363rpx" },
  },
  {
    key: "lagoon-island-mid",
    src: SQUARE_ASSETS.icons.lagoonIslandMid,
    style: { left: "130rpx", top: "931rpx", width: "272rpx", height: "316rpx" },
  },
  {
    key: "lagoon-island-core",
    src: SQUARE_ASSETS.icons.lagoonIslandCore,
    style: { left: "173rpx", top: "968rpx", width: "45rpx", height: "100rpx" },
  },
  {
    key: "sprout-island-spark",
    src: SQUARE_ASSETS.icons.sproutIslandSpark,
    style: { left: "538rpx", top: "1271rpx", width: "65rpx", height: "65rpx" },
  },
  {
    key: "sprout-island-glow",
    islandId: "sprout",
    src: SQUARE_ASSETS.icons.sproutIslandGlow,
    style: { left: "560rpx", top: "823rpx", width: "88rpx", height: "122rpx" },
  },
  {
    key: "mist-island-base",
    islandId: "mist",
    src: SQUARE_ASSETS.icons.mistIslandBase,
    style: { left: "81rpx", top: "334rpx", width: "345rpx", height: "395rpx" },
  },
  {
    key: "mist-island-mid",
    src: SQUARE_ASSETS.icons.mistIslandMid,
    style: { left: "101rpx", top: "362rpx", width: "293rpx", height: "320rpx" },
  },
  {
    key: "mist-island-core",
    src: SQUARE_ASSETS.icons.mistIslandCore,
    style: { left: "198rpx", top: "384rpx", width: "171rpx", height: "81rpx" },
  },
  {
    key: "mist-island-tail",
    src: SQUARE_ASSETS.icons.mistIslandTail,
    style: { left: "115rpx", top: "565rpx", width: "57rpx", height: "100rpx" },
  },
  {
    key: "sprout-island-body",
    islandId: "azure",
    src: SQUARE_ASSETS.icons.sproutIslandBody,
    style: { left: "462rpx", top: "955rpx", width: "128rpx", height: "202rpx" },
  },
  {
    key: "sprout-island-core",
    src: SQUARE_ASSETS.icons.sproutIslandCore,
    style: { left: "571rpx", top: "833rpx", width: "57rpx", height: "75rpx" },
  },
  {
    key: "pebble-island-base",
    islandId: "pebble",
    src: SQUARE_ASSETS.icons.pebbleIslandBase,
    style: { left: "65rpx", top: "1244rpx", width: "106rpx", height: "133rpx" },
  },
  {
    key: "pebble-island-mid",
    src: SQUARE_ASSETS.icons.pebbleIslandMid,
    style: { left: "77rpx", top: "1255rpx", width: "72rpx", height: "111rpx" },
  },
  {
    key: "pebble-island-core",
    src: SQUARE_ASSETS.icons.pebbleIslandCore,
    style: { left: "100rpx", top: "1318rpx", width: "34rpx", height: "36rpx" },
  },
];
