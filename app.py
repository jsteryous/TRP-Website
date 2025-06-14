from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash
import os
import json
import shutil
from datetime import datetime
from urllib.parse import urlparse

# Import our separate modules
from models import db, Listing, Admin
from forms import ListingForm, LoginForm, SearchForm, ContactForm

app = Flask(__name__)

# Database Configuration with persistence
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-change-this-in-production')

# Get database URL from environment or use persistent local SQLite
DATABASE_URL = os.environ.get('DATABASE_URL')

if DATABASE_URL:
    # Production database (PostgreSQL, MySQL, etc.)
    if DATABASE_URL.startswith('postgres://'):
        # Fix for newer PostgreSQL URLs
        DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
    print(f"Using production database: {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else 'configured'}")
else:
    # Local development - ensure database persists in data directory
    basedir = os.path.abspath(os.path.dirname(__file__))
    data_dir = os.path.join(basedir, 'data')
    db_path = os.path.join(data_dir, 'land_listings.db')
    
    # Create data directory if it doesn't exist
    os.makedirs(data_dir, exist_ok=True)
    
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    print(f"Using local SQLite database: {db_path}")

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5MB max file size

# Create upload directory if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize database with app
db.init_app(app)

# Database Backup Functions
def backup_database():
    """Create a JSON backup of all listings"""
    try:
        with app.app_context():
            listings = Listing.query.all()
            admins = Admin.query.all()
            
            backup_data = {
                'backup_date': datetime.utcnow().isoformat(),
                'listings': [listing.to_dict() for listing in listings],
                'admin_count': len(admins)
            }
            
            # Create backups directory
            backup_dir = os.path.join(os.path.dirname(__file__), 'backups')
            os.makedirs(backup_dir, exist_ok=True)
            
            # Save backup with timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_file = os.path.join(backup_dir, f'listings_backup_{timestamp}.json')
            
            with open(backup_file, 'w') as f:
                json.dump(backup_data, f, indent=2)
            
            print(f"Database backed up to: {backup_file}")
            return backup_file
    except Exception as e:
        print(f"Backup failed: {e}")
        return None

def restore_from_backup(backup_file):
    """Restore listings from a JSON backup file"""
    try:
        with app.app_context():
            with open(backup_file, 'r') as f:
                backup_data = json.load(f)
            
            restored_count = 0
            for listing_data in backup_data.get('listings', []):
                # Check if listing already exists (by title and county)
                existing = Listing.query.filter_by(
                    title=listing_data['title'],
                    county=listing_data['county']
                ).first()
                
                if not existing:
                    listing = Listing(
                        title=listing_data['title'],
                        county=listing_data['county'],
                        price=listing_data['price'],
                        acreage=listing_data.get('acreage'),
                        description=listing_data['description'],
                        image_url=listing_data.get('image_url'),
                        featured=listing_data['featured']
                    )
                    db.session.add(listing)
                    restored_count += 1
            
            db.session.commit()
            print(f"Restored {restored_count} listings from backup: {backup_file}")
            return restored_count
    except Exception as e:
        print(f"Restore failed: {e}")
        return 0

# Test route for debugging
@app.route('/test')
def test():
    return "Website is working! Database has {} listings.".format(Listing.query.count())

# Simple test routes
@app.route('/test-home')
def test_home():
    return "Test Home Route Works!"

@app.route('/test-listings') 
def test_listings():
    return "Test Listings Route Works!"

@app.route('/test-admin')
def test_admin():
    if not session.get('admin_logged_in'):
        return "Not logged in to admin"
    return "Admin access works! Available forms and templates ready."

# Routes
@app.route('/')
def index():
    try:
        featured_listings = Listing.query.filter_by(featured=True).limit(3).all()
        return render_template('index.html', featured_listings=featured_listings)
    except Exception as e:
        return f"Error on homepage: {str(e)}<br><br>Template files available: {', '.join([f for f in os.listdir('templates') if f.endswith('.html')])}", 500

