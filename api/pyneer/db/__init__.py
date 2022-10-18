"""
Pyneer's `db.*` API
"""
import json
import sys
import os
import uuid

from api.pyneer.db import handlers

DEFAULT_DATABASE_PATH = 'database/db.json'


def insert_one(collection, document, file_path=DEFAULT_DATABASE_PATH):
    """ This function create single record in the collection

    :param collection: Collection to be used to store the data
    :param document: Data in the form of a dictionary
    :param file_path: File used to store the data

    e.g. document = {'key': 'value', ...}

    Note: If the collection does not exist, it will be created.
    """

    with handlers.file_handler(mode='r+', file_path=file_path) as f:
        if f['message']:
            return {"message": f['message'], "action": False}

        loaded_data = f["loaded_data"]

        if not isinstance(document, dict) or document == {}:
            return {"message": "Action failed.", "action": False}

        if collection in loaded_data:
            loaded_data[collection].append(document)

            f['file'].seek(0)
            json.dump(loaded_data, f['file'], indent=2)

            return {"message": "Action successful.", "action": True}

        else:
            create_collection(collection=collection, file_path=file_path)
            insert_one(collection=collection, document=document, file_path=file_path)

            return {"message": "Action successful.", "action": True}


def insert_many(collection, documents, file_path=DEFAULT_DATABASE_PATH):
    """This function create single record in the collection

    :param collection: Collection to be used to store the data
    :param documents: Data in the form of a dictionary
    :param file_path: File used to store the data

    e.g. documents = [{'key': 'value', ...}, {'key': 'value', ...}]

    Note: If the collection does not exist, it will be created.
    Note: If the document = {} then it will skip.
    """

    with handlers.file_handler(mode='r+', file_path=file_path) as f:
        if f['message']:
            return {"message": f['message'], "action": False}

        loaded_data = f["loaded_data"]

        if isinstance(documents, list) and documents != []:
            if collection in loaded_data:
                for i in documents:
                    if i != {}:
                        loaded_data[collection].append(i)

                    else:
                        continue

                f['file'].seek(0)
                json.dump(loaded_data, f['file'], indent=2)

                return {"message": "Action successful.", "action": True}

            create_collection(collection=collection, file_path=file_path)
            insert_many(collection=collection, documents=documents, file_path=file_path)

            return {"message": "Action successful.", "action": True}

        else:
            return {"message": "Action failed.", "action": False}


def read(collection, query, file_path=DEFAULT_DATABASE_PATH):
    """This function reads a record from the collection

    :param collection: Collection to be used to store the data
    :param query: An array of keys to be queried from the collection
    :param file_path: File used to read the data

    e.g. query = ['username', 'password', 'role']

    Note: If query = [] then all the documents in the collection will be returned.
    Note: If key does not exist, it will be skipped.
   """

    new_lists = []

    with handlers.file_handler(mode='r', file_path=file_path) as f:
        if f['message']:
            return {"message": f['message'], "action": False}

        loaded_data = f["loaded_data"]

        if isinstance(query, list):
            if query:
                for i in loaded_data[collection]:
                    new_dict = {}

                    for key in query:
                        if key in i:
                            new_dict[key] = i[key]
                            new_lists.append(new_dict)

                        else:
                            continue

                return {"message": "Action successful.", "action": True,"matched_count": len(new_lists), "result": new_lists}

            return {"message": "Action successful.", "action": True,"matched_count": len(loaded_data[collection]), "result": loaded_data[collection]}

        else:
            return {"message": "Action failed.", "action": False}


