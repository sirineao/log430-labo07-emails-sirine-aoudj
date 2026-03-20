"""
Users (write-only model)
SPDX - License - Identifier: LGPL - 3.0 - or -later
Auteurs : Gabriel C. Ullmann, Fabio Petrillo, 2025
"""
import json
import datetime
from orders.commands.user_event_producer import UserEventProducer
from orders.models.user import User
from db import get_sqlalchemy_session

USER_TYPE_MAPPING = {
    1: 'client',
    2: 'employee',
    3: 'manager'
}

def get_user_type_name(user_type_id):
    """Convert user_type_id to string type name"""
    return USER_TYPE_MAPPING.get(user_type_id, 'client')

def add_user(name: str, email: str, user_type_id: int = 1):
    """Insert user with items in MySQL"""
    if not name or not email:
        raise ValueError("Cannot create user. A user must have name and email.")
    
    session = get_sqlalchemy_session()

    try: 
        new_user = User(name=name, email=email)
        if hasattr(new_user, 'user_type_id'):
            new_user.user_type_id = user_type_id
        
        session.add(new_user)
        session.flush() 
        session.commit()

        user_type_id_value = getattr(new_user, 'user_type_id', user_type_id) if hasattr(new_user, 'user_type_id') else user_type_id
        user_type_name = get_user_type_name(user_type_id_value)

        user_event_producer = UserEventProducer()
        user_event_producer.get_instance().send('user-events', value={'event': 'UserCreated', 
                                           'id': new_user.id, 
                                           'name': new_user.name,
                                           'email': new_user.email,
                                           'user_type': user_type_name,
                                           'user_type_id': user_type_id_value,
                                           'datetime': str(datetime.datetime.now())})
        return new_user.id
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()

def delete_user(user_id: int):
    """Delete user in MySQL"""
    session = get_sqlalchemy_session()
    try:
        user = session.query(User).filter(User.id == user_id).first()
        if user:
            user_type_id_value = getattr(user, 'user_type_id', 1) if hasattr(user, 'user_type_id') else 1
            user_type_name = get_user_type_name(user_type_id_value)
            
            user_data = {
                'id': user.id,
                'name': user.name,
                'email': user.email,
                'user_type': user_type_name,
                'user_type_id': user_type_id_value
            }
            
            session.delete(user)
            session.commit()
            
            user_event_producer = UserEventProducer()
            user_event_producer.get_instance().send('user-events', value={'event': 'UserDeleted',
                                               'id': user_data['id'],
                                               'name': user_data['name'],
                                               'email': user_data['email'],
                                               'user_type': user_data['user_type'],
                                               'user_type_id': user_data['user_type_id'],
                                               'datetime': str(datetime.datetime.now())})
            return 1  
        else:
            return 0  
            
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()