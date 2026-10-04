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
