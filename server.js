const express = require('express');
const sqlite3 = require('sqlite3').verbose();
const app = express();
const PORT = process.env.PORT || 5000;
const DB_FILE = 'kuafor_platformu.db';

app.use(express.json());
app.use(express.urlencoded({ extended: true }));

const db = new sqlite3.Database(DB_FILE, (err) => {
    if (!err) {
        db.run(`CREATE TABLE IF NOT EXISTS dukkanlar (
            username TEXT PRIMARY KEY, sifre TEXT, dukkan_adi TEXT, ustalar TEXT,
            f_sac INTEGER, f_sakal INTEGER, f_kombin INTEGER, f_yikama INTEGER, f_fon INTEGER, f_maske INTEGER, f_agda INTEGER
        )`);
        db.run(`CREATE TABLE IF NOT EXISTS randevular (
            id TEXT PRIMARY KEY, dukkan_user TEXT, isim TEXT, tel TEXT, hizmet TEXT, usta TEXT, saat TEXT
        )`);
    }
});

const KAYIT_GIRIS_SAYFASI = `<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Kuaför Randevu Paneli</title>
    <style>
        body { font-family: sans-serif; background: #2c3e50; margin: 0; padding: 20px; display: flex; justify-content: center; align-items: center; min-height: 100vh; color: white; }
        .box { width: 100%; max-width: 400px; background: #34495e; padding: 25px; border-radius: 12px; box-shadow: 0 5px 15px rgba(0,0,0,0.3); text-align: center; }
        input, button { width: 100%; padding: 12px; margin-bottom: 12px; border-radius: 6px; border: 1px solid #ddd; box-sizing: border-box; font-size: 14px; }
        button { background: #2ecc71; color: white; font-weight: bold; border: none; cursor: pointer; }
        .tab-btn { background: #7f8c8d; width: 48%; display: inline-block; padding: 8px; margin-bottom: 20px; font-size: 13px; color:white; border:none; border-radius:4px; cursor:pointer;}
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
            <input type="text" name="username" placeholder="Kullanıcı Adı (İngilizce Harfler)" required autocomplete="off">
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
</html>`;

app.get('/', (req, res) => { res.send(KAYIT_GIRIS_SAYFASI); });

app.post('/auth', (req, res) => {
    const { is_login, username, sifre, dukkan_adi, ustalar } = req.body;
    const user = username.trim().lower();
    if (is_login === "0") {
        db.run(`INSERT INTO dukkanlar VALUES (?, ?, ?, ?, 300, 150, 400, 450, 500, 100, 80)`, [user, sifre, dukkan_adi, ustalar], (err) => {
            if (err) return res.send("<h1>❌ Bu kullanıcı adı zaten alınmış!</h1>");
            girişKontrol(user, sifre, res);
        });
    } else {
        girişKontrol(user, sifre, res);
    }
});

