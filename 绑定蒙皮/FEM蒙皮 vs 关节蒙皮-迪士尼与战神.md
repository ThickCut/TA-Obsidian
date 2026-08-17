---
tags:
  - TA
  - 绑定
  - 蒙皮
  - rigging
  - 物理仿真
  - FEM
  - RBF
created: 2026-08-15
source:
  - "https://80.lv/articles/joint-based-skin-deformation-in-god-of-war-ragnar-k-will-be-explained-at-gdc-2023"
  - "https://disneyanimation.com/publications/efficient-elasticity-for-character-skinning-with-contact-and-collisions/"
  - "http://www.disneyanimation.com/library/poseSpaceDef.pdf"
---

# FEM 蒙皮 vs 关节蒙皮:迪士尼与《战神:诸神黄昏》

> 结论先行:**两者不是同源技术**,是"解决同一类问题(肌肉有纤维方向、形变要保体积、皮肉会滑动)的两条完全不同的路线"。
> - 迪士尼 = **有限元物理仿真**(离线电影级、精确、重算力)。
> - 战神 = **关节近似 + 动态骨骼**(游戏实时、装出物理感)。

---

## 一、总览对比

| 维度 | 迪士尼 FEM 方案 | 战神 Ragnarök 关节方案 |
|------|----------------|----------------------|
| 核心原理 | 有限元法(FEM)软体仿真 | 关节(RBF 驱动)+ 动态骨骼抖动 |
| 是否实时 | 否(超算/工作站 ~4–8fps 预览) | 是(游戏引擎 60fps) |
| 肌肉纤维方向 | 各向异性弹性材质精确建模 | 沿纤维方向**额外摆关节**来拟合 |
| 体积保持 | 物理方程(超弹性)严格保证 | 关节布局近似保证 |
| 皮肉滑动/褶皱 | 肌肉→皮肤多级仿真 | 动态骨骼 jiggle 近似 |
| 应用场景 | 电影离线渲染(皮克斯/迪士尼) | 主机游戏实时 |
| 代表论文/来源 | McAdams et al. 2011;Milne et al. 2016 | GDC 2023, Tenghao Wang (SMS) |

---

## 二、迪士尼:FEM 有限元蒙皮

### 2.1 原理

把角色看成**连续介质(连续体)**,不再用"骨骼+权重"近似,而是把肌肉/脂肪/皮肤离散成**实体单元网格**(hex 六面体或 tet 四面体),用**超弹性材料模型 + 隐式时间积分**求解软体在大形变下的真实应力应变。

- 骨骼是真实**刚体**,驱动网格边界;
- 网格内部通过求解**非线性偏微分方程**得到自然形变;
- 通过 **CCD 连续碰撞检测**保证绝不穿插。

**代表论文**
1. *Efficient Elasticity for Character Skinning with Contact and Collisions* — McAdams, Zhu, Selle, Empey, Tamstorf, Teran, Sifakis (SIGGRAPH 2011)。核心贡献:六面体格上的**共旋弹性**、单点积分、多重网格求解、并行 SVD。
2. *Flesh, flab, and fascia simulation on Zootopia* — Milne et al. (SIGGRAPH 2016 Talks)。在《疯狂动物城》里做**肌肉/脂肪/筋膜**多级仿真(皮肤滑动、褶皱)。
3. 对应专利:US 9,135,738 B2(Disney)。配套 Maya 插件 **PhysGrid**。

> 这篇 2011 论文就是知乎那篇回答里引用的 `MZSETTS11.pdf`(McAdams–Zhu–Selle–Empey–Tamstorf–Teran–Sifakis)。

### 2.2 数学:共旋超弹性

**形变梯度(deformation gradient)**
$$
\mathbf{F} = \frac{\partial \mathbf{x}}{\partial \mathbf{X}}
$$
$\mathbf{X}$ 是参考(未变形)坐标,$\mathbf{x}$ 是当前坐标。

