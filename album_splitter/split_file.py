import subprocess
from pathlib import Path
from typing import Dict, List
import ffmpy

from .parse_tracks import Track

def sanitize_filename(filename):
    # Replace invalid characters and trim length if necessary
    invalid_chars = ['<', '>', ':', '"', '/', '\\', '|', '?', '*']
    for char in invalid_chars:
        filename = filename.replace(char, '')
    return filename[:255]  # Limit filename length for safety

def ensure_directory(file_path):
    directory = Path(file_path).parent
    directory.mkdir(parents=True, exist_ok=True)

def split_file(
    input_file: Path, tracks: List[Track], destination: Path, output_format: str
):
    # Ensure the destination directory exists
    ensure_directory(destination)

    # Get the duration of the input file
    duration_command = ffmpy.FFprobe(
        inputs={str(input_file): '-show_entries format=duration -v quiet -of csv="p=0"'}
    )
    stdout, _ = duration_command.run(stdout=subprocess.PIPE)
    file_duration = float(stdout.decode().strip())

    outputs: Dict[Path, str] = {}
    max_zero_padding = len(str(len(tracks)))

    for i, track in enumerate(tracks):
        start_timestamp = track.start_timestamp
        end_timestamp = (
            file_duration if i == len(tracks) - 1 else tracks[i + 1].start_timestamp
        )

        # Sanitize the track title to make a valid filename
        sanitized_title = sanitize_filename(track.title)
        output_filename = f"{str(i + 1).zfill(max_zero_padding)} {sanitized_title}.{output_format}"
        output_file = destination / output_filename

        # Ensure directory for each output file exists
        ensure_directory(output_file)

        outputs[output_file] = f"-vn -c copy -ss {start_timestamp} -to {end_timestamp}"

    # Print the command for debugging
    ffmpeg_command = ffmpy.FFmpeg(
        inputs={str(input_file): "-y -hide_banner -loglevel error -stats"},
        outputs={str(path): v for path, v in outputs.items()},
    )
    print("Running command:")
    print(ffmpeg_command.cmd)

    try:
        ffmpeg_command.run()
    except Exception as e:
        print("FFmpeg error:")
        print(e)
        raise Exception(
            "Something went wrong with the splitting procedure. See the error above."
        ) from e

    return list(outputs.keys())
