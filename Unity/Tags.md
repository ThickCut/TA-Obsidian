---
tags:
  - Unity
  - ShaderLab
  - URP
  - Graphics
aliases:
  - Shader Tags 总结
  - SubShader 标签说明
date: 2026-07-21
---

# 📝 Unity ShaderLab: SubShader Tags 核心标签解析

> [!info] 什么是 SubShader Tags？
> 在 Unity ShaderLab 中，`Tags` 写在 `SubShader` 内部。它们相当于材质的**“身份证”与“配置表”**，负责向 Unity 渲染引擎声明该 Shader 的适用环境、渲染顺序以及物体分类，从而让引擎能够采用正确的策略进行绘制。

---

## 1. 渲染类型：RenderType
**代码示例**：`"RenderType" = "Opaque"`

* **核心作用**：**材质分类与着色器替换 (Shader Replacement)**。
* **详细说明**：
  * 将材质按照其透明属性进行归类（如 `Opaque` 代表不透明，`Transparent` 代表半透明）。
  * 当引擎需要执行特定的全局特效时（例如生成全局深度图、SSAO 屏幕空间环境光遮蔽），摄像机会寻找对应 `RenderType` 的物体，并临时用内置的深度 Shader 替换当前 Shader 进行统一渲染。
* **常见取值**：`Opaque` (不透明)、`Transparent` (半透明)、`TransparentCutout` (镂空/裁剪)。

---

## 2. 渲染管线：RenderPipeline
**代码示例**：`"RenderPipeline" = "UniversalPipeline"`

* **核心作用**：**指定兼容的渲染管线环境**。
* **详细说明**：
  * 明确告知 Unity，当前的 SubShader 是专门为 **URP（通用渲染管线）** 编写的。
  * 如果项目处于 Built-in（内置管线）或 HDRP（高清管线）下，引擎在解析时发现管线不匹配，就会直接跳过这段代码，去寻找其他的 SubShader 或 FallBack，从而避免报错崩溃。

---

## 3. 渲染队列：Queue
**代码示例**：`"Queue" = "Geometry"`

* **核心作用**：**控制物体在屏幕上的绘制先后顺序 (Render Order)**。
* **详细说明**：
  * 引擎通过数字对物体进行排队，数字越小越先画，数字越大越后画。
  * `"Geometry"` 对应底层数值 **2000**，是所有不透明物体的默认队列。
  * 放在此队列的物体，Unity 会利用深度缓冲 (Z-Buffer) 从前往后渲染，能有效剔除被遮挡的像素，优化性能。
* **常用队列阶梯**：
  * `Background` (1000)：最底层背景（如天空盒）。
  * `Geometry` (2000)：不透明实体（如石头、墙壁）。
  * `AlphaTest` (2450)：镂空测试物体（如草、铁丝网）。
  * `Transparent` (3000)：半透明物体（如玻璃、水）。
  * `Overlay` (4000)：屏幕最上层（如 UI、镜头光晕）。

---

> [!tip] 综合理解
> 当把这三个标签写在一起时，就相当于给引擎下达了明确的指令：**“请在 URP 环境下 (`UniversalPipeline`)，把这个物体当作纯正的不透明模型 (`Opaque`)，放进标准实体队列 (`Geometry = 2000`) 里进行最高效的渲染。”**