**共旋(corotational)思路**:先把刚体旋转 $\mathbf{R}$ 从 $\mathbf{F}$ 里分离出去($\mathbf{F}=\mathbf{R}\mathbf{S}$,极分解),只对**纯应变**部分算能量,避免大旋转下线性模型失真。

常用能量(可压缩 Neo-Hookean 或共旋 StVK):
$$
\Psi(\mathbf{F}) = \mu\,\|\mathbf{F}-\mathbf{R}\|_F^2 + \frac{\lambda}{2}\,(J-1)^2,\qquad J=\det\mathbf{F}
$$
其中 $\mu,\lambda$ 是拉梅常数,与杨氏模量/泊松比关系:
$$
\mu=\frac{E}{2(1+\nu)},\qquad \lambda=\frac{E\nu}{(1+\nu)(1-2\nu)}
$$

**第一 Piola–Kirchhoff 应力**(能量对 $\mathbf{F}$ 的导数):
$$
\mathbf{P} = \frac{\partial \Psi}{\partial \mathbf{F}} = 2\mu(\mathbf{F}-\mathbf{R}) + \lambda(J-1)\,J\,\mathbf{F}^{-T}
$$

### 2.3 代码:六面体单元 + 单点积分

> 为便于理解,下面用 **8 节点六面体 + 单点积分(单元中心)** 的简化实现。真实系统会在单点积分基础上加**沙漏(hourglass)稳定项**抑制零能模态,并对 SVD 做**无分支向量化**。

```cpp
// 极分解:从 F 中提取刚体旋转 R(用 SVD)
// F = U * S * V^T,  R = U * V^T
Matrix3 polarRotation(const Matrix3& F) {
    // JacobiSVD / 数值稳定的 3x3 SVD,或直接迭代求解
    Matrix3 U, V; Vector3 S;
    svd(F, U, S, V);          // F = U * diag(S) * V^T
    Matrix3 R = U * V.transpose();
    if (R.determinant() < 0) { // 修正反射(镜像)情况
        U.col(2) *= -1;
        R = U * V.transpose();
    }
    return R;
}

// 一个六面体单元的共旋弹性力
// nodes[8]: 当前世界坐标; X[8]: 参考(rest)坐标
// 返回每个节点的内力求和(向量),以及可选切线刚度
struct HexCorotationalElement {
    Vector3 X[8];            // rest 坐标(不变)
    double mu, lambda;       // 拉梅常数
    double volume;           // rest 体积

    // 单点积分:在单元中心(ξ=η=ζ=0)处的形函数梯度 dN/dX
    // 对三线性六面体,8 个梯度向量固定,可预计算
    static void gradN(Vector3 g[8]) {
        // 参考坐标归一化到 [-1,1]^3,中心处 dN_i/dξ 为 ±1/2
        // 这里给出与 rest 几何无关的"参考域梯度",再乘 J^{-1} 得到 dN/dX
        const double s[8][3] = {
            {-1,-1,-1},{ 1,-1,-1},{ 1, 1,-1},{-1, 1,-1},
            {-1,-1, 1},{ 1,-1, 1},{ 1, 1, 1},{-1, 1, 1}
        };
        for (int i = 0; i < 8; i++)
            g[i] = Vector3(s[i][0], s[i][1], s[i][2]) * 0.125; // 1/8
    }

    // 形变梯度 F = Σ_i x_i ⊗ (∂N_i/∂X)
    Matrix3 deformationGradient(const Vector3 x[8], const Vector3 g[8]) {
        Matrix3 F = Matrix3::Zero();
        for (int i = 0; i < 8; i++)
            F += x[i] * g[i].transpose();   // 外积累加
        return F;
    }

    // 计算内力(和能量)
    void computeForces(const Vector3 x[8], Vector3 f[8], double& energy) {
        Vector3 g[8]; gradN(g);

        Matrix3 F = deformationGradient(x, g);
        double J = F.determinant();
        Matrix3 R = polarRotation(F);
        Matrix3 FinvT = F.inverse().transpose();

        // PK1 应力
        Matrix3 P = 2.0 * mu * (F - R)
                  + lambda * (J - 1.0) * J * FinvT;

        // 内力 f_i = -V0 * P * gradN_i  (注意方向)
        energy = 0.5 * mu * (F - R).squaredNorm()
               + 0.5 * lambda * (J - 1.0) * (J - 1.0);
        energy *= volume;

        for (int i = 0; i < 8; i++) {
            Vector3 Pi = P * g[i];
            f[i] = -volume * Pi;           // 负梯度 = 保守力
        }
    }

    // 切线刚度(Newton 用):K_ij = ∂f_i/∂x_j
    // 简化实现可用数值差分,生产系统用解析/自动微分
    void computeStiffness(const Vector3 x[8], Matrix3 K[8][8]) {
        const double eps = 1e-6;
        Vector3 f0[8], f1[8], xp[8]; double e;
        computeForces(x, f0, e);
        for (int j = 0; j < 8; j++)
            for (int d = 0; d < 3; d++) {
                memcpy(xp, x, sizeof(xp));
                xp[j][d] += eps;
                computeForces(xp, f1, e);
                for (int i = 0; i < 8; i++)
                    K[i][j].col(d) = (f1[i] - f0[i]) / eps;
            }
    }
};
```

