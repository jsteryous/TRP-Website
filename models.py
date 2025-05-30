from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Numeric
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class Listing(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    county = db.Column(db.String(100), nullable=False)
    price = db.Column(Numeric(10, 2), nullable=False)
    acreage = db.Column(Numeric(8, 2), nullable=True)  # New field for actual acreage
    description = db.Column(db.Text, nullable=False)
    image_url = db.Column(db.String(500))
    featured = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Listing {self.title}>'
    
    def get_price_per_acre(self):
        """Calculate price per acre if acreage is available"""
        if self.acreage and self.acreage > 0:
            return float(self.price) / float(self.acreage)
        return None
    
    def get_display_acreage(self):
        """Get the acreage for display, with fallback to estimate"""
        if self.acreage:
            return float(self.acreage)
        else:
            # Fallback to estimate (you can adjust this multiplier)
            return float(self.price) / 5000
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'county': self.county,
            'price': float(self.price),
            'acreage': float(self.acreage) if self.acreage else None,
            'description': self.description,
            'image_url': self.image_url,
            'featured': self.featured,
            'created_at': self.created_at.isoformat()
        }

class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<Admin {self.username}>'