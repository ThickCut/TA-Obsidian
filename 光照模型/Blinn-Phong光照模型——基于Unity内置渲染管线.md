本笔记记录了一个完整的光照 Shader 从无到有的 5 个实现阶段，涵盖了基础渲染、经典光照模型以及现代次世代渲染管线的常用特效。

## 阶段一：纯纹理渲染 

**实现效果**

- 将一张 2D 贴图显示在 3D 模型上。

- 无光照、无阴影，模型无论在什么光照环境下都表现得像一个“自发光的纸板”，没有立体感。


**核心知识点**

- **Properties**：定义暴露给材质面板的属性（如 `_MainTex`）。

- **appdata 包裹**：从 3D 模型接收原始数据（顶点位置 `POSITION`、贴图坐标 `TEXCOORD0`）。

- **v2f 包裹**：顶点着色器传给片元着色器的中转数据包。

- **vert (顶点着色器)**：使用 `UnityObjectToClipPos` 将 3D 模型坐标压扁转换成 2D 屏幕坐标。

- **frag (片元着色器)**：使用 `tex2D` 根据 UV 坐标在贴图上取色，直接输出到屏幕。


> [!example]- 💻 点击展开查看：阶段一完整代码
> 
> OpenGL Shading Language
> 
> ```hlsl
> Shader "Custom/Phase1_UnlitTexture"
> {
>     Properties
>     {
>         _MainTex ("Texture", 2D) = "white" {}
>     }
>     
>     SubShader
>     {
>         Tags { "RenderType"="Opaque" }
> 
>         Pass
>         {
>             CGPROGRAM
>             #pragma vertex vert
>             #pragma fragment frag
>             #include "UnityCG.cginc"
> 
>             struct appdata
>             {
>                 float4 vertex : POSITION;
>                 float2 texcoord : TEXCOORD0;
>             };
> 
>             struct v2f
>             {
>                 float4 pos : SV_POSITION;
>                 float2 uv : TEXCOORD0;
>             };
> 
>             sampler2D _MainTex;
>             float4 _MainTex_ST;
> 
>             v2f vert (appdata v)
>             {
>                 v2f o;
>                 o.pos = UnityObjectToClipPos(v.vertex); 
>                 o.uv = TRANSFORM_TEX(v.texcoord, _MainTex); 
>                 return o;
>             }
> 
>             half4 frag (v2f i) : SV_Target
>             {
>                 half4 color = tex2D(_MainTex, i.uv);
>                 return color;
>             }
>             ENDCG
>         }
>     }
> }
> ```

## 阶段二：基础漫反射 (Lambert 光照)

**实现效果**

- 模型有了基础的“明暗面”，产生了 3D 立体感。

- 迎着光的一面能看到贴图，背着光的一面会变成纯黑色（死黑）。


**核心知识点**

- **法线 (Normal)**：引入模型的法线数据，代表表面朝向（像表面长出的刺）。

- **统一坐标系**：在顶点着色器中，通过 `mul` 将法线从模型空间转换到世界空间，以便与光源方向进行比较。

- **点乘 (Dot Product)**：将法线方向与主光源方向（`_WorldSpaceLightPos0`）进行点乘。结果越接近 1 则越亮，越接近 0 或负数则越暗。使用 `max(0.0, dot(N, L))` 防止背光面出现负数光照。


