---
tags:
  - TA
  - FEM
  - 弹簧法
  - Verlet
  - 实战
created: 2026-08-15
related:
  - "[[FEM蒙皮 vs 关节蒙皮-迪士尼与战神]]"
  - "[[绑定与蒙皮-前置知识入门]]"
---

# FEM 从零实现:2D 弹簧到软体(实战)

> 配套阅读:[[绑定与蒙皮-前置知识入门]]第 5 节(数值方法)、[[FEM蒙皮 vs 关节蒙皮-迪士尼与战神]]第 2 节(FEM 公式)。
>
> 目标:用**可运行的代码**,从最直觉的"弹簧网"一路走到真正的**有限元(FEM)**软体,建立从感性到理性的完整理解。

---

## ⚡ Demo 快速上手(先玩起来,再看理论)

四个 demo 都在 `绑定蒙皮-演示/` 文件夹里。**三个 HTML 双击就能玩,不需要 Python**;Python 版需要先装好 Python + numpy + matplotlib。

| Demo | 文件 | 怎么玩 | 对应知识点 |
|------|------|--------|-----------|
| ① 弹簧法 | `2d_软体_弹簧法.html` | 鼠标拖红点,看回弹抖动 | Verlet + 距离约束 = 动态骨骼/jiggle |
| ② 静态 FEM | `2d_fem_三角形.html` | 拖滑块调载荷/软硬/泊松比 | 共旋 FEM + Newton 迭代 |
| ③ 动态 FEM | `2d_fem_动态_隐式欧拉.html` | 看软块掉落→撞地→反弹 | FEM + 隐式欧拉(Backward Euler) |
| ④ Python 版 | `fem_2d_三角形.py` | 终端运行,弹窗看图 + 存 PNG | 同上 ②,可看数值收敛细节 |

### 各 Demo 详细玩法

**① `2d_软体_弹簧法.html`**
- 双击打开,看到一块"布"挂在顶部、受重力下垂;
- **按住任意红点拖动**,松手看它回弹抖动(金点是钉住的固定点);
- 右侧滑块:刚度(越硬越脆)、阻尼(越接近 1 越软塌)、重力开关、重置按钮。
- 若打开是黑屏:按 **Ctrl + F5** 强制刷新(清缓存)。

**② `2d_fem_三角形.html`**
- 双击打开,左右两张图:左"未变形"、右"变形后"(浅色是参照);
- 三个滑块实时重算:
  - **载荷**:往下拉的力,调大 → 杆子弯得更厉害;
  - **杨氏模量 E**:调小 → 软,调大 → 硬;
  - **泊松比 ν**:拉到 **0.45** → 体积保持最明显(难压扁);
- 底部绿色框实时显示"迭代次数 + 载荷点位移"。

**③ `2d_fem_动态_隐式欧拉.html`**
- 双击打开,软方块自由落体 → 撞地 → 压扁反弹 → 弹几下静止;
- 滑块:重力、E、ν、阻尼、恢复系数(反弹力度);
- **试试**:E 调到 200 → "瘫成一滩";E 调到 8000 → 像硬块反复弹;恢复系数 0.9 → 蹦得老高;
- 底部显示帧率、质心/底部位置、速度。

**④ `fem_2d_三角形.py`(可选)**
1. 按 `Win + R` → 输入 `cmd` 回车;
2. 粘贴运行:
   ```
   python "D:\Obsidian\works\TA\绑定蒙皮-演示\fem_2d_三角形.py"
   ```
3. 弹窗显示变形前后对比图(关掉即可),同时生成 `fem_2d_三角形_结果.png`。

> **建议顺序**:先玩 ①(有手感)→ 再玩 ③(看动态)→ 最后玩 ②(对照公式)。三张 HTML 都无需 Python。

---

## 0. 为什么先学弹簧?

FEM 的难点是"连续体 + 数学"太重。但有一个极好的直觉垫脚石:

