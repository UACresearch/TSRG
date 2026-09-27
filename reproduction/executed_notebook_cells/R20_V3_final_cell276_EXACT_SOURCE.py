
# ======================================================================================
# R20 FINAL ONE-TIME TEST239 V3 | corrected STRICT R11 291-token prompt
# Implementation-only correction of pre-inference V2 failure.
# No training. No Stable101. No post-reveal tuning. No rerunning completed predictions.
# ======================================================================================
import sys, re, gc, json, math, time, hashlib, inspect, shutil, importlib, random
from pathlib import Path
from contextlib import nullcontext
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from PIL import Image
from tqdm.auto import tqdm
import kagglehub
from huggingface_hub import hf_hub_download, snapshot_download
from transformers import AutoConfig, AutoTokenizer, AutoModelForCausalLM
import transformers, peft

PRE_HANDLE = 'caolitong/tourism-puffin-r20-runtime-normalized-oof-v1'
R18_HANDLE = 'caolitong/tourism-puffin-r18-m2-par-freeze-v1'
R19_HANDLE = 'caolitong/tourism-puffin-r19-m2par-full-pitch-specialist-v1'
LEGACY_HANDLE = 'caolitong/tourism-puffin-r20-m2par-final-test-v1'
V2_HANDLE = 'caolitong/tourism-puffin-r20-one-time-batch1-v2'
SAVE_HANDLE = 'caolitong/tourism-puffin-r20-one-time-batch1-r11-v3'
PRE_SIG = 'f352b7ce9359732f15ff837e9766c03f761360c0a279687e07770d5bbd876234'
V2_SIG = '55f2499c3ea93870df0c9e6c0b0b32ff675eaaa9299402f20ea6aab9b5537155'
R19_SIG = 'f83708c4201d3af5e02b2b4623f4723799f3dcdaa6230111473173e5028013f7'
R19_SHA = '1dc8afa37c4947d30f58e9ae3aa260c76730dd7201a042f98fcbfd97ae0da8b0'
RADIO_SHA = '9cc2c5d923cbc3de403cd63bc644ab30567b6ba9729c6717c82e26129e0d370c'
ROOT = Path('/kaggle/input/datasets/caolitong/tourism-puffin-geometry-training')
NBROOT = Path('/kaggle/input/notebooks/caolitong/notebook8473921acb')
WORK = Path('/kaggle/working/r20_final_one_time_batch1_r11_v3')
STAGE = WORK / 'persistent_stage'
CACHE = WORK / 'ephemeral_cache'
STAGE.mkdir(parents=True, exist_ok=True)
CACHE.mkdir(parents=True, exist_ok=True)
VIS_DEV, LLM_DEV = torch.device('cuda:0'), torch.device('cuda:1')
DTYPE = torch.bfloat16
MAX_NEW_TOKENS = 512
BOOT_B, BOOT_SEED = 10000, 20260926
SPECIAL = {'event', 'heritage'}
ALL_CATS = {'event', 'heritage', 'natural', 'purpose_built'}
PROMPT = ('Describe the image in detail. Then reason its spatial distribution and estimate '
          'its camera parameters (roll, pitch, and field-of-view).')
assert torch.cuda.is_available() and torch.cuda.device_count() >= 2
assert torch.__version__.startswith('2.10.0')
assert transformers.__version__ == '5.0.0' and peft.__version__ == '0.19.1'
random.seed(20260908)
np.random.seed(20260908)
torch.manual_seed(20260908)
torch.cuda.manual_seed_all(20260908)
print('=' * 106)
print('R20_FINAL_ONE_TIME_TEST239_V3 | STRICT R11 PROMPT CORRECTION')
print('V2 STOPPED BEFORE MODEL INFERENCE; NO TRAINING; NO Stable101')
print('=' * 106)

# ---- filesystem / remote utilities ---------------------------------------------------
def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for part in iter(lambda: f.read(8 * 1024 * 1024), b''):
            h.update(part)
    return h.hexdigest()

def dump(name, obj):
    path = STAGE / name
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False, allow_nan=False), encoding='utf-8')
    return path

def hash_json(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(',', ':')).encode()).hexdigest()

def get_dataset(handle):
    fn = kagglehub.dataset_download
    kw = {'force_download': True} if 'force_download' in inspect.signature(fn).parameters else {}
    return Path(fn(handle, **kw))

def optional_dataset(handle):
    try:
        return get_dataset(handle)
    except Exception as e:
        if any(x in str(e).lower() for x in ['not found', '404', 'does not exist']):
            return None
        raise

