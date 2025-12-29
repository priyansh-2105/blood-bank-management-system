from datetime import datetime
from app import db

class OTPVerification(db.Model):
    __tablename__ = 'otp_verifications'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), nullable=False)
    otp = db.Column(db.String(6), nullable=False)
    type = db.Column(db.String(20), nullable=False)  # email_verification, password_reset
    is_used = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)
    
    def __repr__(self):
        return f'<OTPVerification {self.email}>'

class DonationAppointment(db.Model):
    __tablename__ = 'donation_appointments'
    
    id = db.Column(db.Integer, primary_key=True)
    donor_id = db.Column(db.Integer, db.ForeignKey('donors.id'), nullable=False)
    hospital_id = db.Column(db.Integer, db.ForeignKey('hospitals.id'), nullable=False)
    appointment_date = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, confirmed, completed, cancelled
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    # donor and hospital relationships are defined in their respective models
    
    def __repr__(self):
        return f'<DonationAppointment {self.donor.user.name} - {self.hospital.user.name}>'

class BloodDonationRecord(db.Model):
    __tablename__ = 'blood_donation_records'
    
    id = db.Column(db.Integer, primary_key=True)
    appointment_id = db.Column(db.Integer, db.ForeignKey('donation_appointments.id'), nullable=False)
    donor_id = db.Column(db.Integer, db.ForeignKey('donors.id'), nullable=False)
    quantity = db.Column(db.Float, nullable=False)  # in units
    blood_group = db.Column(db.String(5), nullable=False)
    donation_date = db.Column(db.DateTime, nullable=False)
    certificate_id = db.Column(db.String(50), unique=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    appointment = db.relationship('DonationAppointment', backref='donation_records', lazy='joined')
    # donor relationship is defined in Donor model
    
    def __repr__(self):
        return f'<BloodDonationRecord {self.donor.user.name} - {self.quantity} units>'

class Recipient(db.Model):
    __tablename__ = 'recipients'
    
    id = db.Column(db.Integer, primary_key=True)
    hospital_id = db.Column(db.Integer, db.ForeignKey('hospitals.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    blood_group = db.Column(db.String(5), nullable=False)
    contact = db.Column(db.String(15))
    age = db.Column(db.Integer)
    gender = db.Column(db.String(10))
    remarks = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    # hospital relationship is defined in Hospital model
    
    def __repr__(self):
        return f'<Recipient {self.name}>'

class BloodTransfusionRequest(db.Model):
    __tablename__ = 'blood_transfusion_requests'
    
    id = db.Column(db.Integer, primary_key=True)
    hospital_id = db.Column(db.Integer, db.ForeignKey('hospitals.id'), nullable=False)
    recipient_id = db.Column(db.Integer, db.ForeignKey('recipients.id'))
    blood_group = db.Column(db.String(5), nullable=False)
    quantity = db.Column(db.Float, nullable=False)  # in units
    urgency = db.Column(db.String(20), default='normal')  # normal, urgent, emergency
    status = db.Column(db.String(20), default='pending')  # pending, approved, fulfilled, rejected
    required_by_date = db.Column(db.Date)
    reason = db.Column(db.Text)
    admin_remarks = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    # hospital relationship is defined in Hospital model
    recipient = db.relationship('Recipient', backref='transfusion_requests', lazy='joined')
    
    def __repr__(self):
        return f'<BloodTransfusionRequest {self.hospital.user.name} - {self.blood_group}>'

class BloodInventory(db.Model):
    __tablename__ = 'blood_inventory'
    
    id = db.Column(db.Integer, primary_key=True)
    blood_group = db.Column(db.String(5), nullable=False, unique=True)
    total_units = db.Column(db.Float, default=0)
    available_units = db.Column(db.Float, default=0)
    reserved_units = db.Column(db.Float, default=0)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<BloodInventory {self.blood_group} - {self.available_units} units>'

class Notification(db.Model):
    __tablename__ = 'notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    message = db.Column(db.Text, nullable=False)
    type = db.Column(db.String(20), default='info')  # info, success, warning, error
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Notification {self.user.name} - {self.title}>'

class Feedback(db.Model):
    __tablename__ = 'feedback'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    subject = db.Column(db.String(200))
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Feedback {self.name} - {self.subject}>' 