def find(collection, query, file_path=DEFAULT_DATABASE_PATH):
    """This function will query from 'file' and return a result
    with all the data that matches the key and value.

    :param collection: Collection's name
    :param query: The query to be used to search the database
    :param file_path: The file used to find the data

    e.g. query = {'key': 'value', ...}
    Note: If nothing is found, it will return an empty list, [].
    Note: If query = {} then all the documents in the collection will be returned.
    """

    read_data = read(collection=collection, query=[], file_path=file_path)

    if read_data['action'] and read_data['result'] and isinstance(query, dict):
        r = filtr(field=query, data=read_data['result'])

        return {"message": "Action successful.", "action": True,'matched_count': r['matched_count'], "result": r['result']}

    else:
        return {'action': False, 'message': 'Action failed.'}


def filtr(data, field):
    """This function will filter the data based on the field

    :param data: The data to be filtered
    :param field: The field to be used to filter the data

    e.g. field = {'key': 'value', ...}
    e.g. data = [{'key': 'value', ...}, {'key': 'value', ...}]
    """

    result = list(filter(lambda x: all(item in x.items() for item in field.items()), data))
    matched_count = len(result)

    return {'acknowledge': True if matched_count > 0 else False, 'matched_count': matched_count, 'result': result}


def update_one(collection, select, update, file_path=DEFAULT_DATABASE_PATH):
    """This function update a single record in the collection

    :param collection: The collection to be used to store the data
    :param select: select: The filter to be used to identify the record to be updated
    :param update: The data to be used to update the record
    :param file_path: The file used to update the data

    e.g. select = {'key': 'value', ...}
    e.g. update = {'key': 'value', ...}

    Note: If the Key in the select does not exist, it will be created and the value will be updated.
    Note: This method will only update the first record that matches the select.
    """

    with handlers.file_handler(mode='r', file_path=file_path) as f:
        if f['message']:
            return {"message": f['message'], "action": False}

        loaded_data = f["loaded_data"]

    try:
        if isinstance(select, dict) and isinstance(update, dict) and update != {}:
            a = filtr(field=select, data=loaded_data[collection])

            if a['acknowledge']:
                for i in a['result']:
                    for key, value in update.items():
                        i[key] = value

                    break

                with open(file_path, 'w+') as f:
                    f.seek(0)
                    json.dump(loaded_data, f, indent=2)

                return {"message": "Action successful.", "action": True, "modified_count": 1,
                        "matched_count": a['matched_count']}

            else:
                return {"message": "Action failed.", "action": False, "modified_count": 0,
                        "matched_count": a['matched_count']}

        else:
            return {"message": "Action failed.", "action": False}

    except KeyError:
        return {"message": "Invalid Key or Value.", "action": False}


def update_many(collection, select, update, file_path=DEFAULT_DATABASE_PATH):
    """
    This function updates multiple records in the collection

    :param collection: The collection to be used to store the data
    :param select: select: The filter to be used to identify the records to be updated
    :param update: The data to be used to update the records
    :param file_path: The file used to update the data

    e.g. select = {'key': 'value', ...}
    e.g. update = {'key': 'value', ...}
    """

    with handlers.file_handler(mode='r', file_path=file_path) as f:
        if f['message']:
            return {"message": f['message'], "action": False}

        loaded_data = f["loaded_data"]

    try:
        modified_count = 0
        if isinstance(select, dict) and isinstance(update, dict) and update != {}:
            a = filtr(field=select, data=loaded_data[collection])

            if a['acknowledge']:
                for i in a['result']:
                    for key, value in update.items():
                        i[key] = value

                    modified_count += 1

                with open(file_path, 'w+') as f:
                    f.seek(0)
                    json.dump(loaded_data, f, indent=2)

                return {"message": "Action successful.", "action": True, "modified_count": modified_count,
                        "matched_count": a['matched_count']}

            else:
                return {"message": "Action failed.", "action": False, "modified_count": modified_count,
                        "matched_count": a['matched_count']}

        else:
            return {"message": "Action failed.", "action": False}

    except KeyError:
        return {"message": "Invalid Key or Value.", "action": False}


