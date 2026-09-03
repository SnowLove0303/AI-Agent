# MSDS 产出物审计清单 v1.0

每个规则 ID 必须恰好生成一条 evidence record。清单是审计运行的覆盖基线；未执行项不能默认为通过。

| ID | 类别 | 严重性 | 必查内容 | 通过条件 |
|---|---|---|---|---|
| ID-001 | package_evidence | B0 | 八文件矩阵与非零字节 | 4 DOCX + 4 PDF，各槽位恰好一个 |
| ID-002 | source_semantics | B1 | 产品和源身份 | 产品标识、源记录、输出矩阵一致 |
| SRC-001 | source_semantics | B1 | 源事实保真 | 每项事实能回到源 semantic payload |
| SRC-002 | source_semantics | B1 | 示例/补充说明泄漏 | 无 PEA-4139 示例事实和草稿话术 |
| SRC-003 | source_semantics | B1 | 语义归类 | 数据进入正确 Section/endpoint |
| S2-001 | source_semantics | B1 | Section 2 | 象形图、标签 tip、换行、无数据行、排序 |
| S3-001 | source_semantics | B1 | Section 3 | 每个成分严格一行 |
| S8-001 | template_control | B1 | Section 8 | 手部防护、8.2 工程控制存在，8.1 父项锁定 |
| S9-001 | source_semantics | B1 | Section 9 | 缺失属性行不展示，剩余项连续重排 |
| S11-001 | source_semantics | B1 | Section 11 | 结构化毒理至 11.10，已有数据不丢失 |
| S14-001 | template_control | B1 | Section 14 | 运输字段按要求逐项换行 |
| TPL-001 | template_control | B0 | 模板 lineage/geometry | CN/EN 对应模板 hash/snapshot 和结构一致 |
| TPL-002 | template_control | B0 | mutation whitelist | 只有白名单允许的值域/整行变更 |
| TPL-003 | template_control | B0 | 锁定骨架 | 序号列、标签列、合并、宽度、受保护格式不变 |
| DOCX-001 | docx_visual | B1 | DOCX 页面 QA | 无截断、溢出、空白页、缺图 |
| DOCX-002 | docx_visual | B2 | DOCX 可读性 | 关键 Section 和客户文字可读 |
| PAR-001 | four_format | B1 | 语义 parity | 四变体产品事实和章节 presence 等价 |
| PAR-002 | four_format | B1 | company parity | 仅获准公司字段不同 |
| PDF-001 | pdf_quality | B0 | PDF 派生 | 每个 PDF 来自对应最终 DOCX |
| PDF-002 | pdf_quality | B1 | PDF QA | 页数、尺寸、文字、图片、关键页通过 |
| PKG-001 | package_evidence | B1 | 发布包清洁度 | 单一 `MSDS Skill/` 根、manifest 精确、无缓存 |
| PKG-002 | package_evidence | B1 | legacy/release coverage | V2.9 inheritance 和必需 release audits 通过 |

## 审计顺序

1. 身份和八文件矩阵
2. 源事实与 semantic model
3. 模板 hash/geometry/白名单/锁定骨架
4. Section 2、3、8、9、11、14 特例
5. 四格式与公司 parity
6. DOCX 逐页 QA
7. DOCX→PDF 派生与 PDF 逐页 QA
8. V2.9 inheritance、ZIP、manifest 和证据覆盖
9. 评分、阻断仲裁和最终报告

## 未通过处理

任何规则失败必须记录 observed、message 和 evidence path。任何缺失、重复、工具异常或未执行的规则必须标记为 `NOT_CHECKED`/`ERROR`，不可手工改成 PASS。