> **把一块软体想象成"很多很多弹簧连成的网"。弹簧拉伸会回弹——这就是弹性;弹簧连得够密,整体就像连续体。**

- **弹簧法(质量-弹簧)**:实现简单、能跑、能看,是游戏里布料/软体的常用近似。
- **FEM**:把"弹簧网"用**数学严格化**——不是离散的弹簧,而是连续的"能量密度函数",求解精确的力。

这篇先让你**看到弹簧网**,再用 FEM 复刻同一个现象,你就懂 FEM 到底在算什么了。

---

## 1. 弹簧法:Verlet + 距离约束(可运行)

这是游戏里动态骨骼/jiggle/布料最常用的套路,和[[FEM蒙皮 vs 关节蒙皮-迪士尼与战神]]第三、五节的动态骨骼是同一套。

**核心三步(每帧)**:
1. **Verlet 积分**:用"当前位置 - 上一帧位置"隐含速度,更新位置(惯性 + 重力 + 阻尼);
2. **约束迭代**:反复把弹簧拉回静息长度(距离约束),迭代次数越多越硬;
3. **固定点**:某些顶点钉住(如布料顶端),其余自由动。

**完整可运行代码**:`绑定蒙皮-演示/2d_软体_弹簧法.html`(双击用浏览器打开,拖拽顶点看效果)。

核心逻辑摘录(JS):

```javascript
// 1. Verlet 积分
for (const p of points) {
    if (p.pinned) continue;
    const vx = (p.x - p.px) * damp;      // 速度 = 位移 × 阻尼
    const vy = (p.y - p.py) * damp;
    p.px = p.x; p.py = p.y;              // 记住上一帧
    p.x += vx; p.y += vy + gravity;      // 惯性 + 重力
}

// 2. 距离约束迭代(拉回静息长度 L)
for (let it = 0; it < 4; it++) {
    for (const [a, b, L] of springs) {
        const pa = points[a], pb = points[b];
        let dx = pb.x - pa.x, dy = pb.y - pa.y;
        let d = Math.hypot(dx, dy) || 1e-6;
        const diff = (d - L) / d * 0.5 * stiffness;  // 各拉一半
        dx *= diff; dy *= diff;
        if (!pa.pinned) { pa.x += dx; pa.y += dy; }
        if (!pb.pinned) { pb.x -= dx; pb.y -= dy; }
    }
}
```

> **这就是"软体"的全部直觉**:质量点 + 弹簧 + Verlet。玩一下 HTML demo,感受 stiffness/damping 对"肉感 vs 干脆"的影响——这正是战神动态骨骼调手感的方式。

---

## 2. FEM:把弹簧网"连续化"

弹簧法的问题:**结果取决于弹簧怎么连、多密**,没有"材料"概念。FEM 换一个问法:

> 不问"这根弹簧伸多长",而问"这块**单位面积的材料**储存了多少能量"。

这就是**能量密度函数** $\Psi$(超弹性)。迪士尼用的就是它(见[[FEM蒙皮 vs 关节蒙皮-迪士尼与战神]]2.2 节):

$$
\Psi(\mathbf{F}) = \mu\|\mathbf{F}-\mathbf{R}\|_F^2 + \frac{\lambda}{2}(J-1)^2,\quad J=\det\mathbf{F}
$$

- $\mathbf{F}$:形变梯度,描述"这块材料被怎么拉扯旋转";
- $\mathbf{R}$:从 $\mathbf{F}$ 极分解出的刚体旋转(把旋转抽走,只对纯形变算能量);
- $\mu,\lambda$:拉梅常数,由杨氏模量 $E$ 和泊松比 $\nu$ 决定——**这就是"材料参数"**。

**内力 = 能量的负梯度**:$\mathbf{f} = -\partial E/\partial \mathbf{x}$。物体停在"能量最低、力平衡"处。

---

## 3. FEM 2D 三角形:完整可运行代码

