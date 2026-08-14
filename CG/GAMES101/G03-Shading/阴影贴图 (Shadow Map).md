## 一、 核心原理与基础概念

### 1. 两通渲染 (Two-Pass Rendering) 流程

阴影贴图的核心思想是通过两次渲染来实现物体间的遮挡关系：

* **Pass 1: 阴影映射生成 (Shadow Pass)**
* **视角**：以光源（Light）的位置和方向作为摄像机视角进行渲染。
* **输出**：不计算复杂的光照和颜色，只将每个片元到光源的距离（深度值）写入一张深度纹理中，即 **Shadow Map**。
* **数学表示**：深度通常存储在非线性或线性的深度空间中（$Z_{light}$）。


* **Pass 2: 场景正式渲染 (Color Pass)**
* **视角**：从主摄像机（Camera）视角正常渲染场景。
* **可见性判定**：在片元着色器中，将当前片元转换到光源空间，采样 Shadow Map 得到该视线方向上最近的遮挡深度 $Z_{shadowmap}$，并与当前片元实际到光源的距离 $Z_{light}$ 进行比较。
* **判定逻辑**：

$$Z_{light} > Z_{shadowmap} + \text{Bias}$$


* 若成立，说明该点被其他物体遮挡，处于**阴影中**。
* 若不成立，说明该点直接被光源照射，处于**光照中**。


---

## 二、 核心痛点与数学根基 (三大走样与误差)

在实际开发中，由于浮点数精度限制和离散像素采样，Shadow Map 会面临三大经典问题：

### 1. 走样与精度问题 (Aliasing)

* **透视走样 (Perspective Aliasing)**：
* *成因*：近处摄像机像素密集，远处稀疏。Shadow Map 的像素网格是均匀分布在光源视锥体内的，投射到近处的像素时会发生“一个像素覆盖多个屏幕像素”，而投射到远处时则相反。
* *后果*：近处的阴影边缘颗粒感重、锯齿明显。


* **投影走样 (Projection Aliasing)**：
* *成因*：当光源照射角度非常低（掠射角，Grazing Angle）时，Shadow Map 上的一个像素在受光面上会被极度拉伸。
* *后果*：阴影边缘出现严重的锯齿和条纹形变。



### 2. 阴影失真与自阴影错误 (Shadow Acne / Shadow "Pinking")

* **成因**：由于 Shadow Map 分辨率有限，相邻像素存储的深度是离散的。当片元在进行深度比较时，其计算出的 $Z_{light}$ 会因为浮点数精度误差或网格微小起伏，导致部分采样的深度小于、部分大于存储的深度，产生明暗相间的条纹（类似斑马纹）。
* **解决方案**：引入**深度偏移 (Depth Bias)**。
* **Constant Bias（常数偏移）**：直接在比较时给 $Z_{light}$ 加上一个固定微小值。缺点是容易引发漏光。
* **Slope-Scaled Bias（斜率缩放偏移）**：根据表面法线与光线方向的夹角动态调整偏移量。夹角越平缓，偏移量越大，能有效缓解掠射角下的失真。


### 3. 悬浮与漏光 (Peter Panning / Light Leaking)

* **Peter Panning (悬浮)**：
* *成因*：Bias 设置得过大，导致阴影与物体本身的接触面脱离，产生物体悬浮在空中的错觉。


* **Light Leaking (漏光)**：
* *成因*：Bias 过大导致原本应该在阴影里的片元穿透到了光照区域，或者由于 Shadow Map 分辨率不足，细小的遮挡物被像素化遗漏，导致光线穿透物体。
* *调优策略*：TA 需要在 **Shadow Acne** 与 **Peter Panning** 之间不断权衡，寻找最优的 Bias 数值。


---

## 三、 高级采样与软阴影技术

硬阴影（Hard Shadow）边缘过渡生硬、缺乏真实感，现代渲染管线广泛使用软阴影技术：

### 1. PCF (Percentage-Closest Filtering)

* **核心思想**：不在 Shadow Map 中只进行单点采样，而是在目标片元对应的纹理坐标周围进行一个区域采样（如 $3\times3$ 或 $5\times5$ 滤波核）。
* **原理**：统计周围多个采样点中有多少比例处于阴影中，将最终的遮挡结果进行平均（0 到 1 之间的连续值），从而让阴影边缘产生柔和的阶梯过渡（抗锯齿）。
* **硬件支持**：现代图形 API 支持比较采样器（Comparison Sampler），可直接在硬件层面执行“深度比较 + 双线性过滤”，大幅提升 PCF 性能。

