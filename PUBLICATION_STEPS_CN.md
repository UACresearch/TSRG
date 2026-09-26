# GitHub 发布操作（首次公开前检查）

1. 在 GitHub 新建一个空仓库，建议名称 `TSRG`，先设为 **Private**，且不要勾选自动生成 README / LICENSE / .gitignore。
2. 将本压缩包解压，按原目录整体上传。确认项目结构与 `README.md` 一致，且没有上传模型权重、旅游照片、数据缓存、私密文件。
3. 先运行 `python -m pip install -r requirements-dev.txt` 和 `python -m pytest -q`；通过的是独立逻辑单元测试，不能解释成模型已完整复现。
4. 按 `RELEASE_CHECKLIST.md` 审查 R20 原脚本来源、共同作者许可及数据再分发权。若尚未取得原脚本的发表许可，删除 `reproduction/r20_saved_source_exact.txt` and `reproduction/r20_syntax_repaired_UNVERIFIED.py` 及对应 hash，再说明公开内容为独立方法代码。
5. 对照 Kaggle 永久存档核实结果文件和源代码 hash，补全客观实测结果后再发布数值；不要把当前尚未取得的结果填进 README。
6. 审核通过后将仓库设为 Public；添加固定 release tag，例如 `v1.0-r20`。之后新增优化使用独立分支，不改写冻结的历史协议。

该包尚未自动创建或公开线上仓库；GitHub 连接提供读写仓库内文件的接口，但本对话中的连接没有“新建仓库”接口。