def locate(root, rel, required=True):
    root, rel = Path(root), Path(rel)
    if (root / rel).is_file():
        return root / rel
    hits = [p for p in root.rglob(rel.name)
            if p.is_file() and str(p).replace('\\', '/').endswith(str(rel).replace('\\', '/'))]
    if len(hits) == 1:
        return hits[0]
    if required:
        raise FileNotFoundError(f'Expected UNIQUE {rel} under {root}; found: {hits}')
    return None

def remote_verify(names, tries=30):
    expected = {n: sha(STAGE / n) for n in names}
    last = None
    for j in range(tries):
        try:
            rr = get_dataset(SAVE_HANDLE)
            bad = [n for n, v in expected.items()
                   if (locate(rr, n, False) is None or sha(locate(rr, n)) != v)]
            if not bad:
                print('REMOTE_SHA256_VERIFIED:', names)
                return rr
            last = f'not yet synchronized: {bad}'
        except Exception as e:
            last = repr(e)
        print(f'Waiting for remote {j+1}/{tries}: {str(last)[:160]}')
        time.sleep(10)
    raise RuntimeError(f'REMOTE VERIFICATION FAILED: {last}')

def upload(names, note):
    kagglehub.dataset_upload(SAVE_HANDLE, str(STAGE), version_notes=note)
    return remote_verify(names)

# ---- audit previous aborted V2, and prevent second formal reveal ------------------------
for handle in [LEGACY_HANDLE, V2_HANDLE]:
    old = optional_dataset(handle)
    if old is None:
        if handle == V2_HANDLE:
            raise RuntimeError('V2 protocol archive missing; do not start formal reveal.')
        continue
    found = [p for p in old.rglob('*') if p.is_file() and (
        'predictions' in p.name.lower() or 'verdict' in p.name.lower() or
        p.name.endswith('_status.json') or p.name.endswith('_summary.csv'))]
    assert not found, f'EXISTING PRIOR TEST OUTPUT! STOP: {found}'
    if handle == V2_HANDLE:
        v2_file = locate(old, 'R20_V2_protocol.json')
        v2_protocol = json.loads(v2_file.read_text())
        assert v2_protocol['signature'] == V2_SIG
        print('ABORTED_V2_ONLY_PROTOCOL_VERIFIED; NO TEST OUTPUT:', sha(v2_file))

pre = get_dataset(PRE_HANDLE)
pv = json.loads(locate(pre, 'runtime_normalized_final_verdict.json').read_text())
assert pv['protocol_signature'] == PRE_SIG
assert pv['RUNTIME_NORMALIZED_M2PAR_COMPATIBILITY_PASS'] is True
assert len(pv['gates']) == 6 and all(v is True for v in pv['gates'].values())
assert pv['rows'] == {'oof_total': 431, 'pitch': 197, 'pitch_locations': 49, 'specialist_pitch': 81}
assert pv['runtime']['batch_size'] == 1
assert pv['runtime']['dtype'] == 'bfloat16'
assert pv['runtime']['projector'] == 'float32'
assert pv['runtime']['attention'] == 'sdpa'
assert pv['test239_model_prediction'] is False and pv['training_performed'] is False
p_manifest = json.loads(locate(pre, 'runtime_normalized_sha256_manifest.json').read_text())
for rel, h in p_manifest.items():
    if isinstance(h, str) and re.fullmatch('[0-9a-f]{64}', h):
        assert sha(locate(pre, rel)) == h
print('PRETEST_PASS_AND_SHA_VERIFIED')

r18 = get_dataset(R18_HANDLE)
r18_manifest = json.loads(locate(r18, 'sha256_manifest.json').read_text())
for rel, h in r18_manifest.items():
    assert sha(locate(r18, rel)) == h, rel
s18 = json.loads(locate(r18, 'R18_M2PAR_system_definition.json').read_text())
t18 = json.loads(locate(r18, 'R18_test239_precommit.json').read_text())
assert s18['status'] == 'FROZEN_CANDIDATE_BEFORE_FINAL_TEST'
assert s18['roll']['source'] == s18['square_vfov']['source'] == 'M0'
assert s18['pitch'] == {'event': 'M1-v4 specialist', 'heritage': 'M1-v4 specialist',
                        'natural': 'M0', 'purpose_built': 'M0'}
assert t18['dataset'] == 'test239' and t18['status_at_R18'] == 'PRISTINE_UNTOUCHED'
r19 = get_dataset(R19_HANDLE)
r19_p = json.loads(locate(r19, 'R19_protocol.json').read_text())
r19_lock = json.loads(locate(r19, 'R19_final_model_lock.json').read_text())
r19_critical = json.loads(locate(r19, 'R19_critical_sha256.json').read_text())
assert r19_p['protocol_signature_sha256'] == R19_SIG
assert r19_lock['status'] == 'FROZEN_BEFORE_TEST239' and r19_lock['final_epoch'] == 3
for flag in ['epoch_selected_using_metrics', 'development_MAE_calculated', 'Stable101_used', 'test239_used']:
    assert r19_lock[flag] is False, flag
