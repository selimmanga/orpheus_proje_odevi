from flask import *
from mysql_fonksiyonlar import select, insert
from datetime import *

import numpy as np
import librosa
import librosa.display
import matplotlib.pyplot as plt
import os
import tempfile
import soundfile as sf
from spotipy.oauth2 import SpotifyOAuth
from authlib.integrations.flask_client import OAuth


app = Flask(__name__)
app.secret_key = "orpheus"

appConf = {
    "OAUTH2_CLIENT_ID": "669185230482-f7q8j62ffbslol5dd54809m4f6atce25.apps.googleusercontent.com",
    "OAUTH2_CLIENT_SECRET": "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",
    "OAUTH2_META_URL": "https://accounts.google.com/.well-known/openid-configuration",
    "FLASK_SECRET": "91a6cd34-93cf-4c5b-8983-d5e5dd2daad4",
    "FLASK_PORT": 5000
}

oauth = OAuth(app)
oauth.register("myApp",
               client_id = appConf.get("OAUTH2_CLIENT_ID"),
               client_secret = appConf.get("OAUTH2_CLIENT_SECRET"),
               authorize_url = "https://accounts.google.com/o/oauth2/auth",
               server_metadata_url = appConf.get("OAUTH2_META_URL"),
               client_kwargs={
                   "scope": "openid profile email https://www.googleapis.com/auth/user.birthday.read https://www.googleapis.com/auth/user.gender.read",
               }
               )

TOKEN_INFO = "token_info"

def create_spotify_oauth():
    return SpotifyOAuth(
        client_id="a564a5f3fa2e4bfd94014f8eafe2cafe",
        client_secret="2de4b15484434849a7c0568b52276675",
        redirect_uri=url_for('redirectPage', _external=True),
        scope="user-library-read",
        cache_path=None,  # Token bilgisini dosyada saklamayı durdurur
        show_dialog=True  # Her seferinde yetkilendirme istemek için
    )

def get_token():
    token_info = session.get(TOKEN_INFO, None)
    if not token_info:
        return None
    sp_oauth = create_spotify_oauth()
    if sp_oauth.is_token_expired(token_info):
        token_info = sp_oauth.refresh_access_token(token_info['refresh_token'])
        session[TOKEN_INFO] = token_info
    return token_info

@app.route('/')
def index():
    token_info = get_token()
    if not token_info:
        return render_template("index.html")
    return render_template('index.html')


@app.route("/google-login")
def googleLogin():
    if "user" not in session:
        return oauth.myApp.authorize_redirect(redirect_uri=url_for("googleCallback", _external=True))
    else:
        return redirect(url_for("ana_sayfa"))

@app.route("/signing-google")
def googleCallback():
    token = oauth.myApp.authorize_access_token()
    session["user"] = token
    return redirect(url_for("ana_sayfa"))

@app.route("/spotify_giris")
def spotify_login():
    sp_oauth = create_spotify_oauth()
    auth_url = sp_oauth.get_authorize_url()
    return redirect(auth_url)

@app.route('/redirect')
def redirectPage():
    sp_oauth = create_spotify_oauth()
    session.clear()
    code = request.args.get('code')
    token_info = sp_oauth.get_access_token(code)
    session[TOKEN_INFO] = token_info
    return redirect(url_for("ana_sayfa"))

@app.route("/anasayfa")
def ana_sayfa():
    #if "ad" in session and session["ad"] != None: 
    token_info = get_token()
    if not token_info:
        return redirect("/")
    return render_template("anasayfa.html")
    #else:
        #return redirect("/giris")

@app.route("/kayit") 
def kayit():
    return render_template("kayit.html")    

@app.route("/giris")
def giris():
    return render_template("giris.html")

@app.route("/cikis") 
def cikis():
    session.clear()
    return redirect("/giris")

@app.route("/hesap-olustur", methods=["POST"])
def kullanici_kayit():
    ad = request.form["ad"]
    soyad = request.form["soyad"]
    sifre = request.form["sifre"]  
    email = request.form["email"]
    dogum = request.form["dogum"]

    sorgu = f"SELECT * FROM kullanicilar WHERE ad = '{ad}'"
    kayitlar = select(sorgu)

    if len(sifre) < 6:
        return render_template('kayit.html', hata="Şifreniz 6 karakterden kısa olamaz!")
    
    if len(kayitlar) == 0:
        sorgu = f"INSERT INTO kullanicilar (ad, soyad, sifre, email, dogum_tarihi) VALUES ('{ad}', '{soyad}', '{sifre}', '{email}', '{dogum}')"
        insert(sorgu)
        return render_template('anasayfa.html')
    else:
        return render_template('kayit.html', hata = "Bu kullanıcı zaten kayıtlı.")

@app.route("/hesap-kontrol", methods=["POST"])
def hesap_kontrol():
    isim = request.form["ad"]
    sifre = request.form["sifre"]

    sorgu = f"SELECT * FROM kullanicilar WHERE ad = '{isim}' AND sifre = '{sifre}'"
    kayitlar = select(sorgu)

    if len(kayitlar) == 0:
        return render_template("giris.html", hata = "Kullanıcı bilgileri hatalı!")
    else:
        session["ad"] = isim
        session["sifre"] = sifre
        return redirect("/anasayfa")
    
@app.route('/muzik_analizi', methods=['GET', 'POST'])
def analiz_sayfasi():
        return render_template("muzik_analizi.html")

