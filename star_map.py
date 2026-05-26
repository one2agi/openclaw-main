#!/usr/bin/env python3
"""
生成一张简单的星辰图
"""
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.colors import LinearSegmentedColormap

# 设置中文字体
plt.rcParams['font.family'] = ['DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

# 创建画布
fig, ax = plt.subplots(figsize=(14, 10), facecolor='#0a0a1a')
ax.set_facecolor('#0a0a1a')

# 随机生成星星
np.random.seed(42)
n_stars = 300
ra = np.random.uniform(0, 360, n_stars)  # 赤经 (度)
dec = np.random.uniform(-90, 90, n_stars)  # 赤纬 (度)
sizes = np.random.exponential(3, n_stars) + 0.5
brightness = np.random.exponential(1, n_stars)

# 颜色映射 (蓝白到黄白)
colors = plt.cm.YlOrRd(brightness / brightness.max())

# 绘制星星
for i in range(n_stars):
    size = sizes[i] * 2
    ax.scatter(ra[i], dec[i], s=size, c=[colors[i]], alpha=0.8, edgecolors='white', linewidths=0.3)

# 添加一些亮星 (特写)
special_stars = [
    (83.82, -5.39, '天狼星 (Sirius)', 150),   # 大犬座 α
    (37.95, 89.26, '北极星 (Polaris)', 120),   # 小熊座 α
    (101.29, 7.41, '参宿七 (Rigel)', 100),    # 猎户座 β
    (88.79, 7.41, '参宿四 (Betelgeuse)', 90), # 猎户座 α
    (279.23, -11.16, '心宿二 (Antares)', 100), # 天蝎座 α
    (37.95, 89.26, '北极星', 80),
]

for ra_s, dec_s, name, size in special_stars:
    ax.scatter(ra_s, dec_s, s=size, c='white', alpha=1, edgecolors='cyan', linewidths=1)
    ax.annotate(name, (ra_s, dec_s), xytext=(5, 5), textcoords='offset points',
                fontsize=8, color='white', alpha=0.9)

# 绘制假想的星座连线
constellations = [
    # 猎户座腰带
    [(88.79, -1.2), (84.05, -0.3), (79.17, 0.3)],
    # 北斗七星
    [(162.1, 57.0), (165.9, 54.9), (172.1, 53.7), (177.3, 54.9), (183.3, 52.0), (192.1, 51.5), (201.8, 49.5)],
]

for constellation in constellations:
    ra_c = [c[0] for c in constellation]
    dec_c = [c[1] for c in constellation]
    ax.plot(ra_c, dec_c, 'b-', alpha=0.3, linewidth=1)

# 添加银河带 (模拟)
for i in range(50):
   银河_ra = np.linspace(0, 360, 100)
    银河_dec = 30 * np.sin(银河_ra * np.pi / 180) + np.random.normal(0, 5, 100)
    ax.scatter(银河_ra, 银河_dec, s=0.3, c='lightblue', alpha=0.15)

# 装饰
ax.set_xlim(0, 360)
ax.set_ylim(-90, 90)
ax.set_xlabel('赤经 RA (°)', color='white', fontsize=12)
ax.set_ylabel('赤纬 Dec (°)', color='white', fontsize=12)
ax.set_title('🌟 星辰图 / Star Map 🌟', color='white', fontsize=18, pad=20)
ax.tick_params(colors='white')
ax.spines['top'].set_color('white')
ax.spines['bottom'].set_color('white')
ax.spines['left'].set_color('white')
ax.spines['right'].set_color('white')
ax.grid(True, alpha=0.1, color='white')

# 添加图例
legend_elements = [
    mpatches.Patch(facecolor='white', edgecolor='cyan', label='亮星 (Bright Stars)'),
    mpatches.Patch(facecolor='lightyellow', edgecolor='white', label='普通恒星 (Ordinary Stars)'),
]
ax.legend(handles=legend_elements, loc='lower left', facecolor='#1a1a2e', edgecolor='white', labelcolor='white')

plt.tight_layout()
plt.savefig('star_map.png', dpi=150, facecolor='#0a0a1a', edgecolor='none')
print("✅ 星辰图已保存为 star_map.png")