assert r19_lock['final_adapter_sha256'] == R19_SHA
for rel, h in r19_critical.items():
    assert sha(locate(r19, rel)) == h, rel
ADAPTER_DIR = locate(r19, 'epoch_3/qwen_lora/adapter_model.safetensors').parent
assert sha(ADAPTER_DIR / 'adapter_model.safetensors') == R19_SHA
cfg = json.loads((ADAPTER_DIR / 'adapter_config.json').read_text())
assert int(cfg['r']) == 8 and int(cfg['lora_alpha']) == 16
assert abs(float(cfg['lora_dropout']) - .05) < 1e-12
assert set(cfg['target_modules']) == {'q_proj', 'k_proj', 'v_proj', 'o_proj'}
print('R18/R19 LOCKS VERIFIED')

# ---- immutable corrected implementation record; no scientific rule change ---------------
protocol = {
    'run': 'R20_FINAL_ONE_TIME_TEST239_V3',
    'correction': 'Pre-inference V2 used 293-token vision-wrapper prompt; restore exact R11 291-token -200 placeholder prompt',
    'aborted_v2_signature': V2_SIG,
    'aborted_v2_protocol_sha256': sha(v2_file),
    'pretest_signature': PRE_SIG,
    'R19_protocol_signature': R19_SIG,
    'R19_adapter_sha256': R19_SHA,
    'runtime': {'torch': torch.__version__, 'transformers': transformers.__version__,
                'peft': peft.__version__, 'dtype': 'bfloat16', 'projector': 'float32',
                'attention': 'sdpa', 'batch_size': 1},
    'prompt': PROMPT,
    'prompt_template': 'LEFT + [-200]*256 + RIGHT; LEFT = <|im_start|>user\\n; RIGHT = \\n+PROMPT+<|im_end|>\\n<|im_start|>assistant\\n',
    'prompt_length': 291, 'image_placeholders': 256,
    'max_new_tokens': MAX_NEW_TOKENS, 'decoding': 'greedy',
    'routes': {'roll': 'M0', 'square_vfov': 'M0', 'event_pitch': 'R19',
               'heritage_pitch': 'R19', 'natural_pitch': 'M0', 'purpose_built_pitch': 'M0'},
    'primary': {'P1': 'all event/heritage specialist test predictions parse',
                'P2': 'M2-PAR reliable pitch MAE < M0 reliable pitch MAE',
                'P3': 'M2-PAR roll == M0 exactly', 'P4': 'M2-PAR square-vFoV == M0 exactly'},
    'bootstrap': {'unit': 'location_id', 'B': BOOT_B, 'seed': BOOT_SEED, 'role': 'descriptive only'},
    'training': False, 'Stable101': False, 'post_reveal_tuning': False
}
protocol['signature'] = hash_json(protocol)
dump('R20_V3_protocol.json', protocol)
remote = optional_dataset(SAVE_HANDLE)
if remote is not None:
    pp = locate(remote, 'R20_V3_protocol.json', False)
    assert pp is not None and json.loads(pp.read_text()) == protocol, 'PROTOCOL COLLISION'
    verdict = locate(remote, 'R20_V3_final_verdict.json', False)
    if verdict is not None:
        print('R20 ALREADY COMPLETED; NO INFERENCE RERUN')
        print(verdict.read_text())
        raise SystemExit('COMPLETED ONE-TIME REVEAL')
else:
    upload(['R20_V3_protocol.json'], 'R20 R11 correction pre-inference, before test performance')
print('R20_V3_PROTOCOL_LOCKED:', protocol['signature'])

# ---- reproduce development mask before viewing test performance --------------------------
manifest_path = ROOT / 'metadata/trainable_manifest_final.csv'
audit_path = ROOT / 'reports/geocalib_filter_audit.csv'
geometry_path = ROOT / 'geometry_training/geometry_train_combined.jsonl'
m0dev_path = Path('/kaggle/input/datasets/caolitong/tourism-puffin-m0-train742-merged-v1/m0_train742_predictions_merged.csv')
manifest = pd.read_csv(manifest_path)
audit_all = pd.read_csv(audit_path)
with geometry_path.open(encoding='utf-8') as f:
    geom = pd.DataFrame([json.loads(line) for line in f if line.strip()])
m0dev = pd.read_csv(m0dev_path)
for df, col in [(manifest, 'sha1'), (audit_all, 'id'), (geom, 'id'), (m0dev, 'id')]:
    df[col] = df[col].astype(str)
