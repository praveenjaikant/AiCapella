import uvicorn
from fastapi import FastAPI, UploadFile, File, BackgroundTasks, Form
from fastapi.responses import RedirectResponse
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import (
    Mail,
    Attachment,
    FileContent,
    FileName,
    FileType,
    Disposition,
)
import base64
import tempfile
import os
import shutil

from separate_demucs import separate


def _send_email(zip_path: str, recipient: str) -> None:
    """Send the zip archive to the recipient using SendGrid."""
    api_key = os.environ.get("SENDGRID_API_KEY")
    from_addr = os.environ.get("SENDGRID_FROM")
    if not api_key or not from_addr:
        raise RuntimeError("SENDGRID_API_KEY and SENDGRID_FROM must be set")

    with open(zip_path, "rb") as f:
        data = f.read()

    encoded = base64.b64encode(data).decode()
    attachment = Attachment(
        FileContent(encoded),
        FileName(os.path.basename(zip_path)),
        FileType("application/zip"),
        Disposition("attachment"),
    )

    message = Mail(
        from_email=from_addr,
        to_emails=recipient,
        subject="Separated stems",
        plain_text_content="See attached archive for your separated stems.",
    )
    message.attachment = attachment

    sg = SendGridAPIClient(api_key)
    sg.send(message)


def _send_error_email(recipient: str, error: str) -> None:
    """Notify the recipient that stem separation failed using SendGrid."""
    api_key = os.environ.get("SENDGRID_API_KEY")
    from_addr = os.environ.get("SENDGRID_FROM")
    if not api_key or not from_addr:
        raise RuntimeError("SENDGRID_API_KEY and SENDGRID_FROM must be set")

    message = Mail(
        from_email=from_addr,
        to_emails=[recipient, os.environ.get("ADMIN_EMAIL")],
        subject="Stem separation failed",
        plain_text_content=f"There was an error during stem separation:\n\n{error}",
    )

    sg = SendGridAPIClient(api_key)
    sg.send(message)


def _separate_and_email(audio_path: str, output_dir: str, workdir: str, recipient: str) -> None:
    """Run separation and email the resulting zip file."""
    try:
        separate(audio_path, output_dir)
        song_name = os.path.splitext(os.path.basename(audio_path))[0]
        stems_dir = os.path.join(output_dir, "htdemucs_ft", song_name)
        zip_path = shutil.make_archive(os.path.join(workdir, song_name), "zip", stems_dir)
        _send_email(zip_path, recipient)
    except Exception as exc:
        try:
            _send_error_email(recipient, str(exc))
        except Exception:
            pass
        raise
    finally:
        _cleanup(workdir)

app = FastAPI(title="AiCapella")


@app.get("/", include_in_schema=False)
async def docs_redirect() -> RedirectResponse:
    """Redirect root path to API documentation."""
    return RedirectResponse(url="/docs")


def _cleanup(path: str) -> None:
    """Remove temporary directory."""
    shutil.rmtree(path, ignore_errors=True)


@app.post("/separate")
async def separate_route(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    email: str = Form(...),
):
    """Separate uploaded audio file into stems and email the result."""
    workdir = tempfile.mkdtemp(prefix="aicapella_")
    try:
        audio_path = os.path.join(workdir, file.filename)
        with open(audio_path, "wb") as f:
            f.write(await file.read())
        output_dir = os.path.join(workdir, "stems")
        background_tasks.add_task(_separate_and_email, audio_path, output_dir, workdir, email)
        return {"detail": f"Processing started. Results will be emailed to {email}."}
    except Exception:
        _cleanup(workdir)
        raise

if __name__ == "__main__":
    uvicorn.run(app)
