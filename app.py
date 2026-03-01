from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///hoop.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'james_nba_aspiration_2026'

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# --- Models ---
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    student_id = db.Column(db.String(20), nullable=False)
    password = db.Column(db.String(120), nullable=False)
    tactics = db.relationship('Tactic', backref='author', lazy=True)
    matches = db.relationship('Match', backref='author', lazy=True)
    practices = db.relationship('Practice', backref='author', lazy=True)

class Tactic(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    type = db.Column(db.String(20))
    strength = db.Column(db.String(200))
    weakness = db.Column(db.String(200))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class Match(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    opponent = db.Column(db.String(100), nullable=False)
    result = db.Column(db.String(20), nullable=False)
    points_scored = db.Column(db.Integer, nullable=False)
    points_conceded = db.Column(db.Integer, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class Practice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    skill = db.Column(db.String(100), nullable=False)
    duration_mins = db.Column(db.Integer, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- Auth ---
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        hashed_pw = generate_password_hash(request.form.get('password'), method='pbkdf2:sha256')
        new_user = User(username=request.form.get('username'), name=request.form.get('name'),
                        student_id=request.form.get('student_id'), password=hashed_pw)
        db.session.add(new_user)
        db.session.commit()
        flash('Account created!', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form.get('username')).first()
        if user and check_password_hash(user.password, request.form.get('password')):
            login_user(user)
            return redirect(url_for('home'))
        flash('Login Failed', 'danger')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# --- App Routes ---
@app.route('/')
@login_required
def home():
    return render_template('index.html', user=current_user)

@app.route('/tactics')
@login_required
def playbook():
    t_type = request.args.get('type')
    all_tactics = Tactic.query.filter_by(user_id=current_user.id, type=t_type).all() if t_type else Tactic.query.filter_by(user_id=current_user.id).all()
    return render_template('tactics.html', tactics=all_tactics)

@app.route('/tactics/add', methods=['GET', 'POST'])
@login_required
def add_tactic():
    if request.method == 'POST':
        new_tactic = Tactic(
            name=request.form.get('name'),
            description=request.form.get('description'),
            type=request.form.get('type'),
            strength=request.form.get('strength'),
            weakness=request.form.get('weakness'),
            user_id=current_user.id
        )
        db.session.add(new_tactic)
        db.session.commit()
        flash('Tactic added! 📋', 'success')
        return redirect(url_for('playbook'))
    return render_template('add_tactic.html')

@app.route('/tactics/<int:id>')
@login_required
def tactic_detail(id): # ตัวแปรต้องชื่อ id ให้ตรงกับ HTML
    tactic = Tactic.query.get_or_404(id)
    return render_template('tactic_detail.html', tactic=tactic)

@app.route('/matches')
@login_required
def match_history():
    matches = Match.query.filter_by(user_id=current_user.id).order_by(Match.id.desc()).all()
    return render_template('matches.html', matches=matches)

@app.route('/practice')
@login_required
def practice_log():
    practices = Practice.query.filter_by(user_id=current_user.id).order_by(Practice.date.desc()).all()
    return render_template('practice.html', practices=practices)

@app.route('/profile/<int:user_id>')
@login_required
def profile(user_id):
    user = User.query.get_or_404(user_id)
    return render_template('profile.html', user=user)

# --- Delete ---
@app.route('/tactics/delete/<int:id>', methods=['POST'])
@login_required
def delete_tactic(id):
    t = Tactic.query.get_or_404(id)
    if t.user_id == current_user.id:
        db.session.delete(t)
        db.session.commit()
        flash('Deleted!', 'danger')
    return redirect(url_for('playbook'))

with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)