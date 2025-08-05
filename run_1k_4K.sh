#!/bin/bash

num_prompts_list=(8 16 16  48 256 384 512 512 1024)
max_concurrency=(1 2 4 8 16 32  64 128 256 512 1024)
input_output_pairs=(
    "128 128 "
    "256 256"
    "128  2048"
    "2048 128"
   "1024  1024"
    "2048  2048"
       
)

model_dir="Qwen3-235B-A22B"
log_dir="benchmark_logs/${model_dir}"
mkdir -p "$log_dir"

for pair in "${input_output_pairs[@]}"; do
    IFS=' ' read -r input_len output_len <<< "$pair"
    
    for i in "${!num_prompts_list[@]}"; do
        num_prompts="${num_prompts_list[$i]}"
        concurrency="${max_concurrency[$i]}"
        
        log_file="${log_dir}/il${input_len}_ol${output_len}_np${num_prompts}_mc${concurrency}.log"

        echo "---------------------------------------------"
        echo "Running benchmark with:"
        echo "Input: ${input_len} | Output: ${output_len} | Total: ${num_prompts} | Concurrency: ${concurrency}"

        python benchmark_serving.py \
            --host 192.2.111.66 \
	    --backend vllm \
            --model "/home/model/${model_dir}" \
	    --served-model-name ${model_dir} \
            --dataset_name random \
            --random_input_len "$input_len" \
            --random_output_len "$output_len" \
            --num-prompts "$num_prompts" \
            --max-concurrency "$concurrency" \
            --ignore-eos \
            --port 8000 2>&1 | tee "$log_file"

        sleep 30
    done
done

echo "All benchmark combinations completed!"