### 2. PCSS (Percentage-Closest Soft Shadows)

* **核心思想**：模拟真实物理世界中“光源有体积，阴影随遮挡物距离摄像机/接受面距离变远而变模糊”的特性。
* **实现三步法**：
1. **Blocker Search (遮挡物搜索)**：在 Shadow Map 的一个固定区域内采样，计算所有比当前片元更近的遮挡物的平均深度。
2. **Penumbra Estimation (半影计算)**：根据光源大小、遮挡物距离、接收面距离之间的相似三角形原理，动态计算出当前片元对应的滤波半径（Filter Size）。遮挡物距离接收面越远，半影越大，阴影越软。
3. **Variable-Radius PCF (可变半径滤波)**：使用第二步计算出的动态半径进行 PCF 采样。


### 3. 高级阴影贴图变体

* **VSM (Variance Shadow Maps)**：利用概率论中的切比雪夫不等式，将深度比较转换为均值和方差的估计。允许对 Shadow Map 进行标准的 Mipmapping 和双线性过滤。
* **ESM / MSM**：通过指数函数或矩估计变换深度，减少 VSM 容易产生的漏光（Light Leaking）Artifacts。

---

## 四、 大场景与复杂环境优化策略

面对开放世界（Open World）或多光源场景时，单张 Shadow Map 无法兼顾远景与近景的精度。

### 1. CSM (Cascaded Shadow Maps / 级联阴影贴图)

* **核心痛点**：摄像机视锥体范围很大，若用一张图覆盖，近处精度极度浪费，远处精度严重不足。
* **核心机制**：
* 将摄像机视锥体沿视线方向切分为多个区段（如近、中、远 3 到 4 个 Cascades）。
* 每个区段分配独立且分辨率适配的 Shadow Map。
* 近处使用小视锥体（高精度），远处使用大视锥体（低精度）。


* **TA 职责与调优**：
* **Cascade Split Scheme（级联划分策略）**：调整切分点的位置（通常结合 Lambda 参数平衡线性切分与对数切分）。
* **Cascade Blending（级联过渡）**：处理不同级联交界处的突变和抖动（Flickering），在边缘处进行混合过渡。



### 2. 裁剪与剔除 (Culling & LOD)

* **Shadow Culling**：不在视锥体内的物体、背对光源的物体无需渲染到 Shadow Map 中。
* **Shadow LOD**：对于远处的级联区域，使用面数更少、顶点更简单的网格模型（Shadow LOD）参与深度写入，降低顶点光栅化压力。

### 3. 全向光源与点光源阴影

* **Cubemap Shadows**：点光源向四周发光，需要渲染 6 个方向的面构成立方体贴图，开销是平行光的 6 倍。
* **Dual Paraboloid Shadow Maps**：使用两个抛物面代替 6 个面，减少 Pass 数量。

---

## 五、 现代图形 API 与引擎落地实践

### 1. 图形底层接口

* **纹理格式**：常采用 `D24S8`（24位深度，8位模板）或 `R32F`。
* **Sampler 状态**：必须开启硬件比较模式（Comparison Mode），利用 GPU 的硬件单元直接输出 0 或 1 的比较结果。

### 2. Unity 引擎实践 (URP / HDRP)

* **配置参数**：在 Renderer Data 中调整 `Shadow Distance`（最大阴影距离）、`Cascades Count`（级联层数，通常设为 2 或 4）、`Shadow Resolution`。
* **HLSL 编写**：
* 使用核心库函数（如 URP 的 `GetShadowCoord` 和 `MainLightRealtimeShadow`）获取阴影衰减值。
* 通过自定义 Shader 采样 Shadow Map 时，需正确应用空间变换矩阵（`TransformWorldToShadowCoord`）。



### 3. Unreal Engine 5 实践

* **VSM (Virtual Shadow Maps)**：
* UE5 的核心次时代阴影方案，将 Shadow Map 分割为巨型的虚拟化纹理（类似 VT 技术）。
* 按需加载高精度瓦片（Tiles），彻底解决传统 CSM 在大场景下的精度不均和级联过渡问题，支持极高精度的几何体阴影。