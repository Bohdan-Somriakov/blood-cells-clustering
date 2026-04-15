import os
from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
import zipfile

from app.services.dataset_service import DatasetService
from app.extensions.db import db

bp = Blueprint("datasets", __name__)

# ⚠️ Better to move this outside project in real use
UPLOAD_DIR = "uploaded_datasets"
os.makedirs(UPLOAD_DIR, exist_ok=True)


# -------------------- GET ALL --------------------
@bp.route("/datasets", methods=["GET"])
def get_datasets():
    datasets = DatasetService.get_all()
    return jsonify([d.to_dict() for d in datasets])


# -------------------- CREATE (manual path, optional) --------------------
@bp.route("/datasets", methods=["POST"])
def create_dataset():
    data = request.json

    if not data or "name" not in data or "path" not in data:
        return {"error": "Invalid input"}, 400

    ds = DatasetService.create(data["name"], data["path"])
    return jsonify(ds.to_dict()), 201


# -------------------- DELETE --------------------
@bp.route("/datasets/<int:ds_id>", methods=["DELETE"])
def delete_dataset(ds_id):
    ok = DatasetService.delete(ds_id)

    if not ok:
        return {"error": "Not found"}, 404

    return {"message": "Deleted ✔"}


# -------------------- UPLOAD ZIP --------------------
@bp.route("/datasets/upload", methods=["POST"])
def upload_dataset():
    file = request.files.get("file")
    name = request.form.get("name")

    if not file or not name:
        return {"error": "Missing file or name"}, 400

    filename = secure_filename(file.filename)

    if not filename.endswith(".zip"):
        return {"error": "Only ZIP files allowed"}, 400

    zip_path = os.path.join(UPLOAD_DIR, filename)
    file.save(zip_path)

    extract_path = os.path.join(UPLOAD_DIR, filename.replace(".zip", ""))
    os.makedirs(extract_path, exist_ok=True)

    try:
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(extract_path)
    except Exception as e:
        return {"error": f"Unzip failed: {str(e)}"}, 500

    ds = DatasetService.create(name=name, path=extract_path)

    return {
        "message": "Dataset uploaded and extracted ✔",
        "dataset": ds.to_dict()
    }, 201