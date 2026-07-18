---
日期: 2026-07-14T12:00:00
tags:
---
## 一、 涉及到的效果

本 Shader 主要用于实现基础的**加法发光贴图**、**地面法阵**或**简单的全息投影**，具有以下视觉特征：

- **加法发光混合**：使用 Blend SrcAlpha One 混合模式，贴图上越亮的地方叠加在背景上越耀眼，纯黑的地方完全透明。

- **自上而下的平面投影**：不依赖模型本身美术做好的 UV 展开，而是直接从物体的正上方（Y轴）往下投射贴图，非常适合做地表的魔法阵或扫描底座。

- **双面显示**：支持通过面板自由切换剔除模式（单双面显示）。

---
## 二、 核心数学原理

1. MVP 矩阵转换

代码的顶点着色器中保留了很长一段被注释掉的代码，这展示了图形学中最著名的**MVP矩阵变换**全过程：

- **第一步 (Model)**：将顶点从模型本地转换到世界空间 `mul(unity_ObjectToWorld, v.vertex)`

- **第二步 (View)**：将世界坐标转换到摄像机的观察空间 `mul(UNITY_MATRIX_V, pos_world)`。

- **第三步 (Projection)**：将观察空间坐标投影到屏幕的裁剪空间 `mul(UNITY_MATRIX_P, pos_view)`。

在较新的 Unity 版本中，直接被封装成了一个性能更高的 API：`UnityObjectToClipPos(v.vertex)`。


2. 向量的自由重组 (Swizzle 操作)    

- **原理**：在 Shader 语言（HLSL/CG）中，一个包含 4 个小数的向量（如 `float4`）可以通过 `.xyzw` 或 `.rgba` 来访问。更强大的是，你可以随意改变它们的顺序组合。

- **代码体现**：代码中提取颜色的写法是 `_MainColor.xwz`。这在数学上等同于把原本的 $(X, Y, Z)$ 变成了 $(X, W, Z)$，也就是提取了原颜色的**红、透明度、蓝**组合成了新的颜色。

---
## 三、 逻辑架构

#### 1. 属性面板 (Properties)

这部分定义了暴露在 Unity 材质面板上的参数：

- `_MainTex`：主贴图。
    
- `_MainColor`：主颜色。
    
- `_Emiss`：发光强度（控制颜色和透明度的倍率）。
    
- `_CullMode`：这是一个带枚举的属性，允许你在材质面板直接下拉选择剔除模式（0=Off 双面, 1=Front 剔除正面, 2=Back 剔除背面，默认是 2）。
    

#### 2. 渲染状态设置 (SubShader & Pass)

这一块决定了物体如何与背景进行混合：

- `Tags { "Queue"="Transparent" }`：将渲染队列设为透明队列。这保证了该物体会在所有不透明物体渲染完之后再渲染，防止遮挡关系出错。
    
- `ZWrite Off`：**关闭深度写入**。这是透明半透明特效的标配，确保当前半透明特效不会用自己的深度信息去遮挡后面的其他半透明物体。
    
- `Blend SrcAlpha One`：**加法混合模式（Additive Blending）**。
    
    - **公式**：`最终颜色 = (当前Shader输出颜色 * 当前Alpha) + (屏幕已有颜色 * 1)`
    
    - **效果**：这种混合方式会让物体叠加在背景上发光。背景越亮，叠加后越亮；如果是纯黑（0,0,0），则完全透明。非常适合做火焰、激光、魔法光效。
- `Cull [_CullMode]`：根据面板选择应用多边形剔除。

#### 3. 顶点着色器 (Vertex Shader)

这是该 Shader 最有趣的部分，它没有使用模型自带的 UV，而是自己算了一套：

- `o.pos = UnityObjectToClipPos(v.vertex);`：常规操作，将顶点从模型空间转换到裁剪空间（屏幕显示所需）。
    
- `float2 xz_uv = v.vertex.xy;`：**特殊操作！** 它抓取了模型顶点的本地坐标的 X 和 Y 轴数值，强行当做 UV 的基础值。这相当于做了一个**基于 Z 轴方向的平面投影（Planar Mapping）**。
    
- `o.uv = xz_uv * _MainTex_ST.xy + _MainTex_ST.zw;`：应用面板上的 Tiling 和 Offset（平铺和偏移）。
    
- `o.pos_uv = v.vertex.xz;`：计算了基于 XZ 轴的坐标，但这在片段着色器中**并没有被使用**，属于冗余代码。
    

### 4. 片段着色器 (Fragment Shader)

这里决定了最终输出到屏幕的颜色和透明度：

- `half3 col = _MainColor.xwz * _Emiss;`：
    
    - 注意这里的 `.xwz` 是一种分量重组（Swizzle）操作。它将面板颜色的 Red 作为 R，**Alpha 作为 G**，Blue 作为 B。这是一个比较不寻常的写法，意味着你在面板调节颜色的 Alpha 通道时，实际上是在改变它输出颜色的绿色（Green）分量。
        
    - 然后乘以 `_Emiss` 放大发光亮度。
        
- `half alpha = saturate(tex2D(_MainTex,i.uv).r * _MainColor.a * _Emiss);`：
    
    - 它只采样了贴图的 **红色通道（.r）** 作为形状遮罩。
        
    - 同样乘以了颜色的 Alpha 和发光倍率，最后用 `saturate` 将结果截取在 0 到 1 之间，防止 Alpha 爆表。
        
- `return float4(col,alpha);`：将颜色和透明度打包输出，交给之前的 `Blend SrcAlpha One` 进行加法混合。