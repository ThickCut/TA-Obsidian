# -*- coding: utf-8 -*-
"""
2D 共旋 FEM 软体(线性三角形单元)
================================
把一块矩形软杆"吊"起来(左边界固定),右端中点施加向下载荷,
用 Newton 迭代求解平衡形变,并画图对比 rest / deformed。

运行:
    python fem_2d_三角形.py
依赖:
    pip install numpy matplotlib
"""
import numpy as np
import matplotlib
# 优先交互式后端;无显示环境自动回退到非交互后端
try:
    matplotlib.use('TkAgg')
except Exception:
    matplotlib.use('Agg')
import matplotlib.pyplot as plt

# 配置中文字体,避免默认字体缺中文字形(标题显示成方框)
matplotlib.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'DejaVu Sans']
matplotlib.rcParams['axes.unicode_minus'] = False

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
mu  = E/(2*(1+nu))               # 拉梅第一常数(剪切)
lam = E*nu/((1+nu)*(1-2*nu))     # 拉梅第二常数(体积)

fixed = [nid(0, j) for j in range(ny)]     # 固定左边界

# ---------- 3. 三角形几何预计算 ----------
Dm_inv, A0 = [], []
gradNu = [np.array([-1., -1.]), np.array([1., 0.]), np.array([0., 1.])]  # 参考三角形梯度
for t in tris:
    X0, X1, X2 = X[t[0]], X[t[1]], X[t[2]]
    Dm = np.column_stack([X1-X0, X2-X0])   # rest 边矩阵
    Dm_inv.append(np.linalg.inv(Dm))
    A0.append(0.5*abs(np.linalg.det(Dm)))  # rest 面积

def polar_R(F):
    """极分解:从形变梯度 F 中提取刚体旋转 R = U V^T"""
    U, S, Vt = np.linalg.svd(F)
    R = U @ Vt
    if np.linalg.det(R) < 0:               # 修正反射(镜像)
        U[:, -1] *= -1
        R = U @ Vt
    return R

# ---------- 4. 内力(所有三角形合力) ----------
def forces(x):
    f = np.zeros_like(x)
    for k, t in enumerate(tris):
        i0, i1, i2 = t
        x0, x1, x2 = x[i0], x[i1], x[i2]
        Ds = np.column_stack([x1-x0, x2-x0])   # 当前边矩阵
        F  = Ds @ Dm_inv[k]                    # 形变梯度
        J  = np.linalg.det(F)
        R  = polar_R(F)
        FinvT = np.linalg.inv(F).T
        P = 2*mu*(F-R) + lam*(J-1)*J*FinvT     # 第一 PK 应力
        g = Dm_inv[k].T                        # Dm^{-T}
        for idx, gnu in zip(t, gradNu):
            f[idx] -= A0[k]*(P @ g @ gnu)
    return f

# ---------- 5. Newton 迭代(切线刚度用有限差分) ----------
def solve(x, load):
    x = x.copy()
    for it in range(60):
        f = forces(x)
        r = (load - f).ravel()               # 残差(净不平衡力),展平成 1D(2n,)
        n = x.size
        K = np.zeros((n, n)); h = 1e-5
        for j in range(n):                   # 数值切线刚度 K = ∂f/∂x
            xp = x.copy().ravel(); xp[j] += h
            K[:, j] = (forces(xp.reshape(-1,2)).ravel() - f.ravel())/h
        for node in fixed:                   # 固定节点:dx=0
            for d in range(2):
                idx = node*2+d
                K[idx,:] = 0; K[:,idx] = 0; K[idx,idx] = 1; r[idx] = 0
        dx = np.linalg.solve(K, r)           # 解 K dx = r
        x += dx.reshape(-1, 2)
        if np.linalg.norm(dx) < 1e-6:
            print(f"  收敛于第 {it+1} 次迭代")
            break
    return x

# ---------- 6. 施加载荷并求解 ----------
load = np.zeros_like(X)
load[nid(nx-1, ny//2), 1] = -20.0           # 右端中点向下拉
print("Newton 求解中 ...")
x_deformed = solve(X, load)
print(f"右端中点 Y 位移 = {x_deformed[nid(nx-1, ny//2),1] - X[nid(nx-1, ny//2),1]:.4f}")

# ---------- 7. 可视化 ----------
fig, ax = plt.subplots(1, 2, figsize=(10, 3.5))
for ax_, pts, title in [(ax[0], X, 'Rest(未变形)'), (ax[1], x_deformed, 'Deformed(变形后)')]:
    for t in tris:
        poly = np.vstack([pts[t[0]], pts[t[1]], pts[t[2]], pts[t[0]]])
        ax_.plot(poly[:,0], poly[:,1], '-', lw=0.7, color='0.4')
    ax_.scatter(pts[:,0], pts[:,1], s=14, c='tab:red')
    ax_.set_aspect('equal'); ax_.set_title(title)
plt.tight_layout()
out = "fem_2d_三角形_结果.png"
plt.savefig(out, dpi=120)
print(f"结果图片已保存: {out}")
try:
    plt.show()
except Exception:
    pass
