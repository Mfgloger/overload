# datastore functions

from sqlalchemy.orm import load_only


from datastore import NYPLOrderTemplate


def update_nypl_template(session, otid, **kwargs):
    instance = session.query(NYPLOrderTemplate).filter_by(otid=otid).one()
    for key, value in kwargs.iteritems():
        setattr(instance, key, value)
        session.commit()
    session.close()


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
        load_only(*args)).all()
    return instances


def retrieve_record(session, model, **kwargs):
    instance = session.query(model).filter_by(**kwargs).one()
    return instance


def delete_record(session, model, **kwargs):
    instance = session.query(model).filter_by(**kwargs).one()
    session.delete(instance)