### 2.4 代码:Newton 迭代 + 隐式(Backward Euler)时间积分

```cpp
// 全局求解:组装所有单元内力 -> 求解 K Δx = -f -> 更新
// 隐式积分(Backward Euler)把"惯性 + 刚度"并成一个系统
struct FEMSolver {
    // nodes: 所有网格节点当前 x, 速度 v, 质量 m(集中质量 = lumped mass)
    std::vector<Vector3> x, v, f;
    std::vector<double> m;

    // 组装全局刚度 + 质量,做一次 Newton 步
    // (M + h^2 K) Δv = h (f_ext + M v ...)   -- 略去外力细节
    void implicitStep(double h) {
        // 1. 组装内力 f 和切线刚度 K(遍历所有单元累加)
        // 2. 构建系统 A = M + h^2 * K
        // 3. 迭代 Newton:解 A * dx = -(f + M*(x - x_pred)/h ... )
        // 4. 更新 x, v
    }
};
```

**Newton 迭代伪代码**(准静态,即忽略惯性、直接解平衡方程):

```
x = rest 位置(或被骨骼刚体驱动后的初猜)
repeat:
    组装内力 f(x) 和切线刚度 K(x)
    残差 r = -f(x)            # 平衡时合力为零
    if |r| < tol: break
    解线性系统  K * dx = r    # ← 用多重网格加速
    x += dx                   # 线搜索(line search)可选
```

**关键:多重网格(Multigrid)**。直接解几十万自由度的稀疏系统太慢,论文用**几何/代数多重网格**把低频误差在粗网格上消除、高频误差在细网格上平滑,使求解器接近线性收敛。

### 2.5 Zootopia 的肌肉/脂肪/筋膜分级

- **肌肉** = 各向异性(带纤维方向)弹性体:纤维方向受力时膨胀/收缩特性不同;
- **脂肪/筋膜** = 更软、更滑的层,负责皮肉之间的滑动与褶皱;
- 流程:**骨骼刚体 → 驱动肌肉仿真 → 驱动脂肪/筋膜 → 驱动皮肤**,逐级传递。

---

## 三、战神:关节蒙皮 + 动态骨骼(RBF)

### 3.1 原理

> ⚠️ 诚实说明:GDC 2023 演讲**未公开 slide 级实现细节**,以下实现是基于演讲透露的两点(①沿肌肉纤维方向布置关节、保体积;②动态骨骼近似 jiggle)结合业界成熟先例(PSD/RBF、spring/Verlet bone)的**重建**。

战神方案本质仍是**蒙皮(LBS)** 的增强,分两层:

1. **关节近似(姿势驱动)**:在肌肉纤维走向上布置"辅助关节(helper joints)",这些关节的位姿由主骨骼旋转通过 **RBF 插值** 驱动,从而在蒙皮时把肌肉隆起、体积保持"做出来"。
2. **动态骨骼(物理近似)**:再加一层 **spring/Verlet 抖动** 系统,近似肌肉、脂肪、皮肤的惯性晃动(jiggle),增强打击感。

