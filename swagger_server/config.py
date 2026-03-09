"""Configuration for the student service."""
import os

# MongoDB configuration - use environment variables for flexibility
MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017")
MONGO_DATABASE = os.environ.get("MONGO_DATABASE", "student_db")
MONGO_COLLECTION = os.environ.get("MONGO_COLLECTION", "students")