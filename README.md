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
