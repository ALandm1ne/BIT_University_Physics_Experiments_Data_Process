import matplotlib.pyplot as plt
import matplotlib.patches as patches
from pathlib import Path

def draw_refined_solar_circuit():
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 8)
    ax.set_aspect('equal')
    ax.axis('off')

    # --- 1. 太阳能电池板 (PV) ---
    ax.add_patch(patches.Rectangle((1, 3), 1.5, 3, fill=False, lw=2))
    ax.text(1.75, 4.5, 'Solar Panel\n(太阳能板)', ha='center', va='center', fontsize=10)
    # 光照符号
    for i in range(3):
        ax.annotate('', xy=(1.2, 5.8+i*0.4), xytext=(0.5, 6.5+i*0.4),
                    arrowprops=dict(arrowstyle='->', color='orange', lw=1.5))

    # --- 2. 防反充二极管 D (关键防倒流元件) ---
    # 根据讲义图4原理，串联在正极
    ax.plot([2.5, 3.5], [5, 5], 'k-', lw=1.5)
    d_x = 3.5
    ax.add_patch(patches.Polygon([[d_x, 5.3], [d_x, 4.7], [d_x+0.5, 5]], closed=True, color='black'))
    ax.plot([d_x+0.5, d_x+0.5], [4.7, 5.3], 'k-', lw=2)
    ax.text(d_x+0.25, 5.6, 'Diode D', ha='center', fontsize=9)
    ax.plot([4, 5], [5, 5], 'k-', lw=1.5)

    # --- 3. 单刀双掷开关 S (核心切换逻辑) ---
    sw_center_x, sw_center_y = 6, 5.5
    ax.scatter(sw_center_x, sw_center_y, color='black', s=50, zorder=5) # 开关支点（连向蓄电池）
    
    # 两个目标触点
    ax.scatter(5, 5, edgecolors='black', facecolors='none', s=50) # Position B (Day)
    ax.scatter(7, 5, edgecolors='black', facecolors='none', s=50) # Position A (Night)
    
    # 画开关柄（当前指向 Night 模式作为示例）
    ax.plot([sw_center_x, 6.8], [sw_center_y, 5.2], 'r-', lw=2.5) 
    
    ax.text(4.5, 4.5, 'B: Day\n(Charge)', ha='center', fontsize=9, color='blue')
    ax.text(7.5, 4.5, 'A: Night\n(Light)', ha='center', fontsize=9, color='red')

    # --- 4. 蓄电池 (Battery) ---
    # 支点向下连接蓄电池正极
    ax.plot([sw_center_x, sw_center_x], [sw_center_y, 4], 'k-', lw=1.5)
    # 标准电池符号
    ax.plot([5.5, 6.5], [4, 4], 'k-', lw=1.2)   # 正极
    ax.plot([5.7, 6.3], [3.8, 3.8], 'k-', lw=3) # 负极
    ax.text(6.8, 3.9, 'Battery', va='center', fontsize=10, fontweight='bold')

    # --- 5. 负载 RL (灯泡) ---
    # 从 Position A 连向灯泡
    ax.plot([7, 9], [5, 5], 'k-', lw=1.5)
    ax.plot([9, 9], [5, 4.5], 'k-', lw=1.5)
    # 电阻矩形框
    ax.add_patch(patches.Rectangle((8.5, 3.5), 1, 1, fill=False, lw=1.5))
    ax.text(9, 4, '$R_L$', ha='center', va='center', fontsize=10)
    ax.plot([9, 9], [3.5, 2], 'k-', lw=1.5)

    # --- 6. 公共负极回路线 (GND) ---
    ax.plot([1.75, 1.75], [3, 2], 'k-', lw=1.5) # 板子负极
    ax.plot([6, 6], [3.8, 2], 'k-', lw=1.5)     # 蓄电池负极
    ax.plot([1.75, 9], [2, 2], 'k-', lw=1.5)    # 底部总线

    plt.title("Solar Charging & Lighting Circuit)", 
              fontsize=12, pad=20, fontproperties='SimHei')
    
    plt.show()
    
if __name__ == '__main__':
    draw_refined_solar_circuit()