> [!example]- 💻 点击展开查看：阶段二完整代码
> 
> OpenGL Shading Language
> 
> ```hlsl
> Shader "Custom/Phase2_Lambert"
> {
>     Properties
>     {
>         _MainTex ("Texture", 2D) = "white" {}
>     }
>     
>     SubShader
>     {
>         Tags { "RenderType"="Opaque" }
> 
>         Pass
>         {
>             Tags{"LightMode" = "ForwardBase"} 
>             
>             CGPROGRAM
>             #pragma vertex vert
>             #pragma fragment frag
>             #include "UnityCG.cginc"
>             #include "Lighting.cginc" 
> 
>             struct appdata
>             {
>                 float4 vertex : POSITION;
>                 float2 texcoord : TEXCOORD0;
>                 float3 normal  : NORMAL; 
>             };
> 
>             struct v2f
>             {
>                 float4 pos : SV_POSITION;
>                 float2 uv : TEXCOORD0;
>                 float3 normal_world : TEXCOORD1; 
>             };
> 
>             sampler2D _MainTex;
>             float4 _MainTex_ST;
> 
>             v2f vert (appdata v)
>             {
>                 v2f o;
>                 o.pos = UnityObjectToClipPos(v.vertex);
>                 o.uv = TRANSFORM_TEX(v.texcoord, _MainTex);
>                 o.normal_world = normalize(mul(float4(v.normal, 0.0), unity_WorldToObject).xyz);
>                 return o;
>             }
> 
>             half4 frag (v2f i) : SV_Target
>             {
>                 half4 base_color = tex2D(_MainTex, i.uv);
>                 half3 normal_dir = normalize(i.normal_world);
>                 half3 light_dir = normalize(_WorldSpaceLightPos0.xyz);
>                 
>                 half diff_term = max(0.0, dot(normal_dir, light_dir));
>                 half3 diffuse_color = diff_term * _LightColor0.rgb * base_color.rgb;
>                 
>                 return half4(diffuse_color, 1.0);
>             }
>             ENDCG
>         }
>     }
> }
> ```

## 阶段三：高光、阴影与环境光 (Blinn-Phong)

**实现效果**

- **环境光**：背光面不再死黑，而是沾染了场景天光的颜色。

- **高光**：向光面出现漂亮的高光光斑，随视线移动而变化。

- **阴影**：模型能够正确接收主光源投射下来的阴影遮挡。


**核心知识点**

- **Blinn-Phong 算法**：引入摄像机视线方向（`view_dir`），计算视线与光线的半角向量（`half_dir`）。半角向量与法线点乘，值越大说明反光越正对眼睛。

- **阴影宏**：使用 `SHADOW_COORDS`、`TRANSFER_SHADOW` 和 `SHADOW_ATTENUATION` 一套组合拳获取阴影遮挡值（0~1）。

- **光照叠加法则**：阴影只应遮挡受光源影响的漫反射和高光，**绝不能遮挡环境光**，否则阴影内会退化为纯黑。


