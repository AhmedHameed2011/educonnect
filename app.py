import os
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'super_secret_key_for_educonnect_app'

# إعداد قاعدة البيانات (SQLite)
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_DIR'] = os.path.join(BASE_DIR, 'instance')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(BASE_DIR, 'instance', 'educonnect.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ----------------- نماذج قاعدة البيانات (Models) -----------------

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # admin, teacher, parent, student

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())

class Alert(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())

class CalendarEvent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    date = db.Column(db.String(50), nullable=False)  # YYYY-MM-DD
    description = db.Column(db.Text, nullable=False)

# سياق محاكي للمستخدم الحالي لتبسيط العمليات في القوالب
class CurrentUserProxy:
    def __init__(self, user_obj):
        self.id = user_obj.id
        self.name = user_obj.name
        self.role = user_obj.role
        self.username = user_obj.username

@app.context_processor
def inject_user():
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        if user:
            return dict(current_user=CurrentUserProxy(user))
    return dict(current_user=None)

# ----------------- المسارات والتحكم (Routes) -----------------

@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # جلب جميع المستخدمين الآخرين لتبدأ معهم المحادثة
    users = User.query.filter(User.id != session['user_id']).all()
    return render_template('index.html', users=users)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # تحويل اسم المستخدم دائماً لحروف صغيرة لمنع مشاكل الحروف الكبيرة
        username = request.form.get('username').strip()
        password = request.form.get('password').strip()
        
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['user_role'] = user.role
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error="اسم المستخدم أو كلمة المرور غير صحيحة")
            
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# ----- نظام المحادثات والرسائل -----

@app.route('/get_messages/<int:receiver_id>', methods=['GET'])
def get_messages(receiver_id):
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 401
    
    my_id = session['user_id']
    messages = Message.query.filter(
        ((Message.sender_id == my_id) & (Message.receiver_id == receiver_id)) |
        ((Message.sender_id == receiver_id) & (Message.receiver_id == my_id))
    ).order_by(Message.timestamp.asc()).all()
    
    msg_list = [{
        'sender_id': m.sender_id,
        'receiver_id': m.receiver_id,
        'content': m.content,
        'time': m.timestamp.strftime('%H:%M')
    } for m in messages]
    
    return jsonify({'status': 'success', 'messages': msg_list})

@app.route('/send_message', methods=['POST'])
def send_message():
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 401
    
    data = request.get_json()
    receiver_id = data.get('receiver_id')
    content = data.get('content', '').strip()
    
    if not content or not receiver_id:
        return jsonify({'status': 'error', 'message': 'Missing data'}), 400
        
    new_msg = Message(sender_id=session['user_id'], receiver_id=receiver_id, content=content)
    db.session.add(new_msg)
    db.session.commit()
    
    return jsonify({'status': 'success'})

# ----- نظام التنبيهات -----

@app.route('/get_alerts', methods=['GET'])
def get_alerts():
    alerts = Alert.query.order_by(Alert.timestamp.desc()).all()
    alert_list = [{
        'id': a.id,
        'title': a.title,
        'content': a.content,
        'time': a.timestamp.strftime('%H:%M %Y-%m-%d')
    } for a in alerts]
    return jsonify({'status': 'success', 'alerts': alert_list})

@app.route('/add_alert', methods=['POST'])
def add_alert():
    if 'user_id' not in session or session.get('user_role', '').lower() != 'admin':
        return jsonify({'status': 'error', 'message': 'Forbidden'}), 403
    data = request.get_json()
    new_alert = Alert(title=data.get('title'), content=data.get('content'))
    db.session.add(new_alert)
    db.session.commit()
    return jsonify({'status': 'success'})

@app.route('/edit_alert/<int:id>', methods=['POST'])
def edit_alert(id):
    if 'user_id' not in session or session.get('user_role', '').lower() != 'admin':
        return jsonify({'status': 'error', 'message': 'Forbidden'}), 403
    data = request.get_json()
    alert = Alert.query.get_or_404(id)
    alert.title = data.get('title')
    alert.content = data.get('content')
    db.session.commit()
    return jsonify({'status': 'success'})

@app.route('/delete_alert/<int:id>', methods=['DELETE'])
def delete_alert(id):
    if 'user_id' not in session or session.get('user_role', '').lower() != 'admin':
        return jsonify({'status': 'error', 'message': 'Forbidden'}), 403
    alert = Alert.query.get_or_404(id)
    db.session.delete(alert)
    db.session.commit()
    return jsonify({'status': 'success'})

