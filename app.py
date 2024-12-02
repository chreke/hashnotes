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
from markdown.extensions import Extension
from markdown.treeprocessors import Treeprocessor
from markupsafe import Markup
from pathlib import Path
from werkzeug.security import safe_join

app = Flask(__name__)

class ExtractMetaProcessor(Treeprocessor):
    @staticmethod
    def clean_string(string):
        return Markup(string).striptags()

    def run(self, root):
        metadata = {}
        first_heading = None
        first_paragraph = None

        for element in root:
            if element.tag == 'h1' and first_heading is None:
                if element.text:
                    first_heading = self.clean_string(element.text)
            elif element.tag == 'p' and first_paragraph is None:
                if element.text:
                    first_paragraph = self.clean_string(element.text)

            if first_heading and first_paragraph:
                break

        metadata["title"] = first_heading
        metadata["description"] = first_paragraph
        setattr(self.md, "metadata", metadata)
        return None

class ExtractMeta(Extension):
    def extendMarkdown(self, md):
        md.treeprocessors.register(ExtractMetaProcessor(md), "extract_meta", 150)

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
    return render_template(
        "index.html",
        title="Hashnotes",
        description="The easy way to share text online",
    )

@app.route("/edit/", methods=["GET", "POST"], defaults={"filename": ""})
@app.route("/edit/<filename>", methods=["GET", "POST"])
def edit(filename):
    content = ""
    if request.method == "POST":
        content = request.form["content"]
        # TODO: Proper form handling
        if len(content) > 10000:
            abort(400)
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
    return render_template("edit.html", title="Edit", content=content)

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
        md = markdown.Markdown(
            extensions=[
                "fenced_code",
                "codehilite",
                "smarty",
                "toc",
                "footnotes",
                ExtractMeta(),
            ])
        content = md.convert(f.read())
        metadata = getattr(md, "metadata")
    print("metadata", metadata)
    return render_template(
        "view.html",
        filename=filename,
        content=content,
        title=metadata["title"] or "Note",
        description=metadata["description"],
    )

# NOTE: Ensure that dir exists on startup
ensure_dir_exists(Path("notes"))
