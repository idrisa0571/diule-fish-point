from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from models import db, Samaki, Mvuvi, Manunuzi, Mteja, Mauzo, Malipo, Matumizi, User
from datetime import datetime, timedelta

app = Flask(__name__)
app.config['SECRET_KEY'] = 'siri_ya_samaki_2026'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///samaki.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

# ==================== LOGIN SETUP ====================
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Tafadhali ingia kwanza.'


class UserLogin(UserMixin):
    def __init__(self, user):
        self.id = str(user.id)
        self.username = user.username


@login_manager.user_loader
def load_user(user_id):
    user = User.query.get(int(user_id))
    if user:
        return UserLogin(user)
    return None


# ==================== LOGIN / LOGOUT ====================
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username, password=password).first()
        if user:
            login_user(UserLogin(user))
            flash(f'Karibu, {user.username}!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Jina la mtumiaji au password si sahihi!', 'danger')

    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Umetoka salama.', 'info')
    return redirect(url_for('login'))


# ==================== DASHBOARD ====================
@app.route('/')
@login_required
def index():
    samaki_wote = Samaki.query.all()
    leo = datetime.utcnow().date()

    # ===== STOCK =====
    jumla_stock_kg = sum(s.stock_kg for s in samaki_wote)
    thamani_stock = sum(s.stock_kg * s.bei_kununua for s in samaki_wote)

    # ===== MAPATO =====
    mauzo_leo = Mauzo.query.filter(db.func.date(Mauzo.tarehe) == leo).all()
    mauzo_yote = Mauzo.query.all()
    mapato_leo = sum(m.jumla for m in mauzo_leo)
    mapato_yote = sum(m.jumla for m in mauzo_yote)

    # ===== MATUMIZI =====
    matumizi_leo_list = Matumizi.query.filter(db.func.date(Matumizi.tarehe) == leo).all()
    matumizi_yote_list = Matumizi.query.all()
    matumizi_leo = sum(m.kiasi for m in matumizi_leo_list)
    matumizi_yote = sum(m.kiasi for m in matumizi_yote_list)

    # ===== GHARAMA YA SAMAKI ILIYOUZWA =====
    gharama_samaki_leo = 0
    for m in mauzo_leo:
        if m.samaki:
            gharama_samaki_leo += m.kiasi_kg * m.samaki.bei_kununua

    gharama_samaki_yote = 0
    for m in mauzo_yote:
        if m.samaki:
            gharama_samaki_yote += m.kiasi_kg * m.samaki.bei_kununua

    # ===== FAIDA HALISI =====
    faida_leo = mapato_leo - matumizi_leo - gharama_samaki_leo
    faida_yote = mapato_yote - matumizi_yote - gharama_samaki_yote

    # ===== MADENI =====
    madeni_yote = db.session.query(db.func.sum(Mteja.deni)).scalar() or 0

    # ===== KILO IN / OUT LEO =====
    kilo_in_leo = sum(m.kiasi_kg for m in Manunuzi.query.filter(
        db.func.date(Manunuzi.tarehe) == leo).all())
    kilo_out_leo = sum(m.kiasi_kg for m in mauzo_leo)

    # ===== KILO IN / OUT JUMLA =====
    kilo_in_yote = sum(m.kiasi_kg for m in Manunuzi.query.all())
    kilo_out_yote = sum(m.kiasi_kg for m in mauzo_yote)

    # ===== SAMAKI KWA KILA MMOJA =====
    samaki_habari = []
    for s in samaki_wote:
        in_jumla = db.session.query(db.func.sum(Manunuzi.kiasi_kg)).filter(
            Manunuzi.samaki_id == s.id).scalar() or 0
        out_jumla = db.session.query(db.func.sum(Mauzo.kiasi_kg)).filter(
            Mauzo.samaki_id == s.id).scalar() or 0
        balance = in_jumla - out_jumla
        thamani = balance * s.bei_kununua

        samaki_habari.append({
            'jina': s.jina,
            'aina': s.aina,
            'in': in_jumla,
            'out': out_jumla,
            'balance': balance,
            'bei_kununua': s.bei_kununua,
            'bei_kuuza': s.bei_kuuza,
            'thamani': thamani
        })

    return render_template('index.html',
                           samaki_habari=samaki_habari,
                           jumla_stock_kg=jumla_stock_kg,
                           thamani_stock=thamani_stock,
                           mapato_leo=mapato_leo,
                           mapato_yote=mapato_yote,
                           matumizi_leo=matumizi_leo,
                           matumizi_yote=matumizi_yote,
                           faida_leo=faida_leo,
                           faida_yote=faida_yote,
                           madeni_yote=madeni_yote,
                           kilo_in_leo=kilo_in_leo,
                           kilo_out_leo=kilo_out_leo,
                           kilo_in_yote=kilo_in_yote,
                           kilo_out_yote=kilo_out_yote,
                           leo=leo)


