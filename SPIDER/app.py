from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import math
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get(
    'SECRET_KEY',
    'development-secret-key'
)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///sems.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
@app.context_processor
def inject_user():
    user = None

    if 'user_id' in session:
        user = db.session.get(User, session['user_id'])

    return {'current_user': user}


# ---------------------------------------------------------------------------
# Database Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(200), nullable=False)
    username = db.Column(db.String(100), unique=True, nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)

    role = db.Column(
        db.String(20),
        nullable=False,
        default='user'
    )

    bookings = db.relationship(
        'Booking',
        backref='user',
        lazy=True
    )

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(
            self.password_hash,
            password
        )

class Hospital(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    address = db.Column(db.Text, nullable=False)
    city = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    emergency_phone = db.Column(db.String(20), nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    total_beds = db.Column(db.Integer, default=50)
    available_beds = db.Column(db.Integer, default=20)
    icu_beds = db.Column(db.Integer, default=10)
    available_icu = db.Column(db.Integer, default=5)
    rating = db.Column(db.Float, default=4.5)
    is_24x7 = db.Column(db.Boolean, default=True)

    doctors = db.relationship('Doctor', backref='hospital', lazy=True)
    bookings = db.relationship('Booking', backref='hospital', lazy=True)


class Doctor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    hospital_id = db.Column(db.Integer, db.ForeignKey('hospital.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    specialty = db.Column(db.String(100), nullable=False)
    is_available = db.Column(db.Boolean, default=True)
    shift = db.Column(db.String(50), default='Day')
    experience_years = db.Column(db.Integer, default=5)


class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    hospital_id = db.Column(db.Integer, db.ForeignKey('hospital.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True) # Optional link to registered user
    patient_name = db.Column(db.String(200), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    emergency_type = db.Column(db.String(100), nullable=False)
    bed_type = db.Column(db.String(50), default='General')
    status = db.Column(db.String(20), default='Confirmed')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
 
class Checkup(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    doctor_name = db.Column(db.String(100))
    diagnosis = db.Column(db.Text)
    checkup_date = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", backref="checkups")


class Prescription(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    medicine = db.Column(db.String(200))
    dosage = db.Column(db.String(100))
    instructions = db.Column(db.Text)
    prescribed_date = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", backref="prescriptions")
# ---------------------------------------------------------------------------
# Helper Functions & Initial Seed Data
# ---------------------------------------------------------------------------

def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2) ** 2)
    return R * 2 * math.asin(math.sqrt(a))


def seed_data():
    if Hospital.query.first():
        return

    hospitals = [
        Hospital(name='Apollo Emergency Care', address='21 Greams Lane, Off Greams Road',
                 city='Chennai', phone='044-28290200', emergency_phone='1066',
                 latitude=13.0604, longitude=80.2496, total_beds=120, available_beds=34,
                 icu_beds=25, available_icu=8, rating=4.8),
        Hospital(name='Global Health Emergency', address='439 Cheran Nagar, Perumbakkam',
                 city='Chennai', phone='044-44777000', emergency_phone='108',
                 latitude=12.8996, longitude=80.2209, total_beds=80, available_beds=18,
                 icu_beds=15, available_icu=3, rating=4.6),
        Hospital(name='City Trauma & ICU Center', address='154 Anna Salai, Teynampet',
                 city='Chennai', phone='044-24311600', emergency_phone='102',
                 latitude=13.0418, longitude=80.2341, total_beds=95, available_beds=22,
                 icu_beds=20, available_icu=6, rating=4.5),
        Hospital(name='LifeLine 24x7 Hospital', address='72 Velachery Main Road',
                 city='Chennai', phone='044-22512121', emergency_phone='104',
                 latitude=12.9758, longitude=80.2207, total_beds=60, available_beds=11,
                 icu_beds=12, available_icu=2, rating=4.4),
        Hospital(name='Metro Critical Care Unit', address='11 GST Road, Chromepet',
                 city='Chennai', phone='044-22345678', emergency_phone='107',
                 latitude=12.9516, longitude=80.1407, total_beds=70, available_beds=29,
                 icu_beds=18, available_icu=9, rating=4.7),
    ]
    db.session.add_all(hospitals)
    db.session.commit()

    doctors = [
        Doctor(hospital_id=1, name='Dr. Priya Sharma', specialty='Emergency Medicine', is_available=True, shift='24x7', experience_years=12),
        Doctor(hospital_id=1, name='Dr. Arun Kumar', specialty='Cardiology', is_available=True, shift='Day', experience_years=15),
        Doctor(hospital_id=1, name='Dr. Meena Raj', specialty='Neurology', is_available=False, shift='Night', experience_years=10),
        Doctor(hospital_id=2, name='Dr. Vikram Singh', specialty='Trauma Surgery', is_available=True, shift='24x7', experience_years=18),
        Doctor(hospital_id=2, name='Dr. Lakshmi Devi', specialty='Pediatrics', is_available=True, shift='Day', experience_years=8),
        Doctor(hospital_id=3, name='Dr. Rahul Menon', specialty='Orthopedics', is_available=True, shift='Day', experience_years=11),
        Doctor(hospital_id=3, name='Dr. Anitha Bose', specialty='ICU Specialist', is_available=True, shift='24x7', experience_years=14),
        Doctor(hospital_id=4, name='Dr. Sanjay Patel', specialty='General Surgery', is_available=False, shift='Night', experience_years=9),
        Doctor(hospital_id=4, name='Dr. Kavitha Nair', specialty='Pulmonology', is_available=True, shift='Day', experience_years=7),
        Doctor(hospital_id=5, name='Dr. Mohamed Ali', specialty='Emergency Medicine', is_available=True, shift='24x7', experience_years=13),
        Doctor(hospital_id=5, name='Dr. Deepa Iyer', specialty='Anesthesiology', is_available=True, shift='Day', experience_years=16),
    ]
    db.session.add_all(doctors)
    db.session.commit()


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route('/')
def index():
    hospitals = Hospital.query.all()
    total_beds = sum(h.total_beds for h in hospitals)
    available_beds = sum(h.available_beds for h in hospitals)
    available_doctors = Doctor.query.filter_by(is_available=True).count()
    total_doctors = Doctor.query.count()
    recent_bookings = Booking.query.order_by(Booking.created_at.desc()).limit(5).all()
    return render_template('index.html',
                           hospitals=hospitals,
                           total_beds=total_beds,
                           available_beds=available_beds,
                           available_doctors=available_doctors,
                           total_doctors=total_doctors,
                           recent_bookings=recent_bookings)


# --- Authentication Routes ---

@app.route('/register', methods=['GET', 'POST'])
def register():

    if request.method == 'POST':

        full_name = request.form.get('full_name', '').strip()
        username = request.form.get('username', '').strip()
        phone = request.form.get('phone', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        # 1. Check fields
        if not full_name or not username or not phone or not password or not confirm_password:
            flash('Please fill in all fields.', 'danger')
            return redirect(url_for('register'))

        # 2. Check password
        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return redirect(url_for('register'))

        # 3. Check username
        existing_user = User.query.filter_by(
            username=username
        ).first()

        if existing_user:
            flash('Username already exists.', 'warning')
            return redirect(url_for('register'))

        # 4. Create patient account
        new_user = User(
            full_name=full_name,
            username=username,
            phone=phone,
            role='user'
        )

        # 5. Encrypt password
        new_user.set_password(password)

        # 6. Save to database
        db.session.add(new_user)
        db.session.commit()

        # 7. Go to login page
        flash(
            'Registration successful! Please login.',
            'success'
        )

        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            session['user_id'] = user.id
            flash(f'Welcome back, {user.full_name}!', 'success')
            return redirect(url_for('patient_dashboard'))

        else:
            flash('Invalid username or password.', 'danger')

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user = User.query.get_or_404(session['user_id'])

    if user.role == 'admin':
        return redirect(url_for('admin_dashboard'))

    return redirect(url_for('patient_dashboard'))


@app.route('/profile')
def profile():
    if 'user_id' not in session:
        flash('Please login to access your profile.', 'warning')
        return redirect(url_for('login'))

    user = User.query.get_or_404(session['user_id'])
    return render_template('profile.html', user=user)


@app.route('/patient_dashboard')
def patient_dashboard():

    if 'user_id' not in session:
        flash('Please login first.', 'warning')
        return redirect(url_for('login'))

    user = User.query.get_or_404(session['user_id'])

    bookings = Booking.query.filter_by(user_id=user.id).all()
    checkups = Checkup.query.filter_by(user_id=user.id).all()
    prescriptions = Prescription.query.filter_by(user_id=user.id).all()

    return render_template(
        'patient_dashboard.html',
        user=user,
        bookings=bookings,
        checkups=checkups,
        prescriptions=prescriptions
    )

# --- Admin Routes ---


@app.route('/admin')
def admin_dashboard():

    if 'user_id' not in session:
        return redirect(url_for('login'))

    user = db.session.get(User, session['user_id'])

    if not user or user.role != 'admin':
        flash('Access denied.', 'danger')
        return redirect(url_for('index'))

    bookings = Booking.query.all()
    users = User.query.all()
    hospitals = Hospital.query.all()
    doctors = Doctor.query.all()

    return render_template(
        'admin.html',
        user=user,
        bookings=bookings,
        users=users,
        hospitals=hospitals,
        doctors=doctors
    )

# --- Existing Hospital & Booking Routes ---

@app.route('/hospitals')
def hospitals():
    all_hospitals = Hospital.query.all()
    return render_template('hospitals.html', hospitals=all_hospitals)


@app.route('/hospital/<int:hospital_id>')
def hospital_detail(hospital_id):
    hospital = Hospital.query.get_or_404(hospital_id)
    return render_template('hospital_detail.html', hospital=hospital)


@app.route('/book', methods=['GET', 'POST'])

@app.route('/book/<int:hospital_id>', methods=['GET', 'POST'])
def book(hospital_id=None):
    hospitals_list = Hospital.query.all()
    selected = Hospital.query.get(hospital_id) if hospital_id else None

    if request.method == 'POST':
        hid = int(request.form.get('hospital_id'))
        bed_type = request.form.get('bed_type')
        hospital = Hospital.query.get_or_404(hid)

        if bed_type == 'ICU' and hospital.available_icu <= 0:
            flash('No ICU beds available at this hospital. Please choose another.', 'danger')
            return redirect(url_for('book', hospital_id=hid))

        if bed_type == 'General' and hospital.available_beds <= 0:
            flash('No general beds available at this hospital. Please choose another.', 'danger')
            return redirect(url_for('book', hospital_id=hid))

        booking = Booking(
            hospital_id=hid,
            user_id=session.get('user_id'), # Link booking to user if logged in
            patient_name=request.form.get('patient_name'),
            phone=request.form.get('phone'),
            age=int(request.form.get('age')),
            emergency_type=request.form.get('emergency_type'),
            bed_type=bed_type,
        )
        if bed_type == 'ICU':
            hospital.available_icu -= 1
        else:
            hospital.available_beds -= 1

        db.session.add(booking)
        db.session.commit()
        flash(f'Bed booked successfully! Booking ID: SEMS-{booking.id:04d}', 'success')
        return redirect(url_for('bookings'))

    return render_template('book.html', hospitals=hospitals_list, selected=selected)


@app.route('/bookings')
def bookings():
    all_bookings = Booking.query.order_by(Booking.created_at.desc()).all()
    return render_template('bookings.html', bookings=all_bookings)

@app.route('/nearest')
def nearest():
    return render_template(
        'nearest.html',
        hospitals=Hospital.query.all()
    )

# --- API Routes ---

@app.route('/api/nearest', methods=['POST'])
def api_nearest():

    data = request.get_json()

    lat = float(data.get('latitude', 0))
    lng = float(data.get('longitude', 0))

    results = []

    for h in Hospital.query.all():

        dist = haversine(
            lat,
            lng,
            h.latitude,
            h.longitude
        )

        available_docs = sum(
            1 for d in h.doctors
            if d.is_available
        )

        results.append({

            'id': h.id,
            'name': h.name,
            'address': h.address,
            'city': h.city,
            'phone': h.phone,
            'emergency_phone': h.emergency_phone,

            'distance_km': round(dist, 2),

            'available_beds': h.available_beds,
            'available_icu': h.available_icu,

            'available_doctors': available_docs,
            'total_doctors': len(h.doctors),

            'rating': h.rating,
            'is_24x7': h.is_24x7

        })

    results.sort(
        key=lambda x: x['distance_km']
    )

    return jsonify(results[:5])


@app.route('/api/availability')
def api_availability():
    data = []
    for h in Hospital.query.all():
        data.append({
            'id': h.id,
            'name': h.name,
            'available_beds': h.available_beds,
            'total_beds': h.total_beds,
            'available_icu': h.available_icu,
            'icu_beds': h.icu_beds,
            'doctors_available': sum(1 for d in h.doctors if d.is_available),
            'doctors_total': len(h.doctors),
        })
    return jsonify(data)

@app.context_processor
def inject_user():

    current_user = None

    if 'user_id' in session:
        current_user = db.session.get(
            User,
            session['user_id']
        )

    return {
        'current_user': current_user
    }

# ---------------------------------------------------------------------------
# App Initialization
# ---------------------------------------------------------------------------
with app.app_context():
    db.create_all()
    seed_data()

if __name__ == '__main__':
    app.run(debug=True, port=5001)

