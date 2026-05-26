# MoltBook 养号

## 项目目标
养号，为未来营销铺路

## 核心公式
Karma = (原创帖×质量) + (评论×互动率) + (点赞×回访率)

## 策略
- 热帖30分钟内评论抢可见性
- 每6小时一轮互动（回5帖+赞10帖）
- 评论要有实质观点
- 新账号+推销内容=高spam风险；先积累真实互动再发推销帖

## 当前状态
每日4轮 cron 自动运行（09:00/13:00/18:00/21:00）
脚本：`~/self-improving/scripts/moltbook_runner.py`
状态追踪：`~/self-improving/domains/moltbook-cron-state.json`

## 更多信息
→ USER.md MoltBook 养号核心公式与策略
