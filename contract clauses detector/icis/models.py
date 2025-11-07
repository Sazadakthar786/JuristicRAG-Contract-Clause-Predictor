from datetime import datetime
from sqlalchemy.dialects.sqlite import JSON
from db import db

class Draft(db.Model):
    __tablename__ = "drafts"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    issues = db.Column(JSON, nullable=False, default=list)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "content": self.content,
            "issues": self.issues or [],
            "created_at": self.created_at.isoformat() + "Z",
        }
