import base64
import hashlib
import markdown

from flask import (
    abort,
    Flask,
    redirect,
    render_template,
    request,
)
from pathlib import Path
from werkzeug.security import safe_join

app = Flask(__name__)

def ensure_dir_exists(path):
    path.mkdir(parents=True, exist_ok=True)

def get_note_path(filename):
    if file_path := safe_join("notes", filename):
        path = Path(file_path)
        if not path.exists():
            return None
        else:
            return path
    return None


def get_digest(content):
    digest = hashlib.sha256(content.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(digest).decode("ascii")

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

# TODO: Add upper limit for text size
@app.route("/edit/", methods=["GET", "POST"], defaults={"filename": ""})
@app.route("/edit/<filename>", methods=["GET", "POST"])
def edit(filename):
    content = ""
    if request.method == "POST":
        content = request.form["content"]
        digest = get_digest(content)
        with open(f"notes/{digest}", "w") as f:
            f.write(content)
        return redirect(f"/{digest}")
    if filename:
        file_path = get_note_path(filename)
        if not file_path:
            abort(404)
        with open(file_path, "r") as f:
            content = f.read()
    return render_template("edit.html", content=content)

# TODO: Cache rendered Markdown somehow (add Nginx file cache?)
# TODO: Support deleting content by adding a "blocklist"
# TODO: Add cache headers (expiry time can theoretically be set to infinity,
# but this would not be compatible with the idea of "deleting" content)
@app.route("/<filename>", methods=["GET"])
def view(filename):
    path = get_note_path(filename)
    if not path:
        abort(404)
    with open(path, "r") as f:
        content = markdown.markdown(
            f.read(),
            extensions=[
                "fenced_code",
                "codehilite",
                "smarty",
                "toc",
                "footnotes",
        ])
    return render_template(
        "view.html", filename=filename, content=content)


# @app.route("/static/<path:path>")
# def static(path):
#     return send_from_directory("static", path)

# NOTE: Ensure that dir exists on startup
ensure_dir_exists(Path("notes"))
