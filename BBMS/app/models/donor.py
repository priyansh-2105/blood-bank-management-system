from datetime import datetime
from app import db

class Donor(db.Model):
    __tablename__ = 'donors'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    blood_group = db.Column(db.String(5), nullable=False)  # A+, B+, AB+, O+, A-, B-, AB-, O-
    city = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(15))
    age = db.Column(db.Integer)
    gender = db.Column(db.String(10))
    address = db.Column(db.Text)
    photo = db.Column(db.String(255))  # Profile image path
    date_of_birth = db.Column(db.Date)
    last_donation_date = db.Column(db.Date)
    medical_conditions = db.Column(db.Text)
    is_available = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    appointments = db.relationship('DonationAppointment', backref='donor', lazy='dynamic', cascade='all, delete-orphan')
    donation_records = db.relationship('BloodDonationRecord', backref='donor', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Donor {self.user.name}>' 