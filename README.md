# MKS WiFi Plugin — Önizleme Düzeltmesi / Preview Fix

- [Türkçe](#türkçe)
- [English](#english)

---

## Türkçe

**Ne işe yarıyor?**  
Cura 5.13 ile MKS WiFi eklentisi kullandığında, yazıcının ekranında dosya adı görünüyor ama küçük model resmi (thumbnail) çıkmıyordu. Bu yama onu düzeltir — hem SD karta kayıtta hem WiFi ile gönderdiğinde resim görünür.

**Uyumlu sürümler**
- Ultimaker Cura **5.13.0**
- MKS WiFi Plugin **v1.4.6-dev** (PrintMakerLab)
- MKS Robin Nano v1.x + Marlin 2.0 (Bluer / Blue Whale)

**Nasıl kurulur? (3 adım)**
1. Cura'yı **tamamen kapat**.
2. Klavyeden `Win + R` → `%APPDATA%\cura\5.13\plugins\` yaz → Enter.  
   Açılan klasörde daha önceki `MKSWifiPlugin` klasörü varsa **sil ya da yedekle**.
3. Bu depodaki **`MKSWifiPlugin`** klasörünü olduğu gibi oraya kopyala.

Sonra Cura'yı aç, model dilimle, kaydet veya WiFi ile gönder. Yazıcı ekranında önizleme resmi görünecek.

> **Not:** Cura Marketplace'ten ayrıca kurmana gerek yok — bu klasör tam plugin'i (v1.4.6-dev + önizleme düzeltmesi) içerir.

**Sorun olursa:** [Detaylı README](README_DETAILED.md) → "Quick self-check" bölümüne bak.

---

## English

**What does it do?**  
When using the MKS WiFi plugin with Cura 5.13, the printer's LCD showed only the file name — the model thumbnail was missing. This patch fixes it: the preview appears both on SD-card saves and WiFi uploads.

**Compatible versions**
- Ultimaker Cura **5.13.0**
- MKS WiFi Plugin **v1.4.6-dev** (PrintMakerLab)
- MKS Robin Nano v1.x + Marlin 2.0 (Bluer / Blue Whale)

**How to install (3 steps)**
1. **Fully close** Cura.
2. Press `Win + R` → type `%APPDATA%\cura\5.13\plugins\` → Enter.  
   If a previous `MKSWifiPlugin` folder exists there, **delete or back it up**.
3. Copy the **`MKSWifiPlugin`** folder from this repo into that location as-is.

Start Cura, slice a model, save or send over WiFi. The preview will appear on the printer's LCD.

> **Note:** You do **not** need to install anything from the Cura Marketplace — this folder already contains the full plugin (v1.4.6-dev + preview fix).

**If something goes wrong:** see [detailed README](README_DETAILED.md) → "Quick self-check".
