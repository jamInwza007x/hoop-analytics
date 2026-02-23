from flask import Flask, render_template, request, redirect, url_for
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

# ----------------- Routes -----------------
@app.route('/')
def home():
    return render_template('index.html')
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

if __name__ == '__main__':
    app.run(debug=True)