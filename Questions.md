---
日期: 2026-07-17T20:00:00
---
NdotV--世界空间法线值

片元阶段注意性能：向量——half

补全三维向量变成四维向量：需要在后面补一个1.0     如果是向量补0.0


片元shader中的normalize

- - **线性插值带来的误差**：法线向量通常是在顶点着色器（Vertex Shader）中计算或获取的，然后通过光栅化阶段线性插值（Linear Interpolation）传递到片元着色器。虽然每个顶点的法线是单位向量（长度为 1），但**两个单位向量之间的插值结果，长度通常不等于 1**。
    
- **光照计算的要求**：绝大多数光照模型（如 Lambert, Blinn-Phong, PBR）都依赖于点积运算（Dot Product）。例如，计算光照强度时常用 $N \cdot L$（法线与光照方向的点积）。
    
    - **数学原理**：$N \cdot L = \vert{}N\vert{} \times \vert{}L\vert{} \times \cos(\theta)$。
        
    - 如果法线向量 $N$ 的长度 $\vert{}N\vert{}$ 不是 1，那么算出来的光照强度就会出现错误，导致光照过亮、过暗或者出现奇怪的伪影。


---


在深度缓冲区（Z-Buffer）中写入物体的深度信息，但不在屏幕上渲染出任何颜色

“隐身并占位”（通常用于遮挡剔除、阴影预处理或一些特殊的遮罩效果）

```hlsl
        Pass
        {
            Cull Off
            ZWrite On
            ColorMask 0

            CGPROGRAM

            float4 _Color;

            #pragma vertex vert
            #pragma fragment frag
            #include "UnityCG.cginc"

            float4 vert(float4 vertexPos : POSITION) : SV_POSITION
            {
                return UnityObjectToClipPos(vertexPos);
            }

            float4 frag(void) : SV_Target
            {
                return _Color;    
            }

            ENDCG   
        }
```
