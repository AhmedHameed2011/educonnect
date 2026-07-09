from translations import TRANSLATIONS
import os
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = 'educonnect_secret_key_123'
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(BASE_DIR, "educonnect.db")}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


# =========================================================
# 📍 هــنــا الـمـكـان الـصـحـيـح لـلـدالـة (أسفل إعدادات الـ db والـ login_manager)
# =========================================================
@app.context_processor
def inject_global_vars():
    lang = session.get('lang', 'ar')  # العربية هي اللغة الافتراضية دائماً
    return {
        'lang': lang,
        'dir': 'rtl' if lang == 'ar' else 'ltr',
        't': TRANSLATIONS[lang]
    }

# 💡 مسار تغيير اللغة الآمن (تم إصلاح مسافات التعليق البرمجي هنا)
@app.route('/set_language/<string:lang_code>')
def set_language(lang_code):
    if lang_code in ['ar', 'en']:
        session['lang'] = lang_code
    return redirect(request.referrer or url_for('index'))


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    name = db.Column(db.String(150), nullable=False)
    role = db.Column(db.String(50), nullable=False, default='student')

@app.route('/')
@login_required
def index():
    # جلب المستخدمين لعرضهم في قائمة المحادثات باستثناء المستخدم الحالي
    users = User.query.filter(User.id != current_user.id).all()
    return render_template('index.html', users=users)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            session['user_id'] = user.id
            return redirect(url_for('index'))
        else:
            flash('اسم المستخدم أو كلمة المرور غير صحيحة!', 'danger')
            
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    session.pop('user_id', None)
    return redirect(url_for('login'))

# ربط المسارات بشكل صحيح وتوجيه الـ GET لقالب إدارة المستخدمين الصحيح
@app.route('/admin/add_user', methods=['GET', 'POST'], endpoint='admin_add_user')
@app.route('/admin_users', methods=['GET', 'POST'], endpoint='admin_users_management')
@login_required
def admin_users_management():
    if current_user.role.lower() != 'admin':
        flash('غير مصرح لك بإجراء هذه العملية', 'danger')
        return redirect(url_for('index'))
        
    if request.method == 'GET':
        all_users = User.query.all()
        return render_template('admin_users.html', all_users=all_users)
        
    username = request.form.get('username')
    name = request.form.get('name')
    password = request.form.get('password')
    role = request.form.get('role')
    
    if User.query.filter_by(username=username).first():
        flash('اسم المستخدم مسجل بالفعل!', 'danger')
    else:
        hashed_password = generate_password_hash(password, method='scrypt')
        new_user = User(username=username, name=name, password=hashed_password, role=role)
        db.session.add(new_user)
        db.session.commit()
        flash('تم إنشاء الحساب بنجاح', 'success')
        
    return redirect(url_for('admin_users_management'))

@app.route('/admin/delete_user/<int:user_id>')
@login_required
def admin_delete_user(user_id):
    if current_user.role.lower() != 'admin':
        flash('غير مصرح لك بإجراء هذه العملية', 'danger')
        return redirect(url_for('index'))
        
    user_to_delete = db.session.get(User, user_id)
    if user_to_delete:
        if user_to_delete.id == current_user.id:
            flash('لا يمكنك حذف حسابك الحالي أثناء تسجيل الدخول!', 'danger')
        else:
            db.session.delete(user_to_delete)
            db.session.commit()
            flash('تم حذف المستخدم بنجاح', 'success')
            
    return redirect(url_for('admin_users_management'))

# مسار خلفي للتعامل مع جافاسكريبت إعادة تعيين باسوورد المستخدمين الموجود في ملف admin_users.html
@app.route('/admin/user/reset-password/<int:user_id>', methods=['POST'])
@login_required
def admin_reset_password(user_id):
    if current_user.role.lower() != 'admin':
        return {'status': 'error', 'message': 'غير مصرح لك'}, 403
        
    user = db.session.get(User, user_id)
    if user:
        user.password = generate_password_hash('123456', method='scrypt')
        db.session.commit()
        return {'status': 'success', 'message': f'تم إعادة تعيين كلمة المرور بنجاح للمستخدم {user.name}'}
    return {'status': 'error', 'message': 'المستخدم غير موجود'}

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        admin_exists = User.query.filter_by(username='admin').first()
        if not admin_exists:
            admin_pwd = generate_password_hash('admin123', method='scrypt')
            default_admin = User(username='admin', name='School Admin', password=admin_pwd, role='admin')
            db.session.add(default_admin)
            db.session.commit()

    app.run(debug=True)