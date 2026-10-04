import os
from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)

DUKKAN_ADI = "DUKKAN_ADI = "Kuaför & Güzellik Sarayı"
USTALAR = ["Ahmet Usta", "Mehmet Usta", "Salih Usta"]
SAATLER = ["09:00", "10:00", "11:00", "13:00", "14:00", "15:00", "16:00", "17:00", "18:00", "19:00", "20:00"]
HIZMETLER = [
    {"ad": "Saç Tıraşı", "fiyat": 300},
    {"ad": "Sakal Tıraşı", "fiyat": 150},
    {"ad": "Saç & Sakal Tıraşı", "fiyat": 400},
    {"ad": "Saç & Sakal Tıraşı Yıkama", "fiyat": 450},
    {"ad": "Saç & Sakal Tıraşı Yıkama Fön", "fiyat": 500}
]
randevular = []

MUSTERI_WEB_SITESI = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ dukkan }} - Randevu</title>
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
        <h2>💈 {{ dukkan }}</h2>
        <p style="text-align:center; font-size:12px; color:#666;">Hızlıca randevunuzu oluşturun</p>
        <label>1. Hizmet Seçin</label>
        <select id="hizmet">
            {% for h in hizmetler %}<option value="{{ h.ad }}">{{ h.ad }} ({{ h.fiyat }} TL)</option>{% endfor %}
        </select>
        <label>2. Usta Seçin</label>
        <select id="usta">
            {% for u in ustalar %}<option value="{{ u }}">{{ u }}</option>{% endfor %}
        </select>
        <label>3. Saat Seçin</label>
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
                id: Date.now(),
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

BERBER_PANELI = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Esnaf Yönetim Paneli</title>
    <style>
        body { font-family: sans-serif; background: #2c3e50; padding: 20px; color: white; display: flex; justify-content: center; }
        .panel { width: 500px; background: #34495e; padding: 20px; border-radius: 12px; box-shadow: 0 5px 15px rgba(0,0,0,0.3); }
        .r-kart { background: #fff; color: #333; padding: 12px; margin-bottom: 8px; border-left: 5px solid #2ecc71; border-radius: 4px; display: flex; justify-content: space-between; align-items: center; }
        .sil-btn { background: #e74c3c; color: white; border: none; padding: 6px 12px; border-radius: 4px; cursor: pointer; font-weight: bold; font-size: 11px; }
    </style>
</head>
<body>
    <div class="panel">
        <h2>⚙️ Gelen Randevular (Canlı Takip)</h2>
        <p style="font-size:12px; color:#bdc3c7;">Yeni randevu geldiğinde sesli uyarı verilir.</p>
        <div id="liste">Yükleniyor...</div>
    </div>
    <script>
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
            let response = await fetch('/api/randevular');
            let data = await response.json();
            if (data.length > sonRandevuSayisi && sonRandevuSayisi !== 0) { sesCal(); }
            sonRandevuSayisi = data.length;
            let listeAlan = document.getElementById('liste');
            if(data.length === 0) { listeAlan.innerHTML = "<p style='color:#ccc;'>Henüz gelen randevu yok...</p>"; return; }
            listeAlan.innerHTML = "";
            data.forEach(r => { 
                listeAlan.innerHTML += `
                    <div class='r-kart'>
                        <div>
                            <b>👤 ${r.isim}</b> (${r.tel})<br>
                            ✂️ ${r.hizmet}<br>
                            ⏰ Saat: ${r.saat} | Usta: ${r.usta}
                        </div>
                        <button class="sil-btn" onclick="randevuSil(${r.id})">Tamamlandı / İptal</button>
                    </div>`; 
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
    </script>
</body>
</html>
"""

@app.route('/')
def ana_yonlendirme():
    return render_template_string(MUSTERI_WEB_SITESI, dukkan=DUKKAN_ADI, hizmetler=HIZMETLER, ustalar=USTALAR, saatler=SAATLER)

@app.route('/panel')
def esnaf_paneli_yeni():
    return render_template_string(BERBER_PANELI)

@app.route('/manifest.json')
def manifest():
    return jsonify({
        "name": "Berber Esnaf Paneli", "short_name": "Esnaf Paneli",
        "start_url": "/panel", "display": "standalone",
        "background_color": "#2c3e50", "theme_color": "#2c3e50", "orientation": "portrait"
    })

@app.route('/api/randevular')
def get_randevular():
    return jsonify(randevular)

@app.route('/api/randevu-ekle', methods=['POST'])
def add_randevu():
    veri = request.json
    randevular.append(veri)
    return jsonify({"mesaj": "Randevunuz başarıyla berbere iletildi!"})

@app.route('/api/randevu-sil/<int:randevu_id>', methods=['DELETE'])
def delete_randevu(randevu_id):
    global randevular
    randevular = [r for r in randevular if r['id'] != randevu_id]
    return jsonify({"mesaj": "Randevu başarıyla silindi."})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
