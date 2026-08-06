set -e
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

# ASR a .srt timeline
if [ -f "$OUTPUT_DIR/speech.srt" ]; then
	echo "Skip ASR: speech.srt already exists"
else
	python whisper-asr/extract_srt.py \
		--audio output/speech-norm.wav \
		--output_file output/speech.srt \
		--language zh
fi

# Split the normalized speech based on SRT timeline
if ls "$OUTPUT_DIR"/smart_chunk_*.wav 1> /dev/null 2>&1; then
	echo "Skip split: smart_chunk files already exist"
else
	python whisper-asr/split_wav_by_srt.py \
		--audio output/speech-norm.wav \
		--srt output/speech.srt \
		--out_dir output \
		--min_duration 5.0 \
		--max_duration 12.0
fi

CHECKPOINT_DIR=/mnt/asus_card/hfdownloader/meituan-longcat/LongCat-Video-Avatar-1.5
GPUS=0,1,3,4
export CUDA_DEVICE_ORDER=PCI_BUS_ID

# Read the initial image from the template
PREV_LAST_FRAME=$(jq -r .cond_image avatar-input.json)

# Loop through all audio chunks
for CHUNK_FILE in "$OUTPUT_DIR"/smart_chunk_*.wav; do
	# Extract the chunk name (e.g., smart_chunk_001)
	CHUNK_BASENAME=$(basename "$CHUNK_FILE" .wav)

	# Paths for this chunk
	CHUNK_JSON="$OUTPUT_DIR/${CHUNK_BASENAME}_input.json"
	CHUNK_INPUTS_PATH="$OUTPUT_DIR/${CHUNK_BASENAME}_inputs.pt"
	CHUNK_LATENT_PATH="$OUTPUT_DIR/${CHUNK_BASENAME}_latent.pt"
	CHUNK_OUT_DIR="$OUTPUT_DIR/${CHUNK_BASENAME}_out"

	echo "=========================================="
	echo "Processing $CHUNK_BASENAME"
	echo "=========================================="

	# Generate JSON for this chunk using the template
	# Use jq to update the JSON template cleanly
	jq --arg audio "$CHUNK_FILE" --arg img "$PREV_LAST_FRAME" \
		'.cond_audio.person1 = $audio | .cond_image = $img' \
		./avatar-input.json > "$CHUNK_JSON"

	# Prepare
	if [ -f "$CHUNK_INPUTS_PATH" ]; then
		echo "Skip prepare: $CHUNK_INPUTS_PATH already exists"
	else
		CUDA_VISIBLE_DEVICES="$GPUS" \
		python longcat-video-avatar/run_demo_avatar_single_low_vram.py prepare \
		--input_json "$CHUNK_JSON" --checkpoint_dir "$CHECKPOINT_DIR" \
		--cache_path "$CHUNK_INPUTS_PATH"
	fi

	# Denoise
	if [ -f "$CHUNK_LATENT_PATH" ]; then
		echo "Skip denoise: $CHUNK_LATENT_PATH already exists"
	else
		pushd longcat-video-avatar
		CUDA_VISIBLE_DEVICES="$GPUS" PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True \
		OMP_NUM_THREADS=1 python -m torch.distributed.run --standalone --nproc_per_node=4 \
		run_demo_avatar_single_low_vram.py denoise \
		--checkpoint_dir "$CHECKPOINT_DIR" \
		--cache_path "$CHUNK_INPUTS_PATH" \
		--latent_path "$CHUNK_LATENT_PATH" \
		--context_parallel_size 4 \
		--dit_subfolder base_model_int8_dmd_merged \
		--text_guidance_scale 2.0 \
		--sequential_block_cpu_offload \
		--block_offload_group_size 1
		popd
	fi

	# Decode
	if [ -f "$CHUNK_OUT_DIR/ai2v_demo_1_low_vram.mp4" ]; then
		echo "Skip decode: $CHUNK_OUT_DIR/ai2v_demo_1_low_vram.mp4 already exists"
	else
		pushd longcat-video-avatar
		CUDA_VISIBLE_DEVICES=4 python run_demo_avatar_single_low_vram.py decode \
		--checkpoint_dir "$CHECKPOINT_DIR" \
		--cache_path "$CHUNK_INPUTS_PATH" \
		--latent_path "$CHUNK_LATENT_PATH" \
		--output_dir "$CHUNK_OUT_DIR"
		popd
	fi

	# Extract the last frame to use as the cond_image for the next chunk (use relative path)
	PREV_LAST_FRAME="./output/${CHUNK_BASENAME}_last_frame.png"
	if [ ! -f "$PREV_LAST_FRAME" ]; then
		echo "Extracting last frame from $CHUNK_OUT_DIR/ai2v_demo_1_low_vram.mp4"
		ffmpeg -y -sseof -1 -i "$CHUNK_OUT_DIR/ai2v_demo_1_low_vram.mp4" -update 1 -q:v 1 "$PREV_LAST_FRAME"
	fi
done