### 3.2 理论基础:Pose Space Deformation(PSD)

PSD(Lewis, Cordner, Fong 2000)是所有"姿势驱动修正"的鼻祖:**对每个顶点**,用一组雕刻好的目标姿势,通过 RBF 插值出当前姿势下的位移修正。

**Maya 里叫 Pose Deformer,Blender 里叫 Corrective Shape Keys,就是同一套思想。**

### 3.3 代码:RBF 驱动辅助关节

```cpp
#include <vector>
#include <cmath>

// 径向基函数可选核
inline double rbfKernel(double r, double radius) {
    // 高斯核(平滑、局部);也可用 thin-plate r^2*ln r(全局)、multiquadric 等
    return std::exp(-(r * r) / (radius * radius));
}

// 姿势空间 = 主关节的若干角度(可为多维)
struct Pose { std::vector<double> angles; };

// 对"一个辅助关节的单个通道(如旋转移位量)"做 RBF 插值
struct RBFChannel {
    std::vector<Pose>   poses;   // N 个训练姿势
    std::vector<double> weights; // N 个权重(训练时解出)
    double radius = 1.0;

    // 训练:解 Φ w = d,其中 Φ_ij = φ(||p_i - p_j||), d_i = 该姿势的雕刻目标值
    void train(const std::vector<double>& targetValues) {
        int N = poses.size();
        // 组装 Φ 矩阵 + 解线性系统(高斯消元 / LU / 正则化)
        // 可加多项式项消除常数漂移,此处略
        weights = solveLinearSystem(buildPhi(), targetValues);
    }

    // 运行时求值:当前姿势 p 下的修正量
    double eval(const Pose& p) const {
        double s = 0.0;
        for (int k = 0; k < (int)poses.size(); k++)
            s += weights[k] * rbfKernel(distance(p, poses[k]), radius);
        return s;
    }
};

// 用法:对每个辅助关节的每个自由度(旋转/平移分量)维护一个 RBFChannel,
// 输入"主关节角度向量",输出该辅助关节的额外变换,叠加到蒙皮前的关节位姿上。
```

**训练数据来源**:在 DCC 里摆主关节到若干代表性姿势 → 手工把辅助关节雕到"肌肉隆起正确、体积保持"的位置 → 记录偏移量作为 RBF 目标。运行时任何中间姿势都被光滑插值出来。

> 这就是"系统性关节绑定"的核心:不是逐帧雕,而是**让关节沿肌肉纤维方向、按姿势自动摆位**。

### 3.4 代码:线性混合蒙皮(LBS)

```cpp
// 标准 LBS:顶点 = Σ 权重 * 骨骼变换 * 绑定姿态逆变换 * 顶点
// 战神的辅助关节作为普通关节参与 LBS,权重刷在肌肉纤维对应的区域
Vector3 skinVertex(const Vector3& vBind,
                   const std::vector<Matrix4>& jointTransforms, // 世界矩阵
                   const std::vector<Matrix4>& bindInverse,
                   const std::vector<float>& weights) {
    Vector3 result(0, 0, 0);
    for (int j = 0; j < (int)weights.size(); j++) {
        if (weights[j] <= 0) continue;
        Matrix4 M = jointTransforms[j] * bindInverse[j];
        result += weights[j] * (M * vBind);
    }
    return result;
}
// 在 GPU 上就是常见的 skinning vertex shader,把 joint index/weight 传进去即可。
```

**体积保持**不是靠公式,而是靠**关节布局**:辅助关节沿纤维方向"顶"出肌肉,权重的分布保证膨胀时体积感不塌陷。这跟 FEM 用方程严格保体积是本质区别。

### 3.5 代码:动态骨骼(Verlet + 距离约束)

