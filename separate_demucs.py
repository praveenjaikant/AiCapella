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
        "htdemucs_6s",
        "-o",
        output_dir,
        audio_path,
    ]
    subprocess.run(command, check=True)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Separate audio into stems using the htdemucs_6s model.")
    parser.add_argument("audio", help="Path to the input audio file")
    parser.add_argument(
        "-o",
        "--output",
        default="separated",
        help="Directory to store the separated stems",
    )
    args = parser.parse_args()
    separate(args.audio, args.output)


if __name__ == "__main__":
    main()
