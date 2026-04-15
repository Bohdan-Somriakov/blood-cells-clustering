import zipfile
import os


def extract_zip(zip_path, extract_path):
    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extractall(extract_path)

    items = os.listdir(extract_path)

    if len(items) == 1:
        inner = os.path.join(extract_path, items[0])

        if os.path.isdir(inner):
            for f in os.listdir(inner):
                src = os.path.join(inner, f)
                dst = os.path.join(extract_path, f)
                os.rename(src, dst)

            os.rmdir(inner)