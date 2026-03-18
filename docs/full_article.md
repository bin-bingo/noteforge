# 全网第一只模拟电路龙虾（下）

> 🔗 原文：https://mp.weixin.qq.com/s/PLryvyOiitMWh6iy05BEyA
> 📅 2026-03-17

---

昨天的文章爆火，阅读量直接达到了1万+，关注人数超过了1000人。这么高的转换比，是一种认可，是一种激励。

可见，天下英雄苦模拟电路久矣！

---

上篇讲了什么是技能包（Skill），以及第一个技能 ngspice 是怎么回事。这篇讲二技能 gmoverid，以及大家关心的模型问题。

## 01 二技能：gmoverid

在 gmoverid 技能里，有两条工作流：**表征**（根据工艺模型，得到特性曲线）和**设计**（根据设计指标，得到管子尺寸）。

![gmoverid 头图](extracted_images/img_000.png)

在表征部分，这个 skill 有一套模板代码，能进行三套仿真：

**第一，IV 特性。** 扫描 Vgs 或者 Vds，观察电流曲线。

![IV 特性](extracted_images/img_002.png)

**第二，gm/ID 扫描。** 把 gm/ID 作为统一设计变量，将过驱动电压、单位宽度电流、速度指标和内在增益之间的关系可视化。

![gm/ID 扫描](extracted_images/img_003.png)

**第三、栅电容图。** 扫描 Vgs，记录 Cgg、Cgs、Cgd、Cgb。

![栅电容图](extracted_images/img_004.png)

**用 Agent 的极大便利之处是——这些代码是参考，不是边界。** Agent 很容易在此基础上泛化。

### 设计部分

通过目标性能指标确定所需 gm/ID，再由对应曲线反查晶体管的电流密度、尺寸参数或者工作点。

![设计流程](extracted_images/img_005.jpg)

AI 自己写了一套 design_gmoverid.py 代码，五百多行。里面有一个 GmIdTable 类，封装了 gmoverid 查表的各种操作。

### 双重核查

**数值检查（人类经验）。** 弱反型极限在不在合理范围、Id/W 有没有单调性。

![数值验证](extracted_images/img_006.png)

**视觉检查（多模态模型）。** 把图片直接扔给大模型看，看曲线是否平滑、是否有异常凸起。

![视觉检查](extracted_images/img_008.png)

**这是玩具和工具的分水岭。** 能跑出结果，不叫工具。跑出结果还能自己判断对错，才叫工具。

### 被动技能：transistor-models

模型来自亚利桑那州立大学（ASU）维护的 PTM 项目，开源的预测性晶体管模型。不能用来流片，覆盖体硅 65~180nm 到 7nm FinFET。

![PTM 模型](extracted_images/img_016.png)

---

> 🔗 项目：https://github.com/Arcadia-1/gmoverid-skill