> [!example]- 💻 点击展开查看：阶段三完整代码
> 
> OpenGL Shading Language
> 
> ```hlsl
> Shader "Custom/Phase3_SpecularShadows"
> {
>     Properties
>     {
>         _MainTex ("Texture", 2D) = "white" {}
>         _Shininess("Shininess (光泽度)", Range(0.01, 100)) = 1.0
>         _SpecIntensity("Specular Intensity (高光强度)", Range(0.01, 5)) = 1.0
>     }
>     
>     SubShader
>     {
>         Tags { "RenderType"="Opaque" }
> 
>         Pass
>         {
>             Tags{"LightMode" = "ForwardBase"}
>             CGPROGRAM
>             #pragma vertex vert
>             #pragma fragment frag
>             #pragma multi_compile_fwdbase
>             #include "UnityCG.cginc"
>             #include "Lighting.cginc"
>             #include "AutoLight.cginc" 
> 
>             struct appdata
>             {
>                 float4 vertex : POSITION;
>                 float2 texcoord : TEXCOORD0;
>                 float3 normal  : NORMAL;
>             };
> 
>             struct v2f
>             {
>                 float4 pos : SV_POSITION;
>                 float2 uv : TEXCOORD0;
>                 float3 normal_world : TEXCOORD1;
>                 float3 pos_world : TEXCOORD2;
>                 SHADOW_COORDS(3)
>             };
> 
>             sampler2D _MainTex;
>             float4 _MainTex_ST;
>             float _Shininess;
>             float _SpecIntensity;
> 
>             v2f vert (appdata v)
>             {
>                 v2f o;
>                 o.pos = UnityObjectToClipPos(v.vertex);
>                 o.uv = TRANSFORM_TEX(v.texcoord, _MainTex);
>                 o.normal_world = normalize(mul(float4(v.normal, 0.0), unity_WorldToObject).xyz);
>                 o.pos_world = mul(unity_ObjectToWorld, v.vertex).xyz;
>                 TRANSFER_SHADOW(o)
>                 return o;
>             }
> 
>             half4 frag (v2f i) : SV_Target
>             {
>                 half4 base_color = tex2D(_MainTex, i.uv);
>                 half3 normal_dir = normalize(i.normal_world);
>                 half3 light_dir = normalize(_WorldSpaceLightPos0.xyz);
>                 
>                 half shadow = SHADOW_ATTENUATION(i);
> 
>                 half diff_term = max(0.0, dot(normal_dir, light_dir)) * shadow;
>                 half3 diffuse_color = diff_term * _LightColor0.rgb * base_color.rgb;
> 
>                 half3 ambient_color = UNITY_LIGHTMODEL_AMBIENT.rgb * base_color.rgb;
> 
>                 half3 view_dir = normalize(_WorldSpaceCameraPos.xyz - i.pos_world);
>                 half3 half_dir = normalize(light_dir + view_dir);
>                 half NdotH = max(0.0, dot(normal_dir, half_dir));
>                 half3 spec_color = pow(NdotH, _Shininess) * diff_term * _LightColor0.rgb * _SpecIntensity;
> 
>                 half3 final_color = diffuse_color + ambient_color + spec_color;
>                 return half4(final_color, 1.0);
>             }
>             ENDCG
>         }
>     }
>     Fallback "Diffuse" 
> }
> ```

## 阶段四：法线贴图与切线空间 (Normal Map)

**实现效果**

- 在不增加任何模型顶点的情况下，通过视觉错觉让平滑表面产生极其丰富的凹凸细节坑洼。


**核心知识点**

- **切线空间**：引入贴图专用的局部坐标系，解决法线贴图方向的解析问题。

- **切线类型 float4 探秘**：请求切线数据时必须用 `float4 tangent`，其中 `w` 值是解决“镜像模型法线反转”问题的补丁开关。计算完副法线后，传给上色车间的数据降级为 `float3`。

- **TBN 矩阵翻译官**：通过法线 (N)、切线 (T)、副法线 (B) 构建 `3x3` 的 TBN 矩阵，将法线贴图中采样的 2D 凹凸数据，完美翻译成 3D 世界空间下凹凸不平的真实法线方向。


