import os
import sqlite3
from flask import Flask, request, jsonify, render_template_string, redirect

app = Flask(__name__)
DB_FILE = "kuafor_platformu.db"

# 🗄️ VERİTABANI BAĞLANTI VE TABLO KURULUMLARI
def veritabani_kur():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    # 1. Dükkanlar Tablosu
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS dukkanlar (
            username TEXT PRIMARY KEY,
            sifre TEXT,
            dukkan_adi TEXT,
            ustalar TEXT,
            acilis INTEGER,
            kapanis INTEGER,
            fiyat_sac INTEGER,
            fiyat_sakal INTEGER,
            fiyat_kombin INTEGER,
            fiyat_yikama INTEGER,
            fiyat_fon INTEGER,
            fiyat_maske INTEGER,
            fiyat_agda INTEGER
        )
    """)
    # 2. Randevular Tablosu
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS randevular (
            id TEXT PRIMARY KEY,
            dukkan_user TEXT,
            isim TEXT,
            tel TEXT,
            hizmet TEXT,
            usta TEXT,
            saat TEXT
        )
    """)
    conn.commit()
    conn.close()

veritabani_kur()

# 🎨 1. BÖLÜM: PLATFORM ANA GİRİŞ VE KAYIT SAYFASI (ESNAF İÇİN)
KAYIT_GIRIS_SAYFASI = """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Kuaför Randevu Paneli - Giriş Yap / Kayıt Ol</title>
    <style>
        body { font-family: sans-serif; background: #2c3e50; margin: 0; padding: 20px; display: flex; justify-content: center; align-items: center; min-height: 100vh; color: white; }
        .box { width: 100%; max-width: 400px; background: #34495e; padding: 25px; border-radius: 12px; box-shadow: 0 5px 15px rgba(0,0,0,0.3); text-align: center; }
        input, button { width: 100%; padding: 12px; margin-bottom: 12px; border-radius: 6px; border: 1px solid #ddd; box-sizing: border-box; font-size: 14px; }
        button { background: #2ecc71; color: white; font-weight: bold; border: none; cursor: pointer; }
        .tab-btn { background: #7f8c8d; width: 48%; display: inline-block; padding: 8px; margin-bottom: 20px; font-size: 13px; }
        .active-tab { background: #e67e22; }
    </style>
</head>
<body>
    <div class="box">
        <h2>💈 Kuaför Randevu Platformu</h2>
        <p style="font-size:12px; color:#bdc3c7; margin-bottom:20px;">Dükkanınızı kaydedin ve canlı panelinizi oluşturun.</p>
        
        <div>
            <button class="tab-btn active-tab" id="btnGiris" onclick="sec(true)">Giriş Yap</button>
            <button class="tab-btn" id="btnKayit" onclick="sec(false)">Kayıt Ol</button>
        </div>

        <form id="anaForm" method="POST" action="/auth">
            <input type="hidden" name="is_login" id="is_login" value="1">
            <input type="text" name="username" placeholder="Kullanıcı Adı (Sadece İngilizce Harfler)" required autocomplete="off">
            <input type="password" name="sifre" placeholder="Şifreniz" required>
            
            <div id="kayitAlanlari" style="display:none;">
                <input type="text" name="dukkan_adi" id="i_dukkan" placeholder="Dükkan / Salon Adı">
                <input type="text" name="ustalar" id="i_usta" placeholder="Ustalar (Virgülle Ayırın: Ahmet,Mehmet)">
            </div>
            
            <button type="submit" id="formButon">Hesabıma Giriş Yap</button>
        </form>
    </div>

    <script>
        function sec(login) {
            document.getElementById('is_login').value = login ? "1" : "0";
            document.getElementById('btnGiris').className = "tab-btn " + (login ? "active-tab" : "");
            document.getElementById('btnKayit').className = "tab-btn " + (!login ? "active-tab" : "");
            document.getElementById('kayitAlanlari').style.display = login ? "none" : "block";
            document.getElementById('formButon').innerText = login ? "Hesabıma Giriş Yap" : "Yeni Dükkan Kayıt Oluştur";
            document.getElementById('formButon').style.background = login ? "#2ecc71" : "#e67e22";
            document.getElementById('i_dukkan').required = !login;
            document.getElementById('i_usta').required = !login;
        }
    </script>
</body>
</html>
"""

