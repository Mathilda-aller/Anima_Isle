# Square Island Mapping

这份映射用于统一：
- 后端 LLM 返回的 `island_category`
- 前端共感群岛视觉岛屿 `island_id`
- 分岛 detail 页顶部英文展示名
- 后续中文岛名配置追溯

当前实际配置来源：
- 前端配置文件：`frontend/src/modules/square/constants/islands.ts`

## Mapping Table

| Backend island key | English display name | Future Chinese display name | Frontend visual island id | Current visual island name |
| --- | --- | --- | --- | --- |
| `MIST` | `MIST` | `待补充` | `mist` | `雾岛` |
| `THUNDER` | `THUNDER` | `待补充` | `ember` | `暖屿` |
| `RAIN` | `RAIN` | `待补充` | `lagoon` | `澄湾` |
| `CLOUD` | `CLOUD` | `待补充` | `azure` | `澈岛` |
| `LIGHT` | `LIGHT` | `待补充` | `sprout` | `芽岛` |
| `SNOW` | `SNOW` | `待补充` | `pebble` | `微光礁` |
| `WIND` | `WIND` | `待补充` | `current` | `心流湾` |

## Notes

- 发布成功后，前端直接使用后端返回的 `TicketDTO.island_category` 做路由分发，不再自行重新分类。
- 如果后端返回未知岛屿 key，前端当前会兜底到 `mist`。
- 后续如果需要改中文名，只需要补全 `futureChineseDisplayName` 配置，不需要改发布流逻辑。