> 用最简单的线性三角单元,把一块 2D 软杆"吊"起来看它变形。代码在 `绑定蒙皮-演示/fem_2d_三角形.py`(需 `numpy + matplotlib`)。**不想装 Python?** 双击打开 `绑定蒙皮-演示/2d_fem_三角形.html`——同样算法,浏览器里直接跑,还能拖动滑块调软硬、载荷、泊松比。

### 3.1 关键公式(对应代码)

对每个三角形:
- **形变梯度**:$\mathbf{F} = \mathbf{D}_s \mathbf{D}_m^{-1}$,其中 $\mathbf{D}_m=[X_1-X_0,\,X_2-X_0]$ 是 rest 边矩阵,$\mathbf{D}_s$ 是当前边矩阵;
- **极分解**:SVD 得 $\mathbf{F}=\mathbf{U}\Sigma\mathbf{V}^T$,取 $\mathbf{R}=\mathbf{U}\mathbf{V}^T$;
- **第一 PK 应力**:
  $$
  \mathbf{P} = 2\mu(\mathbf{F}-\mathbf{R}) + \lambda(J-1)\,J\,\mathbf{F}^{-T}
  $$
- **节点力**(线性三角形,参考三角形梯度 $\nabla N_0=(-1,-1),\ \nabla N_1=(1,0),\ \nabla N_2=(0,1)$):
  $$
  \mathbf{f}_i = -A_0\,\mathbf{P}\,\mathbf{D}_m^{-T}\,\nabla N_i
  $$

### 3.2 完整代码

```python
import numpy as np
import matplotlib
matplotlib.use('TkAgg')          # 本地弹窗显示;若服务器运行改为 'Agg'
import matplotlib.pyplot as plt

# ---------- 1. 网格:矩形软杆,拆成三角形 ----------
nx, ny = 8, 3                    # 节点网格
Lx, Ly = 3.0, 1.0
X = np.array([[i*Lx/(nx-1), j*Ly/(ny-1)] for j in range(ny) for i in range(nx)], float)
def nid(i, j): return j*nx + i

tris = []
for j in range(ny-1):
    for i in range(nx-1):
        a, b, c, d = nid(i,j), nid(i+1,j), nid(i+1,j+1), nid(i,j+1)
        tris.append([a, b, c]); tris.append([a, c, d])
tris = np.array(tris)

# ---------- 2. 材料参数 ----------
E, nu = 1000.0, 0.3
mu  = E/(2*(1+nu))
lam = E*nu/((1+nu)*(1-2*nu))

fixed = [nid(0, j) for j in range(ny)]     # 固定左边界

# ---------- 3. 三角形几何预计算 ----------
Dm_inv, A0 = [], []
gradNu = [np.array([-1., -1.]), np.array([1., 0.]), np.array([0., 1.])]
for t in tris:
    X0, X1, X2 = X[t[0]], X[t[1]], X[t[2]]
    Dm = np.column_stack([X1-X0, X2-X0])
    Dm_inv.append(np.linalg.inv(Dm))
    A0.append(0.5*abs(np.linalg.det(Dm)))

def polar_R(F):
    U, S, Vt = np.linalg.svd(F)
    R = U @ Vt
    if np.linalg.det(R) < 0:               # 修正反射
        U[:, -1] *= -1
        R = U @ Vt
    return R

# ---------- 4. 内力(所有三角形的合力) ----------
def forces(x):
    f = np.zeros_like(x)
    for k, t in enumerate(tris):
        i0, i1, i2 = t
        x0, x1, x2 = x[i0], x[i1], x[i2]
        Ds = np.column_stack([x1-x0, x2-x0])
        F  = Ds @ Dm_inv[k]
        J  = np.linalg.det(F)
        R  = polar_R(F)
        FinvT = np.linalg.inv(F).T
        P = 2*mu*(F-R) + lam*(J-1)*J*FinvT   # 第一 PK 应力
        g = Dm_inv[k].T                      # Dm^{-T}
        for idx, gnu in zip(t, gradNu):
            f[idx] -= A0[k]*(P @ g @ gnu)
    return f

# ---------- 5. Newton 迭代(切线刚度用有限差分) ----------
def solve(x, load):
    x = x.copy()
    for it in range(60):
        f = forces(x)
        r = load - f                         # 残差(净不平衡力)
        n = x.size
        K = np.zeros((n, n)); h = 1e-5
        for j in range(n):                   # 数值切线刚度 K=∂f/∂x
            xp = x.copy().ravel(); xp[j] += h
            K[:, j] = (forces(xp.reshape(-1,2)).ravel() - f.ravel())/h
        for node in fixed:                   # 固定节点:dx=0
            for d in range(2):
                idx = node*2+d
                K[idx,:] = 0; K[:,idx] = 0; K[idx,idx] = 1; r[idx] = 0
        dx = np.linalg.solve(K, r)           # 解 K dx = r
        x += dx.reshape(-1, 2)
        if np.linalg.norm(dx) < 1e-6:
            break
    return x

# ---------- 6. 施加载荷并求解 ----------
load = np.zeros_like(X)
load[nid(nx-1, ny//2), 1] = -20.0           # 右端中点向下拉
x_deformed = solve(X, load)

# ---------- 7. 可视化 ----------
fig, ax = plt.subplots(1, 2, figsize=(10, 3.5))
for ax_, pts, title in [(ax[0], X, 'Rest'), (ax[1], x_deformed, 'Deformed')]:
    for t in tris:
        poly = np.vstack([pts[t[0]], pts[t[1]], pts[t[2]], pts[t[0]]])
        ax_.plot(poly[:,0], poly[:,1], '-', lw=0.7, color='0.4')
    ax_.scatter(pts[:,0], pts[:,1], s=12, c='tab:red')
    ax_.set_aspect('equal'); ax_.set_title(title)
plt.tight_layout(); plt.show()
```

