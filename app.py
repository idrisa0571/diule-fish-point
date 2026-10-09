# ============================================
# DIULE FISH POINT
# Samaki Fresh Kila Siku
# Mfumo wa Usimamizi wa Biashara ya Samaki
# ============================================

from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import func
from datetime import datetime, date, timedelta
import os

# ============================================
# SETUP YA APP
# ============================================

app = Flask(__name__)
app.config['SECRET_KEY'] = 'diule-fish-point-siri-2025'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Tafadhali ingia kwanza / Please login first'

# ============================================
# MODELS (DATABASE TABLES)
# ============================================

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), default='user')


class Samaki(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    jina = db.Column(db.String(100), nullable=False)
    kipimo = db.Column(db.String(20), default='kilo')
    bei_kununua = db.Column(db.Float, default=0)
    bei_kuuza = db.Column(db.Float, default=0)
    stock = db.Column(db.Float, default=0)


class Mvuvi(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    jina = db.Column(db.String(100), nullable=False)
    simu = db.Column(db.String(20))
    eneo = db.Column(db.String(50))


class Mteja(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    jina = db.Column(db.String(100), nullable=False)
    simu = db.Column(db.String(20))
    mahali = db.Column(db.String(100))


class Manunuzi(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tarehe = db.Column(db.Date, default=date.today)
    mvuvi_id = db.Column(db.Integer, db.ForeignKey('mvuvi.id'))
    samaki_id = db.Column(db.Integer, db.ForeignKey('samaki.id'))
    kiasi = db.Column(db.Float, nullable=False)
    bei = db.Column(db.Float, nullable=False)
    usafiri = db.Column(db.Float, default=0)
    barafu = db.Column(db.Float, default=0)
    nyingine = db.Column(db.Float, default=0)
    maelezo = db.Column(db.String(200))
    jumla = db.Column(db.Float, default=0)

    mvuvi = db.relationship('Mvuvi')
    samaki = db.relationship('Samaki')


class Mauzo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tarehe = db.Column(db.Date, default=date.today)
    mteja_id = db.Column(db.Integer, db.ForeignKey('mteja.id'))
    samaki_id = db.Column(db.Integer, db.ForeignKey('samaki.id'))
    kiasi = db.Column(db.Float, nullable=False)
    bei = db.Column(db.Float, nullable=False)
    malipo = db.Column(db.String(20), default='cash')
    jumla = db.Column(db.Float, default=0)

    mteja = db.relationship('Mteja')
    samaki = db.relationship('Samaki')


class Gharama(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tarehe = db.Column(db.Date, default=date.today)
    aina = db.Column(db.String(50))
    maelezo = db.Column(db.String(200))
    kiasi = db.Column(db.Float, default=0)

# ============================================
# ROUTES ZA LOGIN/LOGOUT
# ============================================

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            flash('Karibu DIULE FISH POINT! 🐟', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Jina la mtumiaji au password si sahihi / Wrong credentials', 'danger')
    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Umetoka salama / Logged out', 'success')
    return redirect(url_for('login'))

# ============================================
# DASHBOARD
# ============================================

@app.route('/')
@login_required
def dashboard():
    leo = date.today()

    mauzo_leo = db.session.query(func.sum(Mauzo.jumla)).filter(Mauzo.tarehe == leo).scalar() or 0
    manunuzi_leo = db.session.query(func.sum(Manunuzi.jumla)).filter(Manunuzi.tarehe == leo).scalar() or 0
    gharama_leo = db.session.query(func.sum(Gharama.kiasi)).filter(Gharama.tarehe == leo).scalar() or 0
    faida_leo = mauzo_leo - manunuzi_leo - gharama_leo
    samaki_zote = Samaki.query.all()

    # Wateja na Wavuvi wote
    wateja_zote = Mteja.query.order_by(Mteja.jina).all()
    wavuvi_zote = Mvuvi.query.order_by(Mvuvi.jina).all()

    return render_template('dashboard.html',
        leo=leo,
        mauzo_leo=mauzo_leo,
        manunuzi_leo=manunuzi_leo,
        gharama_leo=gharama_leo,
        faida_leo=faida_leo,
        samaki_zote=samaki_zote,
        wateja_zote=wateja_zote,
        wavuvi_zote=wavuvi_zote
    )

# ============================================
# SAMAKI (CRUD)
# ============================================

@app.route('/samaki')
@login_required
def samaki_list():
    items = Samaki.query.order_by(Samaki.jina).all()
    return render_template('samaki.html', items=items)


@app.route('/samaki/add', methods=['POST'])
@login_required
def samaki_add():
    jina = request.form['jina'].strip()
    kipimo = request.form['kipimo']
    bei_kununua = float(request.form.get('bei_kununua', 0) or 0)
    bei_kuuza = float(request.form.get('bei_kuuza', 0) or 0)
    stock = float(request.form.get('stock', 0) or 0)

    if not jina:
        flash('Jina la samaki linahitajika / Fish name is required', 'danger')
        return redirect(url_for('samaki_list'))

    s = Samaki(jina=jina, kipimo=kipimo, bei_kununua=bei_kununua, bei_kuuza=bei_kuuza, stock=stock)
    db.session.add(s)
    db.session.commit()
    flash(f'Samaki "{jina}" ameongezwa / Fish added', 'success')
    return redirect(url_for('samaki_list'))


@app.route('/samaki/edit/<int:id>', methods=['POST'])
@login_required
def samaki_edit(id):
    s = Samaki.query.get_or_404(id)
    s.jina = request.form['jina'].strip()
    s.kipimo = request.form['kipimo']
    s.bei_kununua = float(request.form.get('bei_kununua', 0) or 0)
    s.bei_kuuza = float(request.form.get('bei_kuuza', 0) or 0)
    s.stock = float(request.form.get('stock', 0) or 0)
    db.session.commit()
    flash('Imehaririwa / Updated', 'success')
    return redirect(url_for('samaki_list'))


@app.route('/samaki/delete/<int:id>')
@login_required
def samaki_delete(id):
    s = Samaki.query.get_or_404(id)
    jina = s.jina
    db.session.delete(s)
    db.session.commit()
    flash(f'Samaki "{jina}" amefutwa / Fish deleted', 'warning')
    return redirect(url_for('samaki_list'))

# ============================================
# MANUNUZI
# ============================================

@app.route('/manunuzi')
@login_required
def manunuzi_list():
    items = Manunuzi.query.order_by(Manunuzi.tarehe.desc(), Manunuzi.id.desc()).all()
    samaki_zote = Samaki.query.order_by(Samaki.jina).all()
    wavuvi = Mvuvi.query.order_by(Mvuvi.jina).all()
    return render_template('manunuzi.html',
        items=items,
        samaki_zote=samaki_zote,
        wavuvi=wavuvi,
        leo=date.today().strftime('%Y-%m-%d')
    )


@app.route('/manunuzi/add', methods=['POST'])
@login_required
def manunuzi_add():
    try:
        kiasi = float(request.form['kiasi'])
        bei = float(request.form['bei'])
        usafiri = float(request.form.get('usafiri', 0) or 0)
        barafu = float(request.form.get('barafu', 0) or 0)
        nyingine = float(request.form.get('nyingine', 0) or 0)
    except ValueError:
        flash('Tafadhali jaza namba sahihi / Please enter valid numbers', 'danger')
        return redirect(url_for('manunuzi_list'))

    if kiasi <= 0:
        flash('Kiasi kinatakiwa kiwe zaidi ya 0', 'danger')
        return redirect(url_for('manunuzi_list'))

    samaki_id = request.form['samaki_id']
    mvuvi_id = request.form.get('mvuvi_id') or None
    maelezo = request.form.get('maelezo', '').strip()

    jumla = (kiasi * bei) + usafiri + barafu + nyingine

    m = Manunuzi(
        tarehe=datetime.strptime(request.form['tarehe'], '%Y-%m-%d').date(),
        mvuvi_id=mvuvi_id,
        samaki_id=samaki_id,
        kiasi=kiasi,
        bei=bei,
        usafiri=usafiri,
        barafu=barafu,
        nyingine=nyingine,
        maelezo=maelezo,
        jumla=jumla
    )
    db.session.add(m)

    # Ongeza stock kwenye samaki
    s = Samaki.query.get(samaki_id)
    if s:
        s.stock += kiasi

    db.session.commit()
    flash('Manunuzi yameongezwa / Purchase recorded', 'success')
    return redirect(url_for('manunuzi_list'))


@app.route('/manunuzi/delete/<int:id>')
@login_required
def manunuzi_delete(id):
    m = Manunuzi.query.get_or_404(id)
    # Toa stock kwenye samaki
    s = Samaki.query.get(m.samaki_id)
    if s:
        s.stock -= m.kiasi
    db.session.delete(m)
    db.session.commit()
    flash('Manunuzi yamefutwa / Purchase deleted', 'warning')
    return redirect(url_for('manunuzi_list'))

# ============================================
# MAUZO
# ============================================

@app.route('/mauzo')
@login_required
def mauzo_list():
    items = Mauzo.query.order_by(Mauzo.tarehe.desc(), Mauzo.id.desc()).all()
    samaki_zote = Samaki.query.order_by(Samaki.jina).all()
    wateja = Mteja.query.order_by(Mteja.jina).all()
    return render_template('mauzo.html',
        items=items,
        samaki_zote=samaki_zote,
        wateja=wateja,
        leo=date.today().strftime('%Y-%m-%d')
    )


@app.route('/mauzo/add', methods=['POST'])
@login_required
def mauzo_add():
    try:
        kiasi = float(request.form['kiasi'])
        bei = float(request.form['bei'])
    except ValueError:
        flash('Tafadhali jaza namba sahihi / Please enter valid numbers', 'danger')
        return redirect(url_for('mauzo_list'))

    if kiasi <= 0:
        flash('Kiasi kinatakiwa kiwe zaidi ya 0', 'danger')
        return redirect(url_for('mauzo_list'))

    samaki_id = request.form['samaki_id']
    mteja_id = request.form.get('mteja_id') or None
    malipo = request.form.get('malipo', 'cash')
    maelezo = request.form.get('maelezo', '').strip()

    # Kagua stock
    s = Samaki.query.get(samaki_id)
    if not s:
        flash('Samaki haipo / Fish not found', 'danger')
        return redirect(url_for('mauzo_list'))

    if s.stock < kiasi:
        flash(f'Stock haitoshi! Uliyopo: {s.stock} {s.kipimo} / Not enough stock', 'danger')
        return redirect(url_for('mauzo_list'))

    jumla = kiasi * bei

    m = Mauzo(
        tarehe=datetime.strptime(request.form['tarehe'], '%Y-%m-%d').date(),
        mteja_id=mteja_id,
        samaki_id=samaki_id,
        kiasi=kiasi,
        bei=bei,
        malipo=malipo,
        jumla=jumla
    )
    db.session.add(m)

    # Punguza stock
    s.stock -= kiasi

    db.session.commit()
    flash('Mauzo yamerekodiwa / Sale recorded', 'success')
    return redirect(url_for('mauzo_list'))


@app.route('/mauzo/delete/<int:id>')
@login_required
def mauzo_delete(id):
    m = Mauzo.query.get_or_404(id)
    # Rudisha stock
    s = Samaki.query.get(m.samaki_id)
    if s:
        s.stock += m.kiasi
    db.session.delete(m)
    db.session.commit()
    flash('Mauzo yamefutwa / Sale deleted', 'warning')
    return redirect(url_for('mauzo_list'))

# ============================================
# WAVUVI (FISHERMEN)
# ============================================

@app.route('/wavuvi')
@login_required
def wavuvi_list():
    items = Mvuvi.query.order_by(Mvuvi.jina).all()
    return render_template('wavuvi.html', items=items)


@app.route('/wavuvi/add', methods=['POST'])
@login_required
def wavuvi_add():
    jina = request.form['jina'].strip()
    simu = request.form.get('simu', '').strip()
    eneo = request.form.get('eneo', '').strip()

    if not jina:
        flash('Jina la mvuvi linahitajika / Fisherman name is required', 'danger')
        return redirect(url_for('wavuvi_list'))

    m = Mvuvi(jina=jina, simu=simu, eneo=eneo)
    db.session.add(m)
    db.session.commit()
    flash(f'Mvuvi "{jina}" ameongezwa / Fisherman added', 'success')
    return redirect(url_for('wavuvi_list'))


@app.route('/wavuvi/edit/<int:id>', methods=['POST'])
@login_required
def wavuvi_edit(id):
    m = Mvuvi.query.get_or_404(id)
    m.jina = request.form['jina'].strip()
    m.simu = request.form.get('simu', '').strip()
    m.eneo = request.form.get('eneo', '').strip()
    db.session.commit()
    flash('Imehaririwa / Updated', 'success')
    return redirect(url_for('wavuvi_list'))


@app.route('/wavuvi/delete/<int:id>')
@login_required
def wavuvi_delete(id):
    m = Mvuvi.query.get_or_404(id)
    jina = m.jina
    db.session.delete(m)
    db.session.commit()
    flash(f'Mvuvi "{jina}" amefutwa / Fisherman deleted', 'warning')
    return redirect(url_for('wavuvi_list'))


# ============================================
# WATEJA (CUSTOMERS)
# ============================================

@app.route('/wateja')
@login_required
def wateja_list():
    items = Mteja.query.order_by(Mteja.jina).all()
    return render_template('wateja.html', items=items)


@app.route('/wateja/add', methods=['POST'])
@login_required
def wateja_add():
    jina = request.form['jina'].strip()
    simu = request.form.get('simu', '').strip()
    mahali = request.form.get('mahali', '').strip()

    if not jina:
        flash('Jina la mteja linahitajika / Customer name is required', 'danger')
        return redirect(url_for('wateja_list'))

    m = Mteja(jina=jina, simu=simu, mahali=mahali)
    db.session.add(m)
    db.session.commit()
    flash(f'Mteja "{jina}" ameongezwa / Customer added', 'success')
    return redirect(url_for('wateja_list'))


@app.route('/wateja/edit/<int:id>', methods=['POST'])
@login_required
def wateja_edit(id):
    m = Mteja.query.get_or_404(id)
    m.jina = request.form['jina'].strip()
    m.simu = request.form.get('simu', '').strip()
    m.mahali = request.form.get('mahali', '').strip()
    db.session.commit()
    flash('Imehaririwa / Updated', 'success')
    return redirect(url_for('wateja_list'))


@app.route('/wateja/delete/<int:id>')
@login_required
def wateja_delete(id):
    m = Mteja.query.get_or_404(id)
    jina = m.jina
    db.session.delete(m)
    db.session.commit()
    flash(f'Mteja "{jina}" amefutwa / Customer deleted', 'warning')
    return redirect(url_for('wateja_list'))


# ============================================
# RIPOTI
# ============================================

@app.route('/ripoti')
@login_required
def ripoti():
    # Chukua tarehe kutoka URL, au tumia default (leo)
    kuanzia = request.args.get('kuanzia', date.today().strftime('%Y-%m-%d'))
    hadi = request.args.get('hadi', date.today().strftime('%Y-%m-%d'))

    # Badilisha kuwa date
    kuanzia_d = datetime.strptime(kuanzia, '%Y-%m-%d').date()
    hadi_d = datetime.strptime(hadi, '%Y-%m-%d').date()

    # Mauzo kwenye kipindi
    mauzo = Mauzo.query.filter(Mauzo.tarehe >= kuanzia_d, Mauzo.tarehe <= hadi_d).order_by(Mauzo.tarehe.desc()).all()
    # Manunuzi kwenye kipindi
    manunuzi = Manunuzi.query.filter(Manunuzi.tarehe >= kuanzia_d, Manunuzi.tarehe <= hadi_d).order_by(Manunuzi.tarehe.desc()).all()
    # Gharama kwenye kipindi
    gharama = Gharama.query.filter(Gharama.tarehe >= kuanzia_d, Gharama.tarehe <= hadi_d).order_by(Gharama.tarehe.desc()).all()

    # Jumla
    jumla_mauzo = sum(m.jumla for m in mauzo)
    jumla_manunuzi = sum(m.jumla for m in manunuzi)
    jumla_gharama = sum(g.kiasi for g in gharama)
    faida = jumla_mauzo - jumla_manunuzi - jumla_gharama

    # Data ya grafu — mauzo kwa siku
    mauzo_kwa_siku = {}
    for m in mauzo:
        tarehe_str = m.tarehe.strftime('%Y-%m-%d')
        mauzo_kwa_siku[tarehe_str] = mauzo_kwa_siku.get(tarehe_str, 0) + m.jumla

    # Panga kwa tarehe
    siku_zote = sorted(mauzo_kwa_siku.keys())
    mauzo_values = [mauzo_kwa_siku[s] for s in siku_zote]

    return render_template('ripoti.html',
        kuanzia=kuanzia,
        hadi=hadi,
        mauzo=mauzo,
        manunuzi=manunuzi,
        gharama=gharama,
        jumla_mauzo=jumla_mauzo,
        jumla_manunuzi=jumla_manunuzi,
        jumla_gharama=jumla_gharama,
        faida=faida,
        siku_zote=siku_zote,
        mauzo_values=mauzo_values,
        leo_str=date.today().strftime('%Y-%m-%d'),
        leo_minus_7=(date.today() - timedelta(days=7)).strftime('%Y-%m-%d'),
        mwezi_kuanzia=date.today().replace(day=1).strftime('%Y-%m-%d')
    )


@app.route('/ripoti/export')
@login_required
def ripoti_export():
    """Download CSV ya mauzo yote"""
    import csv
    from io import StringIO
    from flask import make_response

    kuanzia = request.args.get('kuanzia', date.today().strftime('%Y-%m-%d'))
    hadi = request.args.get('hadi', date.today().strftime('%Y-%m-%d'))
    kuanzia_d = datetime.strptime(kuanzia, '%Y-%m-%d').date()
    hadi_d = datetime.strptime(hadi, '%Y-%m-%d').date()

    mauzo = Mauzo.query.filter(Mauzo.tarehe >= kuanzia_d, Mauzo.tarehe <= hadi_d).order_by(Mauzo.tarehe).all()

    # Tengeneza CSV
    si = StringIO()
    writer = csv.writer(si)
    writer.writerow(['Tarehe', 'Samaki', 'Kiasi', 'Kipimo', 'Bei', 'Malipo', 'Mteja', 'Jumla'])

    for m in mauzo:
        writer.writerow([
            m.tarehe.strftime('%Y-%m-%d'),
            m.samaki.jina if m.samaki else '',
            m.kiasi,
            m.samaki.kipimo if m.samaki else '',
            m.bei,
            m.malipo,
            m.mteja.jina if m.mteja else '',
            m.jumla
        ])

    # Tengeneza response
    output = make_response(si.getvalue())
    output.headers['Content-Type'] = 'text/csv; charset=utf-8'
    output.headers['Content-Disposition'] = f'attachment; filename=ripoti_mauzo_{kuanzia}_{hadi}.csv'
    return output

# ============================================
# KUTENGENEZA DATABASE NA USER WA KWANZA
# ============================================

def init_db():
    with app.app_context():
        db.create_all()
        if not User.query.filter_by(username='admin').first():
            u = User(
                username='admin',
                password=generate_password_hash('admin123'),
                role='admin'
            )
            db.session.add(u)
            db.session.commit()
            print("✅ Mtumiaji wa kwanza ameundwa / First user created")
            print("   Username: admin")
            print("   Password: admin123")

# ============================================
# KUKIMBIZA APP
# ============================================
if __name__ == '__main__':
    print("🐟 DIULE FISH POINT - Inaanza...")
    init_db()
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)