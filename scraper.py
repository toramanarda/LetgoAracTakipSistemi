from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By 
from selenium.webdriver.support.ui import WebDriverWait 
from selenium.webdriver.support import expected_conditions as EC 
from selenium_stealth import stealth
from bs4 import BeautifulSoup
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
import sqlite3
import time

# --- YAPILANDIRMA AYARLARI ---
LETGO_URL = "https://www.letgo.com/arabalar_c15706?price=[-600000]&filter=km:[-200000]" 

# E-POSTA YAPILANDIRMASI 
EMAIL_ADDRESS = "gönderici e-mail" 
EMAIL_PASSWORD = "gönderici e-mail sifre"       
RECEIVER_EMAIL = "alıcı e-mail" 
SMTP_SERVER = "smtp.gmail.com" 
SMTP_PORT = 587

ILAN_SINIFI = 'item-card-container' 

# Veritabanı
DB_NAME = 'ilan_takip.db'

# --- VERİTABANI FONKSİYONLARI ---

def setup_database():
    """ Veritabanını oluşturur ve ilan tablosunu hazırlar. """
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS ilanlar (
            link TEXT PRIMARY KEY,
            baslik TEXT NOT NULL,
            fiyat TEXT,
            eklenme_tarihi TEXT
        )
    ''')
    conn.commit()
    conn.close()

def ilan_kaydet(ilan_verileri):
    """ Yeni ilanları veritabanına kaydeder ve yeni eklenenleri döndürür. """
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    yeni_eklenenler = []
    
    for baslik, fiyat, link in ilan_verileri:
        try:

            c.execute('''
                INSERT OR IGNORE INTO ilanlar (link, baslik, fiyat, eklenme_tarihi)
                VALUES (?, ?, ?, datetime('now'))
            ''', (link, baslik, fiyat)) 
            
            if c.rowcount > 0:
                yeni_eklenenler.append((baslik, fiyat, link))
                
        except sqlite3.IntegrityError:
            pass 
        except Exception as e:
            print(f"Veritabanına kaydetme hatası: {e}. Hata oluşan veri: {baslik}, {fiyat}, {link}")

    conn.commit()
    conn.close()
    return yeni_eklenenler

# --- E-POSTA FONKSİYONU ---

def send_email_notification(yeni_ilanlar):
    """ Yeni bulunan ilanları içeren bir e-posta gönderir. """
    
    if not yeni_ilanlar:
        return 

    msg = MIMEMultipart("alternative")
    msg['Subject'] = f"Letgo Bildirimi: {len(yeni_ilanlar)} Adet Yeni İlan Bulundu!"
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = RECEIVER_EMAIL

    html_content = """
    <html>
        <body>
            <h3>🎉 {count} Adet Yeni İlan Bulundu!</h3>
            <p>Aşağıdaki ilanlar, Letgo'daki aramanızda yeni göründü ve veritabanına kaydedildi:</p>
            <table border="1" style="border-collapse: collapse; width: 100%;">
                <tr>
                    <th style="padding: 10px; text-align: left;">Başlık</th>
                    <th style="padding: 10px; text-align: left;">Fiyat</th>
                    <th style="padding: 10px; text-align: left;">Link</th>
                </tr>
                {rows}
            </table>
            <p>Not: Bu e-posta otomatik olarak Python Botunuz tarafından gönderilmiştir.</p>
        </body>
    </html>
    """.format(count=len(yeni_ilanlar), rows="".join([
        f"""
        <tr>
            <td style="padding: 10px;">{ilan[0]}</td>
            <td style="padding: 10px;">{ilan[1]}</td>
            <td style="padding: 10px;"><a href="{ilan[2]}">İlanı Gör</a></td>
        </tr>
        """ for ilan in yeni_ilanlar
    ]))

    part = MIMEText(html_content, 'html')
    msg.attach(part)

    try:
        print(f"E-posta {RECEIVER_EMAIL} adresine gönderiliyor...")
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()  
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.sendmail(EMAIL_ADDRESS, RECEIVER_EMAIL, msg.as_string())
        print("E-posta başarıyla gönderildi!")
    except Exception as e:
        print(f"E-posta gönderme hatası oluştu: {e}")


# --- VERİ ÇEKME FONKSİYONU ---

def ilanlari_cek_letgo_final():
    driver = None 
    
    ilan_verileri = [] 
    
    try:
        service = Service(ChromeDriverManager().install()) 
        options = webdriver.ChromeOptions()
        
        # Stealth Ayarları
        options.add_argument("start-maximized")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        print("Tarayıcı başlatılıyor ve Letgo'ya erişiliyor...")
        driver = webdriver.Chrome(service=service, options=options)
        stealth(driver, languages=["tr-TR", "tr"], vendor="Google Inc.", platform="Win32", fix_hairline=True)
        
        driver.get(LETGO_URL)
        
        print("İlan listesinin yüklenmesi bekleniyor...")
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CLASS_NAME, ILAN_SINIFI))
        )
        
        time.sleep(3) # Ek bekleme
        
        html = driver.page_source
        
    except Exception as e:
        print(f"Hata: Sayfa yüklenemedi veya ilanlar 15 saniyede bulunamadı. {e}")
        return
    finally:
        if driver:
            driver.quit()

    # Beautiful Soup ile veriyi analiz etme
    soup = BeautifulSoup(html, 'html.parser')
    ilan_listesi = soup.find_all('div', class_=lambda c: c and ILAN_SINIFI in c)
    
    if not ilan_listesi:
        print("Sayfada hiç ilan bulunamadı.")
        return

    print(f"Bulunan İlan Sayısı (Kart): {len(ilan_listesi)}")

    # Veri çıkarma ve listeleme
    ilan_sayac = 0
    for ilan in ilan_listesi:
        # 1. Link 
        link_tag = ilan.find('a')
        link = link_tag['href'] if link_tag and link_tag.get('href') else "Link Yok"
        if link != "Link Yok" and not link.startswith('http'):
             link = "https://www.letgo.com" + link
            
        # 2. Başlık ve Fiyatı çekme
        tum_metinler = ilan.find_all(['p', 'h3', 'span'])
        baslik = "Başlık Yok"
        fiyat = "Fiyat Yok"

        if tum_metinler:
            baslik_aday = [t.text.strip() for t in tum_metinler if len(t.text.strip().split()) > 2]
            if baslik_aday:
                baslik = baslik_aday[0]
            
            fiyat_aday = [t.text.strip() for t in tum_metinler if 'TL' in t.text.strip() or 'taksit' in t.text.strip()]
            if fiyat_aday:
                fiyat = fiyat_aday[0].replace('Taksit', '').strip()

        if baslik == "Başlık Yok" and link_tag and link_tag.get('title'):
             baslik = link_tag.get('title')

        if baslik and baslik != "Başlık Yok":
            # İlan verilerini topla ve ekrana yazdır
            ilan_verileri.append((baslik, fiyat, link))
            
            print("-----------------------------------")
            print(f"Başlık: {baslik}")
            fiyat_gosterim = fiyat if fiyat != "Fiyat Yok" else "Fiyat Bilgisi Çekilemedi"
            print(f"Fiyat: {fiyat_gosterim}")
            print(f"Link: {link}")
            ilan_sayac += 1


    print(f"\nToplamda {ilan_sayac} adet ilan işlenmek üzere toplandı.")

    # 5. Veritabanına kaydetme ve Yeni İlanları Ayıklama 
    print("Veritabanı hazırlanıyor ve ilanlar kaydediliyor...")
    setup_database()

    yeni_ilanlar = ilan_kaydet(ilan_verileri)

    if yeni_ilanlar:
        print(f"\n🎉 {len(yeni_ilanlar)} adet YENİ İLAN bulundu ve veritabanına kaydedildi.")
        # E-POSTA GÖNDERME KISMI 
        send_email_notification(yeni_ilanlar) 
    else:
        print("\n✅ Taranan ilanlar arasında yeni bir ilan bulunamadı.")


if __name__ == "__main__":
    ilanlari_cek_letgo_final()