@app.route('/listings')
def listings():
    try:
        # List available templates for debugging
        template_files = [f for f in os.listdir('templates') if f.endswith('.html')]
        
        # Get filter parameters
        county_filter = request.args.get('county', '')
        min_price = request.args.get('min_price')
        max_price = request.args.get('max_price')
        sort_by = request.args.get('sort', 'newest')
        
        # Convert price strings to floats safely
        try:
            min_price = float(min_price) if min_price else None
        except (ValueError, TypeError):
            min_price = None
            
        try:
            max_price = float(max_price) if max_price else None
        except (ValueError, TypeError):
            max_price = None
        
        # Build query
        query = Listing.query
        
        # Apply filters
        if county_filter:
            query = query.filter(Listing.county == county_filter)
        if min_price:
            query = query.filter(Listing.price >= min_price)
        if max_price:
            query = query.filter(Listing.price <= max_price)
        
        # Apply sorting
        if sort_by == 'oldest':
            query = query.order_by(Listing.created_at.asc())
        elif sort_by == 'price_low':
            query = query.order_by(Listing.price.asc())
        elif sort_by == 'price_high':
            query = query.order_by(Listing.price.desc())
        elif sort_by == 'featured':
            query = query.order_by(Listing.featured.desc(), Listing.created_at.desc())
        else:  # newest (default)
            query = query.order_by(Listing.created_at.desc())
        
        all_listings = query.all()
        
        # Available counties for filter dropdown - all 46 SC counties
        counties = [
            'Abbeville', 'Aiken', 'Allendale', 'Anderson', 'Bamberg', 'Barnwell',
            'Beaufort', 'Berkeley', 'Calhoun', 'Charleston', 'Cherokee', 'Chester',
            'Chesterfield', 'Clarendon', 'Colleton', 'Darlington', 'Dillon',
            'Dorchester', 'Edgefield', 'Fairfield', 'Florence', 'Georgetown',
            'Greenville', 'Greenwood', 'Hampton', 'Horry', 'Jasper', 'Kershaw',
            'Lancaster', 'Laurens', 'Lee', 'Lexington', 'Marion', 'Marlboro',
            'McCormick', 'Newberry', 'Oconee', 'Orangeburg', 'Pickens', 'Richland',
            'Saluda', 'Spartanburg', 'Sumter', 'Union', 'Williamsburg', 'York'
        ]
        
        return render_template('listings.html', 
                             listings=all_listings, 
                             counties=counties,
                             selected_county=county_filter,
                             min_price=request.args.get('min_price', ''),
                             max_price=request.args.get('max_price', ''),
                             selected_sort=sort_by)
    except Exception as e:
        template_files = [f for f in os.listdir('templates') if f.endswith('.html')]
        return f"Error on listings page: {str(e)}<br><br>Template files available: {', '.join(template_files)}<br><br>Looking for: listings.html", 500

