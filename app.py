from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
# استيراد قاموس الترجمة المنفصل لمنع تداخل الأكواد
from translations import TRANSLATIONS

app = Flask(__name__)
app.secret_key = 'super_secret_key_for_school_app'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///school.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# موديل المستخدمين في قاعدة البيانات
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False) # admin, teacher, student

@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # جلب جميع المستخدمين لعرضهم في لوحة التحكم الإدارية والمحادثات
    users = User.query.all()
    current_user = User.query.get(session['user_id'])
    return render_template('index.html', users=users, current_user=current_user)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # معالجة وحل مشكلة حساسية الحروف وحذف الفراغات الزائدة تلقائياً
        username = request.form.get('username').strip().lower()
        password = request.form.get('password').strip()
        
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['user_role'] = user.role
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error="خطأ في اسم المستخدم أو كلمة المرور")
            
    return render_template('login.html')

@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username').strip().lower()
    full_name = request.form.get('full_name').strip()
    password = request.form.get('password').strip()
    role = request.form.get('role')
    
    hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
    
    try:
        new_user = User(username=username, full_name=full_name, password=hashed_password, role=role)
        db.session.add(new_user)
        db.session.commit()
    except:
        db.session.rollback()
        
    return redirect(url_for('index'))

@app.route('/reset_password/<int:user_id>')
def reset_password(user_id):
    user = User.query.get_or_404(user_id)
    # تعيين الباسوورد الافتراضي الآمن 123456
    user.password = generate_password_hash('123456', method='pbkdf2:sha256')
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/delete_user/<int:user_id>')
def delete_user(user_id):
    if 'user_role' in session and session['user_role'] == 'admin':
        user = User.query.get(user_id)
        if user and user.id != session['user_id']:
            db.session.delete(user)
            db.session.commit()
    return redirect(url_for('index'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


# ------------------------------------------------------------------
# 🔥 التحديث الجديد والمنفصل: مسار ودوال نظام اللغة الثنائية تلقائياً
# ------------------------------------------------------------------

@app.route('/set_language/<lang>')
def set_language(lang):
    """تغيير لغة التطبيق وتخزينها في الجلسة ثم العودة لنفس الصفحة"""
    if lang in ['ar', 'en']:
        session['lang'] = lang
    return redirect(request.referrer or url_for('index'))

@app.context_processor
def inject_translations():
    """تزويد كافة قوالب HTML بدالة الترجمة واتجاه الصفحة ديناميكياً دون تعديل المسارات"""
    current_lang = session.get('lang', 'ar') # اللغة الافتراضية التطبيق هي العربية
    
    def translate_key(key):
        # البحث عن الكلمة، إذا لم توجد يتم طباعة المفتاح نفسه كحماية من توقف التطبيق
        return TRANSLATIONS.get(current_lang, TRANSLATIONS['ar']).get(key, key)
        
    # تحديد اتجاه التصميم بناءً على اللغة المحددة
    page_direction = 'rtl' if current_lang == 'ar' else 'ltr'
    
    return dict(_=translate_key, current_lang=current_lang, page_direction=page_direction)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        # إنشاء حساب مدير افتراضي إذا كانت قاعدة البيانات فارغة تماماً
        if not User.query.filter_by(username='admin').first():
            admin_pass = generate_password_hash('admin123', method='pbkdf2:sha256')
            db.session.add(User(username='admin', full_name='School Admin', password=admin_pass, role='admin'))
            db.session.commit()
    app.run(debug=True)