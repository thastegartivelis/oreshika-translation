#!/usr/bin/env bash
set -Eeuo pipefail

TOTAL_STEPS=11
CURRENT_STEP=0
LAST_PERCENT=0
# Latest measured durations with about 10% headroom, in seconds.
STAGE_ESTIMATES=(1 1 24 2 11 55 1 1 1 15 15)
STAGE_LABELS=()
STAGE_ACTUALS=()
TOTAL_ESTIMATE=0
for estimate in "${STAGE_ESTIMATES[@]}"; do
    TOTAL_ESTIMATE=$((TOTAL_ESTIMATE + estimate))
done
BUILD_LOG=$(mktemp)
trap 'rm -f "$BUILD_LOG"' EXIT

format_eta() {
    local seconds=$1
    if ((seconds >= 60)); then
        printf '%dm%02ds' "$((seconds / 60))" "$((seconds % 60))"
    else
        printf '%ds' "$seconds"
    fi
}

draw_progress() {
    local step=$1
    local step_elapsed=$2
    local label=$3
    local width=24
    local current_estimate=${STAGE_ESTIMATES[step]}
    local remaining=$((current_estimate - step_elapsed))
    local completed_estimate=0
    local estimated_elapsed

    # Once a stage exceeds its estimate, hold its contribution at zero rather
    # than increasing the ETA. Progress likewise stops at this step's boundary.
    if ((remaining < 0)); then
        remaining=0
    fi
    if ((step_elapsed > current_estimate)); then
        step_elapsed=$current_estimate
    fi

    for ((i = step + 1; i < TOTAL_STEPS; i++)); do
        remaining=$((remaining + STAGE_ESTIMATES[i]))
    done
    for ((i = 0; i < step; i++)); do
        completed_estimate=$((completed_estimate + STAGE_ESTIMATES[i]))
    done

    estimated_elapsed=$((completed_estimate + step_elapsed))
    local percent=$((estimated_elapsed * 100 / TOTAL_ESTIMATE))
    ((percent > 99)) && percent=99
    if ((percent < LAST_PERCENT)); then
        percent=$LAST_PERCENT
    else
        LAST_PERCENT=$percent
    fi
    local filled=$((percent * width / 100))
    local eta
    local eta_seconds=$remaining
    ((eta_seconds < 1)) && eta_seconds=1
    eta=$(format_eta "$eta_seconds")

    printf '\r['
    for ((i = 0; i < width; i++)); do
        if ((i < filled)); then printf '#'; else printf ' '; fi
    done
    printf '] %3d%% ETA %s | %s' "$percent" "$eta" "$label"
}

run_step() {
    local label=$1
    shift
    local show_output=0
    if [[ ${1:-} == "--show-output" ]]; then
        show_output=1
        shift
    fi
    local spinner='|/-.'
    local frame=0
    local status
    local stage_start=$SECONDS
    local stage_elapsed=0

    : >"$BUILD_LOG"
    draw_progress "$CURRENT_STEP" "$stage_elapsed" "$label ${spinner:0:1}"
    "$@" >"$BUILD_LOG" 2>&1 &
    local command_pid=$!

    while kill -0 "$command_pid" 2>/dev/null; do
        sleep 0.5
        stage_elapsed=$((SECONDS - stage_start))
        frame=$(((frame + 1) % 4))
        draw_progress "$CURRENT_STEP" "$stage_elapsed" "$label ${spinner:frame:1}"
    done

    if wait "$command_pid"; then
        stage_elapsed=$((SECONDS - stage_start))
        STAGE_LABELS+=("$label")
        STAGE_ACTUALS+=("$stage_elapsed")
        CURRENT_STEP=$((CURRENT_STEP + 1))
        if ((CURRENT_STEP == TOTAL_STEPS)); then
            printf '\r['
            printf '%24s' '' | tr ' ' '#'
            printf '] 100%% | Complete: %s' "$label"
        else
            draw_progress "$CURRENT_STEP" 0 "$label"
        fi
        printf '\n'
        if ((show_output)); then
            cat "$BUILD_LOG"
        fi
    else
        status=$?
        printf '\nBuild failed during: %s\n' "$label" >&2
        cat "$BUILD_LOG" >&2
        return "$status"
    fi
}

run_step "Fetch translations" curl -fsSL "https://docs.google.com/spreadsheets/d/1WGbyOT_U6ErMef8GOxGm7yQcT9sqpaA6POoba4LsbTA/export?gid=973457807&format=csv" -o translations.csv
run_step "Warn about title text limits" --show-output python3 ../research/decompilation/scripts/MeasureGameTextWidths.py translations.csv --warn-limits
run_step "Remove old extracted data" rm -rf data
run_step "Copy original data pack" cp "Original game/PSP_Game/USRDIR/data.ore" .
run_step "Unpack data pack" python3 data.ore_unpack_v1.py
run_step "Unpack game archives" python3 EZBIND_Unpack_Folder_v4.py
run_step "Apply translations" python3 autosubstitute.py
run_step "Compress translated text" python3 MLB_compress_v1.py
run_step "Pack game archives" python3 EZBIND_Pack_v2.py
run_step "Repack data pack" python3 data.ore_pack_v2.py
run_step "Generate patched ISO" bash -c 'mv data_new.ore "Rebuilt game/PSP_Game/USRDIR/data.ore" && ./umdgenc_cli.sh'

printf 'Build complete.\n'
printf 'Stage durations (seconds):\n'
for ((i = 0; i < TOTAL_STEPS; i++)); do
    printf '  %-28s %s\n' "${STAGE_LABELS[i]}" "${STAGE_ACTUALS[i]}"
done