### 3.3 逐段读懂

| 段 | 做什么 | 对应前置知识 |
|----|--------|------------|
| 1–3 | 搭网格、算 $\mathbf{D}_m^{-1}$ 和面积 | 三角形几何 |
| `polar_R` | SVD 极分解取旋转 $\mathbf{R}$ | [[绑定与蒙皮-前置知识入门]]3.5 节 |
| `forces` | 形变梯度 → 应力 → 节点力 | FEM 核心公式 |
| `solve` | Newton 迭代:`K dx = r` | 前置知识 5.2/5.3 节 |
| 6–7 | 加负载、求解、画图 | 结果验证 |

> **关键对照**:`forces` 里的 $\mathbf{P}=2\mu(\mathbf{F}-\mathbf{R})+\lambda(J-1)J\mathbf{F}^{-T}$,就是[[FEM蒙皮 vs 关节蒙皮-迪士尼与战神]]2.3 节 3D 六面体代码里**同一个应力公式的 2D 版**。读懂这里,3D 就是"把三角形换成六面体、把 2×2 矩阵换成 3×3"。

---

## 4. 弹簧法 → FEM 的对应关系

| 概念 | 弹簧法 | FEM |
|------|--------|-----|
| 形变 | 弹簧伸长量 | 形变梯度 $\mathbf{F}$ |
| 回弹力 | 弹簧力 $k\Delta L$ | 应力 $\mathbf{P}=2\mu(\mathbf{F}-\mathbf{R})+\dots$ |
| 材料参数 | 弹簧刚度 $k$ | 拉梅常数 $\mu,\lambda$(来自 $E,\nu$) |
| 平衡 | 反复拉弹簧到静息长度 | Newton 解 $K dx = r$ |
| 体积保持 | 弹簧网天然近似 | $\lambda(J-1)$ 项惩罚体积变化 |

一句话:**FEM 是"把弹簧换成能量密度函数、把松弛换成 Newton 迭代"的严格版本。** 弹簧法快但依赖拓扑,FEM 准但贵——这就是为什么游戏用前者、电影用后者的根源(回到[[FEM蒙皮 vs 关节蒙皮-迪士尼与战神]]的总览对比)。