```cpp
// 动态骨骼:一条链上的粒子,用 Verlet 积分 + 距离约束做 jiggle
struct VerletBone {
    Vector3 pos, prev;   // 当前/上一帧位置(速度隐含在 pos-prev 里)
    float   restLength;  // 到父节点的静息长度
    float   stiffness;   // 0~1,越接近 1 越硬
    int     parent;      // 父节点索引(-1 表示绑定到动画骨骼)
};

struct JiggleChain {
    std::vector<VerletBone> bones;

    void simulate(float dt) {
        // 1. Verlet 积分
        for (auto& b : bones) {
            Vector3 vel = (b.pos - b.prev) * damping;   // damping 0~1
            b.prev = b.pos;
            b.pos += vel + gravity * dt * dt;           // 惯性 + 重力
        }
        // 2. 迭代约束(保持链连接、限制拉伸)
        for (int iter = 0; iter < 4; iter++)
            for (auto& b : bones) {
                if (b.parent < 0) continue;
                Vector3& parentPos = bones[b.parent].pos;
                Vector3  delta = b.pos - parentPos;
                float    len   = delta.length();
                float    diff  = (len - b.restLength) / len;
                b.pos -= delta * 0.5f * diff * stiffness;   // 各拉一半
                parentPos += delta * 0.5f * diff * stiffness;
            }
        // 3. 把粒子位置写回骨骼旋转(末端指向),供 LBS 使用
    }
};
```

**要点**
- 动态骨骼是**叠加在动画之上**的次级运动:主骨骼动 → 惯性让子骨骼滞后、过冲、再回摆;
- 用 `damping`、`stiffness`、`gravity` 调手感:硬=干脆,软=肉感;
- 游戏里常见的"乳摇/臀摇/尾巴/头发摆动"都是同一套 Verlet/spring 逻辑。

---

## 四、两张图理解差异

```
迪士尼 FEM:
  骨骼(刚体) ──驱动──► 肌肉FEM ──► 脂肪/筋膜 ──► 皮肤FEM
        (物理精确, 离线超算求解, 保体积/无穿插)

战神 关节+RBF:
  主骨骼旋转 ──RBF插值──► 辅助关节(沿纤维方向) ──LBS──► 蒙皮顶点
                                                └──动态骨骼Verlet──► jiggle
        (实时, 近似"肌肉感", 不求解物理方程)
```

---

## 五、GPU 端实时蒙皮 Shader(HLSL)

战神方案里,RBF 驱动的辅助关节、动态骨骼,最终都收敛成**一个关节矩阵数组**喂给 GPU。所以 GPU 端和普通蒙皮完全一样——区别只在"关节矩阵是怎么算出来的"。

```hlsl
// ============ 顶点着色器蒙皮(关节矩阵已由 CPU/Compute 组装好) ============
cbuffer SkinningConstants : register(b0)
{
    float4x4 g_JointMatrices[256];  // 每块 = world * bindInverse(主关节+辅助关节+jiggle 关节统一编号)
};

cbuffer CameraConstants : register(b1)
{
    float4x4 g_ViewProj;
};

struct VSInput
{
    float3 position : POSITION;
    float3 normal   : NORMAL;
    float4 weights  : BLENDWEIGHTS;   // 4 个关节权重
    uint4  joints   : BLENDINDICES;   // 4 个关节索引
};

struct VSOutput
{
    float4 position : SV_POSITION;
    float3 normal   : NORMAL;
    float3 worldPos : TEXCOORD0;
};

VSOutput main(VSInput input)
{
    // 1. 累加加权关节矩阵
    float4x4 skin =
        g_JointMatrices[input.joints.x] * input.weights.x +
        g_JointMatrices[input.joints.y] * input.weights.y +
        g_JointMatrices[input.joints.z] * input.weights.z +
        g_JointMatrices[input.joints.w] * input.weights.w;

    // 2. 归一化(权重通常已归一,这里是防御性处理)
    float wsum = dot(input.weights, 1.0);
    skin /= max(wsum, 1e-4);

    // 3. 顶点与法线变换
    float4 pos = mul(skin, float4(input.position, 1.0));
    float3x3 skin3 = (float3x3)skin;          // 取 3x3 旋转部分
    float3 nrm = mul(skin3, input.normal);     // 简化;严格应乘逆转置

    VSOutput o;
    o.position = mul(g_ViewProj, pos);
    o.normal   = normalize(nrm);
    o.worldPos = pos.xyz;
    return o;
}
```

