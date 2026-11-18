# COMSOL 与 MPh 操作

用于 `.mph`、COMSOL Java API 和 MPh。采用项目确认的 COMSOL 版本、执行环境、资源和目标研究，不自动选择最新安装版本或固定核数。

## 主模型、节点与结果绑定

修改前保存可恢复副本。只读检查 component、geometry、selection、material、变量、耦合、physics、multiphysics、study、solver、dataset、探针及导出设置；记录真实 tag 与物理意义。

沿“dataset → solution → study/solver → 参数与时间范围”确认目标结果，核对最终启用方程和求解版本。标签和 `dsetN` 只是标识，不按“解 2”或最大编号偏好选解。修改后检查属性被当前版本接受，以及研究、求解器、边界选择和数据集仍指向正确对象。

保留已有边界和求解节点，除非已查明要替换的对象、活动状态及依赖。不要默认删除默认分离组，也不要为消除未知状态无条件“先删后建”；需要替换时备份、限定节点并复查变量覆盖和引用。

## 方程与初边值

明确每个变量代表相浓度、总体积浓度、压力、位移还是相变量，以及对应积分测度。相指标改写后重新推导符号；对流、扩散、界面、弱式源项分别检查单位、法向和积分收支。

Coefficient Form PDE 的边界项应按当前版本通式及实际系数代入推导。不能将旧模型的 `g` 表达式作为通用自由流出公式；核对 `q`、约束反力、非对流通量和外流/反流条件。[^1]

Henry 常数明确浓度/压力定义和单位；相分配与反应动力学分开建模。界面质量源或相一致通量必须有方程依据、正确定位和全局收支，不以调幅掩盖符号或重复计量错误。

初值、加载与约束相容性按实际物理判断。稳态初始化、延续、阻尼或平滑具有适用条件，不能擅自改变真实瞬态的物理初态和加载历史。

## 求解器与 API

- 优先复用项目脚本及 MPh 高层操作，必要时访问 Java API；从版本匹配文档或实际节点属性核实 tag、参数名、取值和重载。
- 重载歧义时检查期望类型，可以按 API 使用字符串或合适数组，不盲目更换物理数值。
- 分离求解需核对变量、场及分量选择。`segvar`、`segvarspec`、`segcomp` 的含义按版本文档确定，不能套用旧案例的名称或固定设置顺序。[^2]
- 分组线性求解器要处于该版本允许的容器，并被对应步骤正确绑定。检查活动求解树，不因节点存在就认定实际使用。
- `LowerLimit`/`UpperLimit` 是相关分离求解控制；检查当前版本节点语义及最终接受的解，不假定它们对每个结果时刻作严格裁剪，也不靠事后裁剪证明解正确。[^3]
- 瞬态输出时间与内部时间步分开记录。时间精度按容差/最大步长或实际步长对照检验，不能只增加输出时刻。[^4]

## MPh 会话与目标研究

先确认现有会话是 stand-alone、已连接服务器还是本任务启动的服务。MPh `start` 的版本选择和进程单例需按已安装版本核对；明确项目版本与核数，不依赖无参数调用自动选择最新版。[^5]

公共 API 的树检查是 `mph.tree(model)`，不是 `model.tree()`。选择目标研究执行 `model.solve(study)`；不带研究参数可能求解所有研究。实际参数形式和研究名称按已安装 MPh 及模型核实。[^6]

清理与会话模式匹配：仅对实际服务器连接采用相应断开操作；stand-alone 不无条件调用 `disconnect()`。只停止本任务拥有的服务或进程，不关闭共享 COMSOL 会话；版本或会话模式变化不能靠在同一进程重复 `start()` 随意切换。[^5]

## 数值结果

从确认的目标解导出原始数值：实际时刻/参数、变量极值及其位置、域/相掩膜、积分储量、边界通量、源汇和主要评价指标。全域定义但只在某相有物理意义的量，应说明相内与相外的解释，不根据全域色图直接下结论。

解析/基准、空间与时间误差及守恒按 [verification.md](verification.md) 执行。有效中断恢复要核对 `.mph` 或其他保存方式是否包含所需历史；保存场结果不自动保证完整续算。

## 来源

以下链接为所示版本的官方文档或 MPh 项目文档；实际操作以安装版本为准。

[^1]: COMSOL 6.4. [Coefficient Form PDE](https://doc.comsol.com/6.4/doc/com.comsol.help.comsol/comsol_ref_equationbased.32.009.html)；[约束反力与通量](https://doc.comsol.com/6.4/doc/com.comsol.help.comsol/comsol_ref_equationbased.32.017.html)。
[^2]: COMSOL 6.4. [SegregatedStep API](https://doc.comsol.com/6.4/doc/com.comsol.help.comsol/comsol_api_solver.51.43.html)。
[^3]: COMSOL 6.4. [Segregated](https://doc.comsol.com/6.4/doc/com.comsol.help.comsol/comsol_ref_solver.36.201.html)；[LowerLimit API](https://doc.comsol.com/6.4/doc/com.comsol.help.comsol/comsol_api_solver.51.32.html)。
[^4]: COMSOL. [Controlling the Time Dependent Solver Timesteps](https://www.comsol.com/support/knowledgebase/1254)。
[^5]: MPh. [session 源码](https://mph.readthedocs.io/en/stable/_modules/mph/session.html)；[Client 源码](https://mph.readthedocs.io/en/stable/_modules/mph/client.html)。
[^6]: MPh. [Model API](https://mph.readthedocs.io/en/stable/api/mph.Model.html)；[tree API](https://mph.readthedocs.io/en/stable/api/mph.tree.html)。
