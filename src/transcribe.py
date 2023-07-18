from collections import defaultdict
from pydub import AudioSegment
from typing import List
import fnmatch
import openai
import os
import re
import argparse
from pathlib import Path


def split_audio(input_file: str, output_dir: str, segment_length: int = 600000, desired_ext: str = ".mp3") -> List[str]:
    audio = AudioSegment.from_file(input_file)
    audio_length_ms = len(audio)
    base_name, ext = os.path.splitext(os.path.basename(input_file))

    os.makedirs(output_dir, exist_ok=True)

    output_files = []

    for i, start_time in enumerate(range(0, audio_length_ms, segment_length)):
        end_time = start_time + segment_length
        segment = audio[start_time:end_time]
        segment_file = os.path.join(output_dir, f"{base_name}-{i + 1:03d}{desired_ext}")

        if not os.path.exists(segment_file):
            print("writing %s" % segment_file)
            segment.export(segment_file, format=desired_ext[1:]).close()
        else:
            print("skipping %s" % segment_file)
        output_files.append(segment_file)

    return output_files


def find_files_with_extension(directory: str, extension: str) -> List[str]:
    print("searching %s for files with extension %s" % (directory, extension))
    return [os.path.join(root, filename)
            for root, _, filenames in os.walk(directory)
            for filename in fnmatch.filter(filenames, f'*.{extension}')]


def get_relative_path(filename: str, current_path: str) -> str:
    current_dir = os.path.dirname(current_path)
    rel_path = os.path.join(current_dir,  filename)
    return rel_path


def path_without_number(path: str) -> str:
    # takes a path like /downloads/audio/file1-001.mp3 and returns /downloads/audio/file1.mp3

    # dirname = /downloads/audio, filename = file1-001.mp3
    dirname, filename = os.path.split(path)

    # eg file_root = file1
    file_root, _, _ = filename.rpartition('-')

    # ext = mp3
    _, ext = os.path.splitext(filename)

    return os.path.join(dirname, file_root + ext)


def group_files_by_number(file_paths: List[str]) -> defaultdict:
    file_groups: defaultdict = defaultdict(list)
    for file in file_paths:
        group_file = path_without_number(file)
        file_groups[group_file].append(file)

    for _, group_files in file_groups.items():
        group_files.sort(key=lambda f: int(re.search(r'\d+', f).group()))

    return file_groups


def transcript_path_for_audio_path(audio_path: str, ext: str = "txt") -> str:
    root, old_ext = os.path.splitext(audio_path)
    return root + '.' + ext

# Create the parser
parser = argparse.ArgumentParser(description="Parse the directory path")

# Add the arguments
parser.add_argument("--input", type=str, required=True, help="Relative directory path to the audio files to transcribe (*.m4a)")
parser.add_argument("--output", type=str, required=True, help="Relative directory path to the transcribed files (*.txt)")
parser.add_argument("--splits", type=str, required=True, help="Where will split audio files be stored?")

# Execute parse_args()
args = parser.parse_args()

input_dir_name: str = get_relative_path(args.input, __file__)
print("input dir name: " + input_dir_name)

unsplit_files: List[str] = find_files_with_extension(input_dir_name, "m4a")
for unsplit_file in unsplit_files:
    print("unsplit audio file: %s" % unsplit_file)

splits_dir: str = get_relative_path(args.splits, __file__)
print("splits dir: " + splits_dir)

output_dir_name: str = get_relative_path(args.output, __file__)
print("output dir: " + output_dir_name)

# split the original audio files
audio_files = [
    split_filename
    for unsplit_filename in unsplit_files
    for split_filename in split_audio(os.path.join(input_dir_name, unsplit_filename), splits_dir)]


for audio_file in audio_files:
    print("split audio file: %s" % audio_file)

prompt: str = "the prompt is a team meeting where software engineers are discussing a new feature or architecture concern."
extension: str = "out.txt"

input_files: List[str] = find_files_with_extension(splits_dir, "mp3")
for input_file in input_files:
    print("input audio file: %s" % input_file)

audio_files_and_transcripts = [
    (audio_file, transcript_path_for_audio_path(audio_file))
    for audio_file in audio_files]

for (audio_file, transcript_file) in audio_files_and_transcripts:
    print(f"audio file: {audio_file} - transcript: {transcript_file}")
    if os.path.exists(transcript_file):
        print(f"transcript: {transcript_file} - already exists - will be skipped")
    else:
        print(f"transcript: {transcript_file} - does not exist - will be transcribed")


for (audio_file, transcript_file) in audio_files_and_transcripts:
    if not os.path.exists(transcript_file):
        print(f"New file does not exist: {transcript_file} - transcribing")

        with open(audio_file, "rb") as audio_file:
            transcript = openai.Audio.transcribe("whisper-1", audio_file, prompt=prompt, response_format="text",
                                                 language="en")

        print(f"New file transcribed to {len(transcript)} characters")

        with open(transcript_file, "w") as new_file:
            new_file.write(transcript)

print("done transcribing")

print("concatenating files")

transcript_files = [transscript_file for _, transscript_file in audio_files_and_transcripts]

for transcript_file in transcript_files:
    print("transcript file: %s" % transcript_file)

groups = group_files_by_number(transcript_files)

for group_file, group_files in groups.items():
    concatenated_content = '\n'.join([open(file, 'r').read() for file in group_files])
    os.makedirs(output_dir_name, exist_ok=True)
    out_file_path = os.path.join(output_dir_name, os.path.basename(group_file))

    with open(out_file_path, 'w') as out_file:
        print("writing %s chars to %s" % (len(concatenated_content), out_file_path))
        out_file.write(concatenated_content)