def replace_one(collection, select, replacement, file_path=DEFAULT_DATABASE_PATH):
    """This function replace a single record in the collection

    :param collection: The collection to be used to store the data
    :param select: The filter to be used to identify the record to be replaced
    :param replacement: The replacement to be used to replace the record
    :param file_path: The file used to store the data

    e.g. select = {'key': 'value', ...}
    e.g. replacement = {'key': 'value', ...}
    Note: This method will only update the first record that matches the select.
    """

    with handlers.file_handler(mode='r', file_path=file_path) as f:
        if f['message']:
            return {"message": f['message'], "action": False}

        loaded_data = f["loaded_data"]

    try:
        if isinstance(select, dict) and select != {} and isinstance(replacement, dict) and replacement != {}:
            a = filtr(field=select, data=loaded_data[collection])

            if a['acknowledge']:
                for i in a['result']:
                    i.clear()
                    i.update(replacement)
                    break

                with open(file_path, 'w+') as f:
                    f.seek(0)
                    json.dump(loaded_data, f, indent=2)

                return {"message": "Action successful.", "action": True, "modified_count": 1,
                        "matched_count": a['matched_count']}
            else:
                return {"message": "Action failed.", "action": False, "modified_count": 0,
                        "matched_count": a['matched_count']}

        else:
            return {"message": "Action failed.", "action": False}

    except KeyError:
        return {"message": "Invalid Key or Value.", "action": False}


def delete_one(collection, select, file_path=DEFAULT_DATABASE_PATH):
    """This function deletes a record from the collection

    :param collection: The collection to be used to store the data
    :param select: The filter to be used to identify the record to be deleted
    :param file_path: The file used to store the data

    e.g. select = {'key': 'value', ...}
    """

    with handlers.file_handler(mode='r', file_path=file_path) as f:
        if f['message']:
            return {"message": f['message'], "action": False}

        loaded_data = f["loaded_data"]

    try:
        if isinstance(select, dict) and select != {}:
            a = filtr(field=select, data=loaded_data[collection])

            if a['acknowledge']:
                for i in a['result']:
                    loaded_data[collection].remove(i)
                    break

                with open(file_path, 'w+') as f:
                    f.seek(0)
                    json.dump(loaded_data, f, indent=2)

                return {"message": "Action successful.", "action": True, "deleted_count": 1,
                        "matched_count": a['matched_count']}
            else:
                return {"message": "Action failed.", "action": False, "deleted_count": 0,
                        "matched_count": a['matched_count']}

        else:
            return {"message": "Action failed.", "action": False}

    except KeyError:
        return {"message": "Invalid Key or Value.", "action": False}


def delete_many(collection, select, file_path=DEFAULT_DATABASE_PATH):
    """
    This function delete multiple records from the collection

    :param collection: The collection to be used to store the data
    :param select: The filters to be used to identify the records to be deleted
    :param file_path: The file used to store the data

    e.g. select = {'key': 'value', ...}
    where key and value is the key value used to identify the records to be deleted.
    """

    with handlers.file_handler(mode='r', file_path=file_path) as f:
        if f['message']:
            return {"message": f['message'], "action": False}

        loaded_data = f["loaded_data"]

    try:
        if isinstance(select, dict) and select != {}:
            a = filtr(field=select, data=loaded_data[collection])

            if a['acknowledge']:
                for i in a['result']:
                    loaded_data[collection].remove(i)

                with open(file_path, 'w+') as f:
                    f.seek(0)
                    json.dump(loaded_data, f, indent=2)

                return {"message": "Action successful.", "action": True, "deleted_count": a['matched_count'],
                        "matched_count": a['matched_count']}
            else:
                return {"message": "Action failed.", "action": False, "deleted_count": 0,
                        "matched_count": a['matched_count']}

        else:
            return {"message": "Action failed.", "action": False}

    except KeyError:
        return {"message": "Invalid Key or Value.", "action": False}


