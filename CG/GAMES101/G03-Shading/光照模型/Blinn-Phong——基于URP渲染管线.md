## 核心架构优化：单 Pass 前向渲染

内置管线（BiRP）处理多光源时通常使用 `ForwardBase`（主光源）+ `ForwardAdd`（附加光源）。如果有 3 个额外光源，模型会被绘制 4 次，导致 Draw Call 暴增。

在 URP 中，**必须彻底删除 `ForwardAdd` Pass**。URP 采用单 Pass 前向渲染（Single-Pass Forward Rendering），主光源和所有的附加光源（点光源/聚光灯）会在同一个 `UniversalForward` Pass 中通过循环一次性计算完毕，极大降低了 Draw Call 和 Overdraw。

## 渲染逻辑修正：拥抱线性空间

在将旧 Shader 迁移到现代 URP 管线时，必须剔除以下**反模式（Anti-pattern）**：

- **移除局部色调映射 (Tonemapping)：** 不要再在 Shader 内部手动写 `ACESFilm`。URP 要求 Shader 输出线性颜色，HDR 到 LDR 的映射以及 ACES 应交由**全局后处理体积 (Post-processing Volume)** 统一处理，否则会破坏场景 PBR 统一性。
    
- **移除手动 Gamma 校正：** 删掉类似 `pow(color, 2.2)` 的代码。URP 默认在**线性空间 (Linear Space)** 下工作。
    

## 语法与 API 映射速查表

底层着色语言从 `CGPROGRAM` 切换到了 `HLSLPROGRAM`。以下是常用的替换映射：

|**内置管线 (BiRP / CG)**|**URP (HLSL)**|
|---|---|
|`#include "UnityCG.cginc"`|`#include "Packages/.../Core.hlsl"`|
|`UnityObjectToClipPos(v)`|`TransformObjectToHClip(v)`|
|`mul(unity_ObjectToWorld, v)`|`TransformObjectToWorld(v)`|
|`_LightColor0`|`GetMainLight().color`|
|`_WorldSpaceLightPos0`|`GetMainLight().direction`|
|`sampler2D _MainTex;`|`TEXTURE2D(_MainTex); SAMPLER(sampler_MainTex);`|
|`tex2D(_MainTex, uv)`|`SAMPLE_TEXTURE2D(_MainTex, sampler_MainTex, uv)`|

> 💡 **重要补充 (SRP Batcher)：** 为了让材质支持 URP 的动态合批，所有在 `Properties` 暴露的变量（除了纹理）都必须包裹在 `CBUFFER_START(UnityPerMaterial)` 和 `CBUFFER_END` 之中。

## 📄 URP 改造后源码

High-level shader language

