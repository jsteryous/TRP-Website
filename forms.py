from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, TextAreaField, DecimalField, SelectField, PasswordField, BooleanField
from wtforms.validators import DataRequired, NumberRange, Length, Email, Optional

class ListingForm(FlaskForm):
    title = StringField('Property Title', validators=[
        DataRequired(message="Please enter a property title"),
        Length(min=10, max=200, message="Title must be between 10 and 200 characters")
    ])
    
    county = SelectField('County', choices=[
        ('Abbeville', 'Abbeville County'),
        ('Aiken', 'Aiken County'),
        ('Allendale', 'Allendale County'),
        ('Anderson', 'Anderson County'),
        ('Bamberg', 'Bamberg County'),
        ('Barnwell', 'Barnwell County'),
        ('Beaufort', 'Beaufort County'),
        ('Berkeley', 'Berkeley County'),
        ('Calhoun', 'Calhoun County'),
        ('Charleston', 'Charleston County'),
        ('Cherokee', 'Cherokee County'),
        ('Chester', 'Chester County'),
        ('Chesterfield', 'Chesterfield County'),
        ('Clarendon', 'Clarendon County'),
        ('Colleton', 'Colleton County'),
        ('Darlington', 'Darlington County'),
        ('Dillon', 'Dillon County'),
        ('Dorchester', 'Dorchester County'),
        ('Edgefield', 'Edgefield County'),
        ('Fairfield', 'Fairfield County'),
        ('Florence', 'Florence County'),
        ('Georgetown', 'Georgetown County'),
        ('Greenville', 'Greenville County'),
        ('Greenwood', 'Greenwood County'),
        ('Hampton', 'Hampton County'),
        ('Horry', 'Horry County'),
        ('Jasper', 'Jasper County'),
        ('Kershaw', 'Kershaw County'),
        ('Lancaster', 'Lancaster County'),
        ('Laurens', 'Laurens County'),
        ('Lee', 'Lee County'),
        ('Lexington', 'Lexington County'),
        ('Marion', 'Marion County'),
        ('Marlboro', 'Marlboro County'),
        ('McCormick', 'McCormick County'),
        ('Newberry', 'Newberry County'),
        ('Oconee', 'Oconee County'),
        ('Orangeburg', 'Orangeburg County'),
        ('Pickens', 'Pickens County'),
        ('Richland', 'Richland County'),
        ('Saluda', 'Saluda County'),
        ('Spartanburg', 'Spartanburg County'),
        ('Sumter', 'Sumter County'),
        ('Union', 'Union County'),
        ('Williamsburg', 'Williamsburg County'),
        ('York', 'York County')
    ], validators=[DataRequired(message="Please select a county")])
    
    price = DecimalField('Price ($)', validators=[
        DataRequired(message="Please enter a price"),
        NumberRange(min=1000, max=10000000, message="Price must be between $1,000 and $10,000,000")
    ])
    
    description = TextAreaField('Property Description', validators=[
        DataRequired(message="Please provide a property description"),
        Length(min=50, max=2000, message="Description must be between 50 and 2000 characters")
    ])
    
    image_url = StringField('Image URL', validators=[
        Optional(),
        Length(max=500, message="URL must be less than 500 characters")
    ])
    
    image_file = FileField('Upload Image', validators=[
        Optional(),
        FileAllowed(['jpg', 'jpeg', 'png', 'gif', 'webp'], 'Images only!')
    ])
    
    featured = SelectField('Featured Listing?', choices=[
        ('0', 'No'),
        ('1', 'Yes')
    ], default='0')

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[
        DataRequired(message="Please enter your username"),
        Length(min=3, max=80, message="Username must be between 3 and 80 characters")
    ])
    
    password = PasswordField('Password', validators=[
        DataRequired(message="Please enter your password"),
        Length(min=6, message="Password must be at least 6 characters")
    ])
    
    remember_me = BooleanField('Remember Me')