assert audit_all.id.is_unique and m0dev.id.is_unique
primary_ids = geom.loc[geom.label_provenance.eq('geocalib_pseudo_parameter_filtered'), 'id'].tolist()
assert len(primary_ids) == 526 and len(set(primary_ids)) == 526
train_ref = (pd.DataFrame({'id': primary_ids})
             .merge(m0dev[['id', 'target_pitch_deg']], on='id', validate='one_to_one')
             .merge(audit_all[['id', 'status', 'pitch', 'pitch_uncertainty_deg']],
                    on='id', validate='one_to_one'))
def reliable_mask(df):
    p = pd.to_numeric(df.pitch, errors='coerce')
    u = pd.to_numeric(df.pitch_uncertainty_deg, errors='coerce')
    return df.status.astype(str).str.lower().eq('ok') & np.isfinite(p) & np.isfinite(u) & u.le(3.0)
trmask = reliable_mask(train_ref)
stored = train_ref.target_pitch_deg.notna()
assert len(train_ref) == 526 and trmask.sum() == stored.sum() == 234 and trmask.equals(stored)
maxdiff = np.abs(np.degrees(train_ref.loc[trmask, 'pitch'].to_numpy(float))
                 - train_ref.loc[trmask, 'target_pitch_deg'].to_numpy(float)).max()
assert maxdiff < .001
print('TRAIN_PITCH_POLICY_PARITY_PASSED: 234/526, maxdiff=', maxdiff)

# ---- test metadata / byte identity; no score yet -----------------------------------------
manifest['category'] = manifest.category.astype(str).str.strip().str.lower()
audit_all['category'] = audit_all.category.astype(str).str.strip().str.lower()
test = manifest.loc[manifest.split.astype(str).str.lower().eq('test')].copy().reset_index(drop=True)
assert len(test) == 239 and test.sha1.is_unique and test.location_id.nunique() == 16
assert test.groupby('category').location_id.nunique().to_dict() == dict.fromkeys(sorted(ALL_CATS), 4)
audit_test = audit_all.loc[audit_all.split.astype(str).str.lower().eq('test')].copy()
assert len(audit_test) == 239 and set(audit_test.id) == set(test.sha1)
tref = (test[['sha1', 'category', 'location_id', 'local_path', 'local_sha256']]
        .rename(columns={'sha1': 'id'})
        .merge(audit_test[['id', 'status', 'pitch', 'pitch_uncertainty_deg']],
               on='id', validate='one_to_one'))
tref['reliable'] = reliable_mask(tref)
tref['target_pitch_deg'] = np.where(tref.reliable, np.degrees(pd.to_numeric(tref.pitch, errors='coerce')), np.nan)
assert int(tref.reliable.sum()) > 0

def image_for(row):
    paths = [ROOT / str(row.local_path), ROOT / 'images' / 'test' / row.category / f'{row.id}.jpg']
    paths = [p for p in paths if p.is_file()]
    if not paths:
        paths = list(ROOT.rglob(f'{row.id}.jpg'))
    assert paths, f'MISSING IMAGE {row.id}'
    hashes = {sha(p) for p in paths}
    assert len(hashes) == 1 and hashes.pop() == str(row.local_sha256).strip().lower(), row.id
    return str(paths[0])
tref['path'] = [image_for(row) for row in tqdm(tref.itertuples(index=False), total=239, desc='Image SHA256')]
print('TEST239 IMAGE SHA256 VERIFIED | 16 LOCATIONS')

# ---- reuse V2 RADIO byte cache if present; otherwise recompute exactly --------------------
V2_RADIO = Path('/kaggle/working/r20_final_one_time_batch1_v2/ephemeral_cache/test239_radio_tokens_float32.npy')
RADIO_PATH = CACHE / 'test239_radio_tokens_float32.npy'
found_cache = None
for path in [V2_RADIO, RADIO_PATH]:
    if path.is_file() and sha(path) == RADIO_SHA:
        found_cache = path
        break
