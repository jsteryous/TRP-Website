from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash
import os
from datetime import datetime

# Import our separate modules
from models import db, Listing, Admin
from forms import ListingForm, LoginForm, SearchForm, ContactForm

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-change-this-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///land_listings.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5MB max file size

# Create upload directory if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize database with app
db.init_app(app)

# Routes
@app.route('/')
def index():
    featured_listings = Listing.query.filter_by(featured=True).limit(3).all()
    return render_template('index.html', featured_listings=featured_listings)

@app.route('/listings')
def listings():
    # Get filter parameters
    county_filter = request.args.get('county', '')
    min_price = request.args.get('min_price', type=float)
    max_price = request.args.get('max_price', type=float)
    sort_by = request.args.get('sort', 'newest')
    
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
    
    # Available counties for filter dropdown
    counties = ['Oconee', 'Pickens', 'Anderson', 'Greenville', 'Spartanburg', 'Cherokee', 'Union', 'Laurens']
    
    return render_template('listings.html', 
                         listings=all_listings, 
                         counties=counties,
                         selected_county=county_filter,
                         min_price=min_price if min_price else '',
                         max_price=max_price if max_price else '',
                         selected_sort=sort_by)

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
            # Handle image upload
            image_url = form.image_url.data
            
            if form.image_file.data:
                file = form.image_file.data
                filename = secure_filename(file.filename)
                # Add timestamp to filename to avoid conflicts
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
                filename = timestamp + filename
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
                image_url = f'/static/uploads/{filename}'
            
            # Create new listing
            listing = Listing(
                title=form.title.data,
                county=form.county.data,
                price=form.price.data,
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
    
    return render_template('admin_form.html', form=form, title='Add New Listing')

@app.route('/admin/edit/<int:listing_id>', methods=['GET', 'POST'])
def admin_edit_listing(listing_id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    listing = Listing.query.get_or_404(listing_id)
    form = ListingForm(obj=listing)
    
    if form.validate_on_submit():
        try:
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
            
            # Update listing fields
            listing.title = form.title.data
            listing.county = form.county.data
            listing.price = form.price.data
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
        flash('Thank you for your message! Alex will contact you soon.', 'success')
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

# Initialize database and create admin user
def create_tables():
    """Initialize database tables and create default admin user"""
    db.create_all()
    
    # Create default admin user if none exists
    if not Admin.query.first():
        admin = Admin(username='admin')
        admin.set_password('password123')  # Change this in production!
        db.session.add(admin)
        db.session.commit()
        print("Default admin user created: admin/password123")

# Create tables when app starts (works with Gunicorn)
with app.app_context():
    create_tables()

if __name__ == '__main__':
    app.run(debug=True)