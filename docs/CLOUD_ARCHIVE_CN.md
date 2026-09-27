# Kaggle → GitHub Release 云端备份（无需本地上传）

本工具只操作两个大型 Kaggle 数据集：

- RADIO: https://www.kaggle.com/datasets/caolitong/tourism-puffin-m1-v3-radio-cache-742
- Geometry: https://www.kaggle.com/datasets/caolitong/tourism-puffin-geometry-training

目标为现有 **Private** 仓库的 Release [archive-20260927](https://github.com/caolitong0717/TSRG/releases/tag/archive-20260927)。已上传的 R14/R16/R17/R18/R19/R20 V3/M0 七个原始 ZIP 不受影响。

## 第一次设置（只需一次）

1. 在 Kaggle [账户设置](https://www.kaggle.com/settings) 的 **API Tokens** 中创建新的 API access token，复制 token 原文（通常以 KGAT_ 开头）。可参考 [Kaggle CLI 认证说明](https://github.com/Kaggle/kaggle-cli/blob/main/docs/README.md)。
2. 打开 GitHub [仓库 Actions Secrets](https://github.com/caolitong0717/TSRG/settings/secrets/actions) → **New repository secret**。
3. Name 填 **KAGGLE_API_TOKEN**；Secret 填刚才的 Kaggle token 原文。不要填整个 kaggle.json，也不要发送到聊天、Issue 或代码中。点击 **Add secret**。
4. 不要修改仓库 Private 状态。工作流会在仓库不是 Private 时停止。

## 启动备份

1. 打开 [Actions 工作流](https://github.com/caolitong0717/TSRG/actions/workflows/archive-kaggle-to-release.yml)。
2. 点击 **Run workflow**，Branch 保持 **main**。
3. dataset 先选 **radio**。version 默认留空，脚本将从 Kaggle 元数据识别当前版本并固定下载这一版本；如果无法识别，可以到 Kaggle 确认版本号后填入数字。
4. 运行完成出现 **BACKUP SUCCESS**，检查 [Release Assets](https://github.com/caolitong0717/TSRG/releases/tag/archive-20260927) 中的 RADIO 分卷及其 MANIFEST.json。
5. 再运行一次，dataset 改选 **geometry**。不要把两个数据集同时运行。

仓库自动提供有限的 GITHUB_TOKEN 写入权限；你无需额外创建 GitHub Personal Access Token。私有仓库 Actions 运行可能消耗账户的免费运行分钟数，超出配额可能产生费用或被暂停。

## 完整性、存储与版本注意

流式下载每次在云端最多暂存一个约 900 MiB 分卷；一卷上传成功、确认 GitHub 返回的 SHA256 digest 后，会删除暂存分卷。不会先下载完整数据 ZIP 到 14 GB 的 runner 硬盘。所有分卷和 manifest 都保存在 Private Release Assets，程序不会覆盖已存在的不同哈希文件。

每个 MANIFEST.json 包含固定 Kaggle 版本、下载时间、整个服务器提供的 ZIP 字节数与 SHA256、每个分卷的字节数与 SHA256、以及恢复顺序。它记录的是**本次 Kaggle 服务器生成的 ZIP 字节流**，可能与此前在 G 盘下载的 ZIP 容器字节不同；不能仅因为两者整包 SHA 不同就认定数据文件发生改变。本操作不宣称逐个 ZIP 成员通过 CRC，也不等于在另一环境重跑训练。

GitHub Release 单文件须小于 2 GiB；本工作流的分卷是 900 MiB。首次运行需要有效 Kaggle 数据集读取权限、GitHub Actions 允许执行，以及能访问 Kaggle 的云端网络。如果某次失败，仅在清楚失败原因后重试；程序不会使用会删除旧附件的 --clobber。

## 恢复数据

下载某一数据集的全部同版本 .part001、.part002……和 MANIFEST.json，放进同一目录。按 manifest 的 sequence 顺序，**以二进制方式拼接**，生成其 archive_name_when_reconstructed 所指定的 ZIP。最后执行 SHA256 检查，结果必须等于 manifest 的 archive_sha256，之后才能解压使用。不能只下载第一个分卷，也不要把 .part001 单独改名成 .zip。

原始 G 盘 ZIP 与 Kaggle 原始 Dataset 仍需保留；Release 是额外的异地备份，不改变 Kaggle 或本地数据。
