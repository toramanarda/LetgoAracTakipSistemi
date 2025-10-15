from flask import Flask, render_template, request, redirect, url_for
import threading 
from scraper import ilanlari_cek_letgo_final 

# --- FLASK ---
app = Flask(__name__) 

# Ana sayfa
@app.route('/')
def index():
    html_content = """
    <!DOCTYPE html>
    <html lang="tr">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Letgo Bot Kontrol Paneli</title>
        <style>
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background-color: #f4f7f6;
                color: #333;
                text-align: center;
                padding-top: 50px;
            }
            .container {
                max-width: 600px;
                margin: 0 auto;
                background-color: #ffffff;
                padding: 40px;
                border-radius: 12px;
                box-shadow: 0 6px 15px rgba(0, 0, 0, 0.1);
            }
            h1 {
                color: #007bff; /* Mavi tonu */
                margin-bottom: 30px;
                font-weight: 600;
            }
            p {
                margin-bottom: 25px;
                line-height: 1.6;
            }
            .btn-start {
                display: inline-block;
                padding: 12px 30px;
                background-color: #28a745; /* Yeşil tonu */
                color: white;
                text-decoration: none;
                border-radius: 8px;
                font-size: 1.1em;
                font-weight: 500;
                transition: background-color 0.3s ease;
            }
            .btn-start:hover {
                background-color: #218838;
            }
            .info-box {
                margin-top: 35px;
                padding: 15px;
                background-color: #e9ecef; /* Açık gri */
                border-left: 5px solid #007bff;
                text-align: left;
                border-radius: 5px;
                font-size: 0.9em;
                color: #555;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Letgo Otomatik İlan Takip Kontrol Paneli</h1>
            <p>Botu başlatmak için butona tıklayın. Bot, <strong>scraper.py</strong> dosyasındaki mevcut filtrelere göre çalışacak ve yeni ilanları anında e-posta ile bildirecektir.</p>
            
            <a href='/start' class='btn-start'>
                🤖 Botu Arka Planda Başlat
            </a>
            
            <div class="info-box">
                <strong>Bilgi Notu:</strong>
                <ul>
                    <li>Bot çalışmaya başladığında tarayıcı kapanana kadar terminalinizi kapatmayın.</li>
                    <li>Sistem, sadece yeni ilan bulduğunda size e-posta gönderecektir.</li>
                    <li>Filtreleri değiştirmek için <strong>scraper.py</strong> dosyasındaki <code>LETGO_URL</code> değişkenini güncelleyin.</li>
                </ul>
            </div>
        </div>
    </body>
    </html>
    """
    return html_content

# Botu başlatma
@app.route('/start')
def start_bot():
    
    try:
        thread = threading.Thread(target=ilanlari_cek_letgo_final)
        thread.start()
    except Exception as e:

        return f"""
        <h1>Hata Oluştu!</h1>
        <p>Bot başlatılırken beklenmedik bir hata oluştu: {e}</p>
        <a href='/' style='color: #dc3545;'>Kontrol Paneline Geri Dön</a>
        """
    
    return """
    <h1>✅ Başarılı!</h1>
    <p>Letgo İlan Botu arka planda çalışmaya başladı. Yeni bir ilan bulduğunda e-posta alacaksınız.</p>
    <p>Lütfen botun ilerlemesini görmek için terminalinizi kontrol edin.</p>
    <br> 
    <a href='/' style='color: #007bff;'>Kontrol Paneline Geri Dön</a>
    """

if __name__ == '__main__':
    app.run(debug=True)