# ==================== SAMAKI ====================
@app.route('/samaki')
@login_required
def samaki_ukurasa():
    samaki_wote = Samaki.query.all()
    return render_template('samaki.html', samaki=samaki_wote)


@app.route('/samaki/ongeza', methods=['POST'])
@login_required
def ongeza_samaki():
    jina = request.form['jina']
    aina = request.form.get('aina', '')
    bei_kununua = float(request.form['bei_kununua'])
    bei_kuuza = float(request.form['bei_kuuza'])
    stock = float(request.form.get('stock', 0))

    mpya = Samaki(jina=jina, aina=aina,
                  bei_kununua=bei_kununua,
                  bei_kuuza=bei_kuuza,
                  stock_kg=stock)
    db.session.add(mpya)
    db.session.commit()
    flash(f'{jina} imeongezwa!', 'success')
    return redirect(url_for('samaki_ukurasa'))


@app.route('/samaki/edit/<int:id>', methods=['POST'])
@login_required
def edit_samaki(id):
    s = Samaki.query.get_or_404(id)
    s.jina = request.form['jina']
    s.aina = request.form.get('aina', '')
    s.bei_kununua = float(request.form['bei_kununua'])
    s.bei_kuuza = float(request.form['bei_kuuza'])
    db.session.commit()
    flash(f'{s.jina} imerekebishwa!', 'success')
    return redirect(url_for('samaki_ukurasa'))


@app.route('/samaki/delete/<int:id>', methods=['POST'])
@login_required
def delete_samaki(id):
    s = Samaki.query.get_or_404(id)

    manunuzi_count = Manunuzi.query.filter_by(samaki_id=id).count()
    mauzo_count = Mauzo.query.filter_by(samaki_id=id).count()

    if manunuzi_count > 0 or mauzo_count > 0:
        flash(f'Haiwezi kufutwa! {s.jina} ina manunuzi {manunuzi_count} na mauzo {mauzo_count}. Futa kwanza.', 'danger')
        return redirect(url_for('samaki_ukurasa'))

    db.session.delete(s)
    db.session.commit()
    flash(f'{s.jina} imefutwa!', 'success')
    return redirect(url_for('samaki_ukurasa'))

# ==================== WAVUVI ====================
@app.route('/wavuvi')
@login_required
def wavuvi_ukurasa():
    wavuvi_wote = Mvuvi.query.all()
    return render_template('wavuvi.html', wavuvi=wavuvi_wote)


@app.route('/wavuvi/ongeza', methods=['POST'])
@login_required
def ongeza_mvuvi():
    jina = request.form['jina']
    simu = request.form.get('simu', '')
    mahali = request.form.get('mahali', '')

    mpya = Mvuvi(jina=jina, simu=simu, mahali=mahali)
    db.session.add(mpya)
    db.session.commit()
    flash(f'Mvuvi {jina} ameongezwa!', 'success')
    return redirect(url_for('wavuvi_ukurasa'))

@app.route('/wavuvi/edit/<int:id>', methods=['POST'])
@login_required
def edit_mvuvi(id):
    w = Mvuvi.query.get_or_404(id)
    w.jina = request.form['jina']
    w.simu = request.form.get('simu', '')
    w.mahali = request.form.get('mahali', '')
    db.session.commit()
    flash(f'{w.jina} amerekebishwa!', 'success')
    return redirect(url_for('wavuvi_ukurasa'))


