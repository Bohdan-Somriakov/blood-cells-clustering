import os
from flask import Blueprint, request, send_file, jsonify

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from app.services.dataset_service import DatasetService
from app.core.clustering_routes import ClusteringPipeline, ClusterMetrics, Plotter

bp = Blueprint("clustering", __name__)

STATE = {}

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PLOT_DIR = os.path.join(BASE_DIR, "static", "plots")

os.makedirs(PLOT_DIR, exist_ok=True)


def save(path):
    plt.tight_layout()
    plt.savefig(path)
    plt.close()


# -------------------- RUN --------------------
@bp.route("/run", methods=["POST"])
def run():
    ds_id = int(request.form["dataset_id"])
    k = int(request.form["k"])

    ds = DatasetService.get_by_id(ds_id)
    if not ds:
        return {"error": "Dataset not found"}, 404

    features, labels, files = ClusteringPipeline(ds.path, k).run()

    STATE["f"] = features
    STATE["l"] = labels
    STATE["files"] = files

    return {"message": "Clustering completed ✔"}


# -------------------- METRICS --------------------
@bp.route("/metrics")
def metrics():
    if "f" not in STATE:
        return {"error": "Run clustering first"}, 400

    return jsonify(ClusterMetrics.compute(STATE["f"], STATE["l"]))


# -------------------- PCA --------------------
@bp.route("/pca")
def pca():
    if "f" not in STATE:
        return {"error": "Run clustering first"}, 400

    path = os.path.join(PLOT_DIR, "pca.png")

    f2d = Plotter.pca_2d(STATE["f"])
    Plotter.clusters_plot(f2d, STATE["l"])
    save(path)

    return send_file(path, mimetype="image/png")


# -------------------- CLUSTERS --------------------
@bp.route("/clusters")
def clusters():
    if "f" not in STATE:
        return {"error": "Run clustering first"}, 400

    path = os.path.join(PLOT_DIR, "clusters.png")

    f2d = Plotter.pca_2d(STATE["f"])
    Plotter.clusters_plot(f2d, STATE["l"])
    save(path)

    return send_file(path, mimetype="image/png")


# -------------------- DISTRIBUTION --------------------
@bp.route("/distribution")
def distribution():
    if "f" not in STATE:
        return {"error": "Run clustering first"}, 400

    path = os.path.join(PLOT_DIR, "dist.png")

    Plotter.distribution(STATE["l"], STATE["files"])
    save(path)

    return send_file(path, mimetype="image/png")


# -------------------- COMPARE --------------------
@bp.route("/compare")
def compare():
    if "f" not in STATE:
        return {"error": "Run clustering first"}, 400

    path = os.path.join(PLOT_DIR, "compare.png")

    f2d = Plotter.pca_2d(STATE["f"])
    Plotter.pca_compare(f2d, STATE["l"], STATE["files"])
    save(path)

    return send_file(path, mimetype="image/png")