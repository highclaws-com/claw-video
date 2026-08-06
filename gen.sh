set -ex
OUTPUT_DIR=`pwd`/output
mkdir -p $OUTPUT_DIR

# TTS
if [ -f "$OUTPUT_DIR/speech.wav" ]; then
	echo "Skip TTS: speech.wav already exists"
else
	pushd qwen-tts
	CUDA_VISIBLE_DEVICES=2 python clone.py \
		--text_file input-long.txt --language Chinese \
		--ref_audio ref.mp3 --ref_text ref.txt \
		--output $OUTPUT_DIR/speech.wav
	popd
fi

# Normalize loudness
if [ -f "$OUTPUT_DIR/speech-norm.wav" ]; then
	echo "Skip normalize: speech-norm.wav already exists"
else
	ffmpeg -y -i "$OUTPUT_DIR/speech.wav" -af loudnorm "$OUTPUT_DIR/speech-norm.wav"
	echo "Normalized -> speech-norm.wav"
fi

CHECKPOINT_DIR=/mnt/asus_card/hfdownloader/LongCat-Video-Avatar-1.5
GPUS=0,1,3,4
export CUDA_DEVICE_ORDER=PCI_BUS_ID

# Prepare
if [ -f "$OUTPUT_DIR/inputs.pt" ]; then
	echo "Skip prepare: inputs.pt already exists"
else
	python longcat-video-avatar/run_demo_avatar_single_low_vram.py prepare \
		--input_json ./avatar-input.json --checkpoint_dir "$CHECKPOINT_DIR" \
		--cache_path $OUTPUT_DIR/inputs.pt
fi

# Denoise
if [ -f "$OUTPUT_DIR/latent.pt" ]; then
	echo "Skip denoise: latent.pt already exists"
else
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
fi

# Decode
if [ -f "$OUTPUT_DIR/output.mp4" ]; then
	echo "Skip decode: output.mp4 already exists"
else
	CUDA_VISIBLE_DEVICES=4 python run_demo_avatar_single_low_vram.py decode \
		 --checkpoint_dir "$CHECKPOINT_DIR" \
		--cache_path "$OUTPUT_DIR/inputs.pt" \
		--latent_path "$OUTPUT_DIR/latent.pt" \
		--output_dir "$OUTPUT_DIR"
fi
