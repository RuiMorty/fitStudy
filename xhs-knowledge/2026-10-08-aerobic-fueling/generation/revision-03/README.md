# 有氧运动供能时间线

- 状态：第 3 版已完成本地检查，待用户审阅。
- 成品：依次使用 `images/01-cover.png`、`02-timeline.png`、`03-onset.png`、`04-routes.png`、`05-duration.png`、`06-amounts.png`、`07-donut.png`，每张 1536 × 2048 像素（3:4）。
- 总览：images/preview-contact-sheet.jpg。
- 可复制文案：caption.txt。
- 内容与参考研究：content.json。
- 生成记录：generation/render-manifest.json。
- 风格参考：`../2026-09-28-warmup/images/warmup-preview-v2-rick.png` 的米白底、砖红标题与细分隔线。
- 插画素材：`assets/` 中的瑞克 RGBA 剪影与 4 张通过 `lingzhi-image` 生成的 RGBA PNG；提示词、原图和请求记录在 `generation/lingzhi-revision-03/`。图表文字仍由渲染器排版，未使用 SVG。
- 历史版本归档：`generation/revision-01/` 和 `generation/revision-02/`。
- 本地栅格绘制草稿归档：`generation/local-raster-draft/`，不用于第 3 版成图。

这些时间节点描述正常进食、平稳开始中等强度运动且运动中不补糖时的常见趋势，不是固定的供能切换时刻。第 3 张 PCr 曲线是基于恒负荷膝伸肌实验时间常数的归一化示意，不是跑步实测。第 6、7 张的糖脂数值基于每小时 600 kcal 和指定 RER 演算，不是个人实测值。

重新渲染：python3 xhs-knowledge/2026-10-08-aerobic-fueling/render_cards.py
