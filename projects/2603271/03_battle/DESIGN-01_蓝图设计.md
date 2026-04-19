# DESIGN-01 蓝图设计（S3）

项目：AF-20260327-001  
名称：bp-reporting-templates 复刻项目  
状态：RUNNING（进入开发前设计冻结）

## 1) 设计目标
在保持“BP原文严谨映射”的前提下，实现可执行、可测试、可审计的模板规范生成链路。

## 2) 端到端流程
```text
用户指令
  -> input_handler（识别对象）
  -> period_selector（列周期并选择）
  -> template_selector（列月/季/半年/年并选择）
  -> api_client（主路径拉取BP）
      -> 失败时 fallback_loader（文件回退）
  -> parser（统一BPData结构）
  -> template_manager（加载目标模板）
  -> filler（填充第2章为核心）
  -> reviewer（合规审查 + 颜色预警）
  -> renderer（输出Markdown）
```

## 3) 模块设计
1. `input_handler.py`
   - 解析组织/个人等基础意图
2. `main.py`（selector逻辑）
   - 周期列表展示与选择（period_id）
   - 模板类型列表展示与选择（月/季/半年/年/四套）
3. `api_client.py`
   - 封装 API 4.4/4.5 主链路
   - 4.13 失败时触发 fallback
3. `parser.py`
   - 统一转为 `BPData / BPGoal / KeyResult`
4. `template_manager.py`
   - 装载四类模板与通用规则
5. `filler.py`
   - 重点：第2章“BP目标承接”严格引用原文
6. `reviewer.py`
   - 校验：编码对齐、数字锚点、衡量标准、阈值判断、零容忍项
7. `main.py`
   - 编排并行生成 + 重试策略 + 结果聚合

## 4) 并行与失败策略
- 门禁：未完成“周期选择 + 模板选择”时不执行生成
- 并行：仅按用户请求子集并行（避免不必要开销）
- 审查失败：自动重试 2 次；仍失败返回“失败项清单 + 原因”

## 5) 数据与规则约束
- 禁止编造：编码/数字锚点/衡量标准必须可追溯到 BP 原文
- 颜色阈值：
  - 财务：红>5%、黄3-5%、绿<3%
  - 得分：红>10%、黄5-10%、绿<5%
  - 节点：delay>2周为红
- 零容忍：重大合规事故、签约率<100%、奖金发放delay

## 6) 可测试验收用例（设计阶段定义）
- Case-01：`生成四套` => 输出4份Markdown
- Case-02：`只做季报` => 仅1份季报
- Case-03：API 401 => 自动走文件回退
- Case-04：缺失锚点 => 审查失败并列出缺失项
- Case-05：零容忍命中 => 直接红色预警

## 7) 开发拆解（S4输入）
- D1：输入解析 + 模板选择器
- D2：API/回退双通道 + parser
- D3：filler/reviewer 主逻辑
- D4：主编排 + 回归测试

## 8) 交付物（下一阶段）
- `04_execution/` 下代码实现
- `tests/` 回归测试清单
- `05_closure/ACCEPTANCE.md` 验收记录