def create_db(file_path):
    """This function creates a database file

    :param file_path: The file used to store the data
    """

    try:
        with open(file_path, mode='x', encoding='utf-8') as f:
            json.dump({}, f, indent=2)

        return {"message": "Successfully.", "action": True}

    except FileExistsError as e:
        return {"message": str(e), "action": False}


def create_collection(collection, file_path=DEFAULT_DATABASE_PATH):
    """This function creates a collection

    :param collection: The collection to be created
    :param file_path: The file used to store the data
    """

    with handlers.file_handler(mode='r+', file_path=file_path) as f:
        if f['message']:
            return {"message": f['message'], "action": False}

        loaded_data = f["loaded_data"]

        try:
            if collection not in loaded_data and collection != '':
                loaded_data[collection] = []

                f['file'].seek(0)
                json.dump(loaded_data, f['file'], indent=2)
                f['file'].close()

                return {"message": "Successfully.", "action": True}

            else:
                return {"message": "Collection already exists or Invalid collection name", "action": False}

        except KeyError:
            return {"message": "Invalid Key or Value.", "action": False}


def drop_db(file_path=DEFAULT_DATABASE_PATH):
    """This function deletes a database file

    :param file_path: The file used to store the data
    """

    try:
        os.remove(file_path)

        return {"message": "Successfully.", "action": True}

    except FileNotFoundError as e:
        return {"message": str(e), "action": False}


def drop_collection(collection, file_path=DEFAULT_DATABASE_PATH):
    """This function deletes a collection

    :param collection: The collection to be deleted
    :param file_path: The file used to store the data
    """

    with handlers.file_handler(mode='r+', file_path=file_path) as f:
        if f['message']:
            return {"message": f['message'], "action": False}

        loaded_data = f["loaded_data"]

    try:
        if collection in loaded_data:
            loaded_data.pop(collection)

            with open(file_path, mode='w+', encoding='utf-8') as f:
                json.dump(loaded_data, f, indent=2)

            return {"message": "Successfully.", "action": True}

        else:
            return {"message": "Collection does not exist or Invalid collection name", "action": False}

    except KeyError:
        return {"message": "Invalid Key or Value.", "action": False}


def count(collection, query, file_path=DEFAULT_DATABASE_PATH):
    """This function counts the number of records in a collection

    :param collection: The collection to be used to store the data
    :param query: The filter to be used to identify the records to be counted
    :param file_path: The file used to store the data

    Note: If query = {} then it counts all the documents in the collection.
    """

    read_data = find(query=query, collection=collection, file_path=file_path)

    if read_data['action']:
        return {"message": "Successfully.", "action": True, "count": len(read_data['result'])}

    return {"message": "Collection does not exist or Invalid collection name", "action": False}


def generate_id(collection, file_path=DEFAULT_DATABASE_PATH):
    """This function will get the last id of the collection and add 1 to it.

    :param collection: The collection name
    :param file_path: The file used to store the data
    """
    read_data = read(collection=collection, query=['id'], file_path=file_path)

    if read_data['action'] and read_data['result']:
        new_id = int(read_data['result'][-1]["id"]) + 1
        return {'action': True, 'message': "", 'result': new_id}

    return {'action': False, 'message': 'No data found.'}


def generate_uuid(salt):
    """This function will generate an uuid

    :param salt: The salt to be used to generate the uuid, which can be a string or a number
    """

    return uuid.uuid5(uuid.NAMESPACE_DNS, str(salt))


def db():
    """This function will return all the databases in 'database' folder
    """

    files = os.listdir('database')

    return files


def total_size(collection, file_path=DEFAULT_DATABASE_PATH):
    """This function will return the total size of the collection

    :param collection: The collection name
    :param file_path: The file used to store the data
    """

    loaded_data = read(collection=collection, query=[], file_path=file_path)

    if loaded_data['action']:
        return {'action': True, 'message': '', 'result': str(sys.getsizeof(loaded_data['result'])) + ' bytes'}

    return {'action': False, 'message': 'No data found.'}