> **LBS 的体积塌陷问题**:上面对关节附近做线性混合会在强烈旋转时出现"糖果纸"(candy-wrapper)收缩——这正是要**保体积**的痛点。战神用"沿纤维方向多插关节"缓解;更彻底的实时做法是 **双四元数蒙皮(Dual Quaternion Skinning, DQS)**。

```hlsl
// ============ DQS 双四元数蒙皮(保体积优于 LBS) ============
// 每个关节存一个对偶四元数:(实部四元数 q, 对偶部四元数 dq)
// 可把 g_JointMatrices 预转换成 DQ 数组上传,或在 shader 内转换
float4 qadd(float4 a, float4 b) { return a + b; }

VSOutput mainDQS(VSInput input)
{
    // 对 4 个影响关节的双四元数做加权混合(注意:若点积为负要取反,保证走最短弧)
    float4 bq = g_DQ[input.joints.x]; float4 bdq = g_DQTrans[input.joints.x];
    float4 q  = bq * input.weights.x;
    float4 dq = bdq * input.weights.x;
    for (int k = 1; k < 4; k++) {
        float w = input.weights[k];
        if (w <= 0) continue;
        float4 tq = g_DQ[input.joints[k]];
        if (dot(bq, tq) < 0) { tq = -tq; g_DQTrans[input.joints[k]] *= -1; }
        q  += tq * w;
        dq += g_DQTrans[input.joints[k]] * w;
    }
    // 归一化实部
    float n = length(q); q /= n; dq /= n;
    // 双四元数 -> 旋转 + 平移,变换顶点
    float3 p = input.position;
    float3 t = 2.0 * (q.w * dq.xyz - dq.w * q.xyz + cross(q.xyz, dq.xyz));
    float3 r = p + 2.0 * cross(q.xyz, cross(q.xyz, p) + q.w * p) + t;
    VSOutput o;
    o.position = mul(g_ViewProj, float4(r, 1.0));
    return o;
}
```

> DQS 把 LBS 的"矩阵线性混合"换成"刚体变换的流形混合",旋转处不再塌陷。代价是多了几行计算、且不支持 LBS 的缩放/剪切变形,但对手臂、躯干这类**纯刚性旋转**的部位是标准升级。

---

## 六、实时游戏里的混合实践:动态骨骼如何接进 LBS 管线

把三、五两节串起来,战神式的完整每帧流程是:

```
动画采样 ──► 主关节 world 矩阵
                 │
     ┌───────────┼───────────────┐
     ▼           ▼               ▼
  RBF 插值   动态骨骼 Verlet     (可选)肌肉辅助关节
  辅助关节      计算抖动方向       沿纤维方向摆位
     └───────────┼───────────────┘
                 ▼
     组装 skinningMatrices[i] = world_i * bindInverse_i
                 ▼
     上传 GPU → LBS 或 DQS 蒙皮
```

### 6.1 CPU 侧每帧组装

```cpp
// 每帧:动画 -> RBF 辅助关节 -> Verlet 抖动 -> 拼矩阵 -> 上传
void updateSkinningMatrices(Character& c, float dt) {
    // 1. 主关节:采样动画,算 world 矩阵
    evaluateAnimation(c);

    // 2. RBF 辅助关节:由主关节姿势插值出额外偏移
    Pose p = poseFromMainJoints(c);
    for (auto& helper : c.helperJoints)
        helper.offset = helper.rbf.eval(p);        // 见 3.3 的 RBFChannel

    // 3. 动态骨骼:Verlet 模拟出每个抖动骨骼的当前方向
    c.jiggle.simulate(dt);                          // 见 3.5 的 JiggleChain

    // 4. 组装矩阵:主/辅助关节 world + jiggle 旋转 统一拼进同一数组
    for (int i = 0; i < c.jointCount; i++) {
        Matrix4 world = c.joints[i].world;          // 主关节或辅助关节
        if (c.joints[i].isJiggle)
            world = world * jiggleRotation(c.jiggle, i);   // 叠加抖动
        c.skinningMatrices[i] = world * c.joints[i].bindInverse;
    }
    uploadToGPU(c.skinningMatrices);                 // → g_JointMatrices
}
```