if found_cache is None:
    official = NBROOT / 'PuffinOfficial/Puffin'
    assert official.exists()
    sys.path.insert(0, str(official))
    from src.models.radiov3.hf_model import RADIOModel
    RADIOModel.all_tied_weights_keys = {}
    RADIOModel._tied_weights_keys = {}
    ckpt_path = Path(hf_hub_download('KangLiao/Puffin', 'Puffin-Base.pth'))
    state_all = torch.load(str(ckpt_path), map_location='cpu', mmap=True, weights_only=True)
    raw = state_all.get('state_dict', state_all)
    rv = {k[len('visual_encoder.'):]: v for k, v in raw.items() if k.startswith('visual_encoder.')}
    assert len(rv) == 390
    try:
        radio = RADIOModel.from_pretrained('nvidia/C-RADIOv3-H', cache_dir=str(NBROOT / 'hf-cache'),
                                           local_files_only=True, torch_dtype=DTYPE)
    except Exception:
        radio = RADIOModel.from_pretrained('nvidia/C-RADIOv3-H', torch_dtype=DTYPE)
    radio.load_state_dict(rv, strict=True)
    radio = radio.to(VIS_DEV).eval().requires_grad_(False)
    del state_all, raw, rv
    gc.collect()
    cache_new = np.lib.format.open_memmap(RADIO_PATH, mode='w+', dtype=np.float32, shape=(239, 256, 5120))
    @torch.inference_mode()
    def extract_radio(path):
        with Image.open(path) as src:
            im = src.convert('RGB')
        w, h = im.size
        side = min(w, h)
        l, t = (w-side)//2, (h-side)//2
        im = im.crop((l, t, l+side, t+side)).resize((512, 512), Image.Resampling.BICUBIC)
        x = torch.from_numpy(np.asarray(im, dtype=np.uint8).copy()).permute(2, 0, 1).float()
        x = (2*x/255-1).unsqueeze(0).to(VIS_DEV, dtype=DTYPE)
        _, spatial = radio((x+1)/2)
        assert tuple(spatial.shape) == (1, 1024, 1280)
        return (spatial.reshape(1, 16, 2, 16, 2, 1280)
                .permute(0, 1, 3, 2, 4, 5).reshape(256, 5120).float().cpu().numpy())
    for i, path in enumerate(tqdm(tref.path, desc='Test239 RADIO')):
        cache_new[i] = extract_radio(path)
    cache_new.flush()
    del radio, cache_new
    gc.collect()
    torch.cuda.empty_cache()
    assert sha(RADIO_PATH) == RADIO_SHA, ('RADIO_SHA_MISMATCH', sha(RADIO_PATH))
    found_cache = RADIO_PATH
radio_cache = np.load(found_cache, mmap_mode='r')
assert tuple(radio_cache.shape) == (239, 256, 5120)
print('TEST239 RADIO SHA256 VERIFIED; source:', found_cache)

# ---- build model / tokenizer --------------------------------------------------------------
ckpt_path = Path(hf_hub_download('KangLiao/Puffin', 'Puffin-Base.pth'))
qdir = WORK / 'qwen_text_assets'
qdir.mkdir(exist_ok=True)
snapshot_download('Qwen/Qwen2.5-1.5B-Instruct', local_dir=str(qdir),
                  allow_patterns=['config.json', 'tokenizer.json', 'tokenizer_config.json'], max_workers=3)
tok = AutoTokenizer.from_pretrained(str(qdir), use_fast=True, local_files_only=True)
config = AutoConfig.from_pretrained(str(qdir), local_files_only=True)
config._attn_implementation = 'sdpa'
checkpoint = torch.load(str(ckpt_path), map_location='cpu', mmap=True, weights_only=True)
state = checkpoint.get('state_dict', checkpoint)
projector = nn.Sequential(nn.Linear(5120, 1536), nn.SiLU(), nn.Linear(1536, 1536))
pstate = {k[len('projector.'):]: v for k, v in state.items() if k.startswith('projector.')}
assert len(pstate) == 4
projector.load_state_dict(pstate, strict=True)
projector = projector.to(VIS_DEV, dtype=torch.float32).eval().requires_grad_(False)
base = AutoModelForCausalLM.from_config(config)
qstate = {k[len('llm.'):]: v for k, v in state.items() if k.startswith('llm.')}
assert len(qstate) == 339 and set(qstate) == set(base.state_dict())
base.load_state_dict(qstate, strict=True)
base = base.to(LLM_DEV, dtype=DTYPE).eval().requires_grad_(False)
base.config.use_cache = True
del checkpoint, state, pstate, qstate
import peft.import_utils as peft_utils
peft_utils.is_torchao_available = lambda: False
try:
    importlib.import_module('peft.tuners.lora.torchao').is_torchao_available = lambda: False
except Exception:
    pass
from peft import PeftModel
model = PeftModel.from_pretrained(base, str(ADAPTER_DIR), adapter_name='r19', is_trainable=False).eval()
model.set_adapter('r19')
model.config.use_cache = True
assert sha(ADAPTER_DIR / 'adapter_model.safetensors') == R19_SHA
print('SHARED BF16/SDPA PEFT MODEL + FP32 PROJECTOR RESTORED')

