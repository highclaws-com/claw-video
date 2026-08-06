set -ex
OUTPUT_DIR=`pwd`/output
mkdir -p $OUTPUT_DIR

pushd qwen-tts
CUDA_VISIBLE_DEVICES=2 python clone.py \
	--text_file input-long.txt --language Chinese \
	--ref_audio ref.mp3 --ref_text ref.txt \
	--output $OUTPUT_DIR/speech.wav
popd

CHECKPOINT_DIR=/mnt/asus_card/hfdownloader/LongCat-Video-Avatar-1.5
GPUS=0,1,3,4
export CUDA_DEVICE_ORDER=PCI_BUS_ID

python longcat-video-avatar/run_demo_avatar_single_low_vram.py prepare \
	--input_json ./avatar-input.json --checkpoint_dir "$CHECKPOINT_DIR" \
	--cache_path $OUTPUT_DIR/inputs.pt

CUDA_VISIBLE_DEVICES="$GPUS" PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True \
OMP_NUM_THREADS=1 python -m torch.distributed.run --standalone --nproc_per_node=4 \
	run_demo_avatar_single_low_vram.py denoise \
	--checkpoint_dir "$CHECKPOINT_DIR" \
	--cache_path "$OUTPUT_DIR/inputs.pt" \
	--latent_path "$OUTPUT_DIR/latent.pt" \
	--context_parallel_size 4 \
	--dit_subfolder base_model_int8_dmd_merged \
	--text_guidance_scale 3.0 \
	--sequential_block_cpu_offload \
	--block_offload_group_size 16

CUDA_VISIBLE_DEVICES=4 python run_demo_avatar_single_low_vram.py decode \
	 --checkpoint_dir "$CHECKPOINT_DIR" \
	--cache_path "$OUTPUT_DIR/inputs.pt" \
	--latent_path "$OUTPUT_DIR/latent.pt" \
	--output_dir "$OUTPUT_DIR"