function girişKontrol(user, sifre, res) {
    db.get(`SELECT * FROM dukkanlar WHERE username=? AND sifre=?`, [user, sifre], (err, row) => {
        if (row) {
            res.send(`<!DOCTYPE html>
            <html>
            <head><meta charset="UTF-8"><title>Yönetim Paneli</title>
            <style>
                body { font-family: sans-serif; background: #2c3e50; padding: 20px; color: white; display: flex; justify-content: center; gap: 20px; flex-wrap:wrap; }
                .panel { width: 450px; background: #34495e; padding: 20px; border-radius: 12px; }
                .r-kart { background: #fff; color: #333; padding: 12px; margin-bottom: 8px; border-left: 5px solid #2ecc71; border-radius: 4px; display: flex; justify-content: space-between; align-items: center; }
                .sil-btn { background: #e74c3c; color: white; border: none; padding: 6px 12px; border-radius: 4px; cursor: pointer; }
                .form-input { width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 6px; box-sizing: border-box; margin-bottom: 8px; }
            </style>
            </head>
            <body>
                <div class="panel">
                    <div style="background:#16a085; padding:10px; text-align:center; margin-bottom:15px; border-radius:6px; font-weight:bold;">
                        🔗 Müşteri Randevu Linkiniz:<br>
                        <a href="/salons/\${row.username}" target="_blank" style="color:white; word-break:break-all;">Müşteri Sayfasını Açmak İçin Tıklayın</a>
                    </div>
                    <h2>⚙️ Gelen Randevular (\${row.dukkan_adi})</h2>
                    <div id="liste">Yükleniyor...</div>
                </div>
                <div class="panel">
                    <h2>🛠️ Dükkan ve Fiyat Ayarları</h2>
                    <form method="POST" action="/save-settings">
                        <input type="hidden" name="username" value="\${row.username}">
                        <label>Salon İsmi:</label><input type="text" name="dukkan_adi" class="form-input" value="\${row.dukkan_adi}">
                        <label>Ustalar (Virgülle Ayırın):</label><input type="text" name="ustalar" class="form-input" value="\${row.ustalar}">
                        <h3 style="margin-top:15px; border-bottom:1px solid #555; padding-bottom:5px;">Fiyat Listesi Güncelle</h3>
                        <table style="width:100%; font-size:12px;">
                            <tr><td>Saç Tıraşı:</td><td><input type="number" name="f_sac" class="form-input" value="\${row.f_sac}"></td></tr>
                            <tr><td>Sakal Tıraşı:</td><td><input type="number" name="f_sakal" class="form-input" value="\${row.f_sakal}"></td></tr>
                            <tr><td>Saç & Sakal Tıraşı:</td><td><input type="number" name="f_kombin" class="form-input" value="\${row.f_kombin}"></td></tr>
                            <tr><td>Saç & Sakal Tıraşı Yıkama:</td><td><input type="number" name="f_yikama" class="form-input" value="\${row.f_yikama}"></td></tr>
                            <tr><td>Saç & Sakal Tıraşı Yıkama Fön:</td><td><input type="number" name="f_fon" class="form-input" value="\${row.f_fon}"></td></tr>
                        </table>
                        <button type="submit" style="background:#e67e22; width:100%; padding:10px; border:none; color:white; font-weight:bold; border-radius:6px; cursor:pointer;">Ayarları Kaydet</button>
                    </form>
                </div>
                <script>
                    let sonSayi = 0;
                    function sesCal() {
                        let audioCtx = new (window.AudioContext || window.webkitAudioContext)();
                        let oscillator = audioCtx.createOscillator();
                        oscillator.connect(audioCtx.destination);
                        oscillator.type = 'sine'; oscillator.frequency.setValueAtTime(587.33, audioCtx.currentTime);
                        oscillator.start(); oscillator.stop(audioCtx.currentTime + 0.3);
                    }
                    async function kontrol() {
                        let res = await fetch('/api/randevular/\${row.username}');
                        let data = await res.json();
                        if (data.length > sonSayi && sonSayi !== 0) sesCal();
                        sonSayi = data.length;
                        let alan = document.getElementById('liste');
                        if(data.length === 0) { alan.innerHTML = "<p>Henüz randevu yok...</p>"; return; }
                        alan.innerHTML = "";
                        data.forEach(r => {
                            alan.innerHTML += "<div class='r-kart'><div><b>👤 "+r.isim+"</b> ("+r.tel+")<br>✂️ "+r.hizmet+"<br>⏰ Saat: "+r.saat+" | Usta: "+r.usta+"</div><button class='sil-btn' onclick='sil(\""+r.id+"\")'>Tamamlandı</button></div>";
                        });
                    }
                    async function sil(id) {
                        if(confirm("Silmek istediğinize emin misiniz?")) {
                            await fetch('/api/randevu-sil/' + id, { method: 'DELETE' });
                            kontrol();
                        }
                    }
                    setInterval(kontrol, 2000); kontrol();
                </script>
            </body>
            </html>`);
        } else {
            res.send("<h1>❌ Hatalı kullanıcı adı veya şifre!</h1>");
        }
    });
}

