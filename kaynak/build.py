"""Builds the Zinciri Kırma website into this repository's root, which GitHub Pages serves.

The legal pages are rendered from the Android app's assets/legal/*.md (../android next to this
repository) and the iOS app's legal/*.md (../ios), the same files the apps show, so the site and
the apps never disagree. Store images, fonts and their licences are copied from the Android one.

    python kaynak/build.py
"""

import hashlib
import html
import re
import shutil
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE.parent
ANDROID = OUT.parent / "android"
LEGAL = ANDROID / "app/src/main/assets/legal"
IOS_LEGAL = OUT.parent / "ios" / "legal"
LICENSES = ANDROID / "app/src/main/assets/licenses"
SHOTS = ANDROID / "docs/play/gorseller"
FONTS = ANDROID / "app/src/main/res/font"

# What a build leaves alone in the repository root: everything else is the built site.
KEEP = {".git", "kaynak", "README.md", ".gitignore"}

# Where the site is served; used only for canonical, hreflang and social preview links.
BASE_URL = "https://bilginapplabs.github.io/zinciri-kirma.github.io/"
PLAY_URL = "https://play.google.com/store/apps/details?id=com.bilginapps.habitchain"
# The iOS app's App Store page; empty until it is published, so the site says "coming soon".
APP_STORE_URL = ""
EMAIL = "bilginapplabs@gmail.com"

# Page key -> path per language. Each page links to its counterpart in the other language.
PATHS = {
    "home": {"tr": "", "en": "en/"},
    "privacy": {"tr": "gizlilik/", "en": "en/privacy/"},
    "terms": {"tr": "kosullar/", "en": "en/terms/"},
    "delete": {"tr": "veri-silme/", "en": "en/delete-data/"},
    # The iPhone and iPad app's own texts (App Store Connect links to these).
    "ios_privacy": {"tr": "ios/gizlilik/", "en": "en/ios/privacy/"},
    "ios_terms": {"tr": "ios/kosullar/", "en": "en/ios/terms/"},
}

