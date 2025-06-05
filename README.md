# AiCapella

Custom GPT that helps users generate Acapella tracks.

## Stem Separation

The repository now provides a simple script for separating audio
tracks into stems using the Demucs `htdemucs_6s` model. You can run it
from the command line as follows:

```bash
python separate_demucs.py path/to/input.wav -o output_directory
```

The script requires the `demucs` package to be installed and will
write all stems to the specified output directory.

## Installation

The project uses `conda` for managing the Python environment. You can create
and activate a new environment and then install the Python dependencies with
`pip`:

```bash
conda create -n aicapella python=3.10
conda activate aicapella
pip install -r requirements.txt
```

Demucs requires `ffmpeg` to handle audio files. On macOS you can install it
with [Homebrew](https://brew.sh/):

```bash
brew install ffmpeg
```

After installing the dependencies you can run stem separation as described
above.
