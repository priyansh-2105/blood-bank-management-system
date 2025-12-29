import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail
from flask_migrate import Migrate
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize extensions
db = SQLAlchemy()
login_manager = LoginManager()
mail = Mail()
migrate = Migrate()

def create_app():
    app = Flask(__name__)
    
    # Configuration
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///bbms.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Email configuration
    app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
    app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
    app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', 'True').lower() == 'true'
    app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
    app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
    app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_USERNAME')
    
    # File upload configuration
    app.config['UPLOAD_FOLDER'] = os.getenv('UPLOAD_FOLDER', 'app/static/uploads')
    app.config['MAX_CONTENT_LENGTH'] = int(os.getenv('MAX_CONTENT_LENGTH', 16777216))
    
    # Initialize extensions with app
    db.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    migrate.init_app(app, db)
    
    # Configure login manager
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'
    
    # Create upload directory if it doesn't exist
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Register blueprints
    from app.routes.auth import auth_bp
    from app.routes.donor import donor_bp
    from app.routes.hospital import hospital_bp
    from app.routes.admin import admin_bp
    from app.routes.appointments import appointments_bp
    from app.routes.notifications import notifications_bp
    from app.api.autocomplete import api_bp
    from app.api.dashboard_stats import stats_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(donor_bp)
    app.register_blueprint(hospital_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(appointments_bp)
    app.register_blueprint(notifications_bp)
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(stats_bp, url_prefix='/api/stats')
    
    # Register error handlers
    from app.error_handlers import register_error_handlers
    register_error_handlers(app)
    
    # Create database tables
    with app.app_context():
        db.create_all()
        
        # Create admin user if not exists
        from app.models.user import User
        from app.models.admin import Admin
        from werkzeug.security import generate_password_hash
        
        admin_email = os.getenv('ADMIN_EMAIL', 'admin@bbms.com')
        admin_user = User.query.filter_by(email=admin_email).first()
        
        if not admin_user:
            admin_user = User(
                name='Admin',
                email=admin_email,
                password_hash=generate_password_hash(os.getenv('ADMIN_PASSWORD', 'admin123')),
                role='admin',
                is_verified=True
            )
            db.session.add(admin_user)
            db.session.commit()
            
            admin = Admin(user_id=admin_user.id)
            db.session.add(admin)
            db.session.commit()
    
    # Register CLI commands
    @app.cli.command('clear-db')
    def clear_database():
        """Clear all data from the database"""
        with app.app_context():
            from app.models.user import User
            from app.models.donor import Donor
            from app.models.hospital import Hospital
            from app.models.admin import Admin
            from app.models.common import Appointment, BloodRequest, Notification
            
            print("🗑️  Clearing database...")
            
            try:
                # Delete in order to avoid foreign key constraints
                Notification.query.delete()
                print("✅ Cleared notifications")
                
                BloodRequest.query.delete()
                print("✅ Cleared blood requests")
                
                Appointment.query.delete()
                print("✅ Cleared appointments")
                
                Donor.query.delete()
                print("✅ Cleared donors")
                
                Hospital.query.delete()
                print("✅ Cleared hospitals")
                
                Admin.query.delete()
                print("✅ Cleared admins")
                
                # Delete all users except admin
                User.query.filter(User.role != 'admin').delete()
                print("✅ Cleared regular users")
                
                # Commit the changes
                db.session.commit()
                print("✅ Database cleared successfully!")
                
            except Exception as e:
                print(f"❌ Error clearing database: {e}")
                db.session.rollback()
    
    return app 