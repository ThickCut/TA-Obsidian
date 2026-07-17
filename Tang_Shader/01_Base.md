- 必备概念
    
    - 渲染管线是什么
        
        - 渲染管线概述
            
            - 什么是渲染管线![](https://api2.mubu.com/v3/document_image/24058158_6a0a605b-ba72-485b-8fa4-4c345043e40c.png?)
            
            - 渲染管线中的数据指的是什么![](https://api2.mubu.com/v3/document_image/24058158_ff3a5361-f02a-4c35-d000-a2435095d35a.png?)
            
            - 渲染管线中的分阶段指的是什么![](https://api2.mubu.com/v3/document_image/24058158_781d2329-ba2a-47c3-92a9-31991f0214b9.png?)
            
            - 渲染管线总结![](https://api2.mubu.com/v3/document_image/24058158_f5985279-cca2-4db0-ddca-655b8e381b77.png?)
        
        - 应用阶段
            
            - 知识必备——CPU和GPU![](https://api2.mubu.com/v3/document_image/24058158_196311fb-bd4d-4809-f215-31936de6ed48.png?)
            
            - 渲染管线在应用阶段主要做什么![](https://api2.mubu.com/v3/document_image/24058158_fb9ce85a-a190-448c-95c7-f0ed5bef1610.png?)
            
            - 应用阶段为渲染准备了什么![](https://api2.mubu.com/v3/document_image/24058158_d0f838ff-4ea6-49b3-877a-664a609f307d.png?)![](https://api2.mubu.com/v3/document_image/24058158_c115fe04-7dd4-4252-99e5-0b0edf669afc.png?)
            
            - Drawcall![](https://api2.mubu.com/v3/document_image/24058158_9b22d625-c2bd-4cf1-dc3d-bd1d23280451.png?)![](https://api2.mubu.com/v3/document_image/24058158_33ecb837-b5e7-4caa-9ca3-3f1f88468566.png?)
        
        - 几何阶段
            
            - 知识必备——图元![](https://api2.mubu.com/v3/document_image/24058158_8c5b4ce0-1a5b-47bd-b4b0-94c5a0d6f12c.png?)
            
            - 渲染管线在集合阶段主要做什么![](https://api2.mubu.com/v3/document_image/24058158_c1531047-988a-4f26-a716-32571262a609.png?)![](https://api2.mubu.com/v3/document_image/24058158_8943f660-fb9f-436c-f1a1-f9f469ea9c71.png?)![](https://api2.mubu.com/v3/document_image/24058158_bc73f4f6-23ca-4794-b437-943d4e3c21b1.png?)
            
            - 几何阶段为渲染准备了些什么![](https://api2.mubu.com/v3/document_image/24058158_34095349-29ce-415a-ab1f-db6b15843ef2.png?)
        
        - 光栅化阶段
            
            - 知识必备——像素![](https://api2.mubu.com/v3/document_image/24058158_ba90166e-d9c9-40a7-a611-9e14558e7b5b.png?)
            
            - 知识必备——片元![](https://api2.mubu.com/v3/document_image/24058158_8e99b377-6e99-469d-ed53-a7f1702428b0.png?)
            
            - 渲染管线在光栅阶段主要做什么![](https://api2.mubu.com/v3/document_image/24058158_d2407467-b6f3-4ed4-9709-941b078f3e60.png?)![](https://api2.mubu.com/v3/document_image/24058158_56256525-2300-4783-eb5c-2ce76108c37b.png?)![](https://api2.mubu.com/v3/document_image/24058158_ebc826d7-c156-4a41-d7d9-df3f48f3b64f.png?)![](https://api2.mubu.com/v3/document_image/24058158_f0620eaa-bb38-44af-e505-475c7ebbb773.png?)![](https://api2.mubu.com/v3/document_image/24058158_2f5f05bb-8805-4efe-a452-e679ab34bc00.png?)
            
            - 光栅化阶段为渲染准备了些什么![](https://api2.mubu.com/v3/document_image/24058158_ca4aec0c-299c-44fb-9429-d86b4474c7ba.png?)
    
    - Shader开发是什么
    
    - 如何学习Shader开发
    
    - 相关必备概念
        
        - Graphics API（图形接口程序）
            
            - OpenGL
            
            - DX
            
            - Metal
            
            - Web GL
        
        - 渲染管线和图形接口程序的关系
            - 图形接口程序提供了对渲染管线的控制和管理功能，它是开发者和硬件打交道的中间层
        
        - Shader和图形接口程序的关系
            - Shader属于图形接口程序的一部分
        
        - 不同图形接口程序对Shader开发的影响
            
            - 开发语言不同
                
                - OpenGL  
                    GLSL
                
                - DX  
                    HLSL
                
                - Metal  
                    MSL
                
                - Web GL  
                    GLSL ES
            
            - 坐标系原点不同
- 必备基础
    
    - 数学基础
        
        - 基本数学知识
            - 点和向量
        
        - 线性代数
            - 矩阵
                
                - 基本概念
                    
                    - 线性代数是什么
                        - 研究向量和变换的数学学科
                    
                    - 矩阵是什么
                        
                        - 用来表示和处理的数学工具
                            
                            - 矩阵的数学表示![](https://api2.mubu.com/v3/document_image/24058158_ed5695fb-5768-4e39-c5e7-ede652db166b.png?)
                            
                            - 矩阵在程序中的表示![](https://api2.mubu.com/v3/document_image/24058158_8892a951-5457-4d9c-9cf3-65a9ed7cbe8b.png?)
                        
                        - 帮助我们有效的管理和计算大量的数据
                    
                    - 为什么要学习矩阵
                        - 能在Shader开发利用其进行相关的数学计算
                
                - 矩阵乘法
                    
                    - 矩阵和标量![](https://api2.mubu.com/v3/document_image/24058158_31108034-1b5b-467a-d22e-1b8d9f8bb6a2.png?)
                    
                    - 矩阵和矩阵
                        
                        - 规则
                            
                            - 首先需要判断两个矩阵是否能够相乘
                                - 判断条件:左列右行要相等
                            
                            - 相乘得到的矩阵结构是定死的规则
                                - 结果结构:左行右列
                            
                            - 标量相乘的规则
                                - 左行乘右列再相加
                        
                        - 举例
                            
                            - 可以相乘 1*3 3*2 ==> 左行右列![](https://api2.mubu.com/v3/document_image/24058158_55eb870f-f5ad-43fa-805f-b157cc3d7627.png?)
                            
                            - 矩阵和矩阵的乘法标量相乘![](https://api2.mubu.com/v3/document_image/24058158_5bce6fdc-4259-4c89-f878-42f1d683e82a.png?)
                            
                            - 矩阵和矩阵的乘法的注意事项![](https://api2.mubu.com/v3/document_image/24058158_0a765582-8065-403e-9a29-ead4f91005f6.png?)
                
                - 特殊矩阵
                    
                    - Part1
                        
                        - 方块矩阵
                            - 定义![](https://api2.mubu.com/v3/document_image/24058158_3afccb2c-21ab-4585-a4ff-e319dd6689b5.png?)
                        
                        - 对角矩阵
                            - 定义![](https://api2.mubu.com/v3/document_image/24058158_eb8fe1c8-55eb-4168-c47d-d5adf0bcb300.png?)
                        
                        - 单位矩阵
                            - 定义![](https://api2.mubu.com/v3/document_image/24058158_d3fcdbc4-20dd-4540-b7dd-901991b407f2.png?)
                        
                        - 数量矩阵
                            - 定义![](https://api2.mubu.com/v3/document_image/24058158_8ba5ce15-9d79-4385-dffa-a89b2c4e5940.png?)
                        
                        - 转置矩阵
                            
                            - 定义![](https://api2.mubu.com/v3/document_image/24058158_59197011-9b54-4ac1-b6c1-2f3e18d4dd0e.png?)
                            
                            - 性质![](https://api2.mubu.com/v3/document_image/24058158_3038ece3-bdb0-4e1f-dc3e-830969faf4ef.png?)
                    
                    - Part2
                        
                        - 逆矩阵
                            
                            - 基本概念![](https://api2.mubu.com/v3/document_image/24058158_42674e61-7c3b-462b-f2de-8a16d4b08a46.png?)
                            
                            - 计算矩阵的逆矩阵![](https://api2.mubu.com/v3/document_image/24058158_61688ec7-537e-484b-f2c9-6f999be68597.png?)
                                
                                - 行列式![](https://api2.mubu.com/v3/document_image/24058158_a7925e68-e15d-428e-c37b-553e07ecbea1.png?)
                                
                                - 代数余子式![](https://api2.mubu.com/v3/document_image/24058158_8a663030-676c-4fcf-e7a8-ced5dad2e521.png?)
                                
                                - 标准伴随矩阵![](https://api2.mubu.com/v3/document_image/24058158_54bd34e9-d137-4916-f966-e71b384b32e1.png?)
                                
                                - 逆矩阵
                                    
                                    - 计算方式![](https://api2.mubu.com/v3/document_image/24058158_479450ed-8ff7-4a97-a559-c438d007d316.png?)
                                    
                                    - 重要性质![](https://api2.mubu.com/v3/document_image/24058158_9b32f681-6899-485a-fa3a-8c2f9f6481d6.png?)
                        
                        - 正交矩阵
                            
                            - 基本概念![](https://api2.mubu.com/v3/document_image/24058158_c4361b46-1b42-4262-89af-957815c81e08.png?)
                            
                            - 重要性质![](https://api2.mubu.com/v3/document_image/24058158_6ba7f8c9-1438-499c-f4d4-7ec7a12cd66f.png?)![](https://api2.mubu.com/v3/document_image/24058158_ac7ee757-d357-4c83-8a92-fb8ea3fe2283.png?)
                            
                            - 判断![](https://api2.mubu.com/v3/document_image/24058158_1d889b6b-4fec-41a7-d877-1b08e148b98b.png?)
                        
                        - 行矩阵和列矩阵
                            
                            - 概念![](https://api2.mubu.com/v3/document_image/24058158_e9faffbd-2393-4cfd-dbed-79d7e8bd6646.png?)![](https://api2.mubu.com/v3/document_image/24058158_87b4d145-5ad7-4923-c0d2-ec69b3885f54.png?)![](https://api2.mubu.com/v3/document_image/24058158_e0090159-1b32-46d0-ea7e-543053903603.png?)
                            
                            - 在unity中的使用![](https://api2.mubu.com/v3/document_image/24058158_63f892f0-3dcf-4c26-fc45-863d6bd2239d.png?)![](https://api2.mubu.com/v3/document_image/24058158_a440b8f3-d707-4aeb-c499-e643f085d857.png?)
                
                - 平移缩放旋转变换
                    
                    - 矩阵的几何意义
                        
                        - 几何意义![](https://api2.mubu.com/v3/document_image/24058158_89dff572-87bf-4f4b-87f9-d7f6bf862131.png?)
                        
                        - 变换![](https://api2.mubu.com/v3/document_image/24058158_4ac65671-f482-42ab-b38b-36e6745e6cf7.png?)
                    
                    - 齐次坐标
                        
                        - 是什么
                            - 原本是n维的向量或矩阵用n+1维来表示![](https://api2.mubu.com/v3/document_image/24058158_6f8413af-bf92-4c65-b518-df36c4eb4206.png?)
                        
                        - 为什么
                            
                            - 明确的区分向量和点![](https://api2.mubu.com/v3/document_image/24058158_5d4ab260-4f62-4397-9843-8f55e442cc2d.png?)
                            
                            - 能够表示出平移变换![](https://api2.mubu.com/v3/document_image/24058158_6f2a755f-06d6-4372-ee50-4b49149a9185.png?)
                    
                    - 平移矩阵
                        
                        - 基础变换矩阵的构成规则
                            - 规则![](https://api2.mubu.com/v3/document_image/24058158_30cc8f73-b125-4496-d726-9cec5478a216.png?)![](https://api2.mubu.com/v3/document_image/24058158_366c5113-7948-453c-d50a-0582e9337ccd.png?)
                        
                        - 平移矩阵的构成
                            - 构成![](https://api2.mubu.com/v3/document_image/24058158_eec762af-e7d9-44aa-98a1-f5b122d9c150.png?)
                        
                        - 平移矩阵的计算
                            
                            - 点和点![](https://api2.mubu.com/v3/document_image/24058158_3e63c9b3-e39f-4544-db10-e64171b5e858.png?)
                            
                            - 点和向量![](https://api2.mubu.com/v3/document_image/24058158_cb623321-6975-4b32-fae5-1b835fabab77.png?)
                        
                        - 平移矩阵是否是正交矩阵![](https://api2.mubu.com/v3/document_image/24058158_7dc37953-d032-418b-dfec-093c98c7a142.png?)![](https://api2.mubu.com/v3/document_image/24058158_49e592ac-bd52-4cf2-e590-61a5fb7f676e.png?)
                    
                    - 旋转矩阵
                        
                        - 构成![](https://api2.mubu.com/v3/document_image/24058158_156d2c81-286f-4ca2-98a7-e2a09160544a.png?)
                        
                        - 计算![](https://api2.mubu.com/v3/document_image/24058158_60f4e19d-c278-4dcc-feac-d225f3affda7.png?)
                        
                        - 是否正交![](https://api2.mubu.com/v3/document_image/24058158_8dd06725-e2dc-4de4-a0e2-7db23c8ac866.png?)
                    
                    - 缩放矩阵
                        
                        - 构成![](https://api2.mubu.com/v3/document_image/24058158_bdb7277f-5fbe-4a8d-8e00-2646ffe12654.png?)
                        
                        - 计算![](https://api2.mubu.com/v3/document_image/24058158_6dad435d-7f1a-47a7-f4a0-62c05af6f8f0.png?)
                        
                        - 是否正交![](https://api2.mubu.com/v3/document_image/24058158_5221772e-ff45-4819-c14b-725289166af7.png?)
                    
                    - 复合运算
                        
                        - 什么是复合运算![](https://api2.mubu.com/v3/document_image/24058158_fb7e92df-71d4-43a9-9803-93a6394a2dad.png?)
                        
                        - 计算顺序对结果的影响![](https://api2.mubu.com/v3/document_image/24058158_661cc234-fa85-4011-bcf9-fe6c376a4088.png?)
                        
                        - 在unity中需要遵守的规则![](https://api2.mubu.com/v3/document_image/24058158_cccd01f0-a276-4df8-e3e9-3571ec56a2b2.png?)
                
                - 坐标系变换
                    
                    - 坐标空间的变换
                        
                        - 是什么![](https://api2.mubu.com/v3/document_image/24058158_58c5020a-b13c-4957-8503-addfc17426af.png?)
                        
                        - 为什么有很多不同的坐标空间![](https://api2.mubu.com/v3/document_image/24058158_d62c8ffd-ae64-42ce-b8e7-6c9979ec646d.png?)
                        
                        - 坐标空间的变换![](https://api2.mubu.com/v3/document_image/24058158_d96850ea-e65b-473b-e6b5-2dfb5199431c.png?)![](https://api2.mubu.com/v3/document_image/24058158_03aab2e9-7ebf-46dd-eba7-2c52deaa14a4.png?)
                    
                    - 坐标空间的变换规则
                        
                        - 坐标空间的组成![](https://api2.mubu.com/v3/document_image/24058158_e9b21ccb-3003-415f-f39f-36ebd515035d.png?)![](https://api2.mubu.com/v3/document_image/24058158_a9f7084e-85f0-412c-c4f4-add506f5c3b7.png?)
                        
                        - 坐标之间的变换矩阵![](https://api2.mubu.com/v3/document_image/24058158_d3870224-e839-47e1-bcfc-92f6f417fdd1.png?)![](https://api2.mubu.com/v3/document_image/24058158_a4aa0231-2bf7-4feb-9f71-1a7cdb5da2e9.png?)![](https://api2.mubu.com/v3/document_image/24058158_84f43039-b6df-4b7f-99e8-dfb37f577498.png?)![](https://api2.mubu.com/v3/document_image/24058158_d78a3f59-12f9-454e-b1af-aa703b63c249.png?)![](https://api2.mubu.com/v3/document_image/24058158_989944fc-ca5b-4523-d4c6-0ba802cdbdfc.png?)![](https://api2.mubu.com/v3/document_image/24058158_9b0f4c21-d99b-4cda-b12d-c291d7852460.png?)
                    
                    - 模型空间变换
                    
                    - 观察空间变换
                    
                    - 裁剪空间变换
                    
                    - 屏幕空间变换
    
    - 语法基础
- 开发知识
- 实践知识
- 进阶知识