from db import db, Dataset


class DatasetService:

    @staticmethod
    def create(name, path):
        ds = Dataset(name=name, path=path)
        db.session.add(ds)
        db.session.commit()
        return ds

    @staticmethod
    def get_all():
        return Dataset.query.all()

    @staticmethod
    def get_by_id(ds_id):
        return Dataset.query.get(ds_id)

    @staticmethod
    def update(ds_id, name=None, path=None):
        ds = Dataset.query.get(ds_id)
        if not ds:
            return None

        if name:
            ds.name = name
        if path:
            ds.path = path

        db.session.commit()
        return ds

    @staticmethod
    def delete(ds_id):
        ds = Dataset.query.get(ds_id)
        if not ds:
            return False

        db.session.delete(ds)
        db.session.commit()
        return True