# 📱 2. BÖLÜM: MÜŞTERİNİN GÖRECEĞİ REZERVASYON WEB SİTESİ (DÜKKANA ÖZEL DİNAMİK)
MUSTERI_WEB_SITESI = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ dukkan_adi }} - Randevu</title>
    <style>
        body { font-family: sans-serif; background: #f0f2f5; margin: 0; padding: 20px; display: flex; justify-content: center; }
        .phone { width: 100%; max-width: 360px; background: white; border-radius: 20px; box-shadow: 0 5px 15px rgba(0,0,0,0.1); padding: 15px; border: 4px solid #111; }
        h2 { text-align: center; margin-top: 0; color: #111; }
        select, input, button { width: 100%; padding: 10px; margin-bottom: 12px; border-radius: 6px; border: 1px solid #ddd; box-sizing: border-box; }
        button { background: #e67e22; color: white; font-weight: bold; border: none; cursor: pointer; }
    </style>
</head>
<body>
    <div class="phone">
        <h2>💈 {{ dukkan_adi }}</h2>
        <p style="text-align:center; font-size:12px; color:#666;">Hızlıca randevunuzu oluşturun</p>
        
        <label>1. Hizmet Seçin</label>
        <select id="hizmet">
            <option value="Saç Tıraşı">Saç Tıraşı ({{ fiyatlar[0] }} TL)</option>
            <option value="Sakal Tıraşı">Sakal Tıraşı ({{ fiyatlar[1] }} TL)</option>
            <option value="Saç & Sakal Tıraşı">Saç & Sakal Tıraşı ({{ fiyatlar[2] }} TL)</option>
            <option value="Saç & Sakal Tıraşı Yıkama">Saç & Sakal Tıraşı Yıkama ({{ fiyatlar[3] }} TL)</option>
            <option value="Saç & Sakal Tıraşı Yıkama Fön">Saç & Sakal Tıraşı Yıkama Fön ({{ fiyatlar[4] }} TL)</option>
            <option value="Maske">Maske ({{ fiyatlar[5] }} TL)</option>
            <option value="Ağda">Ağda ({{ fiyatlar[6] }} TL)</option>
        </select>

        <label>2. Usta Seçin</label>
        <select id="usta">
            {% for u in ustalar %}<option value="{{ u }}">{{ u }}</option>{% endfor %}
        </select>

        <label>3. Saat Seçin ({{ calisma[0] }}:00 - {{ calisma[1] }}:00)</label>
        <select id="saat">
            {% for s in saatler %}<option value="{{ s }}">{{ s }}</option>{% endfor %}
        </select>

        <label>4. Bilgileriniz</label>
        <input type="text" id="isim" placeholder="Adınız Soyadınız">
        <input type="tel" id="tel" placeholder="Telefon Numaranız">

        <button onclick="randevuGonder()">Randevuyu Onayla</button>
    </div>

    <script>
        async function randevuGonder() {
            let veri = {
                id: Date.now().toString(),
                dukkan_user: "{{ username }}",
                isim: document.getElementById('isim').value,
                tel: document.getElementById('tel').value,
                hizmet: document.getElementById('hizmet').value,
                usta: document.getElementById('usta').value,
                saat: document.getElementById('saat').value
            };
            if(!veri.isim || !veri.tel) { alert("Lütfen bilgilerinizi doldurun."); return; }
            let response = await fetch('/api/randevu-ekle', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(veri)
            });
            let sonuc = await response.json();
            alert(sonuc.mesaj);
            document.getElementById('isim').value = "";
            document.getElementById('tel').value = "";
        }
    </script>
</body>
</html>
"""

# 🛠️ 3. BÖLÜM: BAZI ESNAFLARIN KENDİ DÜKKANINI YÖNETECEĞİ CANLI PANEL (ŞİFRELİ GİRİŞLİ)
BERBER_PANELI = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{{ dukkan_adi }} - Yönetim Paneli</title>
    <style>
        body { font-family: sans-serif; background: #2c3e50; padding: 20px; color: white; display: flex; justify-content: center; gap: 20px; flex-wrap: wrap; }
        .panel { width: 450px; background: #34495e; padding: 20px; border-radius: 12px; box-shadow: 0 5px 15px rgba(0,0,0,0.3); }
        .r-kart { background: #fff; color: #333; padding: 12px; margin-bottom: 8px; border-left: 5px solid #2ecc71; border-radius: 4px; display: flex; justify-content: space-between; align-items: center; }
        .sil-btn { background: #e74c3c; color: white; border: none; padding: 6px 12px; border-radius: 4px; cursor: pointer; font-weight: bold; }
        .form-input { width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 6px; box-sizing: border-box; margin-bottom: 8px; }
        .link-kutusu { background: #16a085; padding: 10px; border-radius: 6px; font-weight: bold; text-align: center; margin-bottom: 15px; font-size: 13px; }
    </style>
</head>
<body>
    <div class="panel">
        <div class="link-kutusu">🔗 Müşteri Randevu Linkiniz:<br> <a href="/salons/{{ username }}" target="_blank" style="color:white;">https://randevu-platformu/salons/{{ username }}</a></div>
        <h2>⚙️ Gelen Randevular ({{ dukkan_adi }})</h2>
        <p style="font-size:11px; color:#bdc3c7;">Yeni randevu geldiğinde sesli uyarı (Dın!) verilir.</p>
        <div id="liste">Yükleniyor...</div>
    </div>

    <div class="panel">
        <h2>🛠️ Dükkan ve Fiyat Ayarları</h2>
        <form method="POST" action="/save-settings">
            <input type="hidden" name="username" value="{{ username }}">
            <label>Salon İsmi:</label>
            <input type="text" name="dukkan_adi" class="form-input" value="{{ dukkan_adi }}">
            <label>Ustalar (Virgülle Ayırın):</label>
            <input type="text" name="ustalar" class="form-input" value="{{ ustalar_str }}">
            
Fiyat Listesi Güncelle
Saç Tıraşı:Sakal Tıraşı:Saç & Sakal Tıraşı:Saç & Sakal Tıraşı Yıkama:Saç & Sakal Tıraşı Yıkama Fön:Maske:Ağda:
Ayarları Kaydet

let sonRandevuSayisi = 0;
function sesCal() {
let audioCtx = new (window.AudioContext || window.webkitAudioContext)();
let oscillator = audioCtx.createOscillator();
let gainNode = audioCtx.createGain();
oscillator.connect(gainNode); gainNode.connect(audioCtx.destination);
oscillator.type = 'sine'; oscillator.frequency.setValueAtTime(587.33, audioCtx.currentTime);
gainNode.gain.setValueAtTime(0.5, audioCtx.currentTime);
oscillator.start(); oscillator.stop(audioCtx.currentTime + 0.3);
}
async function randevulariKontrolEt() {
let response = await fetch('/api/randevular/{{ username }}');
let data = await response.json();
if (data.length > sonRandevuSayisi && sonRandevuSayisi !== 0) { sesCal(); }
sonRandevuSayisi = data.length;
let listeAlan = document.getElementById('liste');
if(data.length === 0) { listeAlan.innerHTML = "Henüz gelen randevu yok..."; return; }
listeAlan.innerHTML = "";
data.forEach(r => {
listeAlan.innerHTML +=  <div class='r-kart'> <div> <b>👤 ${r.isim}</b> (${r.tel})<br> ✂️ ${r.hizmet}<br> ⏰ Saat: ${r.saat} | Usta: ${r.usta} </div> <button class="sil-btn" onclick="randevuSil('${r.id}')">Tamamlandı</button> </div>;
});
}
async function randevuSil(id) {
if(confirm("Bu randevuyu silmek istediğinize emin misiniz?")) {
await fetch('/api/randevu-sil/' + id, { method: 'DELETE' });
randevulariKontrolEt();
}
}
setInterval(randevulariKontrolEt, 2000);
randevulariKontrolEt();
# 🔌 4. BÖLÜM: TÜM İNTERNET BAĞLANTI KAPILARI VE PLATFORM LOGİC
@app.route('/')
def ana_giris():
    return render_template_string(KAYIT_GIRIS_SAYFASI)

@app.route('/auth', methods=['POST'])
def kimlik_dogrulama():
    is_login = request.form.get('is_login')
    username = request.form.get('username').strip().lower()
    sifre = request.form.get('sifre')
    
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    if is_login == "0": # KAYIT OLMA MODU
        dukkan_adi = request.form.get('dukkan_adi')
        ustalar = request.form.get('ustalar')
        try:
            cursor.execute("INSERT INTO dukkanlar VALUES (?, ?, ?, ?, 9, 21, 300, 150, 400, 450, 500, 100, 80)", 
                           (username, sifre, dukkan_adi, ustalar))
            conn.commit()
        except sqlite3.IntegrityError:
            conn.close()
            return "<h1>❌ Bu kullanıcı adı zaten alınmış! Geri dönüp başka bir isim seçin.</h1>"
    
    # GİRİŞ KONTROLÜ
    cursor.execute("SELECT * FROM dukkanlar WHERE username=? AND sifre=?", (username, sifre))
    dukkan = cursor.fetchone()
    conn.close()
    
    if dukkan:
        # Esnaf paneline yönlendir ve dükkan verilerini gönder
        ustalar_list = dukkan[3].split(',')
        fiyatlar = dukkan[6:]
        return render_template_string(BERBER_PANELI, username=dukkan[0], dukkan_adi=dukkan[2], ustalar_str=dukkan[3], fiyatlar=fiyatlar)
    else:
        return "<h1>❌ Hatalı kullanıcı adı veya şifre! Geri dönüp tekrar deneyin.</h1>"

@app.route('/salons/<username>')
def musteri_salonu_ac(username):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM dukkanlar WHERE username=?", (username.lower(),))
    dukkan = cursor.fetchone()
    conn.close()
    
    if not dukkan:
        return "<h1>❌ Böyle bir salon bulunamadı! Linki kontrol edin.</h1>"
        
    ustalar_list = dukkan[3].split(',')
    calisma = [dukkan[4], dukkan[5]]
    fiyatlar = dukkan[6:]
    
    # Dinamik saatleri dükkanın çalışma saatine göre dolduruyoruz
    saatler = [f"{k:02d}:00" for k in range(calisma[0], calisma[1])]
    
    return render_template_string(MUSTERI_WEB_SITESI, username=dukkan[0], dukkan_adi=dukkan[2], ustalar=ustalar_list, saatler=saatler, calisma=calisma, fiyatlar=fiyatlar)

@app.route('/save-settings', methods=['POST'])
def save_settings():
    username = request.form.get('username')
    dukkan_adi = request.form.get('dukkan_adi')
    ustalar = request.form.get('ustalar')
    f_sac = int(request.form.get('f_sac', 300))
    f_sakal = int(request.form.get('f_sakal', 150))
    f_kombin = int(request.form.get('f_kombin', 400))
    f_yikama = int(request.form.get('f_yikama', 450))
    f_fon = int(request.form.get('f_fon', 500))
    f_maske = int(request.form.get('f_maske', 100))
    f_agda = int(request.form.get('f_agda', 80))
    
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE dukkanlar SET dukkan_adi=?, ustalar=?, fiyat_sac=?, fiyat_sakal=?, fiyat_kombin=?, fiyat_yikama=?, fiyat_fon=?, fiyat_maske=?, fiyat_agda=?
        WHERE username=?
    """, (dukkan_adi, ustalar, f_sac, f_sakal, f_kombin, f_yikama, f_fon, f_maske, f_agda, username))
    
    cursor.execute("SELECT * FROM dukkanlar WHERE username=?", (username,))
    dukkan = cursor.fetchone()
    conn.close()
    
    fiyatlar = dukkan[6:]
    return render_template_string(BERBER_PANELI, username=dukkan[0], dukkan_adi=dukkan[2], ustalar_str=dukkan[3], fiyatlar=fiyatlar)

@app.route('/api/randevular/<username>')
def api_get_randevular(username):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT id, isim, tel, hizmet, usta, saat FROM randevular WHERE dukkan_user=?", (username.lower(),))
    rows = cursor.fetchall()
    conn.close()
    
    randevu_listesi = []
    for r in rows:
        randevu_listesi.append({"id": r[0], "isim": r[1], "tel": r[2], "hizmet": r[3], "usta": r[4], "saat": r[5]})
    return jsonify(randevu_listesi)

@app.route('/api/randevu-ekle', methods=['POST'])
def api_add_randevu():
    veri = request.json
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO randevular VALUES (?, ?, ?, ?, ?, ?, ?)", 
                   (veri['id'], veri['dukkan_user'], veri['isim'], veri['tel'], veri['hizmet'], veri['usta'], veri['saat']))
    conn.commit()
    conn.close()
    return jsonify({"mesaj": "Randevunuz kuaförün ekranına anında iletildi!"})

@app.route('/api/randevu-sil/<id>', methods=['DELETE'])
def api_delete_randevu(id):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM randevular WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return jsonify({"mesaj": "Randevu başarıyla silindi."})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
