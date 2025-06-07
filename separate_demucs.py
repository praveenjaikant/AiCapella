import argparse
import subprocess


def separate(audio_path: str, output_dir: str = "separated") -> None:
    """Run Demucs stem separation using the htdemucs_6s model.

    Parameters
    ----------
    audio_path: str
        Path to the input audio file.
    output_dir: str
        Directory where the separated stems will be written.
    """
    command = [
        "demucs",
        "-n",
        "htdemucs_ft",
        "-o",
        output_dir,
        audio_path,
    ]
    subprocess.run(command, check=True)