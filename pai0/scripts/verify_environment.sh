#!/usr/bin/env bash
set -euo pipefail

readonly REPO="/home/xiao/pi0-reproduction/openpi"
readonly CACHE="/home/xiao/pi0-reproduction/cache"
readonly EXPECTED_COMMIT="215abfb217dbac7d5f1273282331b9b1866c0479"
readonly UV="/home/xiao/.local/bin/uv"

cd "$REPO"

actual_commit="$(git rev-parse HEAD)"
if [[ "$actual_commit" != "$EXPECTED_COMMIT" ]]; then
  echo "ERROR: openpi commit drifted: $actual_commit" >&2
  exit 1
fi

echo "[1/5] Locked environment"
"$UV" sync --locked --offline >/dev/null

echo "[2/5] Python and package imports"
"$UV" run python - <<'PY'
import platform
import jax
import torch
import openpi

print(f"python={platform.python_version()}")
print(f"jax={jax.__version__}")
print(f"torch={torch.__version__}")
print(f"openpi={openpi.__file__}")
PY

echo "[3/5] JAX GPU execution"
XLA_PYTHON_CLIENT_PREALLOCATE=false "$UV" run python - <<'PY'
import jax
import jax.numpy as jnp

x = jnp.arange(1024 * 1024, dtype=jnp.float32).reshape(1024, 1024)
y = (x @ x.T).block_until_ready()
assert jax.default_backend() == "gpu", jax.default_backend()
assert y.shape == (1024, 1024)
print(f"backend={jax.default_backend()} device={y.device} result={float(y[0, 0])}")
PY

echo "[4/5] Core unit tests"
JAX_PLATFORMS=cpu CUDA_VISIBLE_DEVICES= \
  HF_HUB_OFFLINE=1 \
  "$UV" run pytest -q \
    src/openpi/models/lora_test.py \
    src/openpi/models/tokenizer_test.py \
    src/openpi/shared/image_tools_test.py \
    src/openpi/shared/normalize_test.py \
    src/openpi/transforms_test.py \
    packages/openpi-client/src/openpi_client

JAX_PLATFORMS=cpu CUDA_VISIBLE_DEVICES= \
  "$UV" run pytest -q src/openpi/training/data_loader_test.py -k "not real_dataset"

echo "[5/5] Base checkpoint"
checkpoint="$CACHE/openpi-assets/checkpoints/pi0_base"
test -f "$checkpoint/params/_METADATA"
checkpoint_bytes="$(du -sb "$checkpoint" | cut -f1)"
echo "checkpoint=$checkpoint bytes=$checkpoint_bytes"

echo "PASS: openpi preparation environment is reproducible on this machine."

