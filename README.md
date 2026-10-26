# Zinciri Kırma web sitesi

GitHub Pages'te yayınlanan tanıtım sitesi: Türkçe ve İngilizce ana sayfa, gizlilik politikası, kullanım koşulları, Google Play'in "Hesap silme URL'si" alanına verilen veri silme sayfası ve iOS uygulamasının kendi gizlilik politikası ve kullanım koşulları (`ios/gizlilik/`, `ios/kosullar/`; App Store Connect'e bunlar verilir).

Adres: https://bilginapplabs.github.io/zinciri-kirma.github.io/ (GitHub › Settings › Pages › "Deploy from a branch" › `main` / `(root)`).

## Depo

- Kök klasör yayınlanan sitenin kendisidir: `index.html`, `en/`, `gizlilik/`, `kosullar/`, `veri-silme/`, `assets/` ve diğerleri. Bunları elle düzenleme; üretici yazar.
- `kaynak/`: siteyi üreten `build.py` ve sitenin stil ve betik dosyaları.

Site, yanındaki Android deposundan üretilir:

```
HabitChain/
  android/   Android uygulaması (yasal metinler, mağaza görselleri, yazı tipleri)
  ios/       iOS uygulaması
  website/   bu depo
```

## Üretmek

```bash
python kaynak/build.py
```

Komut, kökteki eski sayfaları silip siteyi baştan yazar. `.git`, `kaynak/` ve bu README'ye dokunmaz. Ardından değişiklikleri commit edip `main` dalına push'la; GitHub Pages birkaç dakikada yayınlar.

- **Yasal metinler** `../android/app/src/main/assets/legal/*.md` ve iOS için `../ios/legal/*.md` dosyalarından üretilir; uygulamalardaki metinle site hep aynıdır. Metin değişince siteyi yeniden üret ve yayınla.
- **App Store:** iOS uygulaması yayınlanana kadar ana sayfada "Yakında App Store'da" yazar. Yayınlanınca `build.py` içindeki `APP_STORE_URL`'yi uygulamanın App Store adresiyle doldur; rozet ve alt bilgideki satır bağlantıya döner.
- **Görseller** `../android/docs/play/gorseller/` klasöründen, yazı tipleri ve lisansları `../android/app/src/main/` altından kopyalanır.
- **Ana sayfa ve veri silme sayfasının metinleri** `kaynak/build.py` içindedir (`T` ve `DELETE`). Bir metin değişirse iki dilde de değiştir.
- `BASE_URL`, sitenin yayınlandığı adrestir (paylaşım önizlemesi, canonical ve hreflang bağlantıları için). Repo adı ya da alan adı değişirse güncelle.
- Site çerez, analiz ya da dış kaynak kullanmaz (yazı tipleri de sitenin içinden yüklenir).

Yerelde bakmak için:

```bash
python -m http.server 8765
```

## Adresler

| Sayfa | Türkçe | İngilizce |
|---|---|---|
| Ana sayfa | `/` | `/en/` |
| Gizlilik Politikası | `/gizlilik/` | `/en/privacy/` |
| Kullanım Koşulları | `/kosullar/` | `/en/terms/` |
| Veri silme | `/veri-silme/` | `/en/delete-data/` |

Play Console'da: gizlilik politikası URL'si `.../gizlilik/`, hesap silme URL'si `.../veri-silme/`.