# ---- exact R11 prompt; fail before any test model inference ------------------------------
LEFT = tok.encode('<|im_start|>user\n', add_special_tokens=False)
RIGHT = tok.encode('\n' + PROMPT + '<|im_end|>\n<|im_start|>assistant\n', add_special_tokens=False)
IMAGE_TOKEN = -200
STRICT_IDS = LEFT + [IMAGE_TOKEN]*256 + RIGHT
assert len(STRICT_IDS) == 291, ('R11_PROMPT_LENGTH_MISMATCH', len(STRICT_IDS))
assert STRICT_IDS.count(IMAGE_TOKEN) == 256
assert all(x >= 0 for x in LEFT + RIGHT)
assert tok.decode(LEFT, skip_special_tokens=False) == '<|im_start|>user\n'
assert '<|vision_start|>' not in tok.decode(LEFT + RIGHT, skip_special_tokens=False)
assert '<|vision_end|>' not in tok.decode(LEFT + RIGHT, skip_special_tokens=False)
STRICT_IDS_T = torch.tensor([STRICT_IDS], dtype=torch.long, device=LLM_DEV)
IMAGE_MASK = STRICT_IDS_T.eq(IMAGE_TOKEN)
print('STRICT_R11_PROMPT_READY:', STRICT_IDS_T.shape[1], 'tokens |', int(IMAGE_MASK.sum()), 'image placeholders')

NUM = r'[+-]?(?:\d+(?:\.\d+)?|\.\d+)(?:[eE][+-]?\d+)?'
CAMERA_RE = re.compile(rf'camera parameters.{{0,100}}?are\s*:\s*({NUM})\s*,\s*({NUM})\s*,\s*({NUM})', re.I)
def parse_camera(txt):
    mm = list(CAMERA_RE.finditer(str(txt)))
    if not mm:
        return None
    v = tuple(math.degrees(float(mm[-1].group(i))) for i in (1,2,3))
    return v if all(math.isfinite(x) for x in v) else None

@torch.inference_mode()
def generate_one(pos, specialist):
    x = torch.from_numpy(np.array(radio_cache[int(pos)], dtype=np.float32, copy=True)).unsqueeze(0).to(VIS_DEV)
    image_embeds = projector(x).to(LLM_DEV, dtype=DTYPE)
    ctx = nullcontext() if specialist else model.disable_adapter()
    with ctx:
        emb = model.get_input_embeddings()
        inputs_embeds = emb(STRICT_IDS_T.clamp_min(0)).clone()
        inputs_embeds[IMAGE_MASK] = image_embeds.reshape(-1, 1536)
        assert tuple(inputs_embeds.shape) == (1, 291, 1536)
        attention_mask = torch.ones(1, 291, dtype=torch.long, device=LLM_DEV)
        position_ids = torch.arange(291, dtype=torch.long, device=LLM_DEV).unsqueeze(0)
        past = None
        generated = []
        for _ in range(MAX_NEW_TOKENS):
            output = model(inputs_embeds=inputs_embeds, attention_mask=attention_mask,
                           position_ids=position_ids, past_key_values=past, use_cache=True, return_dict=True)
            token = int(torch.argmax(output.logits[:, -1, :], dim=-1).item())
            generated.append(token)
            if token == tok.eos_token_id:
                break
            past = output.past_key_values
            inputs_embeds = emb(torch.tensor([[token]], dtype=torch.long, device=LLM_DEV))
            attention_mask = torch.cat([attention_mask, attention_mask.new_ones(1, 1)], dim=1)
            position_ids = position_ids[:, -1:] + 1
    return tok.decode(generated, skip_special_tokens=True).strip()

# ---- model-free exact checkpoint restoration before any replay ----------------------------
def restore_progress(name, positions):
    # Protocol has already been verified remotely; a transient backend 404 must
    # STOP, never silently cause repeated formal test inference.
    rr = get_dataset(SAVE_HANDLE)
    csv = locate(rr, f'{name}_predictions.csv', False)
    status = locate(rr, f'{name}_status.json', False)
    assert (csv is None) == (status is None), f'INCOMPLETE_{name}_REMOTE_CHECKPOINT'
    if csv is None:
        return []
    meta = json.loads(status.read_text())
    assert meta['protocol_signature'] == protocol['signature'] and meta['phase'] == name
    assert sha(csv) == meta['csv_sha256']
    d = pd.read_csv(csv, keep_default_na=False)
    assert len(d) == meta['rows'] and len(d) <= len(positions)
    assert d.test_position.tolist() == positions[:len(d)]
    assert d.id.astype(str).tolist() == tref.iloc[d.test_position].id.astype(str).tolist()
    assert d.id.is_unique
    for row in d.itertuples(index=False):
        p = parse_camera(row.output_text)
        assert (p is not None) == (str(row.parse_ok).lower() == 'true')
        if p is not None:
            assert all(abs(a-b) < 1e-8 for a, b in zip(p, (float(row.roll_deg), float(row.pitch_deg), float(row.square_vfov_deg))))
    shutil.copy2(csv, STAGE / csv.name)
    shutil.copy2(status, STAGE / status.name)
    print('RESUMED VERIFIED', name, len(d), '/', len(positions))
    return d.to_dict('records')