```hlsl
Shader "Custom/URP_Phase5_UltimatePhong"
{
    Properties
    {
        _MainTex ("Texture", 2D) = "white" {}
        _NormalMap("NormalMap",2D) = "bump"{}
        _NormalIntensity("Normal Intensity",Range(0.0,5.0)) = 1.0
        _ParallaxMap("ParallaxMap", 2D) = "black" {}
        _Parallax("_Parallax", float) = 2
        _AOMap("AO Map", 2D) = "white" {}
        _SpecMask("Spec Mask", 2D) = "white" {}
        _Shininess("Shininess",Range(0.01,100)) = 1.0
        _SpecIntensity("SpecIntensity",Range(0.01,5)) = 1.0
    }
    
    SubShader
    {
        // 添加 URP 管线标签，确保管线识别
        Tags { "RenderType"="Opaque" "RenderPipeline"="UniversalPipeline" }
        LOD 100

        Pass
        {
            Name "ForwardLit"
            Tags{"LightMode" = "UniversalForward"}

            HLSLPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            
            // 启用主光源阴影和附加光源循环的关键字
            #pragma multi_compile _ _MAIN_LIGHT_SHADOWS _MAIN_LIGHT_SHADOWS_CASCADE
            #pragma multi_compile _ _ADDITIONAL_LIGHTS_VERTEX _ADDITIONAL_LIGHTS
            
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Lighting.hlsl"
            
            struct Attributes
            {
                float4 positionOS : POSITION;
                float2 texcoord : TEXCOORD0;
                float3 normalOS : NORMAL;
                float4 tangentOS : TANGENT;
            };

            struct Varyings
            {
                float4 positionCS : SV_POSITION;
                float2 uv : TEXCOORD0;
                float3 normalWS : TEXCOORD1;
                float3 positionWS : TEXCOORD2;
                float3 tangentWS : TEXCOORD3;
                float3 bitangentWS : TEXCOORD4;
            };

            // URP 推荐的纹理声明方式（分离纹理与采样器，利于跨平台）
            TEXTURE2D(_MainTex); SAMPLER(sampler_MainTex);
            TEXTURE2D(_NormalMap); SAMPLER(sampler_NormalMap);
            TEXTURE2D(_ParallaxMap); SAMPLER(sampler_ParallaxMap);
            TEXTURE2D(_AOMap); SAMPLER(sampler_AOMap);
            TEXTURE2D(_SpecMask); SAMPLER(sampler_SpecMask);

            // 放入 CBUFFER 以支持 SRP Batcher 合批优化
            CBUFFER_START(UnityPerMaterial)
                float4 _MainTex_ST;
                float _Shininess;
                float _SpecIntensity;
                float _NormalIntensity;
                float _Parallax;
            CBUFFER_END

            Varyings vert (Attributes v)
            {
                Varyings o;
                o.positionWS = TransformObjectToWorld(v.positionOS.xyz);
                o.positionCS = TransformWorldToHClip(o.positionWS);
                o.uv = v.texcoord * _MainTex_ST.xy + _MainTex_ST.zw;
                
                // 统一计算世界空间 TBN
                VertexNormalInputs normalInput = GetVertexNormalInputs(v.normalOS, v.tangentOS);
                o.normalWS = normalInput.normalWS;
                o.tangentWS = normalInput.tangentWS;
                o.bitangentWS = normalInput.bitangentWS;
                
                return o;
            }
            
            half4 frag (Varyings i) : SV_Target
            {       
                half3 viewDirWS = GetWorldSpaceNormalizeViewDir(i.positionWS);
                float3x3 TBN = float3x3(i.tangentWS, i.bitangentWS, i.normalWS);
                
                // 视差贴图计算
                half3 viewDirTS = normalize(mul(TBN, viewDirWS));
                half2 uv_parallax = i.uv;

                for (int j = 0; j < 10; j++)
                {
                    half height = SAMPLE_TEXTURE2D(_ParallaxMap, sampler_ParallaxMap, uv_parallax).r;
                    uv_parallax = uv_parallax - (0.5 - height) * viewDirTS.xy * _Parallax * 0.01f;
                }

                // 移除原有的 pow() Gamma 转换，直接在线性空间采样
                half4 base_color = SAMPLE_TEXTURE2D(_MainTex, sampler_MainTex, uv_parallax);
                half4 ao_color = SAMPLE_TEXTURE2D(_AOMap, sampler_AOMap, uv_parallax);
                half4 spec_mask = SAMPLE_TEXTURE2D(_SpecMask, sampler_SpecMask, uv_parallax);
                
                half4 normalmap = SAMPLE_TEXTURE2D(_NormalMap, sampler_NormalMap, uv_parallax);
                half3 normalTS = UnpackNormalScale(normalmap, _NormalIntensity);
                half3 normalWS = normalize(mul(normalTS, TBN));

                // 获取主光源和阴影衰减
                float4 shadowCoord = TransformWorldToShadowCoord(i.positionWS);
                Light mainLight = GetMainLight(shadowCoord);
                
                // 环境光采用球谐函数 (Spherical Harmonics)
                half3 ambient_color = SampleSH(normalWS) * base_color.rgb;

                // 主光源漫反射与高光
                half NdotL = saturate(dot(normalWS, mainLight.direction));
                half3 diffuse_color = NdotL * mainLight.color * mainLight.distanceAttenuation * mainLight.shadowAttenuation * base_color.rgb;
                
                half3 halfDir = normalize(mainLight.direction + viewDirWS);
                half NdotH = saturate(dot(normalWS, halfDir));
                half3 spec_color = pow(NdotH, _Shininess) * mainLight.color * _SpecIntensity * spec_mask.rgb * mainLight.shadowAttenuation;

                // 最终混合
                half3 final_color = (diffuse_color + spec_color + ambient_color) * ao_color.rgb;

                // 直接输出线性颜色，交由后处理进行 ACES Tonemapping
                return half4(final_color, 1.0);
            }
            ENDHLSL
        }
        
        // 【必须】补充 ShadowCaster 使得模型可以产生投影
        Pass
        {
            Name "ShadowCaster"
            Tags{"LightMode" = "ShadowCaster"}
            
            HLSLPROGRAM
            #pragma vertex ShadowPassVertex
            #pragma fragment ShadowPassFragment
            #include "Packages/com.unity.render-pipelines.universal/Shaders/ShadowCasterPass.hlsl"
            ENDHLSL
        }
    }
}
```

