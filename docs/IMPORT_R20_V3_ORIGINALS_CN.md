# 将 R20 V3 原始 Kaggle 文件移交到 GitHub

**状态：等待 Kaggle 原件导出。** 当前仓库中的 `results/r20_v3/` 保存了原始控制台日志和明确标注的提取结果，尚不包含 Kaggle 原始 JSON/CSV 文件。

1. 在 Kaggle 打开你自己的 Notebook，右侧点击 **Add Input**，添加 `caolitong/tourism-puffin-r20-one-time-batch1-r11-v3` 数据集。
2. 打开本仓库的 [导出脚本](../tools/export_r20_v3_originals.py)，把文件的完整 Python 内容复制到 Kaggle 一个代码单元中运行。**不需在个人电脑安装 Python，也不用重新执行 R20 模型推理。**
3. 脚本读取原始文件并逐字节检查 ZIP 打包的一致性，输出 `/kaggle/working/TSRG_R20_V3_Kaggle_ORIGINALS.zip` 和单独标注的导出端 SHA256 审计文件。
4. 从 Kaggle 的 Output 目录下载该 ZIP，作为附件上传到本对话。收到原件后即可把各个原始文件按原名称提交到私有 GitHub 仓库，并与 ZIP/原 Kaggle 清单核对。

必需文件：`R20_V3_protocol.json`、`R20_V3_final_verdict.json`、`R20_V3_final_predictions_reference.csv`、`R20_V3_sha256_manifest.json`。脚本还会纳入同目录中实际存在的汇总及 M0/R19 状态与预测文件。打包内容不包含原始照片、模型权重或训练缓存。

注意：`EXPORT_LOCAL_SHA256_AUDIT.json` 是导出时计算的本地审计记录，**不是** Kaggle 原始 `R20_V3_sha256_manifest.json`。正式上传前应检查逐样本 CSV 是否包含不可公开的私人路径、图像来源或其他受限字段，仓库保持 Private。