T = {
    "tr": {
        "lang_name": "Türkçe",
        "other": "en",
        "other_label": "English",
        "skip": "İçeriğe geç",
        "nav": [("#features", "Özellikler"), ("#screens", "Ekranlar"), ("#plus", "Zincir+"), ("#faq", "SSS")],
        "play": "Google Play'den indir",
        "app_store": "App Store'dan indir",
        "app_store_soon": "Yakında App Store'da",
        "app_store_soon_short": "App Store (yakında)",
        "site_desc": "Her gün bir halka ekle, zincirini kırma. Hatırlatmalı, reklamsız ve verin yalnızca telefonunda kalan bir alışkanlık takip uygulaması.",
        "home_title": "Zinciri Kırma · Alışkanlık takibi",
        "footer_about": "Her gün bir halka ekle, zincirini kırma. Hatırlatmalı, reklamsız, gizli bir alışkanlık takip uygulaması.",
        "footer_app": "Uygulama",
        "footer_legal": "Yasal",
        "footer_contact": "İletişim",
        "footer_nocookie": "Bu site çerez kullanmaz ve ziyaretini izlemez.",
        "privacy": "Gizlilik Politikası",
        "terms": "Kullanım Koşulları",
        "delete": "Verilerini silme",
        "ios_privacy": "Gizlilik Politikası (iOS)",
        "ios_terms": "Kullanım Koşulları (iOS)",
        "home": "Ana sayfa",
        "contents": "İçindekiler",
        "binding_note": 'Bu metnin İngilizce çevirisi: <a href="{other}">{label}</a>.',
        "eyebrow": "Android için alışkanlık takibi",
        "h1": 'Her gün bir halka.<br><span class="soft">Zinciri kırma.</span>',
        "lead": "Yaptığın her gün zincirine bir halka ekler. Hatırlatmalı, reklamsız ve verin yalnızca telefonunda.",
        "how_btn": "Nasıl çalışır?",
        "perks": ["İlk 30 gün her şey açık", "Kart istenmez", "Hesap yok, reklam yok"],
        "hero_alt": "Zinciri Kırma'nın Bugün ekranı: bu haftanın zinciri ve sıradaki alışkanlıklar",
        "rule_kicker": "Tek kural",
        "rule_title": "İki gün üst üste kaçırma.",
        "rule_lead": "Bir alışkanlığı her yaptığında o güne bir halka eklenir. Halkalar birleştikçe zincirin uzar, serin büyür ve her gün biraz daha kırmak istemezsin. Bir gün kaçarsa telaş yok; ertesi gün yeniden başla.",
        "week_title": "Bu hafta",
        "week_btn": "Ayı aç",
        "days": ["Pzt", "Sal", "Çar", "Per", "Cum", "Cmt", "Paz"],
        "week_note": "<b>3</b> tam gün bu hafta. Bugünü de bitirirsen 4 olur.",
        "features_kicker": "Özellikler",
        "features_title": "Sade, ama ihtiyacın olan her şey içinde.",
        "cards": [
            ("link", "", "Her gün bir halka", [
                "Alışkanlık ya da tek seferlik görev ekle, saatini seç.",
                "Her gün, haftanın belirli günleri, haftada birkaç kez ya da ayın belirli günleri.",
                "Ölçülebilir hedefler: 20 sayfa, 30 dakika, 8 bardak. Hedefe ulaşınca halka eklenir.",
                "Güne kısa bir not bırak.",
                "12 temada 100'ü aşkın hazır program; her temada biri ücretsiz.",
            ]),
            ("chart", "", "Görerek ilerle", [
                "Bu haftanın zinciri, ay takvimi ve her alışkanlığın serisi.",
                "Zincir haritan: son 12 haftanın her günü; parmağını gezdir, günü aç.",
                "Bu dönemin tutarlılığı ve kazandığın rozetler.",
                "Kategoriler: Sağlık, Spor, Zihin, Öğrenme, Üretkenlik.",
                "Serini hikâye kartı olarak paylaş: en uzun serin ve son haftaların zinciriyle.",
            ]),
            ("bell", "warm", "Zamanında hatırlat", [
                "Zamanı gelince hatırlatma al.",
                "Bildirimden tek dokunuşla \"Yaptım\" ya da \"10 dk sonra\".",
                "Koyu ve açık tema, Türkçe ve İngilizce.",
                "Haftanın pazartesi mi pazar mı başlayacağını sen seç.",
            ]),
        ],
        "screens_kicker": "Ekranlar",
        "screens_title": "Uygulamadan kareler",
        "prev": "Önceki",
        "next": "Sonraki",
        "shots": [
            ("01-bugun.png", "Her gün bir halka: Bugün ekranı"),
            ("02-zincirin.png", "Zincirini gör, kırma: alışkanlık detayı"),
            ("03-hedef.png", "Hedefin kadar yap: ölçülebilir hedef"),
            ("04-yeni-aliskanlik.png", "Kendi zincirini kur: yeni alışkanlık ekranı"),
            ("05-istatistik.png", "Ne kadar tutarlısın? İstatistik ekranı"),
            ("06-harita.png", "Zincir haritan: Profil ekranı"),
            ("07-verin.png", "Verin telefonunda kalır: Ayarlar"),
            ("08-zincir-plus.png", "30 gün her şey açık: Zincir+"),
        ],
        "privacy_kicker": "Gizlilik",
        "privacy_title": "Verin senin. Telefonundan çıkmaz.",
        "privacy_lead": "Zinciri Kırma bir hesap, e-posta ya da telefon numarası istemez. Alışkanlıkların, geçmişin ve notların yalnızca senin telefonunda durur.",
        "vault_badge": "Yalnızca bu telefonda",
        "vault": [
            "Alışkanlıkların, notların ve ayarların hiçbir sunucuya gönderilmez.",
            "Hesap açmazsın, reklam yoktur.",
            "Anonim kullanım ve çökme verisi yalnızca sen izin verirsen gönderilir; istediğin an kapatırsın.",
            "Google yedeği verini yeni telefona taşır; Zincir+ ile yedek dosyası da alırsın.",
            "İstediğin an tüm verini silebilirsin.",
        ],
        "plus_kicker": "Zincir+",
        "plus_title": "İlk 30 gün her şey açık.",
        "plus_lead": "Deneme için kart istenmez ve deneme kendiliğinden ücretli aboneliğe dönüşmez. Deneme bitince temel özellikler ücretsiz kalır; hiçbir şey silinmez.",
        "trial_days": "30",
        "trial_unit": "gün",
        "trial_text": "<strong>Ücretsiz deneme.</strong> Uygulamayı ilk açtığın gün başlar; Zincir+ özelliklerinin hepsi açık.",
        "plus_items": [
            ("📊", "Tüm istatistikler: son 8 hafta, haftanın günleri, kategoriler, sıralama"),
            ("🗓️", "Ay ve yıl özeti; PDF raporu önce gör, sonra kaydet ya da paylaş"),
            ("🏷️", "Kendi kategorilerin, emojilerin ve renklerin"),
            ("🎨", "Vurgu renkleri ve uygulama ikonları"),
            ("📱", "Ana ekran widget'ları ve hikâye şablonları: Gece, Kâğıt, Takvim"),
            ("🔔", "Bir alışkanlığa günde birden çok hatırlatma"),
            ("😴", "Yorgun bir günde mola ver, zincir kırılmasın"),
            ("⏪", "Geçmiş günleri sonradan işaretle"),
            ("❤️", "Health Connect ile otomatik halka: adım, uyku, egzersiz, su"),
            ("🏁", "Hazır programların tamamı: 12 temada 100'ü aşkın program"),
            ("💾", "Yedek dosyası: istediğin yere kaydet, yeni telefonda geri yükle"),
        ],
        "plus_fine": "Zincir+ aylık ya da yıllık abonelik olarak sunulur. Güncel fiyatlar uygulamada Google Play'den gösterilir. Aboneliği Google Play › Abonelikler'den istediğin an iptal edebilirsin.",
        "faq_kicker": "SSS",
        "faq_title": "Sık sorulan sorular",
        "faq": [
            ("Hesap açmam gerekiyor mu?",
             "Hayır. Zinciri Kırma hesap, e-posta ya da telefon numarası istemez. Alışkanlıkların, notların ve ayarların yalnızca telefonunda durur; hiçbir sunucuya gönderilmez."),
            ("Telefon değiştirirsem verilerim ne olur?",
             "Telefonunda Google yedeklemesi açıksa Android uygulamanın verisini senin Google hesabına yedekler ve yeni telefonda geri getirir. Zincir+ ile Profil › Ayarlar › Yedekleme › \"Şimdi yedekle\" ile bir yedek dosyası da oluşturup istediğin yere (örneğin Google Drive) kaydedebilir, yeni telefonda \"Geri yükle\" ile açabilirsin; geri yükleme o telefondaki alışkanlıkların yerini alır, önce sorulur."),
            ("Deneme bitince ne olur?",
             "Zincir+ özellikleri kapanır. Alışkanlıkların, geçmişin ve ayarların silinmez; temel özellikler ücretsiz kalır. Deneme kendiliğinden ücretli aboneliğe dönüşmez."),
            ("Aboneliğimi nasıl iptal ederim?",
             "Google Play uygulamasında Profil › Ödemeler ve abonelikler › Abonelikler bölümünden istediğin an iptal edebilirsin. Dönemin sonuna kadar Zincir+ açık kalır."),
            ("Verilerimi nasıl silerim?",
             "Profil › Ayarlar › \"Tüm verilerimi sil\" ile her şeyi bu telefondan kalıcı olarak silersin. Ayrıntılar <a href=\"{root}veri-silme/\">Verilerini silme</a> sayfasında."),
            ("Hangi telefonlarda çalışır?",
             "Android 8.0 ve üzeri sürümlerde çalışır. iPhone ve iPad sürümü (iOS 17 ve üzeri) yakında App Store'da; onun <a href=\"{root}ios/gizlilik/\">gizlilik politikası</a> ayrıdır."),
            ("Bir sorun buldum ya da önerim var.",
             "Bize <a href=\"mailto:{email}\">{email}</a> adresinden yaz; her e-postayı okuyoruz."),
        ],
        "band_title": "Bugün ilk halkayı ekle.",
        "band_text": "30 gün her şey açık. Kart yok, hesap yok.",
    },
    "en": {
        "lang_name": "English",
        "other": "tr",
        "other_label": "Türkçe",
        "skip": "Skip to content",
        "nav": [("#features", "Features"), ("#screens", "Screens"), ("#plus", "Zincir+"), ("#faq", "FAQ")],
        "play": "Get it on Google Play",
        "app_store": "Download on the App Store",
        "app_store_soon": "Coming soon to the App Store",
        "app_store_soon_short": "App Store (coming soon)",
        "site_desc": "Add one link a day and don't break the chain. A habit tracker with reminders, no ads, and your data kept only on your phone.",
        "home_title": "Zinciri Kırma · Habit tracker",
        "footer_about": "Add one link a day and don't break the chain. A private habit tracker with reminders and no ads.",
        "footer_app": "App",
        "footer_legal": "Legal",
        "footer_contact": "Contact",
        "footer_nocookie": "This site uses no cookies and does not track your visit.",
        "privacy": "Privacy Policy",
        "terms": "Terms of Use",
        "delete": "Deleting your data",
        "ios_privacy": "Privacy Policy (iOS)",
        "ios_terms": "Terms of Use (iOS)",
        "home": "Home",
        "contents": "Contents",
        "binding_note": 'The binding text is the Turkish original: <a href="{other}">{label}</a>.',
        "eyebrow": "Habit tracking for Android",
        "h1": 'One link a day.<br><span class="soft">Don\'t break the chain.</span>',
        "lead": "Every day you do it adds a link to your chain. Reminders, no ads, and your data stays on your phone.",
        "how_btn": "How it works",
        "perks": ["Everything open for 30 days", "No card needed", "No account, no ads"],
        "hero_alt": "The Today screen of Zinciri Kırma: this week's chain and the habits up next",
        "rule_kicker": "One rule",
        "rule_title": "Never miss two days in a row.",
        "rule_lead": "Each time you do a habit, that day gets a link. As the links join up your chain grows, your streak climbs, and each day you want to break it a little less. Missed a day? No panic; pick it up again tomorrow.",
        "week_title": "This week",
        "week_btn": "Open month",
        "days": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
        "week_note": "<b>3</b> full days this week. Finish today and it's 4.",
        "features_kicker": "Features",
        "features_title": "Simple, with everything you need.",
        "cards": [
            ("link", "", "One link a day", [
                "Add a habit or a one-time task and pick its time.",
                "Every day, certain weekdays, a few times a week or certain days of the month.",
                "Measurable goals: 20 pages, 30 minutes, 8 glasses. The link is added when you reach it.",
                "Leave a short note on the day.",
                "Over 100 ready-made programs in 12 themes; one in every theme is free.",
            ]),
            ("chart", "", "See your progress", [
                "This week's chain, a month calendar and every habit's streak.",
                "Your chain map: every day of the last 12 weeks; slide a finger to open one.",
                "This period's consistency and the badges you earn.",
                "Categories: Health, Sport, Mind, Learning, Productivity.",
                "Share your streak as a story card, with your longest streak and the last weeks' chain.",
            ]),
            ("bell", "warm", "Reminders on time", [
                "Get a reminder when it's time.",
                "Tap \"Done\" or \"Snooze 10 min\" right from the notification.",
                "Dark and light theme, English and Turkish.",
                "Start your week on Monday or Sunday.",
            ]),
        ],
        "screens_kicker": "Screens",
        "screens_title": "A look inside",
        "prev": "Previous",
        "next": "Next",
        "shots": [
            ("01-today.png", "One link a day: the Today screen"),
            ("02-your-chain.png", "See your chain grow: habit details"),
            ("03-goals.png", "Track goals, not just ticks"),
            ("04-new-habit.png", "Build your own chain: the new habit screen"),
            ("05-stats.png", "How consistent are you? Statistics"),
            ("06-chain-map.png", "Your chain map: the Profile screen"),
            ("07-your-data.png", "Your data stays on your phone: Settings"),
            ("08-zincir-plus.png", "Everything open for 30 days: Zincir+"),
        ],
        "privacy_kicker": "Privacy",
        "privacy_title": "Your data is yours. It stays on your phone.",
        "privacy_lead": "Zinciri Kırma asks for no account, email address or phone number. Your habits, history and notes live only on your phone.",
        "vault_badge": "Only on this phone",
        "vault": [
            "Your habits, notes and settings are never sent to a server.",
            "No account and no ads.",
            "Anonymous usage and crash data is sent only if you allow it, and you can turn it off at any time.",
            "Google backup brings your data to a new phone; with Zincir+ you can also keep a backup file.",
            "Delete all your data at any time.",
        ],
        "plus_kicker": "Zincir+",
        "plus_title": "Everything open for 30 days.",
        "plus_lead": "No card is needed for the trial, and it never turns into a paid subscription by itself. When it ends, the basics stay free and nothing is deleted.",
        "trial_days": "30",
        "trial_unit": "days",
        "trial_text": "<strong>Free trial.</strong> It starts the first day you open the app, with every Zincir+ feature on.",
        "plus_items": [
            ("📊", "All statistics: the last 8 weeks, days of the week, categories, ranking"),
            ("🗓️", "Month and year recaps; see the PDF report first, then save or share it"),
            ("🏷️", "Your own categories, emojis and colours"),
            ("🎨", "Accent colours and app icons"),
            ("📱", "Home screen widgets and story templates: Night, Paper, Calendar"),
            ("🔔", "Several reminders a day for one habit"),
            ("😴", "Take a rest day without breaking the chain"),
            ("⏪", "Mark past days later on"),
            ("❤️", "Automatic links from Health Connect: steps, sleep, exercise, water"),
            ("🏁", "Every ready-made program: over 100 in 12 themes"),
            ("💾", "A backup file: save it anywhere, restore it on a new phone"),
        ],
        "plus_fine": "Zincir+ is offered as a monthly or yearly subscription. Current prices are shown in the app from Google Play. You can cancel a subscription at any time in Google Play › Subscriptions.",
        "faq_kicker": "FAQ",
        "faq_title": "Frequently asked questions",
        "faq": [
            ("Do I need an account?",
             "No. Zinciri Kırma asks for no account, email address or phone number. Your habits, notes and settings stay on your phone and are never sent to a server."),
            ("What happens to my data if I change phones?",
             "If Google backup is on, Android backs up the app's data to your Google account and brings it back on the new phone. With Zincir+ you can also create a backup file with Profile › Settings › Backup › \"Back up now\", save it wherever you like (for example Google Drive) and open it on the new phone with \"Restore\"; a restore replaces the habits on that phone, after asking."),
            ("What happens when the trial ends?",
             "The Zincir+ features close. Your habits, history and settings are not deleted, and the basics stay free. The trial never turns into a paid subscription by itself."),
            ("How do I cancel my subscription?",
             "In the Google Play app, go to Profile › Payments and subscriptions › Subscriptions and cancel at any time. Zincir+ stays on until the end of the period."),
            ("How do I delete my data?",
             "Profile › Settings › \"Delete all my data\" permanently deletes everything from this phone. See <a href=\"{root}en/delete-data/\">Deleting your data</a> for details."),
            ("Which phones does it run on?",
             "Android 8.0 and later. The iPhone and iPad app (iOS 17 and later) is coming soon to the App Store; it has its own <a href=\"{root}en/ios/privacy/\">privacy policy</a>."),
            ("I found a problem or have an idea.",
             "Write to us at <a href=\"mailto:{email}\">{email}</a>; we read every email."),
        ],
        "band_title": "Add your first link today.",
        "band_text": "Everything open for 30 days. No card, no account.",
    },
}

