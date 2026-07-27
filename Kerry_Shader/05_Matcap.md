---
tags:
  - Shader
  - Unity
  - Matcap
  - Ramp
  - NPR
title: Shader解析：Matcap基础与Ramp边缘光渐变
---
## 0. 源码参考 (ShaderPrime/07_Matcap)

> [!note]- 点击展开/折叠 Shader 源码
> ```c
> Shader "ShaderPrime/07_Matcap"
> {
> 	Properties
> 	{
> 		_MainTex ("Texture", 2D) = "white" {}
> 		_Matcap("Matcap",2D) = "white"{}
> 		_MatcapIntensity("Matcap Intensity",Float) = 1.0
> 		_RampTex("Ramp Tex",2D ) = "white"{}
> 		_MatcapAdd("MatcapAdd",2D ) = "white"{}
> 		_MatcapAddIntensity("MatcapAdd Intensity",Float) = 1.0
> 	}
> 	SubShader
> 	{
> 		Tags { "RenderType"="Opaque" }
> 		LOD 100
> 
> 		Pass
> 		{
> 			CGPROGRAM
> 			#pragma vertex vert
> 			#pragma fragment frag
> 			
> 			#include "UnityCG.cginc"
> 
> 			struct appdata
> 			{
> 				float4 vertex : POSITION;
> 				float2 uv : TEXCOORD0;
> 				float3 normal :NORMAL;
> 
> 			};
> 
> 			struct v2f
> 			{
> 				float4 vertex : SV_POSITION;
> 				float2 uv : TEXCOORD0;
> 				float3 normal_world : TEXCOORD1;
> 				float3 pos_world : TEXCOORD2;
> 			};
> 
> 			sampler2D _MainTex;
> 			float4 _MainTex_ST;
> 			sampler2D _Matcap;
> 			float _MatcapIntensity;
> 			sampler2D _RampTex;
> 			sampler2D _MatcapAdd;
> 			float _MatcapAddIntensity;
> 			
> 			v2f vert (appdata v)
> 			{
> 				v2f o;
> 				o.vertex = UnityObjectToClipPos(v.vertex);
> 				o.uv = TRANSFORM_TEX(v.uv, _MainTex);
> 				float3 normal_world = mul(float4(v.normal, 0.0), unity_WorldToObject);
> 				o.normal_world = normal_world;
> 				o.pos_world = mul(unity_ObjectToWorld, v.vertex).xyz;
> 				return o;
> 			}
> 			
> 			fixed4 frag (v2f i) : SV_Target
> 			{
> 				half3 normal_world = normalize(i.normal_world);
> 				
> 				//base matcap
> 				half3 normal_viewspace = mul(UNITY_MATRIX_V, float4(normal_world, 0.0)).xyz;
> 				half2 uv_matcap = (normal_viewspace.xy + float2(1.0, 1.0)) * 0.5;
> 				half4 matcap_color = tex2D(_Matcap, uv_matcap) * _MatcapIntensity;
> 				half4 diffuse_color = tex2D(_MainTex, i.uv);
> 
> 				//Ramp
> 				half3 view_dir = normalize(_WorldSpaceCameraPos.xyz - i.pos_world);
> 				half NdotV = saturate(dot(normal_world, view_dir));
> 				half fresnel = 1.0 - NdotV;
> 				half2 uv_ramp = half2(fresnel, 0.5);
> 				half4 ramp_color = tex2D(_RampTex, uv_ramp);
> 
> 				//add matcap
> 				half4 matcap_add_color = tex2D(_MatcapAdd, uv_matcap) * _MatcapAddIntensity;
> 
> 				half4 combined_color = diffuse_color * matcap_color * ramp_color + matcap_add_color;
> 				return combined_color;
> 			}
> 			ENDCG
> 		}
> 	}
> }
> ```

---

## 1. 具体实现的流程

此 Shader 未参与真实的实时光照计算（如基于物理的漫反射、高光等），而是完全通过数学映射和纹理采样“伪造”光影。

*   **顶点阶段 (Vertex Shader)**：
    *   获取模型的基础数据（顶点位置、UV、法线）。
    *   将顶点从模型空间转换到裁剪空间，以便屏幕渲染。
    *   将法线从模型空间转换到世界空间，并将顶点位置也转换到世界空间，作为 `v2f` 传递给片段着色器。
*   **像素阶段 (Fragment Shader)**：
    *   **计算 Matcap UV**：将世界法线转换到视角空间（View Space），提取 XY 分量映射到 $[0, 1]$ 区间，作为 Matcap 贴图的 UV。
    *   **计算 Ramp UV**：计算视线方向，利用法线与视线方向的点积得出 Fresnel 轮廓值，将其作为 U 坐标采样 Ramp 渐变贴图。
    *   **颜色合成**：采样主贴图、基础 Matcap、Ramp 贴图并相乘作为底色；最后加上 Matcap Add 贴图的颜色作为高光点缀。

---

## 2. 涉及到的着色器效果

*   **Matcap (材质捕获)**：通过预渲染的球体贴图模拟复杂光照和反射。只要视角转动，模型光影就会根据法线相对摄像机的角度发生变化，立体感强且性能开销极低。
*   **Fresnel Ramp (菲涅尔边缘渐变)**：根据视线与模型表面的夹角决定颜色变化。常用于 NPR 渲染中的边缘光（Rim Light）、天鹅绒质感或卡通轮廓过渡。
*   **Additive 叠加高光**：使用第二张 Matcap 贴图进行加法混合，专门用于提取强高光或特殊环境反射，增加材质层次。

---

## 3. 数学原理与公式

### 3.1 视角空间法线映射 (Matcap UV)
Matcap 的核心在于把摄像机当作固定视角的平面，根据模型表面法线朝向去采样球体贴图对应方向的颜色。
*   **法线转换公式**：将世界空间法线 $N_{world}$ 乘以视角矩阵 $V_{matrix}$，剔除平移属性（$w=0$）：
$$N_{view} = V_{matrix} \times \begin{bmatrix} N_{world} \\ 0 \end{bmatrix}$$
*   **UV 映射公式**：视角空间法线的 X 和 Y 分量范围是 $[-1, 1]$，需线性映射到 UV 坐标域 $[0, 1]$：
$$UV_{matcap} = \frac{N_{view}.xy + 1.0}{2.0}$$

### 3.2 菲涅尔效应 (Fresnel Effect)
用于计算视线与模型表面的边缘夹角。
*   **点乘公式**：计算世界法线 $N$ 与观察方向 $V$ 的点积，并截取到 $[0, 1]$：
$$N \cdot V = \max(0, N \cdot V)$$
*   **边缘强度公式**：越靠近边缘（法线与视线垂直），$N \cdot V$ 越趋近 0。取反得到边缘处最强的强度值：
$$Fresnel = 1.0 - (N \cdot V)$$

### 3.3 颜色合成 (Color Compositing)
*   **最终混合公式**：
$$C_{final} = (C_{diffuse} \times C_{matcap\_base} \times C_{ramp}) + C_{matcap\_add}$$

---

## 4. 核心代码架构与重难点剖析

### 4.1 矩阵乘法中 `w` 分量的坑点
```hlsl
mul(UNITY_MATRIX_V, float4(normal_world, 0.0))