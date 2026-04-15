import os
from flask import Flask, request, send_file, jsonify, render_template_string
import matplotlib
import os
import zipfile
from werkzeug.utils import secure_filename

from dataset_service import DatasetService

matplotlib.use("Agg")  # IMPORTANT
from db import db, Dataset


import matplotlib.pyplot as plt

from bloodcells_clustering import ClusteringPipeline, ClusterMetrics, Plotter

app = Flask(__name__)

STATE = {}

PLOT_DIR = "static/plots"
os.makedirs(PLOT_DIR, exist_ok=True)


def save(path):
    plt.tight_layout()
    plt.savefig(path)
    plt.close()


@app.route("/")
def home():
    return render_template_string("""
    <h2>Clustering App</h2>

    <form action="/run" method="post">
        Dataset ID: <input name="dataset_id"><br><br>
        K: <input name="k" value="8"><br><br>
        <button type="submit">Run</button>
    </form>

    <br>

    <h3>Datasets</h3>
    <ul id="datasets"></ul>

    <script>
    fetch('/datasets')
      .then(r => r.json())
      .then(data => {
        const ul = document.getElementById('datasets');
        data.forEach(d => {
          const li = document.createElement('li');
          li.innerText = `${d.id}: ${d.name} (${d.path})`;
          ul.appendChild(li);
        });
      });
    </script>

    <br>
    <a href="/metrics">Metrics</a><br>
    <a href="/pca">PCA</a><br>
    <a href="/clusters">Clusters</a><br>
    <a href="/distribution">Distribution</a><br>
    <a href="/compare">Compare</a><br>
    
<h3>Upload Dataset</h3>

<form id="uploadForm">
    Name: <input name="name"><br><br>
    File: <input type="file" name="file"><br><br>
    <button type="submit">Upload</button>
</form>

<script>
document.getElementById("uploadForm").addEventListener("submit", async (e) => {
    e.preventDefault();

    const form = new FormData(e.target);

    const res = await fetch("/datasets/upload", {
        method: "POST",
        body: form
    });

    const data = await res.json();
    console.log(data);
    location.reload();
});
</script>
    """)


@app.route("/run", methods=["POST"])
def run():
    ds_id = int(request.form["dataset_id"])
    k = int(request.form["k"])

    ds = DatasetService.get_by_id(ds_id)
    if not ds:
        return "Dataset not found", 404

    f, l, files = ClusteringPipeline(ds.path, k).run()

    STATE["f"], STATE["l"], STATE["files"] = f, l, files

    return "Done ✔"


@app.route("/metrics")
def metrics():
    return jsonify(ClusterMetrics.compute(STATE["f"], STATE["l"]))


@app.route("/pca")
def pca():
    path = os.path.join(PLOT_DIR, "pca.png")
    f2d = Plotter.pca_2d(STATE["f"])

    Plotter.clusters_plot(f2d, STATE["l"])
    save(path)

    return send_file(path, mimetype="image/png")


@app.route("/clusters")
def clusters():
    path = os.path.join(PLOT_DIR, "clusters.png")
    f2d = Plotter.pca_2d(STATE["f"])

    Plotter.clusters_plot(f2d, STATE["l"])
    save(path)

    return send_file(path, mimetype="image/png")


@app.route("/distribution")
def distribution():
    path = os.path.join(PLOT_DIR, "dist.png")

    Plotter.distribution(STATE["l"], STATE["files"])
    save(path)

    return send_file(path, mimetype="image/png")


@app.route("/compare")
def compare():
    path = os.path.join(PLOT_DIR, "compare.png")
    f2d = Plotter.pca_2d(STATE["f"])

    Plotter.pca_compare(f2d, STATE["l"], STATE["files"])
    save(path)

    return send_file(path, mimetype="image/png")

@app.route("/datasets", methods=["POST"])
def create_dataset():
    data = request.json
    ds = DatasetService.create(data["name"], data["path"])
    return jsonify(ds.to_dict())

@app.route("/datasets", methods=["GET"])
def get_datasets():
    datasets = DatasetService.get_all()
    return jsonify([d.to_dict() for d in datasets])

@app.route("/datasets/<int:ds_id>", methods=["PUT"])
def update_dataset(ds_id):
    data = request.json
    ds = DatasetService.update(ds_id, data.get("name"), data.get("path"))

    if not ds:
        return {"error": "Not found"}, 404

    return jsonify(ds.to_dict())

@app.route("/datasets/<int:ds_id>", methods=["DELETE"])
def delete_dataset(ds_id):
    ok = DatasetService.delete(ds_id)

    if not ok:
        return {"error": "Not found"}, 404

    return {"message": "Deleted"}

UPLOAD_DIR = "uploaded_datasets"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.route("/datasets/upload", methods=["POST"])
def upload_dataset():
    file = request.files["file"]
    name = request.form.get("name")

    if not file:
        return {"error": "No file provided"}, 400

    filename = secure_filename(file.filename)
    zip_path = os.path.join(UPLOAD_DIR, filename)

    file.save(zip_path)

    extract_path = os.path.join(UPLOAD_DIR, filename.replace(".zip", ""))

    os.makedirs(extract_path, exist_ok=True)

    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extractall(extract_path)

    ds = DatasetService.create(name=name, path=extract_path)

    return {
        "message": "Dataset uploaded and saved successfully ✔",
        "dataset": ds.to_dict()
    }, 201



if __name__ == "__main__":
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///datasets.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)

    with app.app_context():
        db.create_all()

    app.run(debug=True, use_reloader=False)