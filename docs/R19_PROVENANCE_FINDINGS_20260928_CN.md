# R19 训练素材溯源阶段记录（2026-09-28）

本记录仅用于**科研档案**，不属于用户软件包。依据先前存档的 `DATASET_README.md`、2026-09-24 Kaggle 原始数据检查文本和已归档的 R19 实际执行代码；完整源数据的逐行审计尚未在当前轮重新执行。

## 可以追踪的来源

原始 Tourism-Puffin 图片筛选集为 1,425 张、100 个旅游地点，按地点划分 1,018 train / 168 validation / 239 test。存档的 `DATASET_README.md` 记载：候选取自 Wikimedia Commons，经过元数据、CLIP 辅助排序、人工视觉审核、质量和近重复检查；准入许可为 CC0、公有领域、CC BY、CC BY-SA；`metadata/trainable_manifest_final.csv` 保存图片来源、许可链接、作者、许可审核字段、图片 SHA256；另提及 `ATTRIBUTION.csv`。

原始 R19 实际执行脚本从 `tourism-puffin-geometry-training/geometry_training/geometry_train_combined.jsonl` 读入 742 条训练项：526 条 `geocalib_pseudo_parameter_filtered`，216 条 `projection_truth`。此前对 `panorama_truth/manifest.csv` 的检查显示，216 条分别来自 Soissons Cathedral 和 Laon Cathedral 两张内景全景的投影，各 108 条，均为 `train_aux`。该来源清单记录 Commons 页面、作者 Diliff、CC BY-SA 3.0 和 `py360convert.e2p` 投影信息。此信息不能被描述为 216 张独立照片。

## 未完成的核验

需在原始私有 Kaggle 数据集上，对 **526 个训练 image id 与 1,425 行 manifest** 实际连接核对，并对每一条训练图检查许可名称、作者、许可 URL、图片来源和校验字段；重新验证两个辅助全景的全部 source_sha1 和署名；检查 `ATTRIBUTION.csv` 是否在原始数据包且与训练实际图片对应。暂未识别最初逐条图片下载和人工审核的具体执行人；不能由 AI 对话的参与推断版权所有权。开放图片的许可不自动等于公开 LoRA 模型权重的完整授权，还需研究成员意见和上游适用条款核查。

## 审计程序

私有研究分支新增 `tools/audit_r19_training_sources.py`，可在用户 Kaggle 实际数据集上生成 `r19_source_rights_summary.json` 与 `r19_source_rights_flags.csv`，不导出原始照片。对应 `tests/test_r19_source_audit.py` 使用合成数据进行逻辑检查。机器核查只确认来源清单的**结构和记录完整性**，法律许可判断须另行完成。

公开用户仓库 `TSRG-inference` 及 R19 二进制权重在完整授权核验之前仍保持私有。


## 2026-09-28 用户上传原始四表后的逐行机器核验补充

用户从 Kaggle 原始数据集导出四份元数据文件的 ZIP，SHA256 为 `44497031213f740d18a80bd3b0a00d85a8735e797bd64593fb9841c9538c3cb2`；本轮实际读取 CSV / JSONL，对 1,425 行来源清单、1,425 行 ATTRIBUTION、742 条 R19 组合训练记录及 216 行辅助全景来源清单做了跨表关联检查（不是只使用先前记忆或摘录）。

结果：526/526 主训练 ID 能通过图片 SHA1 关联主清单且类别/地点/训练划分及图片相对路径一致；216/216 辅助 ID 能对应其来源清单，其中 Soissons 和 Laon 两张 Diliff 原始全景各生成 108 条投影。主清单与归属清单按 `local_sha256` 匹配 1,425/1,425，所比较的来源、作者、许可及划分字段无不一致。1,425 行 `license_audit` 和 `file_validation` 全部为 `pass`。训练/验证/测试共 1,018/168/239，地点数 72/12/16，各组地点交集为 0。全部源许可类型位于文档的 CC0 / Public Domain / CC BY / CC BY-SA 范围；主训练 526 行中 CC BY-SA 368、CC BY 93、CC0/公有领域 65。结构审核标记 0 项。

维护备注：20 条 CC BY-SA 3.0 许可 URL 使用旧 `http://creativecommons.org/licenses/by-sa/3.0/`，其中 6 条进入主训练。这是有效的具体许可证路径而不是未填写许可；建议未来公开清理版时规范化到 HTTPS，不修改原始存档。导出的原始 CSV 包含本地 Windows 绝对路径等内部字段，不要直接作为公开附件。

审核范围限定：本轮 ZIP 未包含原始照片字节，故只能验证图片哈希字段的格式/跨表一致性，不能重新计算 1,425 张图片实际 SHA256；除两张辅助全景外，没有对全部 Wikimedia Commons 来源页面进行实时逐一复核；资料完整不自动证明 LoRA 再分发许可。R19 公开权重仍需要共同作者/成果归属与上游条款核验，并用实际二进制重新校验冻结模型 SHA256。原科研档案与使用仓库继续 Private。
