import os
import random

from flask import Blueprint, request, jsonify, send_file
from werkzeug.utils import secure_filename
from app.utils.zip_utils import extract_zip
import zipfile

from app.services.dataset_service import DatasetService
from app.extensions.db import db

bp = Blueprint("datasets", __name__)


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
        extract_zip(zip_path, extract_path)
    except Exception as e:
        return {"error": f"Unzip failed: {str(e)}"}, 500

    ds = DatasetService.create(name=name, path=extract_path)

    return {
        "message": "Dataset uploaded and extracted ✔",
        "dataset": ds.to_dict()
    }, 201


@bp.route("/datasets/<int:ds_id>/preview", methods=["GET"])  # Added the missing route
def dataset_preview(ds_id):
    ds = DatasetService.get_by_id(ds_id)
    if not ds:
        return {"error": "Dataset not found in database"}, 404

    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

    full_dataset_path = os.path.abspath(ds.path)

    images = []
    if not os.path.exists(full_dataset_path):
        return {"error": f"Directory not found at {full_dataset_path}"}, 404

    for root, _, files in os.walk(full_dataset_path):
        for f in files:
            if f.lower().endswith((".jpg", ".jpeg", ".png")):
                full_path = os.path.join(root, f)
                images.append(full_path)

    if not images:
        return {"error": "No images found in the dataset folder"}, 404

    return send_file(random.choice(images))