@app.route('/wavuvi/delete/<int:id>', methods=['POST'])
@login_required
def delete_mvuvi(id):
    w = Mvuvi.query.get_or_404(id)

    manunuzi_count = Manunuzi.query.filter_by(mvuvi_id=id).count()
    if manunuzi_count > 0:
        flash(f'Haiwezi kufutwa! {w.jina} ana manunuzi {manunuzi_count}. Futa kwanza.', 'danger')
        return redirect(url_for('wavuvi_ukurasa'))

    db.session.delete(w)
    db.session.commit()
    flash(f'{w.jina} amefutwa!', 'success')
    return redirect(url_for('wavuvi_ukurasa'))

# ==================== MANUNUZI ====================
@app.route('/manunuzi')
@login_required
def manunuzi_ukurasa():
    manunuzi_yote = Manunuzi.query.order_by(Manunuzi.tarehe.desc()).all()
    wavuvi_wote = Mvuvi.query.all()
    samaki_wote = Samaki.query.all()
    return render_template('manunuzi.html',
                           manunuzi=manunuzi_yote,
                           wavuvi=wavuvi_wote,
                           samaki=samaki_wote)


@app.route('/manunuzi/ongeza', methods=['POST'])
@login_required
def ongeza_manunuzi():
    mvuvi_id = int(request.form['mvuvi_id'])
    samaki_id = int(request.form['samaki_id'])
    kiasi = float(request.form['kiasi_kg'])
    bei = float(request.form['bei_kwa_kg'])
    jumla = kiasi * bei

    samaki = Samaki.query.get(samaki_id)
    samaki.stock_kg += kiasi
    samaki.bei_kununua = bei

    mpya = Manunuzi(mvuvi_id=mvuvi_id, samaki_id=samaki_id,
                    kiasi_kg=kiasi, bei_kwa_kg=bei, jumla=jumla)
    db.session.add(mpya)
    db.session.commit()
    flash(f'Manunuzi ya kilo {kiasi} yameongezwa!', 'success')
    return redirect(url_for('manunuzi_ukurasa'))

@app.route('/manunuzi/edit/<int:id>', methods=['POST'])
@login_required
def edit_manunuzi(id):
    m = Manunuzi.query.get_or_404(id)
    samaki = Samaki.query.get(m.samaki_id)

    kiasi_mpya = float(request.form['kiasi_kg'])
    bei_mpya = float(request.form['bei_kwa_kg'])

    # Tofauti ya kiasi
    tofauti = kiasi_mpya - m.kiasi_kg

    # Angalia kama stock inatosha kama tunapunguza
    if tofauti < 0 and samaki.stock_kg + tofauti < 0:
        flash(f'Haiwezi! Stock ya {samaki.jina} haitoshi (iliyopo: {samaki.stock_kg} kg)', 'danger')
        return redirect(url_for('manunuzi_ukurasa'))

    # Sasisha stock
    samaki.stock_kg += tofauti

    # Sasisha manunuzi
    m.kiasi_kg = kiasi_mpya
    m.bei_kwa_kg = bei_mpya
    m.jumla = kiasi_mpya * bei_mpya

    db.session.commit()
    flash('Manunuzi yamerekebishwa!', 'success')
    return redirect(url_for('manunuzi_ukurasa'))


@app.route('/manunuzi/delete/<int:id>', methods=['POST'])
@login_required
def delete_manunuzi(id):
    m = Manunuzi.query.get_or_404(id)
    samaki = Samaki.query.get(m.samaki_id)

    # Angalia kama stock inatosha kupunguza
    if samaki.stock_kg < m.kiasi_kg:
        flash(f'Haiwezi kufutwa! Stock ya {samaki.jina} ({samaki.stock_kg} kg) ni chini ya kilo zilizonunuliwa ({m.kiasi_kg} kg).', 'danger')
        return redirect(url_for('manunuzi_ukurasa'))

    # Punguza stock
    samaki.stock_kg -= m.kiasi_kg

    db.session.delete(m)
    db.session.commit()
    flash('Manunuzi yamefutwa!', 'success')
    return redirect(url_for('manunuzi_ukurasa'))