def commit(name, rows):
    csv_name = f'{name}_predictions.csv'
    status_name = f'{name}_status.json'
    p = STAGE / csv_name
    pd.DataFrame(rows).to_csv(p, index=False)
    dump(status_name, {'phase': name, 'rows': len(rows), 'protocol_signature': protocol['signature'],
                       'csv_sha256': sha(p), 'prediction_frozen': True,
                       'MAE_calculated': False, 'Stable101_used': False})
    upload([csv_name, status_name], f'R20 V3 {name} committed model predictions, no performance metrics')

# ---- irrevocable test239 model predictions, resumable -------------------------------------
spec_positions = tref.index[tref.category.isin(SPECIAL)].tolist()
for name, positions in [('M0', list(range(239))), ('R19', spec_positions)]:
    rows = restore_progress(name, positions)
    for idx in tqdm(range(len(rows), len(positions)), desc=f'R20 V3 {name} batch=1'):
        pos = positions[idx]
        raw_text = generate_one(pos, specialist=(name == 'R19'))
        p = parse_camera(raw_text)
        row = tref.iloc[pos]
        rows.append({'test_position': int(pos), 'id': str(row.id), 'category': str(row.category),
                     'location_id': str(row.location_id), 'parse_ok': bool(p is not None),
                     'output_text': raw_text,
                     'roll_deg': float(p[0]) if p else np.nan,
                     'pitch_deg': float(p[1]) if p else np.nan,
                     'square_vfov_deg': float(p[2]) if p else np.nan})
        if len(rows) % 20 == 0 or len(rows) == len(positions):
            commit(name, rows)
    print(name, 'PREDICTIONS FROZEN:', len(rows), 'PARSED:', sum(bool(r['parse_ok']) for r in rows))

# ---- all predictions must be remotely immutable before any performance computation --------
required = ['M0_predictions.csv', 'M0_status.json', 'R19_predictions.csv', 'R19_status.json']
remote_verify(required)
m0 = pd.DataFrame(restore_progress('M0', list(range(239))))
m1 = pd.DataFrame(restore_progress('R19', spec_positions))
assert len(m0) == 239 and len(m1) == len(spec_positions)
print('ALL TEST MODEL PREDICTIONS FROZEN AND REMOTELY VERIFIED. PERFORMANCE REVEAL STARTS.')

# ---- unchanged original R18 P1-P4 ---------------------------------------------------------
base_ok = bool(m0.parse_ok.astype(str).str.lower().eq('true').all())
P1 = bool(m1.parse_ok.astype(str).str.lower().eq('true').all())
m0_data = m0[['id', 'parse_ok', 'roll_deg', 'pitch_deg', 'square_vfov_deg']].rename(
    columns={'parse_ok': 'm0_parse_ok', 'roll_deg': 'm0_roll_deg', 'pitch_deg': 'm0_pitch_deg',
             'square_vfov_deg': 'm0_square_vfov_deg'})
m1_data = m1[['id', 'parse_ok', 'pitch_deg']].rename(
    columns={'parse_ok': 'm1_parse_ok', 'pitch_deg': 'm1_pitch_deg'})
result = (tref[['id', 'category', 'location_id', 'reliable', 'pitch_uncertainty_deg', 'target_pitch_deg']]
          .merge(m0_data, on='id', validate='one_to_one')
          .merge(m1_data, on='id', how='left', validate='one_to_one'))
result['route'] = np.where(result.category.isin(SPECIAL), 'R19', 'M0')
result['m2_roll_deg'] = result.m0_roll_deg.copy()
result['m2_square_vfov_deg'] = result.m0_square_vfov_deg.copy()
result['m2_pitch_deg'] = np.where(result.category.isin(SPECIAL), result.m1_pitch_deg, result.m0_pitch_deg)
P3 = bool(np.array_equal(result.m2_roll_deg.to_numpy(), result.m0_roll_deg.to_numpy(), equal_nan=True))
P4 = bool(np.array_equal(result.m2_square_vfov_deg.to_numpy(), result.m0_square_vfov_deg.to_numpy(), equal_nan=True))
eval_pitch = result.loc[result.reliable].copy()
valid_eval = bool(base_ok and P1 and eval_pitch[['m0_pitch_deg','m2_pitch_deg','target_pitch_deg']].notna().all().all())
mae0 = mae2 = delta = None
P2 = False
if valid_eval:
    eval_pitch['m0_ae'] = (eval_pitch.m0_pitch_deg - eval_pitch.target_pitch_deg).abs()
    eval_pitch['m2_ae'] = (eval_pitch.m2_pitch_deg - eval_pitch.target_pitch_deg).abs()
    eval_pitch['delta'] = eval_pitch.m2_ae - eval_pitch.m0_ae
    mae0 = float(eval_pitch.m0_ae.mean())
    mae2 = float(eval_pitch.m2_ae.mean())
    delta = mae2 - mae0
    P2 = bool(mae2 < mae0)
