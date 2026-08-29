from extensions import db

class Hackathon(db.Model):
    __tablename__ = 'hackathons'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    location = db.Column(db.String(255))               # City/Venue or N/A
    event_type = db.Column(db.String(50), default='online')  # 'online' or 'offline'
    prize_amount = db.Column(db.String(100))           # e.g., $10,000 / ₹50,000
    idea = db.Column(db.Text)                           # Project concept
    date = db.Column(db.String(100))                    # Event date (YYYY-MM-DD)
    result_date = db.Column(db.String(100))             # Result announcement date
    url = db.Column(db.String(500))                     # Clickable event URL
    registered = db.Column(db.Boolean, default=False)   # Registration status checkbox
    is_idea_submission = db.Column(db.Boolean, default=False) # Online idea submission phase toggle
    header_note = db.Column(db.String(255))             # Mild neon quick note / highlight
    description = db.Column(db.Text)                    # Legacy field support
    progress = db.Column(db.Integer, default=0)         # Auto-calculated percentage

    # Relationships — explicit foreign_keys to avoid ambiguity
    tasks = db.relationship('Task', backref='hackathon', cascade='all, delete-orphan',
                            lazy=True, order_by='Task.id')
    notes = db.relationship('Note', backref='hackathon', cascade='all, delete-orphan', lazy=True,
                            foreign_keys='Note.hackathon_id', order_by='Note.id.desc()')
    file_attachments = db.relationship('Attachment', backref='hackathon', cascade='all, delete-orphan', lazy=True,
                                       foreign_keys='Attachment.hackathon_id')

    def update_progress(self):
        """Recalculates progress percentage based on completed tasks."""
        if not self.tasks:
            self.progress = 0
        else:
            completed_count = sum(1 for task in self.tasks if task.completed)
            self.progress = int((completed_count / len(self.tasks)) * 100)
        return self.progress

class Task(db.Model):
    __tablename__ = 'tasks'
    id = db.Column(db.Integer, primary_key=True)
    hackathon_id = db.Column(db.Integer, db.ForeignKey('hackathons.id'), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    completed = db.Column(db.Boolean, default=False)

class ParticipatedEvent(db.Model):
    __tablename__ = 'participated_events'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    location = db.Column(db.String(255))
    event_type = db.Column(db.String(50), default='online')
    prize_amount = db.Column(db.String(100))
    date = db.Column(db.String(100))
    result_date = db.Column(db.String(100))
    url = db.Column(db.String(500))
    idea = db.Column(db.Text)
    description = db.Column(db.Text)
    result = db.Column(db.String(255))  # e.g., "Won 1st place", "Completed"
    prize_won = db.Column(db.String(255))  # e.g., "$2,500 Cash Prize", "Swag Kit"
    is_idea_submission = db.Column(db.Boolean, default=False)
    source_hackathon_id = db.Column(db.Integer, nullable=True)  # Reference only, not a FK

    # Relationships for preserved notes & attachments
    notes = db.relationship('Note', backref='participated_event', lazy=True,
                            foreign_keys='Note.participated_event_id',
                            cascade='all, delete-orphan', order_by='Note.id.desc()')
    file_attachments = db.relationship('Attachment', backref='participated_event', lazy=True,
                                       foreign_keys='Attachment.participated_event_id',
                                       cascade='all, delete-orphan')

class Note(db.Model):
    __tablename__ = 'notes'
    id = db.Column(db.Integer, primary_key=True)
    hackathon_id = db.Column(db.Integer, db.ForeignKey('hackathons.id'), nullable=True)
    participated_event_id = db.Column(db.Integer, db.ForeignKey('participated_events.id'), nullable=True)
    progress = db.Column(db.Integer, default=0)
    note = db.Column(db.Text, nullable=False)

class Attachment(db.Model):
    __tablename__ = 'attachments'
    id = db.Column(db.Integer, primary_key=True)
    hackathon_id = db.Column(db.Integer, db.ForeignKey('hackathons.id'), nullable=True)
    participated_event_id = db.Column(db.Integer, db.ForeignKey('participated_events.id'), nullable=True)
    original_filename = db.Column(db.String(255), nullable=False)
    stored_filename = db.Column(db.String(255), nullable=False)
    file_type = db.Column(db.String(50), nullable=False)
