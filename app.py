import uvicorn
from fastapi import FastAPI, UploadFile, File, BackgroundTasks
from fastapi.responses import FileResponse, RedirectResponse
import tempfile
import os
import shutil

from separate_demucs import separate

app = FastAPI(title="AiCapella")


@app.get("/", include_in_schema=False)
async def docs_redirect() -> RedirectResponse:
    """Redirect root path to API documentation."""
    return RedirectResponse(url="/docs")


def _cleanup(path: str) -> None:
    """Remove temporary directory."""
    shutil.rmtree(path, ignore_errors=True)


@app.post("/separate")
async def separate_route(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    """Separate uploaded audio file into stems using Demucs."""
    workdir = tempfile.mkdtemp(prefix="aicapella_")
    try:
        audio_path = os.path.join(workdir, file.filename)
        with open(audio_path, "wb") as f:
            f.write(await file.read())
        output_dir = os.path.join(workdir, "stems")
        separate(audio_path, output_dir)
        zip_path = shutil.make_archive(os.path.join(workdir, "stems"), "zip", output_dir)
        background_tasks.add_task(_cleanup, workdir)
        return FileResponse(zip_path, filename="stems.zip", media_type="application/zip")
    except Exception:
        _cleanup(workdir)
        raise

if __name__ == "__main__":
    uvicorn.run(app)