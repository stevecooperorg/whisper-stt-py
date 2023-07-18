# whisper-stt-py

A really simple Python script to convert audio files to text using OpenAI's Whisper APIs.

## Installation

```bash
make setup
```

## Usage

You need to feed it three folders; `--input` is a directory containing m4a files. Typically what you'd get out of a zoom recording. `--output` is where you want the final transcription written. `--splits` is where you want the intermediate files written. These are the files that are sent to the API for transcription -- usually 60s of audio so that whisper can handle it.

```bash
	cd src && python3 transcribe.py \
	   --input "/directory/with/your/mp4files" \
	   --output "/final/answer/goes/in/here" \
	   --splits "/intermediate/files/go/here"
```