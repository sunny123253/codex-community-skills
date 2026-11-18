# OpenFOAM 操作

先确认项目使用的发行分支、版本、运行环境和实际 solver/module；不能默认 WSL、某个发行版本或固定结果目录。

## 方程、网格与字典

识别单/多相、可压缩性、层流/湍流、传热、组分、反应、重力、表面张力和网格运动/加密需求。核对实际求解器支持的方程；传统求解器名称或 `foamRun` 模块按当前分支版本选择。[^1]

复用项目 case，检查 `0/`、`constant/`、`system/` 及依赖。各场 dimensions、边界名称、物理条件、材料字典、`controlDict`、`fvSchemes` 和 `fvSolution` 需与版本及求解模块匹配，不能将旧 `transportProperties`/`turbulenceProperties` 文件名作为所有版本固定要求。

网格按真实几何和重要梯度选择；只有新建或确实改变网格时才生成相应网格并 `checkMesh`。`setFields` 仅用于需要的初始区域设置；恢复已有有效结果或检查完成状态时，不重新生成网格或覆盖初始化字段。

## 求解与结束条件

数值格式、线性求解器、压力—速度耦合、松弛及迭代控制根据方程和版本设定。按需检查 Courant 数、相分数 Courant 数、实际 `deltaT`、方程残差、压力校正、连续性、质量及相分数范围。允许正常迭代和既定步长适应。

- 瞬态任务：核对目标物理时间、每步收敛、实际步长与时间误差，以及相应守恒。
- 稳态任务：核对残差、主要关注量稳定和守恒，记录迭代数和结束原因。时间字段可能只是迭代计数，达到 `endTime` 不独自证明收敛；残差控制允许在其前正常结束。[^2]

日志正常结束和结果场存在只证明对应运行范围，不能替代数值误差与物理检查。已完成且未受修改影响的检查可复用；输入检查或 dry-run 仅在实际需要且当前版本支持时使用，不作为固定预备模拟。

## VOF、传质与动态网格

相分数定义和入口相态与项目相名一致，不假定所有 case 都叫 `alpha.water`。表面张力和界面过程可能要求小实际步长；先检查相关尺度、数值方法及压力/相分数迭代，不任意改变物理过程来加快运行。

标准不可混溶 VOF 求解器本身不提供任意溶解、组分交换或化学反应模型；根据科学问题选择具有相应守恒方程的求解器或扩展，并验证交换源项。第三方求解器不是唯一必选方案。[^3]

移动流体界面不自动要求移动网格。动态网格可以服务于几何运动，也可以用于自适应加密；固定几何中的界面 AMR 是允许的。核对实际动态网格类、场映射、通量修正和守恒，不机械限定为边界运动。[^4]

## 并行、结果与恢复

采用项目实际 MPI 或调度器入口。需要分区时准备正确的 `decomposeParDict` 并分解，进程数与分区相符；是否并行以实际启动和日志进程数确认，不强制启动命令必须包含某一种 MPI 前缀。需要统一后处理时再按版本重构，不对未变化结果反复分解/重构。

保存有效时间目录、必要的网格与分解状态。续算选定实际有效时间，并检查字段、网格、材料与模型历史；修改此前演化的方程或条件不能仅从旧末时刻开始。不要为查看结果删除时间目录或调用重新初始化。

对目标解采样、积分和导出，记录时刻、参数、剖面/区域及单位。解析/基准、网格和时间精度方法见 [verification.md](verification.md)。

## 来源

[^1]: OpenFOAM Foundation. [模块式求解器说明](https://openfoam.org/release/11/)；[v13 foamRun 源码](https://cpp.openfoam.org/v13/foamRun_8C_source.html)。
[^2]: OpenCFD. [稳态计算教程](https://www.openfoam.com/documentation/tutorial-guide/3-compressible-flow/3.1-steady-turbulent-flow-over-a-backward-facing-step)；[case termination](https://doc.openfoam.com/2306/tools/processing/numerics/solvers/case-termination/)。
[^3]: OpenCFD. [Standard solvers](https://www.openfoam.com/documentation/user-guide/a-reference/a.1-standard-solvers)。
[^4]: OpenCFD. [dynamicRefineFvMesh](https://api.openfoam.com/2312/classFoam_1_1dynamicRefineFvMesh.html)。