app.get('/salons/:username', (req, res) => {
db.get(SELECT * FROM dukkanlar WHERE username=?, [req.params.username.toLowerCase()], (err, row) => {
if (!row) return res.send("❌ Salon Bulunamadı!");
const ustalarArr = row.ustalar.split(',');
let ustaOptions = '';
ustalarArr.forEach(u => { ustaOptions += <option value="\${u}">\${u}</option>; });
res.send(`

${row.dukkan_adi}

body { font-family: sans-serif; background: #f0f2f5; margin: 0; padding: 20px; display: flex; justify-content: center; }
.phone { width: 100%; max-width: 360px; background: white; border-radius: 20px; box-shadow: 0 5px 15px rgba(0,0,0,0.1); padding: 15px; border: 4px solid #111; }
select, input, button { width: 100%; padding: 10px; margin-bottom: 12px; border-radius: 6px; border: 1px solid #ddd; box-sizing: border-box; }
button { background: #e67e22; color: white; font-weight: bold; border: none; cursor: pointer; }




💈 ${row.dukkan_adi}
1. Hizmet Seçin
Saç Tıraşı (${row.f_sac} TL)
Sakal Tıraşı (${row.f_sakal} TL)
Saç & Sakal Tıraşı (${row.f_kombin} TL)
Saç & Sakal Tıraşı Yıkama (${row.f_yikama} TL)
Saç & Sakal Tıraşı Yıkama Fön (${row.f_fon} TL)
1. Usta Seçin
${ustaOptions}
1. Saat Seçin
09:0010:0011:00
12:0013:0014:00
15:0016:0017:00



Randevuyu Onayla


async function gonder() {
let veri = { id: Date.now().toString(), dukkan_user: "${row.username}", isim: document.getElementById('isim').value, tel: document.getElementById('tel').value, hizmet: document.getElementById('hizmet').value, usta: document.getElementById('usta').value, saat: document.getElementById('saat').value };
if(!veri.isim || !veri.tel) { alert("Boş alan bırakmayın."); return; }
await fetch('/api/randevu-ekle', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(veri) });
alert("Randevunuz başarıyla iletildi!");
document.getElementById('isim').value = ""; document.getElementById('tel').value = "";
}


`);
});
});
app.post('/save-settings', (req, res) => {
const { username, dukkan_adi, ustalar, f_sac, f_sakal, f_kombin, f_yikama, f_fon } = req.body;
db.run(UPDATE dukkanlar SET dukkan_adi=?, ustalar=?, f_sac=?, f_sakal=?, f_kombin=?, f_yikama=?, f_fon=? WHERE username=?,
[dukkan_adi, ustalar, f_sac, f_sakal, f_kombin, f_yikama, f_fon, username], () => {
girişKontrol(username, "", res); // Şifre boş geçilirse direkt yönlendirmek için logic esnetildi
});
});
app.get('/api/randevular/:username', (req, res) => {
db.all(SELECT * FROM randevular WHERE dukkan_user=?, [req.params.username.toLowerCase()], (err, rows) => { res.json(rows || []); });
});
app.post('/api/randevu-ekle', (req, res) => {
const { id, dukkan_user, isim, tel, hizmet, usta, saat } = req.body;
db.run(INSERT INTO randevular VALUES (?, ?, ?, ?, ?, ?, ?), [id, dukkan_user, isim, tel, hizmet, usta, saat], () => { res.json({ m: "1" }); });
});
app.delete('/api/randevu-sil/:id', (req, res) => {
db.run(DELETE FROM randevular WHERE id=?, [req.params.id], () => { res.json({ m: "1" }); });
});
app.listen(PORT, () => { console.log(Server active on ${PORT}); });