@app.route('/analiz-gonder', methods=['GET', 'POST'])
def analiz_et():
    if request.method == 'POST':
        # Ses dosyasını al
        audio_file = request.files['file']
        temp_file_path = "temp_audio.wav"
        audio_file.save(temp_file_path)

        # Mel spektrogramını oluştur
        y, sr = librosa.load(temp_file_path)
        mel_spec = librosa.feature.melspectrogram(y=y, sr=sr)

        # Mel spektrogramını görselleştir ve kaydet
        plt.figure(figsize=(10, 4))
        librosa.display.specshow(librosa.power_to_db(mel_spec, ref=np.max(y)), y_axis='mel', x_axis='time')
        plt.colorbar(format='%+2.0f dB')
        plt.title('Mel Spectrogram')
        plt.tight_layout()
        mel_spec_path = 'static/mel_spec.png'
        plt.savefig(mel_spec_path)  
        plt.close()

        # BPM değerini hesapla
        tempo = librosa.beat.tempo(y=y, sr=sr)

        # BPM değerlerini örnekleyelim
        bpm_values = [tempo[0], tempo[0] * 1.2, tempo[0] * 0.8]  # Örneğin 1, 1.2 ve 0.8 oranlarında BPM değerleri alalım
        time_intervals = np.arange(len(bpm_values))

        # BPM grafiğini alan grafiği olarak çiz ve kaydet
        plt.figure(figsize=(6, 4))
        plt.fill_between(time_intervals, bpm_values, color='skyblue', alpha=0.4, label='BPM Değeri')
        plt.plot(time_intervals, bpm_values, color='Slateblue', alpha=0.6, linewidth=2)
        plt.xlabel('Örnek')
        plt.ylabel('BPM Değeri')
        plt.title('Müzik BPM Değeri')
        plt.legend()
        bpm_path = 'static/bpm.png'
        plt.savefig(bpm_path)  
        plt.close()

        hop_length = 512 # Liborsanın varsayılan değeri
        frequencies = librosa.fft_frequencies(sr=sr)
        times = np.arange(mel_spec.shape[1]) * (hop_length / sr)

        db_spectrogram = librosa.power_to_db(mel_spec, ref=np.max)

        return render_template('analiz_sonuc.html', 
                               mel_spec_image=mel_spec_path, 
                               bpm_image=bpm_path, 
                               bpm=tempo, 
                               frequencies=frequencies, 
                               times=times, 
                               db_spectrogram=db_spectrogram)
    else:
        return render_template('anasayfa.html')
    
   
@app.route('/soundbooster', methods=['GET','POST'])
def soundbooster():
    if 'file' not in request.files:
        return render_template('soundbooster.html', message='Lütfen bir dosya seçin')
    
    audio_file = request.files['file']
    if audio_file.filename == '':
        return render_template('soundbooster.html', message='Dosya seçilmedi')

    if audio_file:
        # Dosyayı geçici bir yere kaydet
        temp_path = os.path.join(tempfile.gettempdir(), audio_file.filename)
        audio_file.save(temp_path)

        # Kullanıcının belirlediği ekolayzer seviyesini ve frekans aralığını al
        eq_level = float(request.form['eq_level'])
        freq_range = request.form['freq_range']

        # Ses dosyasını yükle ve işle
        y, sr = librosa.load(temp_path)

        # Ekolayzer işlemi
        if freq_range == 'low':
            y_eq = np.copy(y)
            low_freq_cutoff = 100  # Örnek bir düşük frekans kesme frekansı
            y_eq[:int(low_freq_cutoff * len(y_eq) / sr)] *= eq_level
        elif freq_range == 'mid':
            y_eq = np.copy(y) * eq_level
        elif freq_range == 'high':
            y_eq = np.copy(y)
            high_freq_cutoff = 4000  # Örnek bir yüksek frekans kesme frekansı
            y_eq[int(high_freq_cutoff * len(y_eq) / sr):] *= eq_level
        else:  # Tüm ses kaydına uygulanacak
            y_eq = np.copy(y) * eq_level

        # İşlenmiş sesi kaydet
        eq_temp_path = os.path.join(tempfile.gettempdir(), 'eq_' + audio_file.filename)
        sf.write(eq_temp_path, y_eq, sr)

        return render_template('booster_sonuc.html', original_file=audio_file.filename, eq_file='eq_' + audio_file.filename)

@app.route('/download/<filename>')
def download(filename):
    return send_file(os.path.join(tempfile.gettempdir(), filename), as_attachment=True)

@app.route("/slowed-down", methods=["GET", "POST"])
def yavaslatma():
    if request.method == "POST":
        # Formdan gelen dosyayı kontrol et
        if "audio_file" not in request.files:
            return redirect(request.url)

        audio_file = request.files["audio_file"]

        # Dosya yüklenmemişse veya dosya adı boşsa tekrar formu göster
        if audio_file.filename == "":
            return redirect(request.url)

        # Yüklenen dosyayı geçici bir dosyaya kaydet
        temp_path = "temp_audio.wav"
        audio_file.save(temp_path)

        # Ses dosyasını yavaşlat
        y, sr = librosa.load(temp_path, sr=None)
        y_slow = librosa.effects.time_stretch(y, rate=0.5)  # Örnek olarak yarısına yavaşlat

        # Yavaşlatılmış sesi geçici bir dosyaya kaydet
        slow_temp_path = "slow_temp_audio.wav"
        sf.write(slow_temp_path, y_slow, sr)

        # Kullanıcıya yavaşlatılmış ses dosyasını indirme bağlantısı olarak sun
        return send_file(slow_temp_path, as_attachment=True)

    # GET isteği ise, formu göster
    return render_template("slowed-down.html")

if __name__ == "__main__":
    app.run(debug=True)