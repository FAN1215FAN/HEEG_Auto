# 目录说明

- `artifacts/inspectors`：控件树导出文本
- `artifacts/logs`：运行日志
- `artifacts/reports`：pytest HTML 报告、单次运行 JSON 报告和 Word 报告
- `artifacts/screenshots`：失败截图与手动截图
- `docs`：项目文档
- `scripts`：兼容性或扩展脚本入口预留
- `src/heeg_auto/config`：项目配置、控件定位、YAML 用例和中文行式脚本
- `src/heeg_auto/core`：驱动、基础页面、动作运行器、日志、行式脚本编译器、报告生成器
- `src/heeg_auto/pages`：页面对象
- `tests`：pytest 用例与公共 fixture
- `tools/inspectors`：控件树导出工具

## 功能代码定位

- 启动入口：`run_demo.py`
  负责调用默认用例执行，并输出执行结果与报告路径。
- 控件树导出入口：`run_inspector.py`
  负责导出控件树，辅助定位控件与补充 AutomationId。
- 项目配置：`src/heeg_auto/config`
  保存应用路径、默认用例、控件定位、产物目录等配置。
- 用例脚本：`src/heeg_auto/config/cases`
  保存结构化 YAML 用例和中文行式脚本用例。
- 动作执行：`src/heeg_auto/core/actions.py`
  封装点击、输入、下拉选择、单选、断言、截图等通用动作。
- 用例运行：`src/heeg_auto/core/case_runner.py`
  负责加载用例、变量替换、顺序执行、步骤结果采集和异常处理。
- 中文脚本编译：`src/heeg_auto/core/line_dsl.py`
  负责把中文行式脚本转换为统一动作结构。
- 驱动与截图：`src/heeg_auto/core/driver.py`
  负责启动应用、识别主窗口以及失败取证。
- 报告生成：`src/heeg_auto/core/reporting.py`
  负责将执行结果生成 JSON 报告和 Word 报告。
- 页面对象：`src/heeg_auto/pages`
  负责主界面和“创建患者”区域的页面级操作封装。
- 自动化测试：`tests`
  保存 DSL、报告和典型流程的测试用例。
- 检查器工具：`tools/inspectors`
  保存导出控件树等辅助脚本。