class SearchForm(FlaskForm):
    county = SelectField('County', choices=[
        ('', 'All Counties'),
        ('Abbeville', 'Abbeville County'),
        ('Aiken', 'Aiken County'),
        ('Allendale', 'Allendale County'),
        ('Anderson', 'Anderson County'),
        ('Bamberg', 'Bamberg County'),
        ('Barnwell', 'Barnwell County'),
        ('Beaufort', 'Beaufort County'),
        ('Berkeley', 'Berkeley County'),
        ('Calhoun', 'Calhoun County'),
        ('Charleston', 'Charleston County'),
        ('Cherokee', 'Cherokee County'),
        ('Chester', 'Chester County'),
        ('Chesterfield', 'Chesterfield County'),
        ('Clarendon', 'Clarendon County'),
        ('Colleton', 'Colleton County'),
        ('Darlington', 'Darlington County'),
        ('Dillon', 'Dillon County'),
        ('Dorchester', 'Dorchester County'),
        ('Edgefield', 'Edgefield County'),
        ('Fairfield', 'Fairfield County'),
        ('Florence', 'Florence County'),
        ('Georgetown', 'Georgetown County'),
        ('Greenville', 'Greenville County'),
        ('Greenwood', 'Greenwood County'),
        ('Hampton', 'Hampton County'),
        ('Horry', 'Horry County'),
        ('Jasper', 'Jasper County'),
        ('Kershaw', 'Kershaw County'),
        ('Lancaster', 'Lancaster County'),
        ('Laurens', 'Laurens County'),
        ('Lee', 'Lee County'),
        ('Lexington', 'Lexington County'),
        ('Marion', 'Marion County'),
        ('Marlboro', 'Marlboro County'),
        ('McCormick', 'McCormick County'),
        ('Newberry', 'Newberry County'),
        ('Oconee', 'Oconee County'),
        ('Orangeburg', 'Orangeburg County'),
        ('Pickens', 'Pickens County'),
        ('Richland', 'Richland County'),
        ('Saluda', 'Saluda County'),
        ('Spartanburg', 'Spartanburg County'),
        ('Sumter', 'Sumter County'),
        ('Union', 'Union County'),
        ('Williamsburg', 'Williamsburg County'),
        ('York', 'York County')
    ], validators=[Optional()])
    
    min_price = DecimalField('Minimum Price', validators=[
        Optional(),
        NumberRange(min=0, message="Minimum price cannot be negative")
    ])
    
    max_price = DecimalField('Maximum Price', validators=[
        Optional(),
        NumberRange(min=0, message="Maximum price cannot be negative")
    ])
    
    sort = SelectField('Sort By', choices=[
        ('newest', 'Newest First'),
        ('oldest', 'Oldest First'),
        ('price_low', 'Price: Low to High'),
        ('price_high', 'Price: High to Low'),
        ('featured', 'Featured First')
    ], default='newest')

# Complete list of SC counties for reference
SC_COUNTIES = [
    'Abbeville', 'Aiken', 'Allendale', 'Anderson', 'Bamberg', 'Barnwell',
    'Beaufort', 'Berkeley', 'Calhoun', 'Charleston', 'Cherokee', 'Chester',
    'Chesterfield', 'Clarendon', 'Colleton', 'Darlington', 'Dillon',
    'Dorchester', 'Edgefield', 'Fairfield', 'Florence', 'Georgetown',
    'Greenville', 'Greenwood', 'Hampton', 'Horry', 'Jasper', 'Kershaw',
    'Lancaster', 'Laurens', 'Lee', 'Lexington', 'Marion', 'Marlboro',
    'McCormick', 'Newberry', 'Oconee', 'Orangeburg', 'Pickens', 'Richland',
    'Saluda', 'Spartanburg', 'Sumter', 'Union', 'Williamsburg', 'York'
]

class ContactForm(FlaskForm):
    name = StringField('Full Name', validators=[
        DataRequired(message="Please enter your name"),
        Length(min=2, max=100, message="Name must be between 2 and 100 characters")
    ])
    
    email = StringField('Email Address', validators=[
        DataRequired(message="Please enter your email"),
        Email(message="Please enter a valid email address")
    ])
    
    phone = StringField('Phone Number', validators=[
        Optional(),
        Length(max=20, message="Phone number must be less than 20 characters")
    ])
    
    property_interest = StringField('Property of Interest', validators=[
        Optional(),
        Length(max=200, message="Property name must be less than 200 characters")
    ])
    
    message = TextAreaField('Message', validators=[
        DataRequired(message="Please enter your message"),
        Length(min=10, max=1000, message="Message must be between 10 and 1000 characters")
    ])
    
    budget_range = SelectField('Budget Range', choices=[
        ('', 'Select Budget Range'),
        ('under_50k', 'Under $50,000'),
        ('50k_100k', '$50,000 - $100,000'),
        ('100k_200k', '$100,000 - $200,000'),
        ('200k_500k', '$200,000 - $500,000'),
        ('over_500k', 'Over $500,000')
    ], validators=[Optional()])