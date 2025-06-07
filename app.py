import uvicorn
from fastapi import FastAPI, UploadFile, File, BackgroundTasks, Form
from fastapi.responses import RedirectResponse
from email.message import EmailMessage
import smtplib
import tempfile
import os
import shutil

from separate_demucs import separate


def _send_email(zip_path: str, recipient: str) -> None:
    """Send the zip archive to the recipient via Gmail SMTP."""
    user = os.environ.get("GMAIL_USER")
    password = os.environ.get("GMAIL_PASS")
    if not user or not password:
        raise RuntimeError("GMAIL_USER and GMAIL_PASS must be set")

    msg = EmailMessage()
    msg["Subject"] = "Separated stems"
    msg["From"] = user
    msg["To"] = recipient
    with open(zip_path, "rb") as f:
        data = f.read()
    msg.add_attachment(data, maintype="application", subtype="zip", filename="stems.zip")

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(user, password)
        smtp.send_message(msg)


def _send_error_email(recipient: str, error: str) -> None:
    """Notify the recipient that stem separation failed."""
    user = os.environ.get("GMAIL_USER")
    password = os.environ.get("GMAIL_PASS")
    if not user or not password:
        raise RuntimeError("GMAIL_USER and GMAIL_PASS must be set")

    msg = EmailMessage()
    msg["Subject"] = "Stem separation failed"
    msg["From"] = user
    msg["To"] = recipient
    msg.set_content(f"There was an error during stem separation:\n\n{error}")

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(user, password)
        smtp.send_message(msg)


def _separate_and_email(audio_path: str, output_dir: str, workdir: str, recipient: str) -> None:
    """Run separation and email the resulting zip file."""
    try:
        separate(audio_path, output_dir)
        zip_path = shutil.make_archive(os.path.join(workdir, "stems"), "zip", output_dir)
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