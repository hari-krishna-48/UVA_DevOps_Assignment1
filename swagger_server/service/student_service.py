from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError

from swagger_server.config import MONGO_URI, MONGO_DATABASE, MONGO_COLLECTION

_client = None

def _get_db():
    """Get MongoDB database connection."""
    global _client
    if _client is None:
        _client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    return _client[MONGO_DATABASE]


def _students_collection():
    """Get students collection."""
    return _get_db()[MONGO_COLLECTION]


def _serialize_grade_records(grade_records):
    """Convert grade_records to list of dicts for storage."""
    if grade_records is None:
        return []
    result = []
    for gr in grade_records:
        if hasattr(gr, 'to_dict'):
            result.append(gr.to_dict())
        elif isinstance(gr, dict):
            result.append(gr)
        else:
            result.append({"subject_name": gr.subject_name, "grade": gr.grade})
    return result


def _next_student_id():
    """Get next student ID using max + 1."""
    coll = _students_collection()
    doc = coll.find_one(sort=[("student_id", -1)])
    return 1 if doc is None else doc["student_id"] + 1


def add(student=None):
    """Add a new student. Returns (student_id) or (message, status_code)."""
    try:
        coll = _students_collection()
        query = {
            "first_name": student.first_name,
            "last_name": student.last_name
        }
        if coll.find_one(query):
            return 'already exists', 409

        student_id = _next_student_id()
        doc = {
            "student_id": student_id,
            "first_name": student.first_name,
            "last_name": student.last_name,
            "grade_records": _serialize_grade_records(student.grade_records),
        }
        coll.insert_one(doc)
        student.student_id = student_id
        return student.student_id
    except ServerSelectionTimeoutError:
        return 'database unreachable', 503


def get_by_id(student_id=None, subject=None):
    """Get student by ID. Returns student dict or (message, status_code)."""
    try:
        coll = _students_collection()
        doc = coll.find_one({"student_id": int(student_id)})
        if not doc:
            return 'not found', 404
        # Remove MongoDB _id from response
        doc.pop("_id", None)
        return doc
    except (ValueError, TypeError):
        return 'invalid id', 400
    except ServerSelectionTimeoutError:
        return 'database unreachable', 503


def delete(student_id=None):
    """Delete student by ID. Returns student_id or (message, status_code)."""
    try:
        coll = _students_collection()
        result = coll.delete_one({"student_id": int(student_id)})
        if result.deleted_count == 0:
            return 'not found', 404
        return student_id
    except (ValueError, TypeError):
        return 'invalid id', 400
    except ServerSelectionTimeoutError:
        return 'database unreachable', 503


def get_average_grade_svc(student_id):
    """Get average grade for a student (Exercise 3.2).
    Returns (average_grade) or (message, status_code).
    Returns 404 if student does not exist or has no grades.
    """
    try:
        coll = _students_collection()
        doc = coll.find_one({"student_id": int(student_id)})
        if not doc:
            return 'not found', 404

        grade_records = doc.get("grade_records") or []
        if not grade_records:
            return 'not found', 404

        total = sum(gr["grade"] for gr in grade_records)
        average = round(total / len(grade_records), 2)
        return average
    except (ValueError, TypeError):
        return 'invalid id', 400
    except ServerSelectionTimeoutError:
        return 'database unreachable', 503
