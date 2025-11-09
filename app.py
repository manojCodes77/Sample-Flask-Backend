# from flask import Flask, jsonify, request
from flask import Flask, jsonify, request
from flask_cors import CORS
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.exc import OperationalError
from datetime import datetime
import os
from dotenv import load_dotenv
from pathlib import Path

# Load .env from the server directory explicitly (robust against different CWDs)
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Database setup
raw_url = os.getenv("DATABASE_URL")
# Fallback if env var is missing or empty
DATABASE_URL = raw_url or "postgresql+psycopg2://postgres:postgres@localhost:5432/notes_db"

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


class Note(Base):
    __tablename__ = "notes"
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "content": self.content or "",
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


def init_db():
    try:
        Base.metadata.create_all(bind=engine)
    except OperationalError as e:
        # Provide a friendly message if the DB is unreachable
        raise RuntimeError(
            f"Failed to connect to database. Ensure PostgreSQL is running and DATABASE_URL is correct. Original error: {e}"
        )


@app.route("/", methods=["GET"])
def index():
    return jsonify({"status": "ok"})


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


# Notes CRUD
@app.route("/api/notes", methods=["GET"])
def list_notes():
    session = SessionLocal()
    try:
        notes = session.query(Note).order_by(Note.created_at.desc()).all()
        return jsonify([n.to_dict() for n in notes])
    finally:
        session.close()


@app.route("/api/notes", methods=["POST"])
def create_note():
    payload = request.get_json(silent=True) or {}
    title = (payload.get("title") or "").strip()
    content = (payload.get("content") or "").strip()
    if not title:
        return jsonify({"error": "title is required"}), 400
    session = SessionLocal()
    try:
        now = datetime.utcnow()
        note = Note(title=title, content=content, created_at=now, updated_at=now)
        session.add(note)
        session.commit()
        session.refresh(note)
        return jsonify(note.to_dict()), 201
    finally:
        session.close()


@app.route("/api/notes/<int:note_id>", methods=["GET"])
def get_note(note_id: int):
    session = SessionLocal()
    try:
        note = session.get(Note, note_id)
        if not note:
            return jsonify({"error": "not found"}), 404
        return jsonify(note.to_dict())
    finally:
        session.close()


@app.route("/api/notes/<int:note_id>", methods=["PUT"])
def update_note(note_id: int):
    payload = request.get_json(silent=True) or {}
    session = SessionLocal()
    try:
        note = session.get(Note, note_id)
        if not note:
            return jsonify({"error": "not found"}), 404
        title = payload.get("title")
        content = payload.get("content")
        if title is not None:
            note.title = title.strip()
        if content is not None:
            note.content = content.strip()
        note.updated_at = datetime.utcnow()
        session.commit()
        session.refresh(note)
        return jsonify(note.to_dict())
    finally:
        session.close()


@app.route("/api/notes/<int:note_id>", methods=["DELETE"])
def delete_note(note_id: int):
    session = SessionLocal()
    try:
        note = session.get(Note, note_id)
        if not note:
            return jsonify({"error": "not found"}), 404
        session.delete(note)
        session.commit()
        return jsonify({"ok": True})
    finally:
        session.close()


if __name__ == "__main__":
    init_db()
    app.run(debug=True)