# ==================== WATEJA ====================
@app.route('/wateja')
@login_required
def wateja_ukurasa():
    wateja_wote = Mteja.query.all()
    return render_template('wateja.html', wateja=wateja_wote)


@app.route('/wateja/ongeza', methods=['POST'])
@login_required
def ongeza_mteja():
    jina = request.form['jina']
    simu = request.form.get('simu', '')

    mpya = Mteja(jina=jina, simu=simu)
    db.session.add(mpya)
    db.session.commit()
    flash(f'Mteja {jina} ameongezwa!', 'success')
    return redirect(url_for('wateja_ukurasa'))

@app.route('/wateja/edit/<int:id>', methods=['POST'])
@login_required
def edit_mteja(id):
    m = Mteja.query.get_or_404(id)
    m.jina = request.form['jina']
    m.simu = request.form.get('simu', '')
    db.session.commit()
    flash(f'{m.jina} amerekebishwa!', 'success')
    return redirect(url_for('wateja_ukurasa'))


@app.route('/wateja/delete/<int:id>', methods=['POST'])
@login_required
def delete_mteja(id):
    m = Mteja.query.get_or_404(id)

    # Zuia kama ana mauzo au deni
    mauzo_count = Mauzo.query.filter_by(mteja_id=id).count()
    if mauzo_count > 0:
        flash(f'Haiwezi kufutwa! {m.jina} ana mauzo {mauzo_count}. Futa mauzo kwanza.', 'danger')
        return redirect(url_for('wateja_ukurasa'))

    if m.deni > 0:
        flash(f'Haiwezi kufutwa! {m.jina} ana deni la {m.deni:,.0f} TSh. Lipa kwanza.', 'danger')
        return redirect(url_for('wateja_ukurasa'))

    db.session.delete(m)
    db.session.commit()
    flash(f'{m.jina} amefutwa!', 'success')
    return redirect(url_for('wateja_ukurasa'))

# ==================== MAUZO ====================
@app.route('/mauzo')
@login_required
def mauzo_ukurasa():
    mauzo_yote = Mauzo.query.order_by(Mauzo.tarehe.desc()).all()
    samaki_wote = Samaki.query.filter(Samaki.stock_kg > 0).all()
    wateja_wote = Mteja.query.all()
    return render_template('mauzo.html',
                           mauzo=mauzo_yote,
                           samaki=samaki_wote,
                           wateja=wateja_wote)


@app.route('/mauzo/ongeza', methods=['POST'])
@login_required
def ongeza_mauzo():
    samaki_id = int(request.form['samaki_id'])
    kiasi = float(request.form['kiasi_kg'])
    bei = float(request.form['bei_kwa_kg'])
    aina_malipo = request.form['aina_ya_malipo']
    mteja_id = request.form.get('mteja_id')

    samaki = Samaki.query.get(samaki_id)

    if samaki.stock_kg < kiasi:
        flash(f'Stock haitoshi! Iliyopo: {samaki.stock_kg} kg', 'danger')
        return redirect(url_for('mauzo_ukurasa'))

    jumla = kiasi * bei
    samaki.stock_kg -= kiasi

    if aina_malipo == 'deni' and mteja_id:
        mteja = Mteja.query.get(int(mteja_id))
        if mteja:
            mteja.deni += jumla
        else:
            flash('Chagua mteja kwa mauzo ya deni!', 'danger')
            return redirect(url_for('mauzo_ukurasa'))

    mpya = Mauzo(samaki_id=samaki_id,
                 mteja_id=int(mteja_id) if mteja_id else None,
                 kiasi_kg=kiasi, bei_kwa_kg=bei, jumla=jumla,
                 aina_ya_malipo=aina_malipo)
    db.session.add(mpya)
    db.session.commit()
    flash(f'Mauzo ya kilo {kiasi} yamefanikiwa!', 'success')
    return redirect(url_for('mauzo_ukurasa'))