ICONS = {
    "link": '<path d="M10 14a4.2 4.2 0 0 0 6 0l3-3a4.2 4.2 0 0 0-6-6l-1 1"/><path d="M14 10a4.2 4.2 0 0 0-6 0l-3 3a4.2 4.2 0 0 0 6 6l1-1"/>',
    "chart": '<path d="M4 20V13"/><path d="M10 20V5"/><path d="M16 20v-9"/><path d="M21 20H3"/>',
    "bell": '<path d="M6 9a6 6 0 0 1 12 0c0 6 2.5 7.5 2.5 7.5h-17S6 15 6 9"/><path d="M10 20a2 2 0 0 0 4 0"/>',
    "shield": '<path d="M12 3l7 3v6c0 4.5-3 7.5-7 9-4-1.5-7-4.5-7-9V6z"/><path d="M9 12l2 2 4-4"/>',
    "play": '<path d="M7 4.5v15a1 1 0 0 0 1.5.86l12.4-7.5a1 1 0 0 0 0-1.72L8.5 3.64A1 1 0 0 0 7 4.5z"/>',
    "left": '<path d="M15 5l-7 7 7 7"/>',
    "right": '<path d="M9 5l7 7-7 7"/>',
    "arrow": '<path d="M5 12h14"/><path d="M13 6l6 6-6 6"/>',
    "phone": '<rect x="6.5" y="2.5" width="11" height="19" rx="2.5"/><path d="M11 18.5h2"/>',
}