---

## 5. 动态 FEM:隐式欧拉(Backward Euler)

上面的静态求解回答"最终会变成什么样";动态则回答"**过程中怎么动**"——软体掉落、撞地、压缩、反弹、抖动,直到静止。

### 5.1 和静态 Newton 的区别

| | 静态(第 3 节) | 动态(本节) |
|---|---|---|
| 求解目标 | 平衡位置 $\mathbf{x}$ | 每帧速度增量 $\Delta\mathbf{v}$ |
| 方程 | $K\,dx = r$(解平衡) | $(M - h^2K)\Delta v = h(f + hKv + f_{ext})$ |
| 惯性 | 忽略 | 质量矩阵 $M$ 参与 |
| 结果 | 一次解到终态 | 逐帧推进,能看到抖动过程 |

### 5.2 隐式欧拉推导

运动方程(内力 $f$ + 外力 $f_{ext}$):

$$
M\,\mathbf{a} = f(\mathbf{x}) + f_{ext}
$$

隐式欧拉:$v^{n+1}=v^n+h a^{n+1}$,$x^{n+1}=x^n+h v^{n+1}$。把 $f(x^{n+1})$ 一阶线性化 $f(x^{n+1})\approx f(x^n)+K(x^{n+1}-x^n)$,其中 $K=\partial f/\partial x$ 是切线刚度,整理得:

$$
\boxed{(M - h^2K)\,\Delta v = h\,(f^n + h\,K\,v^n + f_{ext})}
$$

- 因为 $K$ 负半定,$M-h^2K$ 正定,可解;
- **无条件稳定**:即使步长 $h$ 大也不"爆炸"(对比显式欧拉)——这就是迪士尼 FEM 能处理大形变的根本原因,对应[[FEM蒙皮 vs 关节蒙皮-迪士尼与战神]]2.4 节。

### 5.3 可运行 demo

`绑定蒙皮-演示/2d_fem_动态_隐式欧拉.html`(双击浏览器打开):
- 一块软方块自由落体 → 撞地 → 压缩波传播 → 弹跳 → 静止;
- 滑块:重力、E、泊松比、阻尼、恢复系数;
- **核心就在 `step(h)` 函数**:数值切线刚度 $K$ → 组装 $M-h^2K$ → 高斯消元解 $\Delta v$ → 更新速度/位置 → 地面碰撞。

**调参体验**:
- E 调小 → 软体落地"瘫"成一滩;
- E 调大 → 像硬块反复弹跳;
- ν → 0.45 → 落地压缩时体积保持明显(更难被压扁);
- 恢复系数 0 → 落地不反弹直接停,0.9 → 蹦得老高。

> 把这里看懂,再回头看[[FEM蒙皮 vs 关节蒙皮-迪士尼与战神]]2.4 节的 Newton/Backward Euler 伪代码,就是"同一个公式,从 2D 三角到 3D 六面体、从节点软体到角色肌肉"。

---

## 6. 下一步

1. **跑通四个 demo**:先玩弹簧 HTML(有手感)→ 再开静态 FEM HTML(看平衡形变)→ 开**动态 FEM HTML**(看掉落/反弹/抖动,即隐式欧拉)→ 装好 Python 后再跑 `fem_2d_三角形.py`(看数值收敛细节);
2. **改参数**:把 $E$ 改大改小看软硬、把 $\nu\to 0.49$ 看体积保持(接近不可压缩);
3. **进阶**:读 Sifakis & Barbic 的 *FEM Simulation of 3D Deformable Solids*,把 2D 三角形升级成 3D 六面体/四面体;
4. **回到主线**:此时再读[[FEM蒙皮 vs 关节蒙皮-迪士尼与战神]]2.3/2.4 节的 3D 代码和多重网格,就完全能看懂了。
