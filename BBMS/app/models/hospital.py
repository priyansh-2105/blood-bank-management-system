from datetime import datetime
from app import db

class Hospital(db.Model):
    __tablename__ = 'hospitals'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    license_id = db.Column(db.String(50), unique=True, nullable=True)  # Old field, kept for compatibility
    license_number = db.Column(db.String(50), unique=True, nullable=True)  # New field
    phone = db.Column(db.String(15), nullable=False)
    address = db.Column(db.Text, nullable=False)
    city = db.Column(db.String(100), nullable=False)
    state = db.Column(db.String(100), nullable=True)  # Added state field
    pincode = db.Column(db.String(10), nullable=True)  # Added pincode field
    age = db.Column(db.Integer)
    gender = db.Column(db.String(10))
    hospital_type = db.Column(db.String(20))  # government, private, charity
    specialties = db.Column(db.Text)
    is_verified = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    recipients = db.relationship('Recipient', backref='hospital', lazy='dynamic', cascade='all, delete-orphan')
    transfusion_requests = db.relationship('BloodTransfusionRequest', backref='hospital', lazy='dynamic', cascade='all, delete-orphan')
    appointments = db.relationship('DonationAppointment', backref='hospital', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Hospital {self.user.name}>' 