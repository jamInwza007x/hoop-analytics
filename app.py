from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
# ตั้งค่าให้เชื่อมต่อกับไฟล์ฐานข้อมูลชื่อ hoop.db
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///hoop.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ----------------- Database Models -----------------

# 1. ตารางบันทึกสถิติและวิเคราะห์หลังแข่ง (Game)
class Game(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    opponent = db.Column(db.String(100), nullable=False)
    result = db.Column(db.String(20), nullable=False) # ชนะ/แพ้
    opp_tactic = db.Column(db.Text, nullable=False)   # แผนคู่แข่ง
    our_tactic = db.Column(db.Text, nullable=False)   # แผนเรา (วิธีแก้เกม)
    worked = db.Column(db.Boolean, default=False)     # แผนเราเวิร์คไหม? (True/False)
    notes = db.Column(db.Text, nullable=True)         # ข้อสังเกตเพิ่มเติม

# 2. ตารางสมุดแผนการเล่น (Tactic)
class Tactic(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    strength = db.Column(db.String(200), nullable=True)
    weakness = db.Column(db.String(200), nullable=True)

# 3. ตารางบันทึกการซ้อม (Practice)
class Practice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    skill = db.Column(db.String(100), nullable=False) # เช่น ชู้ต 3 แต้ม, เลย์อัพ
    duration_mins = db.Column(db.Integer, nullable=False)
class Match(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    opponent = db.Column(db.String(100), nullable=False)
    result = db.Column(db.String(20), nullable=False)
    points_scored = db.Column(db.Integer, nullable=False)
    points_conceded = db.Column(db.Integer, nullable=False)

# ----------------- Routes -----------------
@app.route('/')
def home():
    # นับจำนวนแมตช์และแผนการเล่นทั้งหมดจากฐานข้อมูล
    total_matches = Match.query.count()
    total_tactics = Tactic.query.count()
    return render_template('index.html', total_matches=total_matches, total_tactics=total_tactics)
@app.route('/tactics')
def playbook():
    # ดึงข้อมูลแผนการเล่นทั้งหมดจากฐานข้อมูล
    all_tactics = Tactic.query.all()
    return render_template('tactics.html', tactics=all_tactics)
@app.route('/tactics/add', methods=['GET', 'POST'])
def add_tactic():
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        strength = request.form.get('strength')
        weakness = request.form.get('weakness')
        
        new_tactic = Tactic(name=name, description=description, strength=strength, weakness=weakness)
        db.session.add(new_tactic)
        db.session.commit()
        
        return redirect(url_for('playbook'))
    
    return render_template('add_tactic.html')

@app.route('/tactics/<int:id>')
def tactic_detail(id):
    tactic = Tactic.query.get_or_404(id)
    return render_template('tactic_detail.html', tactic=tactic)
@app.route('/matches')
def match_history():
    all_matches = Match.query.all()
    return render_template('matches.html', matches=all_matches)

@app.route('/matches/add', methods=['GET', 'POST'])
def add_match():
    if request.method == 'POST':
        opponent = request.form.get('opponent')
        result = request.form.get('result')
        points_scored = request.form.get('points_scored')
        points_conceded = request.form.get('points_conceded')
        
        new_match = Match(opponent=opponent, result=result, points_scored=points_scored, points_conceded=points_conceded)
        db.session.add(new_match)
        db.session.commit()
        
        return redirect(url_for('match_history'))
    
    return render_template('add_match.html')
@app.route('/practice')
def practice_log():
    # ดึงข้อมูลการซ้อมทั้งหมด เรียงจากล่าสุดไปเก่าสุด
    logs = Practice.query.order_by(Practice.date.desc()).all()
    return render_template('practice.html', practices=logs)

@app.route('/practice/add', methods=['GET', 'POST'])
def add_practice():
    if request.method == 'POST':
        date_str = request.form.get('date')
        skill = request.form.get('skill')
        duration = request.form.get('duration')
        
        # แปลงวันที่จากข้อความให้เป็นวันที่จริงๆ
        from datetime import datetime
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        
        new_log = Practice(date=date_obj, skill=skill, duration_mins=duration)
        db.session.add(new_log)
        db.session.commit()
        flash('Practice log added! 🏀', 'success')
        return redirect(url_for('practice_log'))
    
    return render_template('add_practice.html')

@app.route('/profile')
def profile():
    return render_template('profile.html')
@app.route('/practice/delete/<int:id>', methods=['POST'])
def delete_practice(id):
    log_to_delete = Practice.query.get_or_404(id)
    db.session.delete(log_to_delete)
    db.session.commit()
    flash('Practice log deleted! 🗑️', 'danger')
    return redirect(url_for('practice_log'))
@app.route('/matches/delete/<int:id>', methods=['POST'])
def delete_match(id):
    match_to_delete = Match.query.get_or_404(id)
    db.session.delete(match_to_delete)
    db.session.commit()
    return redirect(url_for('match_history'))
@app.route('/tactics/delete/<int:id>', methods=['POST'])
def delete_tactic(id):
    tactic_to_delete = Tactic.query.get_or_404(id)
    db.session.delete(tactic_to_delete)
    db.session.commit()
    return redirect(url_for('tactics'))
@app.route('/practice/edit/<int:id>', methods=['GET', 'POST'])
def edit_practice(id):
    practice_to_edit = Practice.query.get_or_404(id)
    if request.method == 'POST':
        date_str = request.form.get('date')
        practice_to_edit.skill = request.form.get('skill')
        practice_to_edit.duration_mins = request.form.get('duration')
        from datetime import datetime
        practice_to_edit.date = datetime.strptime(date_str, '%Y-%m-%d')
        db.session.commit()
        flash('Practice log updated! ✏️', 'info')
        return redirect(url_for('practice_log'))
    return render_template('edit_practice.html', practice=practice_to_edit)
@app.route('/matches/edit/<int:id>', methods=['GET', 'POST'])
def edit_match(id):
    match_to_edit = Match.query.get_or_404(id)
    if request.method == 'POST':
        match_to_edit.opponent = request.form.get('opponent')
        match_to_edit.result = request.form.get('result')
        match_to_edit.points_scored = request.form.get('points_scored')
        match_to_edit.points_conceded = request.form.get('points_conceded')
        db.session.commit()
        return redirect(url_for('match_history'))
    return render_template('edit_match.html', match=match_to_edit)
@app.route('/tactics/edit/<int:id>', methods=['GET', 'POST'])
def edit_tactic(id):
    tactic_to_edit = Tactic.query.get_or_404(id)
    if request.method == 'POST':
        tactic_to_edit.name = request.form.get('name')
        tactic_to_edit.description = request.form.get('description')
        tactic_to_edit.type = request.form.get('type')
        tactic_to_edit.strength = request.form.get('strength')
        tactic_to_edit.weakness = request.form.get('weakness')
        db.session.commit()
        return redirect(url_for('tactic_detail', id=tactic_to_edit.id))
    return render_template('edit_tactic.html', tactic=tactic_to_edit)
with app.app_context():
    db.create_all()
if __name__ == '__main__':
    app.run(debug=True)