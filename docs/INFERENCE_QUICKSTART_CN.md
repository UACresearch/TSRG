# TSRG 相机参数预测下载版（开发分支）

本页用于**新照片**的推理。已冻结的 R20 V3 test239 结果保持原样；这里的示例不会重新运行那一批正式测试，也不涉及训练或挑选模型。第一版只输出相机参数，不包含图片生成网页。

## 0. 下载代码

有权访问本私有仓库的成员可以在终端运行（首次下载时按 GitHub 提示完成登录）：

```bash
git clone --branch feature/inference-download-v1 --single-branch https://github.com/caolitong0717/TSRG.git
cd TSRG
git clone https://github.com/KangLiao929/Puffin.git upstream/Puffin
```

上面的第二个 `git clone` 将上游源代码放在 `upstream/Puffin/Puffin/`；它不包含本研究的 LoRA 权重。开发分支通过真实 GPU 检查和发布权限审核后，才会合并到主分支及制作正式 Release。

## 1. 准备文件

需要自行下载或准备：

1. 原始代码：[上游 Puffin](https://github.com/KangLiao929/Puffin)，使用仓库内部的 `Puffin/` 子目录（此目录应含 `src/models/radiov3/hf_model.py`）。
2. 基础模型 `Puffin-Base.pth`：从 [上游官方模型页面](https://huggingface.co/KangLiao/Puffin) 获取。仅从官方来源取得，遵守相关许可。
3. 本研究冻结的 R19 Epoch 3 LoRA：从 [本仓库的私有研究归档 Release](https://github.com/caolitong0717/TSRG/releases/tag/archive-20260927) 的 `tourism-puffin-r19-m2par-full-pitch-specialist-v1.zip` 解压，找到 `epoch_3/qwen_lora/`，里面应有 `adapter_model.safetensors` 与 `adapter_config.json`。原始 Kaggle 备份同样可用。

程序自动核对最终 LoRA 文件 SHA256。这个适配器约 8.75 MB；不要把整个约 73 MB 归档 ZIP 当作模型路径传给程序。R19 的历史训练日志与优化器恢复文件无需用于普通推理。

本仓库保持私有，资料授权审核完成之前不要修改为公开发布。

## 2. 环境

原始 R20 V3 执行环境是 **两块 CUDA GPU**（视觉编码器使用 cuda:0，语言模型使用 cuda:1），PyTorch 2.10.0、Transformers 5.0.0 和 PEFT 0.19.1。本开发版沿用这一分配，当前未验证单显卡或纯 CPU 的大型模型推理。

先安装适配本机驱动和 CUDA 的 **GPU 版 PyTorch 2.10.0**，参考 [PyTorch 官方安装方法](https://pytorch.org/get-started/locally/)，再在 TSRG 根目录运行：

```bash
python -m pip install -r requirements-inference.txt
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

依赖文件与原始上游教程的包版本有区别。不要直接用上游的旧版 requirements 覆盖这里记录的 R20 V3 环境。第一次运行需联网获取 RADIO 的公开基础结构、Qwen 的文本配置与分词器；基础模型权重使用传入的本地文件。

## 3. 新照片推理

先运行 `python -m tsrg.inference --help` 查看命令。下面是示例路径，按实际解压目录修改：

```bash
python -m tsrg.inference \
  --image "my_photos/attraction.jpg" \
  --category heritage \
  --puffin-source "upstream/Puffin/Puffin" \
  --base-checkpoint "models/Puffin-Base.pth" \
  --adapter-dir "models/r19/epoch_3/qwen_lora" \
  --output "outputs/attraction_camera.json"
```

景点类别 `--category` 由使用者提供，当前可选 `event`（活动）、`heritage`（遗产）、`natural`（自然）、`purpose_built`（专门建造）。该版没有通用图片景点类型识别器。计算逻辑自动取 M0 的 Roll 与方形裁剪垂直 FoV；仅在活动、遗产类取 R19 的 Pitch，其余类型采用 M0 的 Pitch。输出 JSON 包含三个角度制参数和来源标记。

该程序复用了经过审计的 R20 V3 模型配置、291-token 提示词、中心方形裁剪、视觉特征形状、适配器校验和文本角度解析逻辑。作为新的下载推理入口，它还需要进行**真实 GPU 端到端冒烟测试**，在通过前属于开发版本，不宣称已复现完整独立测试指标。CPU 单元测试仅覆盖参数转换、资源校验与路由规则。

## 4. 文件许可与来源

上游软件采用 S-Lab License 1.0，含非商业使用及保留版权声明等条件。TSRG 自有工具代码的许可范围详见仓库 `LICENSE` 与 `THIRD_PARTY_NOTICES.md`。大型原始权重、第三方原始图片和历史训练数据均须分别核对分发权。正式公开前完成 `RELEASE_CHECKLIST.md` 中的检查。
