from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)

# --- Configuration ---
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///hoop.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# Secret Key สำหรับระบบ Flash Messages และ Session
app.config['SECRET_KEY'] = 'james_nba_aspiration_2026' 

db = SQLAlchemy(app)

# --- Database Models ---

# 1. ตารางสมุดแผนการเล่น (Tactic)
class Tactic(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    type = db.Column(db.String(20), nullable=True) # เพิ่มประเภท Offense/Defense
    strength = db.Column(db.String(200), nullable=True)
    weakness = db.Column(db.String(200), nullable=True)

# 2. ตารางบันทึกการซ้อม (Practice)
class Practice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    skill = db.Column(db.String(100), nullable=False)
    duration_mins = db.Column(db.Integer, nullable=False)

# 3. ตารางประวัติการแข่ง (Match)
class Match(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    opponent = db.Column(db.String(100), nullable=False)
    result = db.Column(db.String(20), nullable=False)
    points_scored = db.Column(db.Integer, nullable=False)
    points_conceded = db.Column(db.Integer, nullable=False)

# --- Routes ---

@app.route('/')
def home():
    total_matches = Match.query.count()
    total_tactics = Tactic.query.count()
    return render_template('index.html', total_matches=total_matches, total_tactics=total_tactics)

# หน้า Playbook พร้อมระบบ Filter
@app.route('/tactics')
def playbook():
    filter_type = request.args.get('type')
    if filter_type:
        all_tactics = Tactic.query.filter_by(type=filter_type).all()
    else:
        all_tactics = Tactic.query.all()
    return render_template('tactics.html', tactics=all_tactics)

@app.route('/tactics/add', methods=['GET', 'POST'])
def add_tactic():
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        t_type = request.form.get('type') # รับค่าจาก select
        strength = request.form.get('strength')
        weakness = request.form.get('weakness')
        
        new_tactic = Tactic(name=name, description=description, type=t_type, strength=strength, weakness=weakness)
        db.session.add(new_tactic)
        db.session.commit()
        flash('Tactic added! 📋', 'success')
        return redirect(url_for('playbook'))
    return render_template('add_tactic.html')

@app.route('/tactics/<int:id>')
def tactic_detail(id):
    tactic = Tactic.query.get_or_404(id)
    return render_template('tactic_detail.html', tactic=tactic)

# หน้าประวัติการแข่ง พร้อมระบบ Search
@app.route('/matches')
def match_history():
    search = request.args.get('search')
    if search:
        matches = Match.query.filter(Match.opponent.contains(search)).order_by(Match.id.desc()).all()
    else:
        matches = Match.query.order_by(Match.id.desc()).all()
    return render_template('matches.html', matches=matches)

@app.route('/matches/add', methods=['GET', 'POST'])
def add_match():
    if request.method == 'POST':
        new_match = Match(
            opponent=request.form.get('opponent'),
            result=request.form.get('result'),
            points_scored=request.form.get('points_scored'),
            points_conceded=request.form.get('points_conceded')
        )
        db.session.add(new_match)
        db.session.commit()
        flash('Match record added! 🏀', 'success')
        return redirect(url_for('match_history'))
    return render_template('add_match.html')

# หน้าบันทึกการซ้อม พร้อมระบบ Search
@app.route('/practice')
def practice_log():
    search = request.args.get('search')
    if search:
        logs = Practice.query.filter(Practice.skill.contains(search)).order_by(Practice.date.desc()).all()
    else:
        logs = Practice.query.order_by(Practice.date.desc()).all()
    return render_template('practice.html', practices=logs)

@app.route('/practice/add', methods=['GET', 'POST'])
def add_practice():
    if request.method == 'POST':
        date_str = request.form.get('date')
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        new_log = Practice(date=date_obj, skill=request.form.get('skill'), duration_mins=request.form.get('duration'))
        db.session.add(new_log)
        db.session.commit()
        flash('Practice log added! 🏀', 'success')
        return redirect(url_for('practice_log'))
    return render_template('add_practice.html')

@app.route('/profile')
def profile():
    return render_template('profile.html')

# --- Delete & Edit Routes ---
@app.route('/practice/delete/<int:id>', methods=['POST'])
def delete_practice(id):
    log_to_delete = Practice.query.get_or_404(id)
    db.session.delete(log_to_delete)
    db.session.commit()
    flash('Practice log deleted! 🗑️', 'danger')
    return redirect(url_for('practice_log'))

@app.route('/tactics/delete/<int:id>', methods=['POST'])
def delete_tactic(id):
    tactic_to_delete = Tactic.query.get_or_404(id)
    db.session.delete(tactic_to_delete)
    db.session.commit()
    flash('Tactic deleted! 🗑️', 'danger')
    return redirect(url_for('playbook'))

# --- Initialization ---
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)