def icon(name, fill=False):
    style = 'fill="currentColor"' if fill else 'fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"'
    return f'<svg viewBox="0 0 24 24" {style} aria-hidden="true">{ICONS[name]}</svg>'


def version(name):
    """A short fingerprint of a stylesheet or script, so a new build is never shown with an old copy
    a browser kept (GitHub Pages lets browsers keep them for ten minutes)."""
    return hashlib.sha1((HERE / "assets" / name).read_bytes()).hexdigest()[:8]


def root_of(path):
    return "../" * path.count("/")


def play_url(lang):
    return PLAY_URL if lang == "tr" else PLAY_URL + "&hl=en"


def app_store_button(lang):
    """The App Store's place next to Google Play: a link once the app is out, "coming soon" until then.
    A plain phone sign, not Apple's logo, which only Apple's own badge may carry."""
    t = T[lang]
    if APP_STORE_URL:
        return f'<a class="btn btn-play" href="{APP_STORE_URL}" rel="noopener">{icon("phone")}{t["app_store"]}</a>'
    return f'<span class="btn btn-soon" role="note">{icon("phone")}{t["app_store_soon"]}</span>'


def app_store_item(lang):
    t = T[lang]
    if APP_STORE_URL:
        return f'<li><a href="{APP_STORE_URL}" rel="noopener">App Store</a></li>'
    return f"<li>{t['app_store_soon_short']}</li>"


# ---------- Shared frame ----------


def page(key, lang, title, desc, body, og_image=None):
    t = T[lang]
    path = PATHS[key][lang]
    root = root_of(path)
    other = t["other"]
    other_href = root + PATHS[key][other]
    og = og_image or ("assets/og-tr.png" if lang == "tr" else "assets/og-en.png")
    alternates = "\n".join(
        f'  <link rel="alternate" hreflang="{l}" href="{BASE_URL}{PATHS[key][l]}">' for l in ("tr", "en")
    )
    home = root + PATHS["home"][lang]
    nav = "".join(f'<a href="{home if key != "home" else ""}{h}">{label}</a>' for h, label in t["nav"])
    return f"""<!doctype html>
<html lang="{lang}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(title)}</title>
  <meta name="description" content="{html.escape(desc)}">
  <meta name="theme-color" content="#2f6be0">
  <link rel="canonical" href="{BASE_URL}{path}">
{alternates}
  <link rel="alternate" hreflang="x-default" href="{BASE_URL}{PATHS[key]['tr']}">
  <meta property="og:type" content="website">
  <meta property="og:site_name" content="Zinciri Kırma">
  <meta property="og:title" content="{html.escape(title)}">
  <meta property="og:description" content="{html.escape(desc)}">
  <meta property="og:url" content="{BASE_URL}{path}">
  <meta property="og:image" content="{BASE_URL}{og}">
  <meta property="og:locale" content="{'tr_TR' if lang == 'tr' else 'en_US'}">
  <meta name="twitter:card" content="summary_large_image">
  <link rel="icon" type="image/png" href="{root}assets/icon-512.png">
  <link rel="apple-touch-icon" href="{root}assets/icon-512.png">
  <link rel="preload" href="{root}assets/fonts/bricolage_grotesque.ttf" as="font" type="font/ttf" crossorigin>
  <link rel="stylesheet" href="{root}assets/site.css?v={version('site.css')}">
</head>
<body>
<a class="skip" href="#main">{t['skip']}</a>
<header class="top">
  <div class="wrap">
    <a class="brand" href="{home}"><img src="{root}assets/icon-512.png" alt="" width="34" height="34">Zinciri Kırma</a>
    <nav class="nav" aria-label="{'Bölümler' if lang == 'tr' else 'Sections'}">{nav}</nav>
    <a class="lang" href="{other_href}" hreflang="{other}" lang="{other}">{t['other_label']}</a>
  </div>
</header>
<main id="main">
{body}
</main>
{footer(lang, root)}
<script src="{root}assets/site.js?v={version('site.js')}" defer></script>
</body>
</html>
"""


def footer(lang, root):
    t = T[lang]
    home = root + PATHS["home"][lang]
    links_app = "".join(f'<li><a href="{home}{h}">{label}</a></li>' for h, label in t["nav"])
    return f"""<footer>
  <div class="wrap">
    <div class="about">
      <a class="brand" href="{home}"><img src="{root}assets/icon-512.png" alt="" width="34" height="34">Zinciri Kırma</a>
      <p>{t['footer_about']}</p>
      <p>© 2026 Bilgin Apps · Erhan Bilgin</p>
      <p>{t['footer_nocookie']}</p>
    </div>
    <div>
      <h4>{t['footer_app']}</h4>
      <ul>{links_app}<li><a href="{play_url(lang)}" rel="noopener">Google Play</a></li>{app_store_item(lang)}</ul>
    </div>
    <div>
      <h4>{t['footer_legal']}</h4>
      <ul>
        <li><a href="{root}{PATHS['privacy'][lang]}">{t['privacy']}</a></li>
        <li><a href="{root}{PATHS['terms'][lang]}">{t['terms']}</a></li>
        <li><a href="{root}{PATHS['delete'][lang]}">{t['delete']}</a></li>
        <li><a href="{root}{PATHS['ios_privacy'][lang]}">{t['ios_privacy']}</a></li>
        <li><a href="{root}{PATHS['ios_terms'][lang]}">{t['ios_terms']}</a></li>
        <li><a href="mailto:{EMAIL}">{EMAIL}</a></li>
      </ul>
    </div>
  </div>
</footer>"""


