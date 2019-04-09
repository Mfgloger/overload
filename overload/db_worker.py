# datastore functions

from sqlalchemy.orm import load_only, subqueryload


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


def retrieve_related(session, model, related, **kwargs):
    # retrieves a record and related data from other
    # tables based on created relationship
    instances = session.query(model).options(
        subqueryload(related)).filter_by(**kwargs).all()
    return instances


def retrieve_record(session, model, **kwargs):
    instance = session.query(model).filter_by(**kwargs).one()
    return instance


def delete_record(session, model, **kwargs):
    instance = session.query(model).filter_by(**kwargs).one()
    session.delete(instance)


def delete_records(session, model, **kwargs):
    instances = session.query(model).all()
    for instance in instances:
        session.delete(instance)


def create_db_object(model, **kwargs):
    instance = model(**kwargs)
    return instance
