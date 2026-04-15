import os
import numpy as np
import matplotlib
matplotlib.use("Agg")  # IMPORTANT for Flask (no GUI backend)
import matplotlib.pyplot as plt

from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.applications.mobilenet_v2 import MobileNetV2, preprocess_input
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import (
    silhouette_score,
    calinski_harabasz_score,
    davies_bouldin_score
)


# ----------------------- Data Loader -----------------------
class ImageLoader:
    def __init__(self, dataset_path):
        self.dataset_path = dataset_path

    def load(self, batch_size=32, target_size=(224, 224)):
        datagen = ImageDataGenerator(preprocessing_function=preprocess_input)
        gen = datagen.flow_from_directory(
            self.dataset_path,
            target_size=target_size,
            batch_size=batch_size,
            class_mode=None,
            shuffle=False
        )
        return gen, gen.filenames


# ------------------- Feature Extraction -------------------
class FeatureExtractor:
    def __init__(self, input_shape=(224, 224, 3)):
        self.model = MobileNetV2(
            weights="imagenet",
            include_top=False,
            pooling="avg",
            input_shape=input_shape
        )

    def extract(self, generator):
        return self.model.predict(generator, verbose=1)


# ----------------------- Clustering -----------------------
class Clusterer:
    def __init__(self, k):
        self.k = k

    def cluster(self, features):
        return KMeans(n_clusters=self.k, random_state=42).fit_predict(features)


# --------------------- Metrics ----------------------
class ClusterMetrics:
    @staticmethod
    def compute(features, labels):
        sil = silhouette_score(features, labels) if len(np.unique(labels)) > 1 else float("nan")
        ch = calinski_harabasz_score(features, labels)
        db = davies_bouldin_score(features, labels)

        return {
            "Silhouette": float(sil),
            "Calinski-Harabasz": float(ch),
            "Davies-Bouldin": float(db)
        }


# --------------------- Plotting ----------------------
class Plotter:

    @staticmethod
    def pca_2d(features):
        return PCA(n_components=2).fit_transform(features)

    @staticmethod
    def clusters_plot(features_2d, labels):
        plt.figure(figsize=(10, 8))
        for c in np.unique(labels):
            idx = labels == c
            plt.scatter(features_2d[idx, 0], features_2d[idx, 1], label=f"Cluster {c}")
        plt.legend()
        plt.title("PCA Clusters")

    @staticmethod
    def distribution(labels, filenames):
        classes = np.array([os.path.basename(os.path.dirname(f)) for f in filenames])
        uniq_c = np.unique(classes)
        uniq_k = np.unique(labels)

        dist = np.zeros((len(uniq_k), len(uniq_c)))

        c_map = {c: i for i, c in enumerate(uniq_c)}

        for l, c in zip(labels, classes):
            dist[np.where(uniq_k == l)[0][0], c_map[c]] += 1

        bottom = np.zeros(len(uniq_k))

        plt.figure(figsize=(10, 6))
        for i, c in enumerate(uniq_c):
            plt.bar(uniq_k, dist[:, i], bottom=bottom, label=c)
            bottom += dist[:, i]

        plt.title("Cluster Distribution")
        plt.legend()

    @staticmethod
    def pca_compare(features_2d, labels, filenames):
        classes = np.array([os.path.basename(os.path.dirname(f)) for f in filenames])
        uniq = np.unique(classes)
        cmap = {c: i for i, c in enumerate(uniq)}
        cls_idx = np.array([cmap[c] for c in classes])

        # Increased height to accommodate the legend at the bottom
        fig, ax = plt.subplots(1, 3, figsize=(22, 10))

        # ---------------- Clusters ----------------
        for c in np.unique(labels):
            ax[0].scatter(*features_2d[labels == c].T, label=f"Cluster {c}", s=10, alpha=0.6)
        ax[0].set_title("Clusters")
        ax[0].legend(fontsize=8, loc='upper right')
        ax[0].grid(True)

        # ---------------- Classes ----------------
        for i, c in enumerate(uniq):
            ax[1].scatter(*features_2d[cls_idx == i].T, label=c, s=10, alpha=0.6)
        ax[1].set_title("Classes")
        ax[1].legend(fontsize=8, loc='upper right')
        ax[1].grid(True)

        # ---------------- Combined ----------------
        for c in np.unique(labels):
            for i, cls in enumerate(uniq):
                idx = (labels == c) & (cls_idx == i)
                if np.any(idx):
                    ax[2].scatter(
                        features_2d[idx, 0],
                        features_2d[idx, 1],
                        label=f"{cls}/C{c}",
                        s=10,
                        alpha=0.6
                    )

        ax[2].set_title("Combined")
        ax[2].legend(
            loc='upper center',
            bbox_to_anchor=(0.5, -0.15),
            ncol=5,
            fontsize=7,
            frameon=True
        )
        ax[2].grid(True)

        plt.tight_layout()

        plt.subplots_adjust(bottom=0.25)

        return fig


# ---------------------- Pipeline -----------------------
class ClusteringPipeline:
    def __init__(self, path, k):
        self.path = path
        self.k = k

    def run(self):
        loader = ImageLoader(self.path)
        gen, files = loader.load()

        features = FeatureExtractor().extract(gen)
        labels = Clusterer(self.k).cluster(features)

        return features, labels, files