# ---------- Home ----------


def week_svg(lang):
    days = T[lang]["days"]
    xs = [40 + i * 80 for i in range(7)]
    cy = 82
    parts = []
    # Links between the days already done; the one into today appears when today closes.
    for i in range(2):
        parts.append(f'<rect x="{xs[i]}" y="{cy - 9}" width="80" height="18" fill="rgba(255,255,255,.35)"/>')
    parts.append(f'<rect class="link-new" x="{xs[2]}" y="{cy - 9}" width="80" height="18" fill="rgba(255,255,255,.35)"/>')
    for i, (x, name) in enumerate(zip(xs, days)):
        if i == 3:
            parts.append(f'<rect x="{x - 26}" y="2" width="52" height="26" rx="13" fill="#ffb870"/>')
        parts.append(f'<text class="day-name{" today" if i == 3 else ""}" x="{x}" y="20" text-anchor="middle">{name}</text>')
        num = 12 + i
        if i < 3:
            parts.append(f'<circle cx="{x}" cy="{cy}" r="28" fill="#ffffff"/>')
            parts.append(f'<text class="day-num" x="{x}" y="{cy + 6}" text-anchor="middle" fill="#2f6be0">{num}</text>')
        elif i == 3:
            parts.append(f'<circle cx="{x}" cy="{cy}" r="28" fill="none" stroke="rgba(255,255,255,.9)" stroke-width="2.5"/>')
            parts.append(f'<circle class="ring" cx="{x}" cy="{cy}" r="34" fill="none" stroke="#ffb870" stroke-width="4" stroke-linecap="round" transform="rotate(-90 {x} {cy})"/>')
            parts.append(f'<text class="day-num today-num" x="{x}" y="{cy + 6}" text-anchor="middle" fill="#ffffff">{num}</text>')
            parts.append(f'<circle class="today-fill" cx="{x}" cy="{cy}" r="28" fill="#ffffff"/>')
            parts.append(f'<path class="tick" d="M{x - 10} {cy + 1}l7 7 13-14" fill="none" stroke="#2f6be0" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/>')
        else:
            parts.append(f'<circle cx="{x}" cy="{cy}" r="28" fill="none" stroke="rgba(255,255,255,.6)" stroke-width="2" stroke-dasharray="2 5" stroke-linecap="round"/>')
            parts.append(f'<text class="day-num" x="{x}" y="{cy + 6}" text-anchor="middle" fill="#ffffff">{num}</text>')
    label = "Bu haftanın zinciri: üç gün yapıldı, bugün tamamlanıyor" if lang == "tr" else "This week's chain: three days done, today closing"
    return f'<svg viewBox="0 0 560 124" role="img" aria-label="{label}">{"".join(parts)}</svg>'


def home(lang):
    t = T[lang]
    root = root_of(PATHS["home"][lang])
    folder = lang
    shots = "".join(
        f'<figure><img src="{root}assets/shots/{folder}/{f}" alt="{html.escape(alt)}" width="1080" height="1920" loading="lazy" decoding="async"></figure>'
        for f, alt in t["shots"]
    )
    cards = "".join(
        f"""<article class="card"><div class="icon {tone}">{icon(name)}</div><h3>{title}</h3>
<ul class="ticks">{''.join(f'<li>{html.escape(x)}</li>' for x in items)}</ul></article>"""
        for name, tone, title, items in t["cards"]
    )
    vault = "".join(f"<li>{html.escape(x)}</li>" for x in t["vault"])
    plus = "".join(f'<li><span class="em" aria-hidden="true">{e}</span><span>{html.escape(x)}</span></li>' for e, x in t["plus_items"])
    faq = "".join(
        f"<details><summary>{html.escape(q)}</summary><p>{a.format(root=root, email=EMAIL)}</p></details>"
        for q, a in t["faq"]
    )
    perks = "".join(f"<li>{p}</li>" for p in t["perks"])
    hero_shot = t["shots"][0][0]
    play_btn = f'<a class="btn btn-play" href="{play_url(lang)}" rel="noopener">{icon("play", fill=True)}{t["play"]}</a>'
    body = f"""<div class="hero">
  <div class="wrap">
    <div class="hero-copy">
      <span class="eyebrow">{t['eyebrow']}</span>
      <h1>{t['h1']}</h1>
      <p class="lead">{t['lead']}</p>
      <div class="cta">{play_btn}{app_store_button(lang)}<a class="btn btn-ghost" href="#how">{t['how_btn']}</a></div>
      <ul class="perks">{perks}</ul>
    </div>
    <div class="hero-phone"><img src="{root}assets/shots/{folder}/{hero_shot}" alt="{html.escape(t['hero_alt'])}" width="1080" height="1920" fetchpriority="high"></div>
  </div>
</div>

<section id="how">
  <div class="wrap rule">
    <div>
      <p class="kicker">{t['rule_kicker']}</p>
      <h2 class="section-title">{t['rule_title']}</h2>
      <p class="section-lead">{t['rule_lead']}</p>
    </div>
    <div class="week">
      <div class="week-head">{t['week_title']}<span>{t['week_btn']} ›</span></div>
      {week_svg(lang)}
      <p class="week-note">{t['week_note']}</p>
    </div>
  </div>
</section>

<section id="features" style="padding-top:0">
  <div class="wrap">
    <p class="kicker">{t['features_kicker']}</p>
    <h2 class="section-title">{t['features_title']}</h2>
    <div class="features">{cards}</div>
  </div>
</section>

<section id="screens" class="screens">
  <div class="wrap screens-head">
    <div>
      <p class="kicker">{t['screens_kicker']}</p>
      <h2 class="section-title">{t['screens_title']}</h2>
    </div>
    <div class="arrows">
      <button type="button" data-shots="-1" aria-label="{t['prev']}">{icon('left')}</button>
      <button type="button" data-shots="1" aria-label="{t['next']}">{icon('right')}</button>
    </div>
  </div>
  <div class="shots" tabindex="0" aria-label="{t['screens_title']}">{shots}</div>
</section>

<section id="privacy">
  <div class="wrap privacy">
    <div>
      <p class="kicker">{t['privacy_kicker']}</p>
      <h2 class="section-title">{t['privacy_title']}</h2>
      <p class="section-lead">{t['privacy_lead']}</p>
      <div class="links-row">
        <a class="chip-link" href="{root}{PATHS['privacy'][lang]}">{t['privacy']} ›</a>
        <a class="chip-link" href="{root}{PATHS['delete'][lang]}">{t['delete']} ›</a>
        <a class="chip-link" href="{root}{PATHS['ios_privacy'][lang]}">{t['ios_privacy']} ›</a>
      </div>
    </div>
    <div class="vault">
      <span class="vault-badge">{icon('shield')}{t['vault_badge']}</span>
      <ul class="ticks">{vault}</ul>
    </div>
  </div>
</section>

<section id="plus" class="plus">
  <div class="wrap plus-grid">
    <div>
      <p class="kicker">{t['plus_kicker']}</p>
      <h2 class="section-title">{t['plus_title']}</h2>
      <p class="section-lead">{t['plus_lead']}</p>
      <div class="trial"><div class="trial-days">{t['trial_days']}<small>{t['trial_unit']}</small></div><p>{t['trial_text']}</p></div>
    </div>
    <div>
      <ul class="plus-list">{plus}</ul>
      <p class="fine">{t['plus_fine']}</p>
    </div>
  </div>
</section>

<section id="faq">
  <div class="wrap center">
    <p class="kicker">{t['faq_kicker']}</p>
    <h2 class="section-title">{t['faq_title']}</h2>
  </div>
  <div class="wrap"><div class="faq">{faq}</div></div>
</section>

<div class="wrap">
  <div class="band">
    <div><h2>{t['band_title']}</h2><p>{t['band_text']}</p></div>
    {play_btn}
  </div>
</div>"""
    return page("home", lang, t["home_title"], t["site_desc"], body)