PRIMARY_SUCCESS = bool(base_ok and P1 and P2 and P3 and P4)
cat_rows = []
for cat in ['event','heritage','natural','purpose_built']:
    sub = eval_pitch.loc[eval_pitch.category.eq(cat)]
    cat_rows.append({'category': cat, 'n': len(sub), 'locations': sub.location_id.nunique(),
                     'route': 'R19' if cat in SPECIAL else 'M0',
                     'M0_MAE': float(sub.m0_ae.mean()) if valid_eval and len(sub) else None,
                     'M2_MAE': float(sub.m2_ae.mean()) if valid_eval and len(sub) else None,
                     'delta': float(sub.delta.mean()) if valid_eval and len(sub) else None})
cat_table = pd.DataFrame(cat_rows)
boot = None
if valid_eval:
    cl = eval_pitch.groupby('location_id', sort=True).agg(n=('delta','size'), sum_delta=('delta','sum'))
    ns = cl.n.to_numpy(float)
    sums = cl.sum_delta.to_numpy(float)
    rng = np.random.default_rng(BOOT_SEED)
    draws = np.empty(BOOT_B)
    for b in range(BOOT_B):
        ii = rng.integers(0, len(cl), size=len(cl))
        draws[b] = sums[ii].sum()/ns[ii].sum()
    lo, hi = np.percentile(draws, [2.5,97.5])
    boot = {'unit': 'location_id', 'clusters': len(cl), 'B': BOOT_B,
            'CI95': [float(lo), float(hi)], 'fraction_delta_below_zero': float((draws<0).mean()),
            'role': 'descriptive only'}
verdict = {'run': 'R20_FINAL_ONE_TIME_TEST239_V3', 'protocol_signature': protocol['signature'],
           'pretest_signature': PRE_SIG, 'R19_adapter_sha256': R19_SHA,
           'test_rows': 239, 'test_locations': 16,
           'reliable_pitch_rows': len(eval_pitch), 'reliable_pitch_locations': eval_pitch.location_id.nunique(),
           'specialist_test_rows': len(spec_positions), 'm0_parse_100pct': base_ok,
           'specialist_parse_100pct': P1,
           'M0_pitch_MAE_deg': mae0, 'M2PAR_pitch_MAE_deg': mae2,
           'delta_M2_minus_M0_deg': delta,
           'relative_change_pct': 100*delta/mae0 if valid_eval and mae0 else None,
           'P1_specialist_parse': P1, 'P2_pitch_MAE_better': P2,
           'P3_roll_exact_M0': P3, 'P4_square_vfov_exact_M0': P4,
           'PRIMARY_SUCCESS': PRIMARY_SUCCESS, 'cluster_bootstrap': boot,
           'scientific_status': 'Post-hoc R18 pitch-only test; original R14 primary endpoint remains FAILED.',
           'training_performed': False, 'Stable101_reused': False, 'post_reveal_tuning_allowed': False}
result.to_csv(STAGE / 'R20_V3_final_predictions_reference.csv', index=False)
cat_table.to_csv(STAGE / 'R20_V3_category_summary.csv', index=False)
pd.DataFrame([{k:v for k,v in verdict.items() if not isinstance(v, dict)}]).to_csv(
    STAGE / 'R20_V3_summary.csv', index=False)
dump('R20_V3_final_verdict.json', verdict)
file_hashes = {p.name: sha(p) for p in sorted(STAGE.iterdir())
               if p.is_file() and p.name != 'R20_V3_sha256_manifest.json'}
dump('R20_V3_sha256_manifest.json', file_hashes)
upload(list(file_hashes) + ['R20_V3_sha256_manifest.json'], 'R20 V3 FINAL immutable one-time test239 verdict')
print('\n'+'='*110)
print('R20 FINAL ONE-TIME TEST239 RESULT')
print('='*110)
print(json.dumps(verdict, indent=2, ensure_ascii=False))
print('\nCATEGORY RESULTS\n'+cat_table.to_string(index=False))
print('FINAL REMOTE SHA256 VERIFIED. NO TRAINING. NO Stable101. NO RETUNING.')
