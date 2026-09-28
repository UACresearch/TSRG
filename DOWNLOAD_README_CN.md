# TSRG 相机参数预测下载版 · v0.1.0-rc1

这是 TSRG 的**相机参数预测**研究用下载包，支持对新旅游照片估计 Roll（横滚角）、Pitch（俯仰角）与中心方形裁剪口径的垂直 FoV（视场角），输出单位均为**度**。本包以原始基础模型与经校验的 R19 Epoch-3 LoRA 适配器运行，按照预设景点类别自动组合两组参数。包含代码、安装说明与基础单元测试；模型权重、原始旅游图片及完整历史训练资料需另外获取。

当前为**私有发布候选版**，供内部验收与获得授权的研究合作者使用。已在 Kaggle 双 Tesla T4 / FP16 环境中，使用新照片验证独立命令行完整运行；这次运行与原 Notebook 的同图结果一致。正式 R20 V3 的 BF16 测试记录不受本下载包影响。

## 下载后准备

1. 安装具有 **两块 CUDA GPU** 的 Python 环境；已验证配置为 PyTorch 2.10.0+cu128、Transformers 5.0.0、PEFT 0.19.1，T4 使用 FP16，支持原生 BF16 的显卡可使用 BF16。单 GPU 或纯 CPU 大型模型推理尚未测试。PyTorch 请按照 [官方安装页面](https://pytorch.org/get-started/locally/) 选择与 CUDA 驱动匹配的 GPU 版本。
2. 在下载包根目录运行 `python -m pip install -r requirements-inference.txt`。安装开发测试依赖可使用 `python -m pip install -r requirements-dev.txt`。
3. 下载[官方基础模型代码](https://github.com/KangLiao929/Puffin)，保留其仓库内部的 `Puffin/` 目录，其中包含 `src/models/radiov3/hf_model.py`。从[官方模型页面](https://huggingface.co/KangLiao/Puffin)单独获取 `Puffin-Base.pth`。
4. 从[项目原始 R19 私有归档](https://github.com/caolitong0717/TSRG/releases/tag/archive-20260927)或经授权的 [Kaggle R19 备份](https://www.kaggle.com/datasets/caolitong/tourism-puffin-r19-m2par-full-pitch-specialist-v1)获取 `epoch_3/qwen_lora/`，其内须同时有 `adapter_config.json` 和 `adapter_model.safetensors`。本程序会自动验证适配器的 SHA256。

已核定的 R19 适配器 SHA256：

```text
1dc8afa37c4947d30f58e9ae3aa260c76730dd7201a042f98fcbfd97ae0da8b0
```

## 使用示例

在项目根目录执行（将路径替换成自己的文件位置）：

```bash
python -m tsrg.inference \
  --image "my_photos/attraction.jpg" \
  --category heritage \
  --puffin-source "upstream/Puffin/Puffin" \
  --base-checkpoint "models/Puffin-Base.pth" \
  --adapter-dir "models/r19/epoch_3/qwen_lora" \
  --output "outputs/attraction_camera.json"
```

`--category` 可选：`event`（活动）、`heritage`（历史文化遗产）、`natural`（自然）与 `purpose_built`（专门建造）。类别由使用者或其元数据提供；当前没有通用景点类别自动识别器。系统自动采用 M0 的 Roll 与方形裁剪 FoV；活动与遗产类采用 R19 的 Pitch，其余采用 M0 的 Pitch。程序输出 JSON，包含数值、景点类别和每个参数的来源。运行前可以先检查 `python -m tsrg.inference --help`。

## 检查与范围

```bash
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

这些 CPU 单元测试检查计算、解析及路由逻辑，不代表运行了大型模型。独立推理的实际成功记录、数值及运行环境见[私有仓库原版技术文档](https://github.com/caolitong0717/TSRG/blob/feature/inference-download-v1/docs/INFERENCE_QUICKSTART_CN.md)。**本版输出相机参数，不包含在线网页或多视角图片生成程序。**

这个精简下载包经过明确的文件白名单打包；历史 Notebook、实验原始预测、用户照片、缓存、个人路径与第三方模型权重均不随包分发。包内 `MANIFEST_SHA256.txt` 记录源文件摘要。请遵守本项目 `LICENSE` 与 `THIRD_PARTY_NOTICES.md` 的各自许可范围：上游 Puffin 的 S-Lab License 1.0 涉及非商业使用及版权声明，任何第三方模型或适配器的再分发均须单独确认权限。仓库当前保持 Private，正式公开需经相关授权审查。
