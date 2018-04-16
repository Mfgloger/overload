# datastore functions

from sqlalchemy.orm import load_only


def insert_or_ignore(session, model, **kwargs):
    """
    adds data to specified table
    if data is found to exist in the table nothing is added
    args:
        sqlalchemy session obj
        model table class
    kwargs:
        values to be entered to the table
    """

    instance = session.query(model).filter_by(**kwargs).first()
    if not instance:
        instance = model(**kwargs)
        session.add(instance)
    return instance


def retrieve_values(session, model, *args, **kwargs):
    instances = session.query(model).filter_by(**kwargs).options(
        load_only(*args)).order_by(model.timestamp.desc()).all()
    session.close()
    return instances