# ---------- Documents ----------

TR_FOLD = str.maketrans("çğıİöşüÇĞÖŞÜâîû", "cgiiosucgosuaiu")


def slug(text):
    s = text.translate(TR_FOLD).lower()
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")


def inline(text):
    s = html.escape(text, quote=False)
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"\[(.+?)\]\((.+?)\)", r'<a href="\2">\1</a>', s)
    s = re.sub(r"(?<![\w.:/@])([\w.+-]+@[\w-]+\.[\w.]+)", r'<a href="mailto:\1">\1</a>', s)
    return s


def markdown(md):
    """The small Markdown the legal texts use: #/##/### headings, paragraphs, '-' lists, bold, links."""
    title, meta, blocks, toc = None, None, [], []
    para, items = [], []

    def flush():
        if para:
            blocks.append(f"<p>{inline(' '.join(para))}</p>")
            para.clear()
        if items:
            blocks.append("<ul>" + "".join(f"<li>{inline(i)}</li>" for i in items) + "</ul>")
            items.clear()

    for raw in md.splitlines():
        line = raw.rstrip()
        if not line:
            flush()
        elif line.startswith("# "):
            flush()
            title = line[2:].strip()
        elif line.startswith("## "):
            flush()
            text = line[3:].strip()
            hid = slug(text)
            toc.append((hid, text))
            blocks.append(f'<h2 id="{hid}">{inline(text)}</h2>')
        elif line.startswith("### "):
            flush()
            blocks.append(f"<h3>{inline(line[4:].strip())}</h3>")
        elif line.startswith("- "):
            if para:
                flush()
            items.append(line[2:].strip())
        elif items and raw.startswith("  "):
            items[-1] += " " + line.strip()
        elif meta is None and title and not blocks and not para and re.search(r"\d{4}", line) and "·" in line:
            meta = line.strip()
        else:
            if items:
                flush()
            para.append(line.strip())
    flush()
    return title, meta, blocks, toc


def doc_page(key, lang, title, meta_pills, note, blocks, toc, desc):
    t = T[lang]
    root = root_of(PATHS[key][lang])
    toc_html = "".join(f'<li><a href="#{i}">{html.escape(x)}</a></li>' for i, x in toc)
    pills = "".join(meta_pills)
    note_html = f'<p class="note">{note}</p>' if note else ""
    body = f"""<div class="wrap doc-head">
  <div class="crumbs"><a href="{root}{PATHS['home'][lang]}">Zinciri Kırma</a> › {html.escape(title)}</div>
  <h1>{html.escape(title)}</h1>
  <div class="doc-meta">{pills}</div>
</div>
<div class="wrap doc">
  <nav class="toc" aria-label="{t['contents']}"><p>{t['contents']}</p><ol>{toc_html}</ol></nav>
  <article class="prose">{note_html}{''.join(blocks)}</article>
</div>"""
    return page(key, lang, f"{title} · Zinciri Kırma", desc, body)


LEGAL_FILES = {
    ("privacy", "tr"): LEGAL / "gizlilik-politikasi.md",
    ("privacy", "en"): LEGAL / "privacy-policy.md",
    ("terms", "tr"): LEGAL / "kullanim-kosullari.md",
    ("terms", "en"): LEGAL / "terms-of-use.md",
    ("ios_privacy", "tr"): IOS_LEGAL / "gizlilik-politikasi.md",
    ("ios_privacy", "en"): IOS_LEGAL / "privacy-policy.md",
    ("ios_terms", "tr"): IOS_LEGAL / "kullanim-kosullari.md",
    ("ios_terms", "en"): IOS_LEGAL / "terms-of-use.md",
}


def legal(key, lang):
    t = T[lang]
    md = LEGAL_FILES[(key, lang)].read_text(encoding="utf-8")
    title, meta, blocks, toc = markdown(md)
    root = root_of(PATHS[key][lang])
    other = t["other"]
    pills = [f'<span class="pill">{html.escape(meta)}</span>'] if meta else []
    pills.append(f'<a class="pill" href="{root}{PATHS[key][other]}" hreflang="{other}">{t["other_label"]}</a>')
    if lang == "en":
        # The English file opens with its own translation notice; drop it for the linked note below.
        if blocks and blocks[0].startswith("<p>") and "translation" in blocks[0].lower():
            blocks = blocks[1:]
        note = t["binding_note"].format(other=f"{root}{PATHS[key]['tr']}", label=html.escape(T["tr"][key]))
    else:
        note = t["binding_note"].format(other=f"{root}{PATHS[key]['en']}", label=html.escape(T["en"][key]))
    return doc_page(key, lang, title, pills, note, blocks, toc, f"{title}: Zinciri Kırma, Bilgin Apps.")


# ---------- Data deletion (what Google Play's account deletion link points to) ----------

