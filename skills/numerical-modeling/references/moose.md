# MOOSE 应用操作

用于 MOOSE 及其物理应用；应用对象、版本、环境和数值阈值从当前项目确定。

## 应用与方程

- 确认应用可执行文件、MOOSE 版本/commit、编译模块、运行环境、主输入和依赖。已有运行入口可复用，没有包装器时直接使用实际应用，不新建强制框架。
- 优先查同版本应用源码、对象文档及匹配的 tests/examples。框架存在某个类不代表当前应用已注册它；用该应用支持的 `--help`、`--dump`、`--json` 或输入工具核实对象和参数。
- 将方程项、本构、初边值与耦合对应到适用的 Physics/Action、Kernel、Material、BC/IC 等对象。只有现有对象不足且任务包括开发时才新增 C++，检查对象注册、导数、Jacobian 和状态变量。
- 核对 HIT 块、include、变量与单位、block/boundary、网格和数据库引用及重复定义。先检查实际应用支持的输入选项；静态阅读不能代替程序接受输入。

## 求解与记录

按任务需要使用当前应用输入检查与主模型求解，调用形状如下，实际程序、输入和输出位置由项目替换：

```text
<application> -i <main_input> --check-input
<application> -i <main_input> Outputs/file_base=<result_base>
```

输入检查不是完整求解，也不要求在每次结果查看前重复。采用实际应用支持的线性/非线性方法、预条件、时间积分、变量尺度、耦合容差和 TimeStepper，记录接受步长及拒步原因。

`IterationAdaptiveDT` 按迭代难度调整步长；它不直接保证目标关注量的时间离散误差足够小，仍按验证计划检查时间精度。[^1]

保存发生变化的输入、依赖、覆盖参数、软件版本和实际日志，并关联结果目录。修改后复查受影响部分，已证明适用的结果不一律重跑。

## MultiApps、Transfers 与状态

核对源/目标变量含义、空间区域、单位、积分权重、映射方法、执行时机和交换守恒。按耦合方案核对时间窗、交换时刻及同步或明确偏移关系，允许已设计的子循环和稳态子应用。拒步、回退和恢复必须保持材料、子应用及交换状态与耦合方案一致，不能仅重设主应用时间。[^3]

区分导入已有场、restart 和 recover。场文件通常不等于完整 checkpoint；按目标应用和同版本文档确认网格、解向量、材料与时间积分历史的保存和恢复。旧解可作稳态猜测，但不自动成为新增耦合的真实瞬态初态。[^2]

对解析或制造解可使用当前应用可用的误差 Postprocessor，例如适用的 L2 误差、单元尺寸及时间步记录；积分守恒、反力或交换量根据对应物理定义选择。具体误差方法见 [verification.md](verification.md)。

## 来源

[^1]: Idaho National Laboratory. [IterationAdaptiveDT](https://mooseframework.inl.gov/source/timesteppers/IterationAdaptiveDT.html)。
[^2]: Idaho National Laboratory. [Restart and Recover](https://mooseframework.inl.gov/application_usage/restart_recover.html)。
[^3]: Idaho National Laboratory. [TransientMultiApp](https://mooseframework.inl.gov/source/multiapps/TransientMultiApp.html)。