@app.route('/mauzo/edit/<int:id>', methods=['POST'])
@login_required
def edit_mauzo(id):
    m = Mauzo.query.get_or_404(id)
    samaki = Samaki.query.get(m.samaki_id)

    kiasi_mpya = float(request.form['kiasi_kg'])
    bei_mpya = float(request.form['bei_kwa_kg'])

    # Tofauti ya kiasi
    tofauti = kiasi_mpya - m.kiasi_kg

    # Kama tunaongeza kiasi, angalia stock
    if tofauti > 0 and samaki.stock_kg < tofauti:
        flash(f'Stock haitoshi! Iliyopo: {samaki.stock_kg} kg, unahitaji {tofauti} kg zaidi.', 'danger')
        return redirect(url_for('mauzo_ukurasa'))

    # Sasisha stock (kama tofauti ni +, punguza zaidi; kama ni -, rudisha stock)
    samaki.stock_kg -= tofauti

    # Sasisha deni la mteja kama ni mauzo ya deni
    if m.aina_ya_malipo == 'deni' and m.mteja:
        jumla_ya_zamani = m.jumla
        jumla_mpya = kiasi_mpya * bei_mpya
        tofauti_deni = jumla_mpya - jumla_ya_zamani
        m.mteja.deni += tofauti_deni
        if m.mteja.deni < 0:
            m.mteja.deni = 0

    # Sasisha mauzo
    m.kiasi_kg = kiasi_mpya
    m.bei_kwa_kg = bei_mpya
    m.jumla = kiasi_mpya * bei_mpya

    db.session.commit()
    flash('Mauzo yamerekebishwa!', 'success')
    return redirect(url_for('mauzo_ukurasa'))


@app.route('/mauzo/delete/<int:id>', methods=['POST'])
@login_required
def delete_mauzo(id):
    m = Mauzo.query.get_or_404(id)
    samaki = Samaki.query.get(m.samaki_id)

    # Rudisha stock
    samaki.stock_kg += m.kiasi_kg

    # Punguza deni la mteja kama ni mauzo ya deni
    if m.aina_ya_malipo == 'deni' and m.mteja:
        m.mteja.deni -= m.jumla
        if m.mteja.deni < 0:
            m.mteja.deni = 0

    db.session.delete(m)
    db.session.commit()
    flash('Mauzo yamefutwa! Stock imerudi.', 'success')
    return redirect(url_for('mauzo_ukurasa'))


# ==================== MALIPO ====================
@app.route('/malipo', methods=['GET', 'POST'])
@login_required
def malipo_ukurasa():
    if request.method == 'POST':
        mteja_id = int(request.form['mteja_id'])
        kiasi = float(request.form['kiasi'])
        maelezo = request.form.get('maelezo', '')

        mteja = Mteja.query.get(mteja_id)
        if mteja:
            mteja.deni -= kiasi
            if mteja.deni < 0:
                mteja.deni = 0

            mpya = Malipo(mteja_id=mteja_id, kiasi=kiasi, maelezo=maelezo)
            db.session.add(mpya)
            db.session.commit()
            flash(f'Malipo ya {kiasi} yamepokelewa!', 'success')
        return redirect(url_for('malipo_ukurasa'))

    wateja_wenye_deni = Mteja.query.filter(Mteja.deni > 0).all()
    malipo_yote = Malipo.query.order_by(Malipo.tarehe.desc()).limit(20).all()
    return render_template('malipo.html',
                           wateja=wateja_wenye_deni,
                           malipo=malipo_yote)

@app.route('/malipo/edit/<int:id>', methods=['POST'])
@login_required
def edit_malipo(id):
    m = Malipo.query.get_or_404(id)
    mteja = Mteja.query.get(m.mteja_id)

    kiasi_mpya = float(request.form['kiasi'])
    maelezo_mpya = request.form.get('maelezo', '')

    # Tofauti ya malipo
    tofauti = kiasi_mpya - m.kiasi

    # Sasisha deni la mteja
    # Kama malipo yameongezeka → deni linapungua zaidi
    # Kama malipo yamepungua → deni linaongezeka
    mteja.deni -= tofauti
    if mteja.deni < 0:
        mteja.deni = 0

    # Sasisha malipo
    m.kiasi = kiasi_mpya
    m.maelezo = maelezo_mpya

    db.session.commit()
    flash('Malipo yamerekebishwa!', 'success')
    return redirect(url_for('malipo_ukurasa'))