@app.route('/listing/<int:listing_id>')
def listing_detail(listing_id):
    listing = Listing.query.get_or_404(listing_id)
    
    # Get related listings (same county, excluding current)
    related_listings = Listing.query.filter(
        Listing.county == listing.county,
        Listing.id != listing_id
    ).limit(3).all()
    
    return render_template('listing_detail.html', 
                         listing=listing, 
                         related_listings=related_listings)

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    form = LoginForm()
    if form.validate_on_submit():
        admin = Admin.query.filter_by(username=form.username.data).first()
        if admin and admin.check_password(form.password.data):
            session['admin_logged_in'] = True
            session['admin_id'] = admin.id
            flash('Welcome back!', 'success')
            return redirect(url_for('admin_dashboard'))
        flash('Invalid username or password', 'error')
    return render_template('admin_login.html', form=form)

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    session.pop('admin_id', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

@app.route('/admin')
def admin_dashboard():
    if not session.get('admin_logged_in'):
        flash('Please log in to access the admin panel.', 'warning')
        return redirect(url_for('admin_login'))
    
    try:
        # Get all listings
        listings = Listing.query.order_by(Listing.created_at.desc()).all()
        
        # Get statistics safely
        total_listings = len(listings)
        featured_count = sum(1 for listing in listings if listing.featured)
        total_value = sum(float(listing.price) for listing in listings)
        avg_price = total_value / total_listings if total_listings > 0 else 0
        
        stats = {
            'total_listings': total_listings,
            'featured_count': featured_count,
            'total_value': total_value,
            'avg_price': avg_price
        }
        
        return render_template('admin_dashboard.html', listings=listings, stats=stats)
    
    except Exception as e:
        # If there's an error, show a simple version
        return render_template('admin_dashboard.html', listings=[], stats={
            'total_listings': 0,
            'featured_count': 0,
            'total_value': 0,
            'avg_price': 0
        })

@app.route('/admin/add', methods=['GET', 'POST'])
def admin_add_listing():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    form = ListingForm()
    if form.validate_on_submit():
        try:
            # Auto-backup before adding new listing
            backup_database()
            
            # Handle image upload
            image_url = form.image_url.data or ''
            
            if form.image_file.data:
                file = form.image_file.data
                if file.filename:  # Check if a file was actually selected
                    filename = secure_filename(file.filename)
                    # Add timestamp to filename to avoid conflicts
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
                    filename = timestamp + filename
                    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    file.save(file_path)
                    image_url = f'/static/uploads/{filename}'
            
            # Create new listing with acreage field
            listing = Listing(
                title=form.title.data,
                county=form.county.data,
                price=form.price.data,
                acreage=form.acreage.data,
                description=form.description.data,
                image_url=image_url,
                featured=bool(int(form.featured.data))
            )
            
            db.session.add(listing)
            db.session.commit()
            flash('Listing added successfully!', 'success')
            return redirect(url_for('admin_dashboard'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding listing: {str(e)}', 'error')
            return redirect(url_for('admin_add_listing'))
    
    return render_template('admin_form.html', form=form, title='Add New Listing')

@app.route('/admin/edit/<int:listing_id>', methods=['GET', 'POST'])
def admin_edit_listing(listing_id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    listing = Listing.query.get_or_404(listing_id)
    form = ListingForm(obj=listing)
    
    if form.validate_on_submit():
        try:
            # Auto-backup before editing
            backup_database()
            
            # Handle image upload
            if form.image_file.data:
                file = form.image_file.data
                filename = secure_filename(file.filename)
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
                filename = timestamp + filename
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
                listing.image_url = f'/static/uploads/{filename}'
            elif form.image_url.data:
                listing.image_url = form.image_url.data
            
            # Update listing fields including acreage
            listing.title = form.title.data
            listing.county = form.county.data
            listing.price = form.price.data
            listing.acreage = form.acreage.data
            listing.description = form.description.data
            listing.featured = bool(int(form.featured.data))
            
            db.session.commit()
            flash('Listing updated successfully!', 'success')
            return redirect(url_for('admin_dashboard'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating listing: {str(e)}', 'error')
    
    # Pre-populate featured field
    form.featured.data = str(int(listing.featured))
    
    return render_template('admin_form.html', form=form, title='Edit Listing', listing=listing)

@app.route('/admin/delete/<int:listing_id>')
def admin_delete_listing(listing_id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    try:
        # Auto-backup before deletion
        backup_database()
        
        listing = Listing.query.get_or_404(listing_id)
        
        # Delete associated image file if it exists
        if listing.image_url and listing.image_url.startswith('/static/uploads/'):
            file_path = listing.image_url[1:]  # Remove leading slash
            if os.path.exists(file_path):
                os.remove(file_path)
        
        db.session.delete(listing)
        db.session.commit()
        flash('Listing deleted successfully!', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting listing: {str(e)}', 'error')
    
    return redirect(url_for('admin_dashboard'))

# Admin backup routes
@app.route('/admin/backup')
def admin_backup():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    backup_file = backup_database()
    if backup_file:
        flash('Database backed up successfully!', 'success')
    else:
        flash('Backup failed!', 'error')
    
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/restore', methods=['POST'])
def admin_restore():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    # This would handle file upload for restore
    # Implementation depends on your needs
    flash('Restore functionality would be implemented here', 'info')
    return redirect(url_for('admin_dashboard'))

@app.route('/api/listings')
def api_listings():
    """API endpoint for listings data"""
    listings = Listing.query.all()
    return jsonify([listing.to_dict() for listing in listings])

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    """Contact form page"""
    form = ContactForm()
    if form.validate_on_submit():
        # Here you would typically send an email or save to database
        # For now, just flash a success message
        flash('Thank you for your message! Table Rock Partners will contact you soon.', 'success')
        return redirect(url_for('contact'))
    
    return render_template('contact.html', form=form)

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return render_template('base.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return "Internal server error. Please try again later.", 500

@app.errorhandler(413)
def too_large(error):
    flash('File too large. Please upload an image smaller than 5MB.', 'error')
    return redirect(request.url)

# Template filters
@app.template_filter('currency')
def currency_filter(amount):
    """Format currency"""
    return f"${amount:,.0f}"

@app.template_filter('date_format')
def date_format_filter(date):
    """Format date"""
    return date.strftime('%B %d, %Y')

# Context processors (simplified to avoid errors)
@app.context_processor
def inject_stats():
    """Make site statistics available to all templates"""
    try:
        total_listings = Listing.query.count()
        featured_listings = Listing.query.filter_by(featured=True).count()
        return {
            'site_stats': {
                'total_listings': total_listings,
                'featured_listings': featured_listings
            }
        }
    except:
        return {
            'site_stats': {
                'total_listings': 0,
                'featured_listings': 0
            }
        }

# Initialize database and create admin user with migration support
def create_tables():
    """Initialize database tables and create default admin user"""
    try:
        with app.app_context():
            # Check if we have existing data to preserve
            existing_listings_count = 0
            try:
                existing_listings_count = Listing.query.count()
                if existing_listings_count > 0:
                    print(f"Found {existing_listings_count} existing listings - creating backup")
                    backup_database()
            except Exception:
                print("No existing database found or database needs migration")
            
            # Create all tables (this will add new columns if they don't exist)
            db.create_all()
            
            # Create default admin user only if no admin exists
            admin_count = 0
            try:
                admin_count = Admin.query.count()
            except Exception:
                pass
                
            if admin_count == 0:
                admin = Admin(username='admin')
                admin.set_password('password123')  # Change this in production!
                db.session.add(admin)
                db.session.commit()
                print("Default admin user created: admin/password123")
                print("WARNING: Change the default password in production!")
            else:
                print(f"Found {admin_count} existing admin user(s)")
            
            # Final count
            try:
                final_listing_count = Listing.query.count()
                print(f"Database initialized successfully. Total listings: {final_listing_count}")
                
                # Show database location
                if 'sqlite' in app.config['SQLALCHEMY_DATABASE_URI']:
                    db_location = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
                    print(f"Database location: {db_location}")
                    
            except Exception as e:
                print(f"Error checking final database state: {e}")
                
    except Exception as e:
        print(f"Database initialization error: {e}")
        print("This may be normal for first-time setup or migrations")

# Create tables when app starts (works with Gunicorn)
with app.app_context():
    create_tables()

if __name__ == '__main__':
    app.run(debug=True)