"""Standalone, research-use TSRG camera inference for *new* photos.

Based on the frozen R20 V3 model-loading and prompt contract. This command
does not access the R20 test set, recompute reported results, or train a model.
Upstream model code/weights and the R19 adapter are supplied by the user.
"""
from __future__ import annotations

import argparse
from contextlib import nullcontext
import hashlib
import importlib
import json
import math
from pathlib import Path
import re
import sys

from .routing import ALL_CATEGORIES, CameraPrediction, m2_par_prediction

R19_ADAPTER_SHA256 = "1dc8afa37c4947d30f58e9ae3aa260c76730dd7201a042f98fcbfd97ae0da8b0"
PROMPT = (
    "Describe the image in detail. Then reason its spatial distribution and estimate "
    "its camera parameters (roll, pitch, and field-of-view)."
)
CAMERA_RE = re.compile(
    r"camera parameters.{0,100}?are\s*:\s*"
    r"([+-]?(?:\d+(?:\.\d+)?|\.\d+)(?:[eE][+-]?\d+)?)\s*,\s*"
    r"([+-]?(?:\d+(?:\.\d+)?|\.\d+)(?:[eE][+-]?\d+)?)\s*,\s*"
    r"([+-]?(?:\d+(?:\.\d+)?|\.\d+)(?:[eE][+-]?\d+)?)",
    re.IGNORECASE,
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_camera_text(text: str) -> CameraPrediction:
    """Last model camera triple is (roll, pitch, square-vFoV), in radians."""
    matches = list(CAMERA_RE.finditer(text))
    if not matches:
        raise ValueError("Camera triple not found in model output")
    values = tuple(math.degrees(float(matches[-1].group(i))) for i in (1, 2, 3))
    if not all(math.isfinite(value) for value in values):
        raise ValueError("Non-finite camera estimate")
    return CameraPrediction(*values)


def validate_assets(source_dir: Path, base_checkpoint: Path, adapter_dir: Path) -> None:
    if not (source_dir / "src" / "models" / "radiov3" / "hf_model.py").is_file():
        raise FileNotFoundError("Set --puffin-source to the official repository's Puffin/ subdirectory containing src/")
    if not base_checkpoint.is_file():
        raise FileNotFoundError(f"Base checkpoint not found: {base_checkpoint}")
    adapter = adapter_dir / "adapter_model.safetensors"
    if not (adapter_dir / "adapter_config.json").is_file() or not adapter.is_file():
        raise FileNotFoundError("R19 adapter directory needs adapter_config.json and adapter_model.safetensors")
    actual = sha256_file(adapter)
    if actual != R19_ADAPTER_SHA256:
        raise ValueError(f"R19 adapter SHA256 mismatch: {actual}")


def choose_compute_dtype(torch_module):
    """Select native BF16 on both devices or FP16 on older dual-GPU cards.

    The frozen R20 benchmark used BF16; FP16 is a separate new-photo
    compatibility path, not a replay of that benchmark.
    """
    has_native_bf16 = all(
        torch_module.cuda.get_device_capability(i)[0] >= 8
        for i in (0, 1)
    )
    return torch_module.bfloat16 if has_native_bf16 else torch_module.float16



class CameraInference:
    """Two-GPU runtime following R20 V3's vision / language model split."""

    def __init__(self, source_dir: Path, base_checkpoint: Path, adapter_dir: Path):
        validate_assets(source_dir, base_checkpoint, adapter_dir)

        import numpy as np
        import torch
        import torch.nn as nn
        from huggingface_hub import snapshot_download
        from transformers import AutoConfig, AutoModelForCausalLM, AutoTokenizer

        if not torch.cuda.is_available() or torch.cuda.device_count() < 2:
            raise RuntimeError("This R20-compatible first release requires two CUDA GPUs (vision cuda:0, language cuda:1).")
        # The original frozen run used torch 2.10, transformers 5.0 and peft 0.19.1.
        import transformers
        import peft
        if not torch.__version__.startswith("2.10.0") or transformers.__version__ != "5.0.0" or peft.__version__ != "0.19.1":
            raise RuntimeError("Use the R20 V3 runtime versions documented in docs/INFERENCE_QUICKSTART_CN.md")

        self.np, self.torch = np, torch
        self.visual_device, self.llm_device = torch.device("cuda:0"), torch.device("cuda:1")
        self.dtype = choose_compute_dtype(torch)
        source_str = str(source_dir.resolve())
        if source_str not in sys.path:
            sys.path.insert(0, source_str)
        from src.models.radiov3.hf_model import RADIOModel
        RADIOModel.all_tied_weights_keys = {}
        RADIOModel._tied_weights_keys = {}

        checkpoint = torch.load(str(base_checkpoint), map_location="cpu", mmap=True, weights_only=True)
        state = checkpoint.get("state_dict", checkpoint)
        visual_state = {k[len("visual_encoder."):]: v for k, v in state.items() if k.startswith("visual_encoder.")}
        projector_state = {k[len("projector."):]: v for k, v in state.items() if k.startswith("projector.")}
        llm_state = {k[len("llm."):]: v for k, v in state.items() if k.startswith("llm.")}
        if (len(visual_state), len(projector_state), len(llm_state)) != (390, 4, 339):
            raise RuntimeError("Unexpected checkpoint structure; this loader expects the archived Puffin-Base model.")

        radio = RADIOModel.from_pretrained("nvidia/C-RADIOv3-H", torch_dtype=self.dtype)
        radio.load_state_dict(visual_state, strict=True)
        self.radio = radio.to(self.visual_device).eval().requires_grad_(False)
        projector = nn.Sequential(nn.Linear(5120, 1536), nn.SiLU(), nn.Linear(1536, 1536))
        projector.load_state_dict(projector_state, strict=True)
        self.projector = projector.to(self.visual_device, dtype=torch.float32).eval().requires_grad_(False)

        # Only the text configuration/tokenizer is fetched; the model weights
        # come from the provided foundation checkpoint, not a new Qwen model.
        qwen_dir = Path.home() / ".cache" / "tsrg" / "qwen_text_assets"
        qwen_dir.mkdir(parents=True, exist_ok=True)
        snapshot_download(
            "Qwen/Qwen2.5-1.5B-Instruct", local_dir=str(qwen_dir),
            allow_patterns=["config.json", "tokenizer.json", "tokenizer_config.json"],
        )
        self.tokenizer = AutoTokenizer.from_pretrained(str(qwen_dir), use_fast=True, local_files_only=True)
        config = AutoConfig.from_pretrained(str(qwen_dir), local_files_only=True)
        config._attn_implementation = "sdpa"
        base = AutoModelForCausalLM.from_config(config)
        if set(llm_state) != set(base.state_dict()):
            raise RuntimeError("Foundation language-model keys do not match Qwen configuration")
        base.load_state_dict(llm_state, strict=True)
        base = base.to(self.llm_device, dtype=self.dtype).eval().requires_grad_(False)
        base.config.use_cache = True
        del checkpoint, state, visual_state, projector_state, llm_state

        # Mirrors the compatibility guard in the executed R20 V3 environment.
        import peft.import_utils as peft_utils
        peft_utils.is_torchao_available = lambda: False
        try:
            importlib.import_module("peft.tuners.lora.torchao").is_torchao_available = lambda: False
        except ImportError:
            pass
        from peft import PeftModel
        self.model = PeftModel.from_pretrained(
            base, str(adapter_dir), adapter_name="r19", is_trainable=False
        ).eval()
        self.model.set_adapter("r19")
        self.model.config.use_cache = True

        left = self.tokenizer.encode("<|im_start|>user\n", add_special_tokens=False)
        right = self.tokenizer.encode(
            "\n" + PROMPT + "<|im_end|>\n<|im_start|>assistant\n",
            add_special_tokens=False,
        )
        ids = left + [-200] * 256 + right
        if len(ids) != 291 or ids.count(-200) != 256:
            raise RuntimeError("R20 V3 prompt contract mismatch: expected 291 tokens, 256 image placeholders")
        self.prompt_ids = torch.tensor([ids], dtype=torch.long, device=self.llm_device)
        self.image_mask = self.prompt_ids.eq(-200)

    def _visual_tokens(self, image_path: Path):
        from PIL import Image
        with Image.open(image_path) as src:
            image = src.convert("RGB")
        width, height = image.size
        side = min(width, height)
        left, top = (width - side) // 2, (height - side) // 2
        image = image.crop((left, top, left + side, top + side)).resize(
            (512, 512), Image.Resampling.BICUBIC
        )
        arr = self.np.asarray(image, dtype=self.np.uint8).copy()
        tensor = self.torch.from_numpy(arr).permute(2, 0, 1).float()
        tensor = (2 * tensor / 255 - 1).unsqueeze(0).to(self.visual_device, dtype=self.dtype)
        _, spatial = self.radio((tensor + 1) / 2)
        if tuple(spatial.shape) != (1, 1024, 1280):
            raise RuntimeError(f"Unexpected RADIO spatial shape: {tuple(spatial.shape)}")
        return spatial.reshape(1, 16, 2, 16, 2, 1280).permute(
            0, 1, 3, 2, 4, 5
        ).reshape(1, 256, 5120).float()

    def _generate(self, visual_tokens, specialist: bool) -> str:
        torch = self.torch
        image_embeddings = self.projector(visual_tokens).to(self.llm_device, dtype=self.dtype)
        context = nullcontext() if specialist else self.model.disable_adapter()
        with context:
            emb = self.model.get_input_embeddings()
            inputs_embeds = emb(self.prompt_ids.clamp_min(0)).clone()
            inputs_embeds[self.image_mask] = image_embeddings.reshape(-1, 1536)
            attention_mask = torch.ones(1, 291, dtype=torch.long, device=self.llm_device)
            position_ids = torch.arange(291, dtype=torch.long, device=self.llm_device).unsqueeze(0)
            past, output_tokens = None, []
            for _ in range(512):
                output = self.model(
                    inputs_embeds=inputs_embeds, attention_mask=attention_mask,
                    position_ids=position_ids, past_key_values=past,
                    use_cache=True, return_dict=True,
                )
                next_id = int(torch.argmax(output.logits[:, -1, :], dim=-1).item())
                output_tokens.append(next_id)
                if next_id == self.tokenizer.eos_token_id:
                    break
                past = output.past_key_values
                inputs_embeds = emb(torch.tensor([[next_id]], dtype=torch.long, device=self.llm_device))
                attention_mask = torch.cat([attention_mask, attention_mask.new_ones(1, 1)], dim=1)
                position_ids = position_ids[:, -1:] + 1
        return self.tokenizer.decode(output_tokens, skip_special_tokens=True).strip()

    def predict(self, image_path: Path, category: str) -> dict:
        category = category.strip().lower()
        if category not in ALL_CATEGORIES:
            raise ValueError(f"Unknown category {category!r}; use one of: {', '.join(sorted(ALL_CATEGORIES))}")
        if not image_path.is_file():
            raise FileNotFoundError(image_path)
        with self.torch.inference_mode():
            visual = self._visual_tokens(image_path)
            m0 = parse_camera_text(self._generate(visual, specialist=False))
            if category in {"event", "heritage"}:
                specialist = parse_camera_text(self._generate(visual, specialist=True))
                pitch = specialist.pitch_deg
                pitch_source = "r19"
            else:
                pitch = None
                pitch_source = "m0"
            result = m2_par_prediction(category, m0, pitch)
        return {
            "image": str(image_path),
            "category": category,
            "roll_deg": result.roll_deg,
            "pitch_deg": result.pitch_deg,
            "square_vfov_deg": result.square_vfov_deg,
            "sources": {"roll": "m0", "pitch": pitch_source, "square_vfov": "m0"},
            "reference": "R20 V3 frozen parameter-routing rule; new-image inference",
        }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="TSRG new-image camera inference (requires two CUDA GPUs)")
    parser.add_argument("--image", required=True, type=Path)
    parser.add_argument("--category", required=True, choices=sorted(ALL_CATEGORIES))
    parser.add_argument("--puffin-source", required=True, type=Path, help="Upstream Puffin/ subdirectory containing src/")
    parser.add_argument("--base-checkpoint", required=True, type=Path, help="Original Puffin-Base.pth")
    parser.add_argument("--adapter-dir", required=True, type=Path, help="R19 epoch_3/qwen_lora directory")
    parser.add_argument("--output", type=Path, help="Optional JSON output path")
    args = parser.parse_args(argv)
    session = CameraInference(args.puffin_source, args.base_checkpoint, args.adapter_dir)
    result = session.predict(args.image, args.category)
    serialized = json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(serialized + "\n", encoding="utf-8")
    print(serialized)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