## 📄 URP2


```hlsl
Shader "lit/PhongURP"
{
    Properties
    {
        _MainTex ("Texture", 2D) = "white" {}
        _NormalMap("NormalMap",2D) = "bump"{}
        _NormalIntensity("Normal Intensity",Range(0.0,5.0)) = 1.0
        _ParallaxMap("ParallaxMap", 2D) = "black" {}
        _Parallax("_Parallax", float) = 2
        _AOMap("AO Map", 2D) = "white" {}
        _SpecMask("Spec Mask", 2D) = "white" {}
        _Shininess("Shininess",Range(0.01,100)) = 1.0
        _SpecIntensity("SpecIntensity",Range(0.01,5)) = 1.0
    }
    
    SubShader
    {
        Tags { "RenderType"="Opaque" "RenderPipeline"="UniversalPipeline" }
        LOD 100

        // ================= UniversalForward Pass =================
        Pass
        {
            Name "ForwardLit"
            Tags{"LightMode" = "UniversalForward"}

            HLSLPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            
            #pragma multi_compile _ _MAIN_LIGHT_SHADOWS _MAIN_LIGHT_SHADOWS_CASCADE
            #pragma multi_compile _ _ADDITIONAL_LIGHTS_VERTEX _ADDITIONAL_LIGHTS
            
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Lighting.hlsl"
            
            struct Attributes
            {
                float4 positionOS : POSITION;
                float2 texcoord : TEXCOORD0;
                float3 normalOS : NORMAL;
                float4 tangentOS : TANGENT;
            };

            struct Varyings
            {
                float4 positionCS : SV_POSITION;
                float2 uv : TEXCOORD0;
                float3 normalWS : TEXCOORD1;
                float3 positionWS : TEXCOORD2;
                float3 tangentWS : TEXCOORD3;
                float3 bitangentWS : TEXCOORD4;
            };

            TEXTURE2D(_MainTex); SAMPLER(sampler_MainTex);
            TEXTURE2D(_NormalMap); SAMPLER(sampler_NormalMap);
            TEXTURE2D(_ParallaxMap); SAMPLER(sampler_ParallaxMap);
            TEXTURE2D(_AOMap); SAMPLER(sampler_AOMap);
            TEXTURE2D(_SpecMask); SAMPLER(sampler_SpecMask);

            CBUFFER_START(UnityPerMaterial)
                float4 _MainTex_ST;
                float _Shininess;
                float _SpecIntensity;
                float _NormalIntensity;
                float _Parallax;
            CBUFFER_END

            Varyings vert (Attributes v)
            {
                Varyings o;
                o.positionWS = TransformObjectToWorld(v.positionOS.xyz);
                o.positionCS = TransformWorldToHClip(o.positionWS);
                o.uv = v.texcoord * _MainTex_ST.xy + _MainTex_ST.zw;
                
                VertexNormalInputs normalInput = GetVertexNormalInputs(v.normalOS, v.tangentOS);
                o.normalWS = normalInput.normalWS;
                o.tangentWS = normalInput.tangentWS;
                o.bitangentWS = normalInput.bitangentWS;
                
                return o;
            }
            
            half4 frag (Varyings i) : SV_Target
            {       
                half3 viewDirWS = GetWorldSpaceNormalizeViewDir(i.positionWS);
                float3x3 TBN = float3x3(i.tangentWS, i.bitangentWS, i.normalWS);
                
                // 视差计算
                half3 viewDirTS = normalize(mul(TBN, viewDirWS));
                half2 uv_parallax = i.uv;

                for (int j = 0; j < 10; j++)
                {
                    half height = SAMPLE_TEXTURE2D(_ParallaxMap, sampler_ParallaxMap, uv_parallax).r;
                    uv_parallax = uv_parallax - (0.5 - height) * viewDirTS.xy * _Parallax * 0.01f;
                }

                half4 base_color = SAMPLE_TEXTURE2D(_MainTex, sampler_MainTex, uv_parallax);
                half4 ao_color = SAMPLE_TEXTURE2D(_AOMap, sampler_AOMap, uv_parallax);
                half4 spec_mask = SAMPLE_TEXTURE2D(_SpecMask, sampler_SpecMask, uv_parallax);
                
                half4 normalmap = SAMPLE_TEXTURE2D(_NormalMap, sampler_NormalMap, uv_parallax);
                half3 normalTS = UnpackNormalScale(normalmap, _NormalIntensity);
                half3 normalWS = normalize(mul(normalTS, TBN));

                // 采样主光源与阴影
                float4 shadowCoord = TransformWorldToShadowCoord(i.positionWS);
                Light mainLight = GetMainLight(shadowCoord);
                
                // 环境光
                half3 ambient_color = SampleSH(normalWS) * base_color.rgb;

                // 漫反射与高光
                half NdotL = saturate(dot(normalWS, mainLight.direction));
                half3 diffuse_color = NdotL * mainLight.color * mainLight.distanceAttenuation * mainLight.shadowAttenuation * base_color.rgb;
                
                half3 halfDir = normalize(mainLight.direction + viewDirWS);
                half NdotH = saturate(dot(normalWS, halfDir));
                half3 spec_color = pow(NdotH, _Shininess) * mainLight.color * _SpecIntensity * spec_mask.rgb * mainLight.shadowAttenuation;

                half3 final_color = (diffuse_color + spec_color + ambient_color) * ao_color.rgb;

                return half4(final_color, 1.0);
            }
            ENDHLSL
        }
        
        // ================= 修复后的 ShadowCaster Pass =================
        Pass
        {
            Name "ShadowCaster"
            Tags{"LightMode" = "ShadowCaster"}

            ZWrite On
            ZTest LEqual
            ColorMask 0

            HLSLPROGRAM
            #pragma vertex ShadowPassVertex
            #pragma fragment ShadowPassFragment

            // 引入 URP 的 Shadows.hlsl 库以支持阴影计算宏
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Lighting.hlsl"
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Shadows.hlsl"

            struct Attributes
            {
                float4 positionOS   : POSITION;
                float3 normalOS     : NORMAL;
            };

            struct Varyings
            {
                float4 positionCS   : SV_POSITION;
            };

            float3 _LightDirection;

            Varyings ShadowPassVertex(Attributes input)
            {
                Varyings output;
                float3 positionWS = TransformObjectToWorld(input.positionOS.xyz);
                float3 normalWS = TransformObjectToWorldNormal(input.normalOS);

                // 使用全版本通用的 ApplyShadowBias 方法
                float3 positionWS_Biased = ApplyShadowBias(positionWS, normalWS, _LightDirection);
                output.positionCS = TransformWorldToHClip(positionWS_Biased);
                
                return output;
            }

            half4 ShadowPassFragment(Varyings input) : SV_Target
            {
                return 0;
            }
            ENDHLSL
        }
    }
}
```