DELETE = {
    "tr": {
        "title": "Zinciri Kırma: verilerini silme",
        "desc": "Zinciri Kırma'da (Bilgin Apps) verilerini nasıl silersin, ne silinir, ne kalır ve ne kadar süre saklanır.",
        "updated": "Güncelleme: 21 Ekim 2026",
        "sections": [
            ("Hesap yok, silinecek veri telefonunda",
             """<p><strong>Zinciri Kırma</strong>, Bilgin Apps adıyla yayın yapan Erhan Bilgin tarafından geliştirilir. Uygulamada hesap yoktur: kayıt, giriş, e-posta ya da şifre istenmez. Alışkanlıkların, geçmişin ve notların hiçbir sunucuya gönderilmez, yalnızca telefonunda durur. Bu yüzden silmek için bize başvurman gerekmez; verilerini uygulamanın içinden, istediğin an kendin silersin.</p>"""),
            ("Uygulamanın içinden silme",
             """<ol class="steps">
<li>Zinciri Kırma'yı aç ve alttaki <strong>Profil</strong> sekmesine dokun.</li>
<li>Sağ üstteki dişliye dokunarak <strong>Ayarlar</strong>'ı aç.</li>
<li><strong>Gizlilik ve veri</strong> bölümünde <strong>Tüm verilerimi sil</strong>'e dokun.</li>
<li><strong>Her şeyi sil</strong> ile onayla.</li>
</ol>
<p>Silme hemen gerçekleşir ve geri alınamaz. Uygulamayı telefonundan kaldırmak da telefondaki bütün verisini siler.</p>"""),
            ("Paylaşımı durdurma",
             """<p>Anonim kullanım ve çökme verisi paylaşımına izin verdiysen aynı bölümdeki <strong>Anonim kullanım ve çökme verisi paylaş</strong> anahtarını kapat. Kapattığın an yeni veri gönderilmez, telefondaki analiz kimliği sıfırlanır ve gönderilmemiş çökme raporları silinir. "Tüm verilerimi sil" bu anahtarı da kapatır.</p>"""),
            ("E-postayla talep",
             f"""<p>Uygulamaya ulaşamıyorsan (örneğin telefonunu kaybettiysen) ya da bir sorun olursa <a href="mailto:{EMAIL}?subject=Veri%20silme%20talebi">{EMAIL}</a> adresine "Veri silme talebi" konulu bir e-posta gönder. Elimizde seni tanıyan bir hesap ya da kişisel veri bulunmadığından telefonundaki verileri uzaktan silemeyiz; talebine en geç 30 gün içinde yanıt veririz.</p>"""),
            ("Ne silinir, ne kalır?",
             """<table class="table">
<thead><tr><th>Veri</th><th>Ne olur?</th></tr></thead>
<tbody>
<tr><td>Alışkanlıklar ve görevler, geçmiş (yapılan ve mola günleri, miktarlar), notlar, kategoriler, hatırlatmalar, rozetler, profil adın ve ayarların</td><td><span class="tag gone">Silinir</span> Hemen ve kalıcı olarak, telefonundan.</td></tr>
<tr><td>Paylaşım izni cevabın</td><td><span class="tag gone">Silinir</span> Paylaşım kapanır, uygulama tekrar sorar.</td></tr>
<tr><td>Health Connect'ten okunan adım, uyku, egzersiz ve su verisi</td><td><span class="tag gone">Hiç saklanmaz</span> Uygulama bu veriyi yalnızca o an okur. Health Connect'teki kendi verilerini Health Connect'ten yönetirsin.</td></tr>
<tr><td>Deneme başlangıç günü ve son satın alma durumu</td><td><span class="tag kept">Telefonda kalır</span> Denemenin yeniden başlamaması için; hiçbir yere gönderilmez ve uygulamayı kaldırınca silinir.</td></tr>
<tr><td>Daha önce gönderilmiş anonim kullanım verisi (yalnızca izin verdiysen)</td><td><span class="tag kept">Google'da kalır</span> Kimliğini taşımaz. Google Analytics for Firebase'de en çok 14 ay saklanır, sonra Google tarafından silinir. Bundan üretilen toplu sayılar (örneğin günlük kullanıcı sayısı) kalabilir.</td></tr>
<tr><td>Daha önce gönderilmiş çökme raporları (yalnızca izin verdiysen)</td><td><span class="tag kept">Google'da kalır</span> Firebase Crashlytics'te 90 gün saklanır, sonra silinir.</td></tr>
<tr><td>Zincir+ satın alımları</td><td><span class="tag kept">Google Play'de kalır</span> Satın alma ve sipariş kayıtları, ilgili mevzuatın öngördüğü süre boyunca Google Play'de ve Google hesabında tutulur. Satın alımın Google hesabına bağlıdır; uygulamayı yeniden kurduğunda geri gelir.</td></tr>
<tr><td>Google yedeği</td><td><span class="tag kept">Google hesabında kalır</span> Telefonunda Google yedeklemesi açıksa uygulama verisinin bir kopyası Google hesabında durur. Google Drive › Yedekler bölümünden silebilirsin.</td></tr>
<tr><td>Kendi kaydettiğin yedek dosyaları</td><td><span class="tag kept">Kaydettiğin yerde kalır</span> Bu dosyaları sen silersin.</td></tr>
</tbody>
</table>"""),
            ("Daha fazlası",
             """<p>Hangi verinin neden işlendiği <a href="{root}gizlilik/">Gizlilik Politikası ve KVKK Aydınlatma Metni</a>'nde yazar.</p>"""),
        ],
    },
    "en": {
        "title": "Zinciri Kırma: deleting your data",
        "desc": "How to delete your data in Zinciri Kırma (Bilgin Apps), what is deleted, what is kept and for how long.",
        "updated": "Updated: 21 October 2026",
        "sections": [
            ("No account; your data is on your phone",
             """<p><strong>Zinciri Kırma</strong> is developed by Erhan Bilgin, publishing as Bilgin Apps. The app has no accounts: no sign-up, sign-in, email or password. Your habits, history and notes are never sent to a server; they stay on your phone. So you don't need to ask us to delete them; you delete your data yourself, inside the app, at any time.</p>"""),
            ("Deleting in the app",
             """<ol class="steps">
<li>Open Zinciri Kırma and tap the <strong>Profile</strong> tab at the bottom.</li>
<li>Tap the gear at the top right to open <strong>Settings</strong>.</li>
<li>Under <strong>Privacy and data</strong>, tap <strong>Delete all my data</strong>.</li>
<li>Confirm with <strong>Delete everything</strong>.</li>
</ol>
<p>Deletion happens at once and cannot be undone. Uninstalling the app also deletes all of its data on the phone.</p>"""),
            ("Stopping sharing",
             """<p>If you allowed anonymous usage and crash data, turn off <strong>Share anonymous usage and crash data</strong> in the same section. From then on nothing new is sent, the analytics identifier on the phone is reset and crash reports not yet sent are deleted. "Delete all my data" turns this switch off too.</p>"""),
            ("Asking by email",
             f"""<p>If you can't reach the app (for example, you lost your phone) or something goes wrong, email <a href="mailto:{EMAIL}?subject=Data%20deletion%20request">{EMAIL}</a> with the subject "Data deletion request". We hold no account or personal data that identifies you, so we cannot delete the data on your phone remotely; we will answer your request within 30 days.</p>"""),
            ("What is deleted, what is kept?",
             """<table class="table">
<thead><tr><th>Data</th><th>What happens</th></tr></thead>
<tbody>
<tr><td>Habits and tasks, history (done and rest days, amounts), notes, categories, reminders, badges, your profile name and settings</td><td><span class="tag gone">Deleted</span> At once and permanently, from your phone.</td></tr>
<tr><td>Your answer to the sharing question</td><td><span class="tag gone">Deleted</span> Sharing turns off and the app asks again.</td></tr>
<tr><td>Steps, sleep, exercise and water read from Health Connect</td><td><span class="tag gone">Never stored</span> The app reads it only in the moment. You manage your own data in Health Connect itself.</td></tr>
<tr><td>Trial start day and last purchase status</td><td><span class="tag kept">Kept on the phone</span> So the trial doesn't start over; never sent anywhere, and deleted when you uninstall the app.</td></tr>
<tr><td>Anonymous usage data already sent (only if you allowed it)</td><td><span class="tag kept">Kept by Google</span> It does not identify you. Kept in Google Analytics for Firebase for up to 14 months, then deleted by Google. Aggregate numbers made from it (such as daily users) may remain.</td></tr>
<tr><td>Crash reports already sent (only if you allowed it)</td><td><span class="tag kept">Kept by Google</span> Kept in Firebase Crashlytics for 90 days, then deleted.</td></tr>
<tr><td>Zincir+ purchases</td><td><span class="tag kept">Kept by Google Play</span> Purchase and order records are kept by Google Play and in your Google account for the period the law requires. Your purchase belongs to your Google account and comes back when you reinstall the app.</td></tr>
<tr><td>Google backup</td><td><span class="tag kept">Kept in your Google account</span> If Google backup is on, a copy of the app's data is in your Google account. You can delete it in Google Drive › Backups.</td></tr>
<tr><td>Backup files you saved</td><td><span class="tag kept">Kept where you saved them</span> You delete these files yourself.</td></tr>
</tbody>
</table>"""),
            ("More",
             """<p>Which data is processed and why is set out in the <a href="{root}en/privacy/">Privacy Policy and KVKK Notice</a>.</p>"""),
        ],
    },
}