@app.route('/malipo/delete/<int:id>', methods=['POST'])
@login_required
def delete_malipo(id):
    m = Malipo.query.get_or_404(id)
    mteja = Mteja.query.get(m.mteja_id)

    # Rudisha deni la mteja
    mteja.deni += m.kiasi

    db.session.delete(m)
    db.session.commit()
    flash(f'Malipo yamefutwa! Deni la {mteja.jina} limerudi.', 'success')
    return redirect(url_for('malipo_ukurasa'))


# ==================== MATUMIZI ====================
@app.route('/matumizi', methods=['GET', 'POST'])
@login_required
def matumizi_ukurasa():
    if request.method == 'POST':
        aina = request.form['aina']
        kiasi = float(request.form['kiasi'])
        maelezo = request.form.get('maelezo', '')

        mpya = Matumizi(aina=aina, kiasi=kiasi, maelezo=maelezo)
        db.session.add(mpya)
        db.session.commit()
        flash(f'Matumizi ya {kiasi} yameongezwa!', 'success')
        return redirect(url_for('matumizi_ukurasa'))

    matumizi_yote = Matumizi.query.order_by(Matumizi.tarehe.desc()).all()
    return render_template('matumizi.html', matumizi=matumizi_yote)

@app.route('/matumizi/edit/<int:id>', methods=['POST'])
@login_required
def edit_matumizi(id):
    m = Matumizi.query.get_or_404(id)
    m.aina = request.form['aina']
    m.kiasi = float(request.form['kiasi'])
    m.maelezo = request.form.get('maelezo', '')
    db.session.commit()
    flash('Matumizi yamerekebishwa!', 'success')
    return redirect(url_for('matumizi_ukurasa'))


@app.route('/matumizi/delete/<int:id>', methods=['POST'])
@login_required
def delete_matumizi(id):
    m = Matumizi.query.get_or_404(id)
    db.session.delete(m)
    db.session.commit()
    flash('Matumizi yamefutwa!', 'success')
    return redirect(url_for('matumizi_ukurasa'))


# ==================== CHATI ====================
@app.route('/chati')
@login_required
def chati_ukurasa():
    leo = datetime.utcnow().date()

    # ===== 1. MAUZO KWA SIKU 7 ZILIZOPITA =====
    siku_7 = []
    mapato_kwa_siku = []
    for i in range(6, -1, -1):
        siku = leo - timedelta(days=i)
        mauzo_siku = Mauzo.query.filter(db.func.date(Mauzo.tarehe) == siku).all()
        jumla = sum(m.jumla for m in mauzo_siku)
        siku_7.append(siku.strftime('%d/%m'))
        mapato_kwa_siku.append(jumla)

    # ===== 2. SAMAKI WANAOUZA ZAIDI (Top 5) =====
    samaki_mauzo = db.session.query(
        Samaki.jina,
        db.func.sum(Mauzo.kiasi_kg).label('jumla_kg')
    ).join(Mauzo, Mauzo.samaki_id == Samaki.id).group_by(Samaki.id).order_by(
        db.func.sum(Mauzo.kiasi_kg).desc()
    ).limit(5).all()

    samaki_labels = [s[0] for s in samaki_mauzo]
    samaki_data = [float(s[1]) for s in samaki_mauzo]

    # ===== 3. MAPATO vs MATUMIZI KWA MWEZI =====
    miezi_6 = []
    mapato_kwa_mwezi = []
    matumizi_kwa_mwezi = []

    for i in range(5, -1, -1):
        mwezi = leo.month - i
        mwaka = leo.year
        while mwezi <= 0:
            mwezi += 12
            mwaka -= 1

        mauzo_mwezi = Mauzo.query.filter(
            db.extract('month', Mauzo.tarehe) == mwezi,
            db.extract('year', Mauzo.tarehe) == mwaka
        ).all()
        matumizi_mwezi = Matumizi.query.filter(
            db.extract('month', Matumizi.tarehe) == mwezi,
            db.extract('year', Matumizi.tarehe) == mwaka
        ).all()

        jina_mwezi = ['Jan', 'Feb', 'Mac', 'Apr', 'Mei', 'Jun',
                      'Jul', 'Ago', 'Sep', 'Okt', 'Nov', 'Des'][mwezi - 1]

        miezi_6.append(f'{jina_mwezi} {mwaka}')
        mapato_kwa_mwezi.append(sum(m.jumla for m in mauzo_mwezi))
        matumizi_kwa_mwezi.append(sum(m.kiasi for m in matumizi_mwezi))

    return render_template('chati.html',
                           siku_7=siku_7,
                           mapato_kwa_siku=mapato_kwa_siku,
                           samaki_labels=samaki_labels,
                           samaki_data=samaki_data,
                           miezi_6=miezi_6,
                           mapato_kwa_mwezi=mapato_kwa_mwezi,
                           matumizi_kwa_mwezi=matumizi_kwa_mwezi)

