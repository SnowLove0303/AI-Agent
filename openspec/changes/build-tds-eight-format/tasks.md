# Tasks

- [x] 建立独立 `TDS Skill` 目录、版本文档和 manifest。
- [x] 复制并登记四个用户 TDS `.doc` 模板的来源路径、大小和 SHA-256。
- [x] 将四个 `.doc` 转换为 active `.docx`，记录转换工具和 hash。
- [x] 对四个 active 模板执行表格/合并/grid width/段落字符属性/页眉页脚/包部件结构快照与几何审计。
- [x] 建立统一 TDS semantic model、字段别名、四变体 registry、映射白名单和 fail-closed 规则。
- [x] 将原始证据、标准化值和模板呈现值分层，并为字段/性能行增加 provenance 与 decision ledger。
- [x] 增加 Agent 判断协议：强标注框架作为硬约束，别名/示例/历史案例作为候选线索，客户含义歧义进入判断门。
- [x] 明确英文只从标准化模型进行专业技术翻译，英文源文件只作证据和交叉校验。
- [x] 将性能表改为 source-led：保留源行顺序、原始标签、限定条件、值、单位和测试方法；裁剪未使用模板示例行。
- [x] 禁止限定条件不一致的语义映射，补齐源行—输出行 parity 数据和审计阻断。
- [x] 支持更多性能指标行和更多产品特性段落的模板样式克隆扩展，并审计新增项不改变既有骨架。
- [x] 实现一次抽取、一次映射、四模板 fresh clone 原位覆写的 CLI。
- [x] 实现 DOCX→PDF 单一路径、DOCX/PDF 配对追溯和八文件包审计。
- [x] 迁移可复用的 TDS 测试模式，补齐四变体模板基线、映射、示例事实隔离、PDF 派生和 ZIP 完整性测试。
- [x] 用真实源文件回放并保留失败证据；不以模板示例事实代替。
- [x] 增加真实源文件逐行 parity、限定条件保真、模板示例行裁剪和视觉回归审计。
- [x] 运行 OpenSpec 校验、TDS 全部自动测试、MSDS/V2.9 继承审计、模板 geometry audit、semantic/company parity、八文件/ZIP 完整性审计；本次真实 CN-only 回放按发布闸门正确阻断 EN 缺失。
- [x] 生成独立 TDS v1.3.0 发布 ZIP，提交并推送 `feature/msds-tds-eight-format`。
