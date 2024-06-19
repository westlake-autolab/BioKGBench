#!/usr/bin/bash
progress_bar() {
    local progress=$1
    local total=$2
    local width=50 
    local percent=$((progress * 100 / total))
    local completed=$((progress * width / total))
    local remaining=$((width - completed))

    local progress_bar=$(printf "%0.s#" $(seq 1 $completed))
    local remaining_bar=$(printf "%0.s-" $(seq 1 $remaining))

    printf "\rProgress: [%-${width}s] %d%%" "$progress_bar$remaining_bar" "$percent"
}

test_data_path=
output_path=
total_num=$(jq '. | length' "$test_data_path")

for i in $(seq 0 $total_num)
do
    instruction=$(python3 ./helper.py "$i")
    printf "\n%s\n" "$instruction" >> "$output_path"
    echo "Instruction for step $i: $instruction"
    /root/mambaforge/envs/autogen/bin/python3.11 ./team.py "$instruction"
    progress_bar $((i+1)) $total_num
    echo ""
done

echo