### 6.2 抖动骨骼如何"转成旋转"

Verlet 得到的是粒子**位置**,而蒙皮需要的是**旋转矩阵**。做法:每个抖动骨骼记一个 rest 方向(绑定姿态下子关节相对父关节的朝向),每帧用当前粒子方向与 rest 方向求旋转:

```cpp
// 从"父->子"两个方向向量,求把 restDir 转到 curDir 的最小旋转
Matrix3 jiggleRotation(const JiggleChain& j, int i) {
    Vector3 curDir  = (j.bones[i].pos - j.bones[j.bones[i].parent].pos).normalized();
    Vector3 restDir = j.bones[i].restDir;
    Vector3 axis = cross(restDir, curDir);
    float   s    = axis.length();
    float   c    = dot(restDir, curDir);
    if (s < 1e-6f) return Matrix3::Identity();       // 同向或反向,特殊处理
    axis /= s;
    // Rodrigues 公式: R = I + sinθ·[axis]× + (1-cosθ)·[axis]×²
    return Matrix3::rotation(axis, atan2f(s, c));
}
```

### 6.3 关键取舍(游戏工程视角)

- **抖动骨骼不进物理引擎**,只做"程序化次级运动",因此便宜、可控、可无限调手感(`stiffness/damping/gravity`)。
- **动态骨骼数量要克制**:它每帧要做 Verlet + 约束迭代,角色身上放几十根即可,多了反而吃掉 CPU 预算;远处可 LOD 掉(不模拟)。
- **RBF 辅助关节是"离线训练、运行时零成本"**:权重在 DCC 里一次性解好,运行时只是几次乘加,非常适合主机实时。
- **和 FEM 的分界**:
  - 需要**电影级真实**、能接受离线算力 → 走迪士尼 FEM(第二节);
  - 需要**60fps 实时**、要的是"手感/打击感"而非物理精确 → 走战神关节 + 动态骨骼(第三、五、六节)。

---

## 七、参考文献

- **FEM 蒙皮**
  - McAdams, Zhu, Selle, Empey, Tamstorf, Teran, Sifakis. *Efficient Elasticity for Character Skinning with Contact and Collisions*. SIGGRAPH 2011. [Disney 页](https://disneyanimation.com/publications/efficient-elasticity-for-character-skinning-with-contact-and-collisions/)
  - Milne et al. *Flesh, flab, and fascia simulation on Zootopia*. SIGGRAPH 2016 Talks. [DOI](https://dl.acm.org/doi/10.1145/2897839.2927390)
  - US 9,135,738 B2 — *Efficient Elasticity for Character Skinning*.
- **Pose Space Deformation / RBF**
  - Lewis, Cordner, Fong. *Pose Space Deformation: A Unified Approach to Shape Interpolation and Skeleton-Driven Deformation*. SIGGRAPH 2000. [PDF](http://www.disneyanimation.com/library/poseSpaceDef.pdf)
  - Lee, Hanner. *Practical Experiences with Pose Space Deformation*. SIGGRAPH Asia 2009.
- **关节蒙皮(战神)**
  - 80.lv 报道: [Joint-Based Skin Deformation in Ragnarök Will Be Explained at GDC 2023](https://80.lv/articles/joint-based-skin-deformation-in-god-of-war-ragnar-k-will-be-explained-at-gdc-2023)

---

## 附:一句话记忆

> **迪士尼 = 把身体当连续介质来"算";战神 = 沿肌肉多插几根关节、再加个 Verlet 抖动来"装"。**
> 前者精确昂贵(电影),后者实时廉价(游戏),殊途同归地模拟了同一件事——肌肉有纤维方向、形变要保体积、皮肉会滑动。
