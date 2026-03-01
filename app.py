from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///hoop.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'james_ultimate_hoop_2026'

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

# --- Auth Routes ---
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        hashed_pw = generate_password_hash(request.form.get('password'), method='pbkdf2:sha256')
        new_user = User(username=request.form.get('username'), name=request.form.get('name'),
                        student_id=request.form.get('student_id'), password=hashed_pw)
        db.session.add(new_user)
        db.session.commit()
        flash('สร้างบัญชีสำเร็จ! เข้าสู่ระบบเพื่อลุยกันเลย 🏀', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form.get('username')).first()
        if user and check_password_hash(user.password, request.form.get('password')):
            login_user(user)
            return redirect(url_for('home'))
        flash('เข้าสู่ระบบไม่สำเร็จ กรุณาตรวจสอบ Username และ Password', 'danger')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# --- Dashboard & Profile ---
@app.route('/')
@login_required
def home():
    total_m = len(current_user.matches)
    total_wins = sum(1 for m in current_user.matches if m.result == 'Win')
    win_rate = int((total_wins / total_m * 100)) if total_m > 0 else 0
    total_prac_mins = sum(p.duration_mins for p in current_user.practices)
    
    return render_template('index.html', user=current_user, 
                           total_matches=total_m, win_rate=win_rate, 
                           total_tactics=len(current_user.tactics),
                           total_prac_mins=total_prac_mins)

@app.route('/profile/<int:user_id>')
@login_required
def profile(user_id):
    user = User.query.get_or_404(user_id)
    return render_template('profile.html', user=user)

# --- Playbook (Tactics) Routes ---
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
        new_tactic = Tactic(name=request.form.get('name'), description=request.form.get('description'),
                            type=request.form.get('type'), strength=request.form.get('strength'),
                            weakness=request.form.get('weakness'), user_id=current_user.id)
        db.session.add(new_tactic)
        db.session.commit()
        flash('เพิ่มแผนใหม่เรียบร้อย! 📋', 'success')
        return redirect(url_for('playbook'))
    return render_template('add_tactic.html')

@app.route('/tactics/<int:id>')
@login_required
def tactic_detail(id):
    tactic = Tactic.query.get_or_404(id)
    return render_template('tactic_detail.html', tactic=tactic)

@app.route('/tactics/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_tactic(id):
    tactic = Tactic.query.get_or_404(id)
    if tactic.user_id != current_user.id:
        return redirect(url_for('playbook'))
    if request.method == 'POST':
        tactic.name = request.form.get('name')
        tactic.description = request.form.get('description')
        tactic.type = request.form.get('type')
        tactic.strength = request.form.get('strength')
        tactic.weakness = request.form.get('weakness')
        db.session.commit()
        flash('อัปเดตแผนเรียบร้อย! ✨', 'success')
        return redirect(url_for('tactic_detail', id=tactic.id))
    return render_template('edit_tactic.html', tactic=tactic)

@app.route('/tactics/delete/<int:id>', methods=['POST'])
@login_required
def delete_tactic(id):
    t = Tactic.query.get_or_404(id)
    if t.user_id == current_user.id:
        db.session.delete(t)
        db.session.commit()
        flash('ลบแผนออกจาก Playbook แล้ว! 🗑️', 'danger')
    return redirect(url_for('playbook'))

# --- Match Routes ---
@app.route('/matches')
@login_required
def match_history():
    search = request.args.get('search')
    if search:
        matches = Match.query.filter(Match.user_id == current_user.id, Match.opponent.contains(search)).order_by(Match.id.desc()).all()
    else:
        matches = Match.query.filter_by(user_id=current_user.id).order_by(Match.id.desc()).all()
    return render_template('matches.html', matches=matches)

@app.route('/matches/add', methods=['GET', 'POST'])
@login_required
def add_match():
    if request.method == 'POST':
        new_match = Match(opponent=request.form.get('opponent'), result=request.form.get('result'),
                          points_scored=request.form.get('points_scored'), points_conceded=request.form.get('points_conceded'),
                          user_id=current_user.id)
        db.session.add(new_match)
        db.session.commit()
        flash('บันทึกผลการแข่งสำเร็จ! 🏆', 'success')
        return redirect(url_for('match_history'))
    return render_template('add_match.html')

@app.route('/matches/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_match(id):
    match = Match.query.get_or_404(id)
    if match.user_id != current_user.id:
        return redirect(url_for('match_history'))
    if request.method == 'POST':
        match.opponent = request.form.get('opponent')
        match.result = request.form.get('result')
        match.points_scored = request.form.get('points_scored')
        match.points_conceded = request.form.get('points_conceded')
        db.session.commit()
        flash('อัปเดตผลการแข่งเรียบร้อย! ✨', 'success')
        return redirect(url_for('match_history'))
    return render_template('edit_match.html', match=match)

@app.route('/matches/delete/<int:id>', methods=['POST'])
@login_required
def delete_match(id):
    m = Match.query.get_or_404(id)
    if m.user_id == current_user.id:
        db.session.delete(m)
        db.session.commit()
        flash('ลบประวัติการแข่งแล้ว! 🗑️', 'danger')
    return redirect(url_for('match_history'))

# --- Practice Routes ---
@app.route('/practice')
@login_required
def practice_log():
    search = request.args.get('search')
    if search:
        practices = Practice.query.filter(Practice.user_id == current_user.id, Practice.skill.contains(search)).order_by(Practice.date.desc()).all()
    else:
        practices = Practice.query.filter_by(user_id=current_user.id).order_by(Practice.date.desc()).all()
    return render_template('practice.html', practices=practices)

@app.route('/practice/add', methods=['GET', 'POST'])
@login_required
def add_practice():
    if request.method == 'POST':
        date_obj = datetime.strptime(request.form.get('date'), '%Y-%m-%d')
        new_log = Practice(date=date_obj, skill=request.form.get('skill'), 
                           duration_mins=request.form.get('duration'), user_id=current_user.id)
        db.session.add(new_log)
        db.session.commit()
        flash('บันทึกการฝึกซ้อมเรียบร้อย! ลุยต่อ! 👟', 'success')
        return redirect(url_for('practice_log'))
    return render_template('add_practice.html')

@app.route('/practice/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_practice(id):
    practice = Practice.query.get_or_404(id)
    if practice.user_id != current_user.id:
        return redirect(url_for('practice_log'))
    if request.method == 'POST':
        practice.date = datetime.strptime(request.form.get('date'), '%Y-%m-%d')
        practice.skill = request.form.get('skill')
        practice.duration_mins = request.form.get('duration')
        db.session.commit()
        flash('อัปเดตการฝึกซ้อมเรียบร้อย! ✨', 'success')
        return redirect(url_for('practice_log'))
    return render_template('edit_practice.html', practice=practice)

@app.route('/practice/delete/<int:id>', methods=['POST'])
@login_required
def delete_practice(id):
    p = Practice.query.get_or_404(id)
    if p.user_id == current_user.id:
        db.session.delete(p)
        db.session.commit()
        flash('ลบประวัติการฝึกซ้อมแล้ว! 🗑️', 'danger')
    return redirect(url_for('practice_log'))

with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)