def delete_page(lang):
    d = DELETE[lang]
    t = T[lang]
    root = root_of(PATHS["delete"][lang])
    toc, blocks = [], []
    for heading, content in d["sections"]:
        hid = slug(heading)
        toc.append((hid, heading))
        blocks.append(f'<h2 id="{hid}">{html.escape(heading)}</h2>' + content.replace("{root}", root))
    other = t["other"]
    pills = [
        f'<span class="pill">{d["updated"]}</span>',
        f'<a class="pill" href="{root}{PATHS["delete"][other]}" hreflang="{other}">{t["other_label"]}</a>',
    ]
    return doc_page("delete", lang, d["title"], pills, None, blocks, toc, d["desc"])


# ---------- Not found ----------


def not_found():
    # Served from any depth, so its links are absolute to the site.
    base = BASE_URL.split("github.io", 1)[-1] if "github.io" in BASE_URL else "/"
    return f"""<!doctype html>
<html lang="tr">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Sayfa bulunamadı · Zinciri Kırma</title>
  <meta name="robots" content="noindex">
  <link rel="icon" type="image/png" href="{base}assets/icon-512.png">
  <link rel="stylesheet" href="{base}assets/site.css?v={version('site.css')}">
</head>
<body>
<main class="wrap lost">
  <div>
    <h1>Bu halka kopmuş.</h1>
    <p>Aradığın sayfa yok. · This page doesn't exist.</p>
    <a class="btn btn-primary" href="{base}">Ana sayfa</a>
    <a class="btn" href="{base}en/">Home</a>
  </div>
</main>
</body>
</html>
"""


# ---------- Build ----------


def write(path, text):
    target = OUT / path / "index.html" if not path.endswith(".html") else OUT / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8", newline="\n")


def copy_assets():
    assets = OUT / "assets"
    (assets / "fonts").mkdir(parents=True, exist_ok=True)
    for name in ("site.css", "site.js"):
        shutil.copy2(HERE / "assets" / name, assets / name)
    for font in ("bricolage_grotesque.ttf", "figtree.ttf"):
        shutil.copy2(FONTS / font, assets / "fonts" / font)
    # The OFL asks every copy of the fonts to travel with its licence, as the app's assets do.
    for licence in ("OFL-BricolageGrotesque.txt", "OFL-Figtree.txt"):
        shutil.copy2(LICENSES / licence, assets / "fonts" / licence)
    for lang in ("tr", "en"):
        (assets / "shots" / lang).mkdir(parents=True, exist_ok=True)
        for f, _ in T[lang]["shots"]:
            shutil.copy2(SHOTS / lang / f, assets / "shots" / lang / f)
    shutil.copy2(SHOTS / "simge-512.png", assets / "icon-512.png")
    shutil.copy2(SHOTS / "ozellik-grafigi-tr.png", assets / "og-tr.png")
    shutil.copy2(SHOTS / "feature-graphic-en.png", assets / "og-en.png")


def clean():
    """Removes the last build, so a page that is gone does not linger."""
    for entry in OUT.iterdir():
        if entry.name in KEEP:
            continue
        if entry.is_dir():
            shutil.rmtree(entry)
        else:
            entry.unlink()


def main():
    if not LEGAL.is_dir():
        raise SystemExit(f"The Android app is not at {ANDROID}; the site is built from its texts and images.")
    if not IOS_LEGAL.is_dir():
        raise SystemExit(f"The iOS app is not at {IOS_LEGAL.parent}; its legal texts are published here too.")
    clean()
    copy_assets()
    for lang in ("tr", "en"):
        write(PATHS["home"][lang], home(lang))
        write(PATHS["privacy"][lang], legal("privacy", lang))
        write(PATHS["terms"][lang], legal("terms", lang))
        write(PATHS["ios_privacy"][lang], legal("ios_privacy", lang))
        write(PATHS["ios_terms"][lang], legal("ios_terms", lang))
        write(PATHS["delete"][lang], delete_page(lang))
    write("404.html", not_found())
    (OUT / ".nojekyll").write_text("", encoding="utf-8")
    (OUT / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {BASE_URL}sitemap.xml\n", encoding="utf-8")
    urls = "".join(f"  <url><loc>{BASE_URL}{p[l]}</loc></url>\n" for p in PATHS.values() for l in ("tr", "en"))
    (OUT / "sitemap.xml").write_text(
        f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{urls}</urlset>\n',
        encoding="utf-8",
    )
    print(f"Built {sum(1 for _ in OUT.rglob('*.html'))} pages into {OUT}")


if __name__ == "__main__":
    main()
