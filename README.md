# MKS WiFi Plugin — Önizleme Düzeltmesi / Preview Fix

> 🖨️ **Bu proje 3D yazıcılar içindir / This is for 3D printers.**  
> **TR:** 3D yazıcılarda bilgisayardaki tasarımı yazıcıya göndermek için "dilimleyici" (slicer) yazılım kullanılır. Bu depo, **Ultimaker Cura** dilimleyicisi için yazılmış olan **MKS WiFi eklentisi**'ndeki bir hatayı düzeltir. Hata: yazıcının LCD ekranında **model önizleme resmi** (thumbnail) hiç görünmüyordu. Bu yamayla artık yazıcı ekranında hangi modeli bastığını görebilirsin.  
> **EN:** 3D printers use "slicer" software to prepare a design for printing. This repo fixes a bug in the **MKS WiFi Plugin** for the **Ultimaker Cura** slicer where the **preview thumbnail** never appeared on the printer's LCD screen. With this patch you can finally see which model is being printed on the printer's display.

> 🤖 **Vibe coding / AI-assisted — Açık Bildirim / Full Disclosure**  
> **TR:** Bu düzeltmedeki kök neden analizi, kod yamaları ve dökümantasyon **AI destekli "vibe coding"** ile üretildi (GitHub Copilot + Claude). İnsan (@hobibilgisi) sorunu tanımladı, testleri gerçek donanımda (MKS Robin Nano + Bluer) yaptı, sonuçları doğruladı. AI, kod aramasını, kok neden hipotezlerini ve yamaları yazdı.  
> **EN:** The root-cause analysis, code patches and documentation in this fix were produced through **AI-assisted "vibe coding"** (GitHub Copilot + Claude). A human (@hobibilgisi) defined the problem, ran the tests on real hardware (MKS Robin Nano + Bluer), and validated the results. The AI drove the code search, root-cause hypotheses and patch writing.

- [Türkçe](#türkçe)
- [English](#english)
- [Credits & License](#credits--license)

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

---

## Credits & License

Bu proje, aşağıdaki açık kaynak projeye dayanan **değiştirilmiş bir dağıtımdır** /
This project is a **modified redistribution** based on:

- **[MKS WiFi Plugin](https://github.com/PrintMakerLab/mks-wifi-plugin)** — © 2021 Makerbase, Jeredian, Elkin-Vasily — AGPL-3.0.

Bu depodaki tüm kod aynı **[AGPL-3.0](LICENSE)** lisansı altındadır /
All code in this repository is released under the same **[AGPL-3.0](LICENSE)** license.

Yapılan değişikliklerin ayrıntıları için / For full modification details see **[NOTICE.md](NOTICE.md)**.

> **Ticari Markalar / Trademarks**  
> "MKS", "MKS Robin Nano" — Makerbase; "Ultimaker Cura" — Ultimaker B.V.; "Marlin" — Marlin Firmware.  
> Bu isimler yalnızca uyumluluk açıklamak için (nominative use) kullanılmıştır.  
> **Bu proje Makerbase, Ultimaker ya da Marlin ile bağlantılı, sponsorlu veya onaylı DEĞİLDİR.**  
> These names are used only to describe compatibility (nominative use).  
> **This project is NOT affiliated with, sponsored by, or endorsed by Makerbase, Ultimaker, or Marlin.**

> **Sorumluluk Reddi / Disclaimer**  
> Yazılım "olduğu gibi" sunulmaktadır. Kullanıma bağlı olabilecek yazıcı arızası, veri kaybı vb. sorumluluğu kabul etmez.  
> Software is provided "AS IS", without warranty of any kind. Use at your own risk.