# ==================== BADILISHA PASSWORD ====================
@app.route('/badilisha_password', methods=['GET', 'POST'])
@login_required
def badilisha_password():
    if request.method == 'POST':
        password_ya_sasa = request.form['password_ya_sasa']
        password_mpya = request.form['password_mpya']
        password_thibitisha = request.form['password_thibitisha']

        # Angalia password ya sasa
        user = User.query.filter_by(username=current_user.username).first()

        if user.password != password_ya_sasa:
            flash('Password ya sasa si sahihi!', 'danger')
            return redirect(url_for('badilisha_password'))

        # Angalia password mpya inalingana
        if password_mpya != password_thibitisha:
            flash('Password mpya na uthibitisho hazilingani!', 'danger')
            return redirect(url_for('badilisha_password'))

        # Angalia urefu wa password
        if len(password_mpya) < 6:
            flash('Password mpya iwe na herufi 6 au zaidi!', 'danger')
            return redirect(url_for('badilisha_password'))

        # Badilisha password
        user.password = password_mpya
        db.session.commit()

        flash('Password imebadilishwa! Tafadhali ingia tena.', 'success')
        logout_user()
        return redirect(url_for('login'))

    return render_template('badilisha_password.html')
# ==================== PWA ====================
from flask import send_from_directory

@app.route('/service-worker.js')
def service_worker():
    return send_from_directory('static', 'service-worker.js', mimetype='application/javascript')

# ==================== BACKUP ====================
@app.route('/backup')
@login_required
def backup_ukurasa():
    import os
    from datetime import datetime as dt

    # Orodha ya backups zilizopo
    backup_dir = 'backup'
    backups = []
    if os.path.exists(backup_dir):
        for f in os.listdir(backup_dir):
            if f.endswith('.db'):
                path = os.path.join(backup_dir, f)
                backups.append({
                    'jina': f,
                    'ukubwa': os.path.getsize(path),
                    'tarehe': dt.fromtimestamp(os.path.getmtime(path))
                })
    backups.sort(key=lambda x: x['tarehe'], reverse=True)

    return render_template('backup.html', backups=backups)


@app.route('/backup/fanya', methods=['POST'])
@login_required
def fanya_backup():
    import shutil
    import os
    from datetime import datetime as dt

    # Tengeneza folder ya backup kama haipo
    if not os.path.exists('backup'):
        os.makedirs('backup')

    # Jina la file lenye tarehe na saa
    jina = f'samaki_{dt.now().strftime("%Y-%m-%d_%H-%M-%S")}.db'
    path = os.path.join('backup', jina)

    # Copy database
    shutil.copy('instance/samaki.db', path)

    flash(f'Backup imefanywa: {jina}', 'success')
    return redirect(url_for('backup_ukurasa'))


@app.route('/backup/pakua/<jina>')
@login_required
def pakua_backup(jina):
    from flask import send_file
    import os

    path = os.path.join('backup', jina)
    if os.path.exists(path):
        return send_file(path, as_attachment=True)
    flash('Backup haipo!', 'danger')
    return redirect(url_for('backup_ukurasa'))