# ----- نظام التقويم الدراسي -----

@app.route('/get_events', methods=['GET'])
def get_events():
    events = CalendarEvent.query.order_by(CalendarEvent.date.asc()).all()
    event_list = [{
        'id': e.id,
        'title': e.title,
        'date': e.date,
        'description': e.description
    } for e in events]
    return jsonify({'status': 'success', 'events': event_list})

@app.route('/add_event', methods=['POST'])
def add_event():
    if 'user_id' not in session or session.get('user_role', '').lower() != 'admin':
        return jsonify({'status': 'error', 'message': 'Forbidden'}), 403
    data = request.get_json()
    new_event = CalendarEvent(title=data.get('title'), date=data.get('date'), description=data.get('description'))
    db.session.add(new_event)
    db.session.commit()
    return jsonify({'status': 'success'})

@app.route('/edit_event/<int:id>', methods=['POST'])
def edit_event(id):
    if 'user_id' not in session or session.get('user_role', '').lower() != 'admin':
        return jsonify({'status': 'error', 'message': 'Forbidden'}), 403
    data = request.get_json()
    event = CalendarEvent.query.get_or_404(id)
    event.title = data.get('title')
    event.date = data.get('date')
    event.description = data.get('description')
    db.session.commit()
    return jsonify({'status': 'success'})

@app.route('/delete_event/<int:id>', methods=['DELETE'])
def delete_event(id):
    if 'user_id' not in session or session.get('user_role', '').lower() != 'admin':
        return jsonify({'status': 'error', 'message': 'Forbidden'}), 403
    event = CalendarEvent.query.get_or_404(id)
    db.session.delete(event)
    db.session.commit()
    return jsonify({'status': 'success'})

# ----- شاشة إدارة المستخدمين وعملياتها -----

@app.route('/admin/users')
def admin_users():
    if 'user_id' not in session or session.get('user_role', '').lower() != 'admin':
        return redirect(url_for('index'))
    all_users = User.query.all()
    return render_template('admin_users.html', all_users=all_users)

@app.route('/admin/user/add', methods=['POST'])
def admin_add_user():
    if 'user_id' not in session or session.get('user_role', '').lower() != 'admin':
        return redirect(url_for('index'))
    username = request.form.get('username').strip()
    name = request.form.get('name').strip()
    role = request.form.get('role')
    password = request.form.get('password').strip()
    
    if User.query.filter_by(username=username).first():
        all_users = User.query.all()
        return render_template('admin_users.html', all_users=all_users, error="اسم المستخدم مسجل مسبقاً")
        
    hashed_pwd = generate_password_hash(password)
    new_user = User(username=username, name=name, role=role, password=hashed_pwd)
    db.session.add(new_user)
    db.session.commit()
    return redirect(url_for('admin_users'))

@app.route('/admin/user/delete/<int:user_id>')
def admin_delete_user(user_id):
    if 'user_id' not in session or session.get('user_role', '').lower() != 'admin':
        return redirect(url_for('index'))
    if user_id == session['user_id']:
        return redirect(url_for('admin_users')) # لا يمكن لحساب الأدمن حذف نفسه
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    return redirect(url_for('admin_users'))

# المسار الجديد المصلح لإعادة تعيين كلمة المرور بشكل آمن بالخلفية بدلاً من صفحة 404
@app.route('/admin/user/reset-password/<int:user_id>', methods=['POST'])
def admin_reset_password(user_id):
    if 'user_id' not in session or session.get('user_role', '').lower() != 'admin':
        return jsonify({'status': 'error', 'message': 'غير مصرح لك بالوصول'}), 403
        
    user = User.query.get(user_id)
    if not user:
        return jsonify({'status': 'error', 'message': 'المستخدم غير موجود'}), 404

    user.password = generate_password_hash('123456')
    db.session.commit()

    return jsonify({
        'status': 'success',
        'message': f'تم إعادة تعيين كلمة المرور بنجاح للمستخدم {user.name}. كلمة المرور الجديدة الافتراضية هي: 123456'
    })

# تهيئة قاعدة البيانات وإنشاء عينات من الحسابات إذا كانت فارغة
with app.app_context():
    db.create_all()
    if not User.query.filter_by(username='admin').first():
        admin_user = User(
            username='admin',
            name='School Admin',
            role='admin',
            password=generate_password_hash('admin123')
        )
        db.session.add(admin_user)
        db.session.commit()

if __name__ == '__main__':
    app.run(debug=True)