> [!example]- 💻 点击展开查看：阶段四完整代码
> 
> OpenGL Shading Language
> 
> ```h
> Shader "Custom/Phase4_NormalMap"
> {
>     Properties
>     {
>         _MainTex ("Texture", 2D) = "white" {}
>         _NormalMap("Normal Map", 2D) = "bump" {}
>         _NormalIntensity("Normal Intensity", Range(0.0, 5.0)) = 1.0
>         
>         _Shininess("Shininess", Range(0.01, 100)) = 1.0
>         _SpecIntensity("Specular Intensity", Range(0.01, 5)) = 1.0
>     }
>     
>     SubShader
>     {
>         Tags { "RenderType"="Opaque" }
> 
>         Pass
>         {
>             Tags{"LightMode" = "ForwardBase"}
>             CGPROGRAM
>             #pragma vertex vert
>             #pragma fragment frag
>             #pragma multi_compile_fwdbase
>             #include "UnityCG.cginc"
>             #include "Lighting.cginc"
>             #include "AutoLight.cginc"
> 
>             struct appdata
>             {
>                 float4 vertex : POSITION;
>                 float2 texcoord : TEXCOORD0;
>                 float3 normal  : NORMAL;
>                 float4 tangent : TANGENT; 
>             };
> 
>             struct v2f
>             {
>                 float4 pos : SV_POSITION;
>                 float2 uv : TEXCOORD0;
>                 float3 normal_dir : TEXCOORD1; 
>                 float3 pos_world : TEXCOORD2;
>                 float3 tangent_dir : TEXCOORD3;
>                 float3 binormal_dir : TEXCOORD4;
>                 SHADOW_COORDS(5)
>             };
> 
>             sampler2D _MainTex;
>             float4 _MainTex_ST;
>             float _Shininess;
>             float _SpecIntensity;
>             sampler2D _NormalMap;
>             float _NormalIntensity;
> 
>             v2f vert (appdata v)
>             {
>                 v2f o;
>                 o.pos = UnityObjectToClipPos(v.vertex);
>                 o.uv = TRANSFORM_TEX(v.texcoord, _MainTex);
>                 o.pos_world = mul(unity_ObjectToWorld, v.vertex).xyz;
>                 
>                 o.normal_dir = normalize(mul(float4(v.normal, 0.0), unity_WorldToObject).xyz);
>                 o.tangent_dir = normalize(mul(unity_ObjectToWorld, float4(v.tangent.xyz, 0.0)).xyz);
>                 o.binormal_dir = normalize(cross(o.normal_dir, o.tangent_dir)) * v.tangent.w;
>                 
>                 TRANSFER_SHADOW(o)
>                 return o;
>             }
> 
>             half4 frag (v2f i) : SV_Target
>             {		
>                 half shadow = SHADOW_ATTENUATION(i);
>                 half4 base_color = tex2D(_MainTex, i.uv);
> 
>                 half3 normal_dir = normalize(i.normal_dir);
>                 half3 tangent_dir = normalize(i.tangent_dir);
>                 half3 binormal_dir = normalize(i.binormal_dir);
>                 
>                 float3x3 TBN = float3x3(tangent_dir, binormal_dir, normal_dir);
>                 
>                 half4 normalmap = tex2D(_NormalMap, i.uv);
>                 half3 normal_data = UnpackNormal(normalmap);
>                 normal_data.xy = normal_data.xy * _NormalIntensity;
>                 normal_dir = normalize(mul(normal_data.xyz, TBN));
> 
>                 half3 light_dir = normalize(_WorldSpaceLightPos0.xyz);
>                 half diff_term = max(0.0, dot(normal_dir, light_dir)) * shadow;
>                 half3 diffuse_color = diff_term * _LightColor0.rgb * base_color.rgb;
> 
>                 half3 view_dir = normalize(_WorldSpaceCameraPos.xyz - i.pos_world);
>                 half3 half_dir = normalize(light_dir + view_dir);
>                 half NdotH = max(0.0, dot(normal_dir, half_dir));
>                 half3 spec_color = pow(NdotH, _Shininess) * diff_term * _LightColor0.rgb * _SpecIntensity;
> 
>                 half3 ambient_color = UNITY_LIGHTMODEL_AMBIENT.rgb * base_color.rgb;
>                 half3 final_color = diffuse_color + ambient_color + spec_color;
>                 
>                 return half4(final_color, 1.0);
>             }
>             ENDCG
>         }
>     }
>     Fallback "Diffuse"
> }
> ```

## 阶段五：进阶渲染 (视差、AO、滤镜与多光源)

**实现效果**

- 提供侧面视角的真实深度错觉（视差）。

- 缝隙处被压暗，局部高光受到遮罩精确控制。

- 画面呈现电影级抗过曝质感（ACES 滤镜）。

- 支持被场景内的手电筒、篝火（点光源）等附加灯光照亮。


**核心知识点**

- **视差映射 (Parallax Mapping)**：利用 `for` 循环和高度图，根据视线方向在切线空间内不断偏移 UV 坐标（产生“假 UV”），所有贴图采样改用该偏移 UV 以实现深度错觉。