# ==================== STOCK ====================
@app.route('/stock')
@login_required
def stock_ukurasa():
    samaki_wote = Samaki.query.all()
    leo = datetime.utcnow().date()

    # Chuja kwa tarehe (kama imetolewa)
    tarehe_kutoka = request.args.get('kutoka', '')
    tarehe_hadi = request.args.get('hadi', '')

    samaki_habari = []
    jumla_in = 0
    jumla_out = 0
    jumla_balance = 0
    jumla_thamani = 0

    for s in samaki_wote:
        # Manunuzi (IN)
        query_in = Manunuzi.query.filter(Manunuzi.samaki_id == s.id)
        if tarehe_kutoka:
            query_in = query_in.filter(db.func.date(Manunuzi.tarehe) >= tarehe_kutoka)
        if tarehe_hadi:
            query_in = query_in.filter(db.func.date(Manunuzi.tarehe) <= tarehe_hadi)
        manunuzi_list = query_in.all()
        in_jumla = sum(m.kiasi_kg for m in manunuzi_list)

        # Mauzo (OUT)
        query_out = Mauzo.query.filter(Mauzo.samaki_id == s.id)
        if tarehe_kutoka:
            query_out = query_out.filter(db.func.date(Mauzo.tarehe) >= tarehe_kutoka)
        if tarehe_hadi:
            query_out = query_out.filter(db.func.date(Mauzo.tarehe) <= tarehe_hadi)
        mauzo_list = query_out.all()
        out_jumla = sum(m.kiasi_kg for m in mauzo_list)

        balance = in_jumla - out_jumla
        thamani = balance * s.bei_kununua

        jumla_in += in_jumla
        jumla_out += out_jumla
        jumla_balance += balance
        jumla_thamani += thamani

        samaki_habari.append({
            'id': s.id,
            'jina': s.jina,
            'aina': s.aina,
            'in': in_jumla,
            'out': out_jumla,
            'balance': balance,
            'bei_kununua': s.bei_kununua,
            'bei_kuuza': s.bei_kuuza,
            'thamani': thamani
        })

    return render_template('stock.html',
                           samaki_habari=samaki_habari,
                           jumla_in=jumla_in,
                           jumla_out=jumla_out,
                           jumla_balance=jumla_balance,
                           jumla_thamani=jumla_thamani,
                           tarehe_kutoka=tarehe_kutoka,
                           tarehe_hadi=tarehe_hadi,
                           leo=leo)


@app.route('/stock/undani/<int:id>')
@login_required
def stock_undani(id):
    s = Samaki.query.get_or_404(id)
    manunuzi = Manunuzi.query.filter_by(samaki_id=id).order_by(Manunuzi.tarehe.desc()).all()
    mauzo = Mauzo.query.filter_by(samaki_id=id).order_by(Mauzo.tarehe.desc()).all()

    in_jumla = sum(m.kiasi_kg for m in manunuzi)
    out_jumla = sum(m.kiasi_kg for m in mauzo)
    balance = in_jumla - out_jumla

    return render_template('stock_undani.html',
                           samaki=s,
                           manunuzi=manunuzi,
                           mauzo=mauzo,
                           in_jumla=in_jumla,
                           out_jumla=out_jumla,
                           balance=balance)

# ==================== RIPOTI ====================
@app.route('/ripoti')
@login_required
def ripoti_ukurasa():
    mauzo_yote = Mauzo.query.all()
    matumizi_yote = Matumizi.query.all()

    mapato = sum(m.jumla for m in mauzo_yote)
    gharama = sum(m.kiasi for m in matumizi_yote)

    gharama_samaki = 0
    for m in mauzo_yote:
        if m.samaki:
            gharama_samaki += m.kiasi_kg * m.samaki.bei_kununua

    faida = mapato - gharama - gharama_samaki

    madeni = db.session.query(db.func.sum(Mteja.deni)).scalar() or 0

    return render_template('ripoti.html',
                           mapato=mapato,
                           gharama=gharama,
                           gharama_samaki=gharama_samaki,
                           faida=faida,
                           madeni=madeni)


# ==================== KUANZISHA DATABASE + USER ====================
with app.app_context():
    db.create_all()

    if not User.query.filter_by(username='DIULE').first():
        user_mpya = User(username='DIULE', password='SAMAKI2026')
        db.session.add(user_mpya)
        db.session.commit()
        print("User DIULE ameundwa!")


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)