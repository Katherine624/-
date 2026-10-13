#!/usr/bin/env bash
set -u

# Evaluation only: published pi0_libero checkpoint served separately on port 8000.
# Keep each suite's raw log and every rollout video, then archive that suite.
project=/root/autodl-tmp/pi0-project
openpi=/root/autodl-tmp/openpi
python=/root/autodl-tmp/libero-py38/bin/python
run_root="$project/reports/libero-runs/2026-09-29-official-50"
mkdir -p "$run_root"

export PYTHONPATH="$openpi/third_party/libero:$openpi/packages/openpi-client/src"
export LIBERO_CONFIG_PATH="$project/config/libero-runtime"
export MUJOCO_GL=egl

started_epoch=$(date +%s)
deadline_epoch=$((started_epoch + 15300)) # 4 h 15 min, leaving transfer time before watchdog shutdown.
printf 'run_started=%s\nmodel_source=official-published\ncheckpoint=%s\nopenpi_commit=%s\ntrials_per_task=50\nseed=7\nreplan_steps=5\nevaluation_deadline=%s\n' \
  "$(date -Is)" \
  /root/autodl-tmp/openpi-assets/checkpoints/pi0_libero \
  "$(git -C "$openpi" rev-parse HEAD)" \
  "$(date -d "@$deadline_epoch" -Is)" > "$run_root/run-manifest.txt"

for suite in libero_10 libero_spatial libero_object libero_goal; do
  now=$(date +%s)
  remaining=$((deadline_epoch - now))
  if (( remaining < 300 )); then
    printf '%s\tSKIPPED_DEADLINE\t%s\n' "$suite" "$(date -Is)" >> "$run_root/progress.tsv"
    continue
  fi

  suite_dir="$run_root/$suite"
  mkdir -p "$suite_dir/videos"
  log="$suite_dir/evaluation.log"
  printf '%s\tSTARTED\t%s\n' "$suite" "$(date -Is)" >> "$run_root/progress.tsv"
  {
    printf 'RUN_START=%s\n' "$(date -Is)"
    printf 'SUITE=%s\nTRIALS_PER_TASK=50\nSEED=7\nSOURCE=official-published\n' "$suite"
  } > "$log"

  timeout --signal=INT --kill-after=30s "${remaining}s" \
    "$python" "$project/scripts/libero_eval_preserve_videos.py" \
      --args.host 127.0.0.1 \
      --args.task-suite-name "$suite" \
      --args.num-trials-per-task 50 \
      --args.replan-steps 5 \
      --args.seed 7 \
      --args.video-out-path "$suite_dir/videos" >> "$log" 2>&1
  exit_code=$?
  printf '\nRUN_EXIT=%s\nRUN_END=%s\n' "$exit_code" "$(date -Is)" >> "$log"

  video_count=$(find "$suite_dir/videos" -maxdepth 1 -type f -name '*.mp4' | wc -l)
  printf '%s\tEXIT_%s\t%s\tVIDEOS_%s\n' "$suite" "$exit_code" "$(date -Is)" "$video_count" >> "$run_root/progress.tsv"
  tar -czf "$run_root/${suite}.tar.gz" -C "$run_root" "$suite"
  sha256sum "$run_root/${suite}.tar.gz" > "$run_root/${suite}.sha256"
  printf '%s\tARCHIVED\t%s\tBYTES_%s\n' "$suite" "$(date -Is)" "$(stat -c %s "$run_root/${suite}.tar.gz")" >> "$run_root/progress.tsv"
done

printf 'RUNNER_END=%s\n' "$(date -Is)" >> "$run_root/run-manifest.txt"
printf 'RUNNER_DONE\t%s\n' "$(date -Is)" >> "$run_root/progress.tsv"