- **纹理遮罩控制**：在最终计算阶段，将 AO 贴图（压暗缝隙）和 Specular 贴图（控制高光区域）直接乘入物理量结果中。

- **伽马与 ACES 电影色调**：运算前使用 `pow(color, 2.2)` 去除颜色伽马值进入线性空间；输出前使用 `ACESFilm` 函数压制高光防瞎眼过曝，再用 `pow(color, 1.0/2.2)` 恢复给显示器。

- **ForwardAdd 通道**：新增第二个 Pass 处理额外灯光，利用 `Blend One One` 指令将计算出的多余灯光颜色叠加到主画面的颜色之上。


> [!example]- 💻 点击展开查看：阶段五完整代码
> 
> OpenGL Shading Language
> 
> ```
> Shader "Custom/Phase5_UltimatePhong"
> {
> 	Properties
> 	{
> 		_MainTex ("Texture", 2D) = "white" {}
> 		_NormalMap("NormalMap",2D) = "bump"{}
> 		_NormalIntensity("Normal Intensity",Range(0.0,5.0)) = 1.0
> 		_ParallaxMap("ParallaxMap (高度图)", 2D) = "black" {}
> 		_Parallax("_Parallax (视差深度)", float) = 2
> 		_AOMap("AO Map (环境遮蔽图)", 2D) = "white" {}
> 		_SpecMask("Spec Mask (高光遮罩图)", 2D) = "white" {}
> 		_Shininess("Shininess",Range(0.01,100)) = 1.0
> 		_SpecIntensity("SpecIntensity",Range(0.01,5)) = 1.0
> 	}
> 	
> 	SubShader
> 	{
> 		Tags { "RenderType"="Opaque" }
> 		LOD 100
> 
>         // ================= ForwardBase =================
> 		Pass
> 		{
> 			Tags{"LightMode" = "ForwardBase"}
> 			CGPROGRAM
> 			#pragma vertex vert
> 			#pragma fragment frag
> 			#pragma multi_compile_fwdbase
> 			#include "UnityCG.cginc"
> 			#include "AutoLight.cginc"
> 			
> 			struct appdata
> 			{
> 				float4 vertex : POSITION;
> 				float2 texcoord : TEXCOORD0;
> 				float3 normal  : NORMAL;
> 				float4 tangent : TANGENT;
> 			};
> 
> 			struct v2f
> 			{
> 				float4 pos : SV_POSITION;
> 				float2 uv : TEXCOORD0;
> 				float3 normal_dir : TEXCOORD1;
> 				float3 pos_world : TEXCOORD2;
> 				float3 tangent_dir : TEXCOORD3;
> 				float3 binormal_dir : TEXCOORD4;
> 				SHADOW_COORDS(5)
> 			};
> 
> 			sampler2D _MainTex;
> 			float4 _MainTex_ST;
> 			float4 _LightColor0;
> 			float _Shininess;
> 			float _SpecIntensity;
> 			sampler2D _NormalMap;
> 			float _NormalIntensity;
> 			sampler2D _AOMap;
> 			sampler2D _SpecMask;
> 			sampler2D _ParallaxMap;
> 			float _Parallax;
> 			
> 			float3 ACESFilm(float3 x)
> 			{
> 				float a = 2.51f;
> 				float b = 0.03f;
> 				float c = 2.43f;
> 				float d = 0.59f;
> 				float e = 0.14f;
> 				return saturate((x*(a*x + b)) / (x*(c*x + d) + e));
> 			};
> 
> 			v2f vert (appdata v)
> 			{
> 				v2f o;
> 				o.pos = UnityObjectToClipPos(v.vertex);
> 				o.uv = TRANSFORM_TEX(v.texcoord, _MainTex);
> 				o.normal_dir = normalize(mul(float4(v.normal, 0.0), unity_WorldToObject).xyz);
> 				o.tangent_dir = normalize(mul(unity_ObjectToWorld, float4(v.tangent.xyz, 0.0)).xyz);
> 				o.binormal_dir = normalize(cross(o.normal_dir,o.tangent_dir)) * v.tangent.w;
> 				o.pos_world = mul(unity_ObjectToWorld, v.vertex).xyz;
> 				TRANSFER_SHADOW(o)
> 				return o;
> 			}
> 			
> 			half4 frag (v2f i) : SV_Target
> 			{		
> 				half shadow = SHADOW_ATTENUATION(i);
> 
> 				half3 view_dir = normalize(_WorldSpaceCameraPos.xyz - i.pos_world);
> 				half3 normal_dir = normalize(i.normal_dir);
> 				half3 tangent_dir = normalize(i.tangent_dir);
> 				half3 binormal_dir = normalize(i.binormal_dir);
> 				float3x3 TBN = float3x3(tangent_dir, binormal_dir, normal_dir);
> 				
> 				half3 view_tangentspace = normalize(mul(TBN, view_dir));
> 				half2 uv_parallax = i.uv;
> 
> 				for (int j = 0; j < 10; j++)
> 				{
> 					half height = tex2D(_ParallaxMap, uv_parallax);
> 					uv_parallax = uv_parallax - (0.5 - height) * view_tangentspace.xy * _Parallax * 0.01f;
> 				}
> 
> 				half4 base_color = tex2D(_MainTex, uv_parallax);
> 				base_color = pow(base_color, 2.2); 
> 				half4 ao_color = tex2D(_AOMap, uv_parallax);
> 				half4 spec_mask = tex2D(_SpecMask, uv_parallax);
> 				half4 normalmap = tex2D(_NormalMap, uv_parallax);
> 				half3 normal_data = UnpackNormal(normalmap);
> 				normal_data.xy = normal_data.xy * _NormalIntensity;
> 				normal_dir = normalize(mul(normal_data.xyz, TBN));
> 
> 				half3 light_dir = normalize(_WorldSpaceLightPos0.xyz);
> 				half diff_term = min(shadow, max(0.0,dot(normal_dir, light_dir)));
> 				half3 diffuse_color = diff_term * _LightColor0.xyz * base_color.xyz;
> 				
> 				half3 half_dir = normalize(light_dir + view_dir);
> 				half NdotH = dot(normal_dir, half_dir);
> 				half3 spec_color = pow(max(0.0, NdotH),_Shininess) 
> 					 * diff_term * _LightColor0.xyz * _SpecIntensity * spec_mask.rgb;
> 
> 				half3 ambient_color = UNITY_LIGHTMODEL_AMBIENT.rgb * base_color.xyz;
> 				half3 final_color = (diffuse_color + spec_color + ambient_color) * ao_color.rgb;
>                 
> 				half3 tone_color = ACESFilm(final_color);
> 				tone_color = pow(tone_color, 1.0 / 2.2);
> 				return half4(tone_color,1.0);
> 			}
> 			ENDCG
> 		}
> 
>         // ================= ForwardAdd =================
> 		Pass
> 		{
> 			Tags{"LightMode" = "ForwardAdd"}
> 			Blend One One 
> 			CGPROGRAM
> 			#pragma vertex vert
> 			#pragma fragment frag
> 			#pragma multi_compile_fwdadd 
> 			#include "UnityCG.cginc"
> 			#include "AutoLight.cginc"
> 
> 			struct appdata {
> 				float4 vertex : POSITION;
> 				float2 texcoord : TEXCOORD0;
> 				float3 normal  : NORMAL;
> 				float4 tangent : TANGENT;
> 			};
> 			struct v2f {
> 				float4 pos : SV_POSITION;
> 				float2 uv : TEXCOORD0;
> 				float3 normal_dir : TEXCOORD1;
> 				float3 pos_world : TEXCOORD2;
> 				float3 tangent_dir : TEXCOORD3;
> 				float3 binormal_dir : TEXCOORD4;
> 				LIGHTING_COORDS(5, 6)
> 			};
> 
> 			sampler2D _MainTex;
> 			float4 _MainTex_ST;
> 			float4 _LightColor0;
> 			float _Shininess;
> 			float _SpecIntensity;
> 			sampler2D _NormalMap;
> 			float _NormalIntensity;
> 			sampler2D _AOMap;
> 			sampler2D _SpecMask;
> 			sampler2D _ParallaxMap;
> 			float _Parallax;
> 
> 			v2f vert(appdata v) {
> 				v2f o;
> 				o.pos = UnityObjectToClipPos(v.vertex);
> 				o.uv = TRANSFORM_TEX(v.texcoord, _MainTex);
> 				o.normal_dir = normalize(mul(float4(v.normal, 0.0), unity_WorldToObject).xyz);
> 				o.tangent_dir = normalize(mul(unity_ObjectToWorld, float4(v.tangent.xyz, 0.0)).xyz);
> 				o.binormal_dir = normalize(cross(o.normal_dir,o.tangent_dir)) * v.tangent.w;
> 				o.pos_world = mul(unity_ObjectToWorld, v.vertex).xyz;
> 				TRANSFER_VERTEX_TO_FRAGMENT(o);
> 				return o;
> 			}
> 
> 			half4 frag(v2f i) : SV_Target {
> 				half atten = LIGHT_ATTENUATION(i);
> 				half3 view_dir = normalize(_WorldSpaceCameraPos.xyz - i.pos_world);
> 				half3 normal_dir = normalize(i.normal_dir);
> 				half3 tangent_dir = normalize(i.tangent_dir);
> 				half3 binormal_dir = normalize(i.binormal_dir);
> 				float3x3 TBN = float3x3(tangent_dir, binormal_dir, normal_dir);
> 				
> 				half3 view_tangentspace = normalize(mul(TBN, view_dir));
> 				half2 uv_parallax = i.uv;
> 
> 				for (int j = 0; j < 10; j++) {
> 					half height = tex2D(_ParallaxMap, uv_parallax);
> 					uv_parallax = uv_parallax - (0.5 - height) * view_tangentspace.xy * _Parallax * 0.01f;
> 				}
> 
> 				half4 base_color = tex2D(_MainTex, uv_parallax);
> 				half4 ao_color = tex2D(_AOMap, uv_parallax);
> 				half4 spec_mask = tex2D(_SpecMask, uv_parallax);
> 				half4 normalmap = tex2D(_NormalMap, uv_parallax);
> 				half3 normal_data = UnpackNormal(normalmap);
> 				normal_data.xy = normal_data.xy * _NormalIntensity;
> 				normal_dir = normalize(mul(normal_data.xyz, TBN));
> 
> 				half3 light_dir_point = normalize(_WorldSpaceLightPos0.xyz - i.pos_world);
> 				half3 light_dir = normalize(_WorldSpaceLightPos0.xyz);
> 				light_dir = lerp(light_dir, light_dir_point, _WorldSpaceLightPos0.w);
> 				
> 				half diff_term = min(atten, max(0.0,dot(normal_dir, light_dir)));
> 				half3 diffuse_color = diff_term * _LightColor0.xyz * base_color.xyz;
> 
> 				half3 half_dir = normalize(light_dir + view_dir);
> 				half NdotH = dot(normal_dir, half_dir);
> 				half3 spec_color = pow(max(0.0, NdotH),_Shininess)
> 					 * diff_term * _LightColor0.xyz * _SpecIntensity * spec_mask.rgb;
> 
> 				half3 final_color = (diffuse_color + spec_color) * ao_color.rgb;
> 				return half4(final_color,1.0);
> 			}
> 			ENDCG
> 		}
> 	}
> 	Fallback "Diffuse"
> }
> ```

