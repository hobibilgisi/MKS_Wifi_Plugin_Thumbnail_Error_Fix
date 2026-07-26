# MKS WiFi Plugin — Preview Thumbnail Fix (Cura 5.13)

> **TL;DR** — In Cura 5.13 the MKS WiFi plugin fails to inject the LCD preview
> block (`;simage:` / `;;gimage:`) because `cura.Snapshot.snapshot()` reliably
> returns `None`. Falling back to `Snapshot.isometricSnapshot()` fixes it.
> The WiFi upload path also needs a direct call to `add_preview` because
> `MKSOutputDevice.requestWrite` does not fire the manager-level
> `writeStarted` signal.

- [English](#english)
- [Türkçe](#türkçe)
- [Files changed](#files-changed)
- [How to apply](#how-to-apply)

---

## English

### Problem

Using **MKS WiFi Plugin v1.4.6-dev** with **Ultimaker Cura 5.13.0**, the
firmware preview thumbnail (`;simage:` / `;;gimage:` header block used by
MKS Robin Nano and similar boards) is **never written** into the gcode file,
whether the user hits **Save to File** or **Print over WiFi**. The printer's
LCD only shows the file name, never the model preview.

### Root Causes

Four defects layer on top of each other. Any single one of them alone is
enough to break preview injection.

#### 1. WiFi path never triggers preview generation

The plugin subscribes to `OutputDeviceManager.writeStarted` in
`MKSOutputDevicePlugin.__init__`:

```python
Application.getInstance().getOutputDeviceManager().writeStarted.connect(MKSPreview.add_preview)
```

But `MKSOutputDevice.requestWrite` (the WiFi upload path) only fires its
**own** `self.writeStarted`, not the manager's signal. So `add_preview` is
never called when uploading over WiFi.

Cura's built-in `LocalFileOutputDevice._performWrite` **does** raise the
manager signal, which is why local "Save to File" appears to work — but see
defect #4, it still fails silently.

#### 2. `mks_simage` / `mks_gimage` default to `0`

For printer profiles that do not define `mks_simage` / `mks_gimage`
container settings (many community profiles including Bluer / Blue Whale),
`GlobalContainerStack.getMetaDataEntry` returns `None`. The original code
does `int(...)` on that, effectively producing `0`, and then encodes a
zero-sized image — an empty string. Nothing appears on the printer.

#### 3. `gcode_dict` mutation reaches the file only for the local writer

For SD card / local writes, `GCodeWriter.write` re-reads `scene.gcode_dict`,
so mutating it in `add_preview` propagates. For the WiFi path the network
uploader may serialize the gcode from a different source. Belt-and-suspenders:
we also monkey-patch `GCodeWriter.write` to prepend the preview to the
outgoing stream directly.

#### 4. **`cura.Snapshot.snapshot()` returns `None` — the actual show-stopper**

This is the real root cause. Cura 5.13 has an OpenGL / QQuickView timing
issue where `Snapshot.snapshot()` fails to crop a valid image and, after 10
retries, gives up:

```
WARNING - cura.Snapshot.snapshot [200]: Failed to crop the snapshot even after 10 attempts!
```

Once `take_screenshot()` returns `None`, `add_preview` bails out with
`Skipping adding screenshot` and nothing is injected.

The obvious fallback `CuraEngineBackend.getLatestSnapshot()` **does not
help** because it internally uses the same broken `Snapshot.snapshot()`.

**The fix**: use `Snapshot.isometricSnapshot()` instead. It is a completely
separate code path in `cura/Snapshot.py` that builds its own `Camera`,
`PreviewPass`, and `QtRenderer`, computes bounds from the scene root, and
does an offscreen isometric render. It does not depend on the live viewport
being renderable, so it works every time there is a model on the plate.

### Fix Summary

| Where | Change |
| --- | --- |
| `MKSPreview.take_screenshot()` | Fallback chain: `snapshot` → `isometricSnapshot` → `backend.getLatestSnapshot` |
| `MKSPreview.generate_preview()` | Default `simage=100`, `gimage=200` for profiles that don't define them; clamp non-positive to defaults |
| `MKSOutputDevice.requestWrite()` | Directly call `MKSPreview.add_preview(self)` after `self.writeStarted.emit(self)` so WiFi uploads get preview too |
| `MKSOutputDevicePlugin` | Belt-and-suspenders monkey-patch of `GCodeWriter.write` to prepend preview to the outgoing stream, uses shared `take_screenshot()` |

### Verified environment

- Windows 10/11
- Ultimaker Cura **5.13.0**
- MKS WiFi Plugin **v1.4.6-dev** (branch `master` of PrintMakerLab)
- Printer: MKS Robin Nano v1.x running Marlin 2.0 (Blue Whale / Bluer variant), Chitu 480×320 LCD

---

## Türkçe

### Sorun

**Cura 5.13.0** ile **MKS WiFi Plugin v1.4.6-dev** kullanılırken, yazıcının
LCD ekranında model önizlemesini gösteren `;simage:` / `;;gimage:` başlık
bloğu **hiçbir zaman** gcode dosyasına yazılmıyor. Ne "Save to File" ne de
"Print over WiFi" işe yarıyor — yazıcı ekranında sadece dosya adı görünüyor,
model resmi asla çıkmıyor.

### Kök nedenler

Dört ayrı kusur üst üste biniyor. Herhangi biri tek başına önizlemeyi bozmaya
yeter.

#### 1. WiFi yolu önizleme üretimini hiç tetiklemiyor

Plugin başlangıçta şuna abone oluyor:

```python
Application.getInstance().getOutputDeviceManager().writeStarted.connect(MKSPreview.add_preview)
```

Ama `MKSOutputDevice.requestWrite` (WiFi yükleme yolu) **kendi**
`self.writeStarted` sinyalini yayıyor, manager sinyalini değil. Bu yüzden
WiFi ile gönderirken `add_preview` **hiçbir zaman** çağrılmıyor.

Cura'nın yerleşik `LocalFileOutputDevice._performWrite` fonksiyonu manager
sinyalini yayıyor, o yüzden yerel kayıt çalışıyormuş gibi görünüyor — ama
4. kusur nedeniyle o da sessizce başarısız oluyor.

#### 2. `mks_simage` / `mks_gimage` varsayılan olarak `0`

`mks_simage` / `mks_gimage` container ayarlarını tanımlamayan yazıcı
profillerinde (Bluer / Mavi Balina dahil pek çok topluluk profili),
`getMetaDataEntry` `None` döndürüyor. Orijinal kod bunu `int(...)` ile
sarıyor ve `0` üretiyor, ardından 0 boyutlu görüntü kodluyor — boş string.
Yazıcıda hiçbir şey görünmüyor.

#### 3. `gcode_dict` mutasyonu WiFi yolunda dosyaya ulaşmıyor

SD/yerel yazımda `GCodeWriter.write` `scene.gcode_dict`'i yeniden okuyor,
o yüzden `add_preview`'daki değişiklik yayılıyor. WiFi yolunda ise ağ
uploader'ı gcode'u farklı bir kaynaktan serileştirebiliyor. Belt-and-
suspenders (kemer + pantolon askısı) prensibi: `GCodeWriter.write`'ı
monkey-patch ederek önizlemeyi doğrudan giden stream'e ekliyoruz.

#### 4. **`cura.Snapshot.snapshot()` `None` döndürüyor — asıl felaket**

Gerçek kök neden bu. Cura 5.13'te bir OpenGL / QQuickView zamanlama sorunu
var; `Snapshot.snapshot()` geçerli bir görüntü kırpamıyor ve 10 denemeden
sonra pes ediyor:

```
WARNING - cura.Snapshot.snapshot [200]: Failed to crop the snapshot even after 10 attempts!
```

`take_screenshot()` `None` dönünce `add_preview` `Skipping adding screenshot`
diyor ve hiçbir şey enjekte etmiyor.

Bariz fallback olan `CuraEngineBackend.getLatestSnapshot()` **işe yaramıyor**
çünkü o da içeride aynı bozuk `Snapshot.snapshot()`'ı çağırıyor.

**Çözüm**: yerine `Snapshot.isometricSnapshot()` kullanmak. Bu, `cura/Snapshot.py`
içinde **tamamen ayrı** bir kod yolu — kendi `Camera`, `PreviewPass` ve
`QtRenderer`'ını kuruyor, sahne bounds'ından izometrik açı hesaplayıp
offscreen render yapıyor. Canlı viewport'un renderable olmasına bağımlı
değil, tabla üzerinde model varsa her seferinde çalışıyor.

### Düzeltme özeti

| Yer | Değişiklik |
| --- | --- |
| `MKSPreview.take_screenshot()` | Fallback zinciri: `snapshot` → `isometricSnapshot` → `backend.getLatestSnapshot` |
| `MKSPreview.generate_preview()` | Tanımsız profiller için `simage=100`, `gimage=200` varsayılanları; ≤0 değerleri varsayılana çekiliyor |
| `MKSOutputDevice.requestWrite()` | `self.writeStarted.emit(self)` sonrasında doğrudan `MKSPreview.add_preview(self)` çağrısı — WiFi yüklemelerinde de önizleme üretilsin diye |
| `MKSOutputDevicePlugin` | `GCodeWriter.write` monkey-patch (yedek yol), ortak `take_screenshot()` kullanıyor |

### Doğrulanan ortam

- Windows 10/11
- Ultimaker Cura **5.13.0**
- MKS WiFi Plugin **v1.4.6-dev** (PrintMakerLab'in `master` dalı)
- Yazıcı: MKS Robin Nano v1.x + Marlin 2.0 (Blue Whale / Bluer varyantı), Chitu 480×320 LCD

---

## Files changed

Three files inside `MKSWifiPlugin/`:

1. **`MKSPreview.py`** — new `take_screenshot()` fallback chain; default sizes in `generate_preview()`; debug logging in `add_preview()`.
2. **`MKSOutputDevice.py`** — extra `MKSPreview.add_preview(self)` call inside `requestWrite()` for the WiFi path.
3. **`MKSOutputDevicePlugin.py`** — `_serhat_install_gcodewriter_patch()` monkey-patch for `GCodeWriter.write`, wired lazily via `writeStarted`.

See [PATCH_NOTES.md](PATCH_NOTES.md) for the concrete code snippets ready to
paste over the upstream source.

## How to apply

### Easiest — drop-in the pre-patched plugin folder (recommended for end users)

1. Close Cura completely.
2. Open `%APPDATA%\cura\5.13\plugins\` (`Win + R` → paste that path → Enter).
3. If a `MKSWifiPlugin` folder already exists there, delete or back it up.
4. Copy the [`MKSWifiPlugin/`](MKSWifiPlugin) folder from this repository
   into that location as-is. The result must be:
   ```
   %APPDATA%\cura\5.13\plugins\MKSWifiPlugin\MKSWifiPlugin\__init__.py
   %APPDATA%\cura\5.13\plugins\MKSWifiPlugin\MKSWifiPlugin\MKSPreview.py
   ...
   ```
5. Start Cura. Load a model, slice, then **Save to File** or **Print over WiFi**.

You do **not** need to install the plugin from the Cura Marketplace first —
this folder is the full v1.4.6-dev plugin plus the preview fix.

### Manual (for developers / small patch only)

If you already have the plugin installed and want the smallest possible
diff, use the three files under [`patched-files/`](patched-files) to
overwrite the corresponding files in your existing plugin folder:

1. Close Cura.
2. Back up `%APPDATA%\cura\5.13\plugins\MKSWifiPlugin\MKSWifiPlugin\`.
3. Copy the three files from `patched-files/` over the same-named files.
4. Start Cura.

Note: this method assumes your installed version is compatible with the
v1.4.6-dev API. If your marketplace-installed version is older (e.g.
v1.4.5), prefer the drop-in method above.

### Quick self-check

Open `%APPDATA%\cura\5.13\cura.log` and search for:

- `MKS SERHAT: using Snapshot.isometricSnapshot fallback` — confirms the fallback fired.
- `SERHAT: plate 0 modified, new item[0] len=…, starts with: ;simage:` — confirms the gcode dict got updated.

If neither line appears but `Failed to crop the snapshot even after 10 attempts!`
does, the patch was not loaded (Cura still using unpatched plugin — verify
file path and restart Cura).

## License

The MKS WiFi Plugin is AGPLv3. All patches in this folder are provided under
the same license, ready to be upstreamed as a pull request to
[PrintMakerLab/mks-wifi-plugin](https://github.com/PrintMakerLab/mks-wifi-plugin).
