# Patch Notes — MKS WiFi Plugin Preview Fix

Concrete diffs against upstream **PrintMakerLab/mks-wifi-plugin `master`**
(commit as of 2026‑07‑27). Copy/paste ready.

---

## 1. `MKSWifiPlugin/MKSPreview.py`

### 1.a — Replace `take_screenshot()`

**Old** (single line, fails silently in Cura 5.13):

```python
def take_screenshot():
    # param width: width of the aspect ratio default 300
    # param height: height of the aspect ratio default 300
    # return: None when there is no model on the build plate otherwise it will return an image
    return Snapshot.snapshot(width = 900, height = 900)
```

**New** — fallback chain that survives the Cura 5.13 snapshot bug:

```python
def take_screenshot():
    # Cura 5.13's Snapshot.snapshot() often returns None due to an OpenGL
    # timing bug ("Failed to crop the snapshot even after 10 attempts!").
    # Fall back to isometricSnapshot (independent code path, no viewport
    # dependency) and finally to the backend's cached snapshot.
    img = None
    try:
        img = Snapshot.snapshot(width=900, height=900)
    except Exception as e:
        Logger.log("w", "MKS: Snapshot.snapshot failed: " + str(e))
    if img is None:
        try:
            if hasattr(Snapshot, "isometricSnapshot"):
                img = Snapshot.isometricSnapshot(width=900, height=900)
                if img is not None:
                    Logger.log("d", "MKS: using Snapshot.isometricSnapshot fallback")
        except Exception as e:
            Logger.log("w", "MKS: Snapshot.isometricSnapshot failed: " + str(e))
    if img is None:
        try:
            backend = Application.getInstance().getBackend()
            if backend is not None and hasattr(backend, "getLatestSnapshot"):
                img = backend.getLatestSnapshot()
                if img is not None:
                    Logger.log("d", "MKS: using CuraEngineBackend.getLatestSnapshot fallback")
        except Exception as e:
            Logger.log("w", "MKS: backend snapshot fallback failed: " + str(e))
    if img is None:
        Logger.log("w", "MKS: no snapshot available (snapshot, isometricSnapshot, backend all failed)")
    return img
```

### 1.b — Harden `generate_preview()` defaults

Change the head of `generate_preview` so unset / non-positive `simage` and
`gimage` values do not silently become zero-sized images.

**Old**:

```python
def generate_preview(global_container_stack, image):
    screenshot_string = ""
    simage = 0
    gimage = 0
    meta_data = global_container_stack.getMetaData()
    Logger.log("d", "Get current preview settings.")
    encoded = False
    if Constants.IS_PREVIEW_ENCODED in meta_data:
        encoded = True
    if Constants.SIMAGE in meta_data:
        simage = int(global_container_stack.getMetaDataEntry(Constants.SIMAGE))
    if Constants.GIMAGE in meta_data:
        gimage = int(global_container_stack.getMetaDataEntry(Constants.GIMAGE))
```

**New** (sensible defaults matching a Chitu 480×320 LCD):

```python
def generate_preview(global_container_stack, image):
    screenshot_string = ""
    # Default fallback sizes so preview is always emitted even for community
    # profiles that don't declare mks_simage / mks_gimage.
    simage = 100
    gimage = 200
    meta_data = global_container_stack.getMetaData()
    Logger.log("d", "Get current preview settings.")
    encoded = False
    if Constants.IS_PREVIEW_ENCODED in meta_data:
        encoded = True
    if Constants.SIMAGE in meta_data:
        try:
            simage = int(global_container_stack.getMetaDataEntry(Constants.SIMAGE))
            if simage <= 0:
                simage = 100
        except (ValueError, TypeError):
            simage = 100
    if Constants.GIMAGE in meta_data:
        try:
            gimage = int(global_container_stack.getMetaDataEntry(Constants.GIMAGE))
            if gimage <= 0:
                gimage = 200
        except (ValueError, TypeError):
            gimage = 200
```

---

## 2. `MKSWifiPlugin/MKSOutputDevice.py`

Inside `requestWrite`, immediately after the existing
`self.writeStarted.emit(self)` line, add a direct call to
`MKSPreview.add_preview`:

**Old**:

```python
def requestWrite(self,
                 node,
                 file_name=None,
                 filter_by_machine=False,
                 file_handler=None,
                 **kwargs):
    self.writeStarted.emit(self)
    self._update_timer.stop()
    self._isSending = True
```

**New**:

```python
def requestWrite(self,
                 node,
                 file_name=None,
                 filter_by_machine=False,
                 file_handler=None,
                 **kwargs):
    self.writeStarted.emit(self)
    # OutputDeviceManager.writeStarted does not fire on the WiFi upload path,
    # so call add_preview directly to guarantee ;simage / ;;gimage headers
    # are injected before the gcode is uploaded.
    try:
        MKSPreview.add_preview(self)
    except Exception as e:
        Logger.log("w", "MKSPreview.add_preview failed on WiFi path: " + str(e))
    self._update_timer.stop()
    self._isSending = True
```

Also make sure the import exists at the top of the file:

```python
from . import MKSPreview
```

---

## 3. `MKSWifiPlugin/MKSOutputDevicePlugin.py` (optional belt-and-suspenders)

Adds a monkey-patch on the resolved `GCodeWriter` instance so that even if
the `writeStarted` → `add_preview` path is bypassed by some future Cura
change, the preview still gets injected directly into the output stream.

Add near the top of the module, after imports:

```python
def _install_gcodewriter_patch():
    """Monkey-patch the actual GCodeWriter instance Cura uses for
    text/x-gcode so the MKS preview is injected into the outgoing stream."""
    try:
        from UM.Application import Application as _App
        handler = _App.getInstance().getMeshFileHandler()
        writer = None
        for tid in ("text/x-gcode", "application/x-gcode", "text/gcode"):
            try:
                w = handler.getWriter(tid)
                if w is not None:
                    writer = w
                    break
            except Exception:
                pass
        if writer is None:
            try:
                for mime, w in handler._writers.items():
                    if "gcode" in str(mime).lower():
                        writer = w
                        break
            except Exception:
                pass
        if writer is None:
            Logger.log("w", "MKS: could not locate GCodeWriter instance to patch")
            return

        cls = writer.__class__
        if getattr(cls, "_mks_patched", False):
            return

        _orig_write = cls.write

        def _patched_write(self, stream, nodes, mode=None, **kwargs):
            try:
                gcs = _App.getInstance().getGlobalContainerStack()
                image = MKSPreview.take_screenshot()
                if gcs is not None and image is not None:
                    _simage, _gimage, screenshot_string = MKSPreview.generate_preview(gcs, image)
                    if screenshot_string:
                        stream.write(screenshot_string)
                        stream.write(";MKSPREVIEWPROCESSED\n")
                        stream.write("; Postprocessed by [MKS WiFi plugin](https://github.com/PrintMakerLab/mks-wifi-plugin)\n")
                        stream.write("; simage=%d\n" % _simage)
                        stream.write("; gimage=%d\n" % _gimage)
            except Exception as e:
                Logger.log("w", "MKS: preview injection failed: " + str(e))
            if mode is None:
                return _orig_write(self, stream, nodes, **kwargs)
            return _orig_write(self, stream, nodes, mode, **kwargs)

        cls.write = _patched_write
        cls._mks_patched = True
        Logger.log("d", "MKS: patched %s.write" % cls.__name__)
    except Exception as e:
        Logger.log("w", "MKS: install gcode-writer patch failed: " + str(e))
```

Then in `MKSOutputDevicePlugin.__init__`, right after the existing
`writeStarted.connect(MKSPreview.add_preview)` line, add:

```python
# Belt-and-suspenders: install GCodeWriter monkey-patch lazily on the
# first write so all plugins are guaranteed to be loaded.
Application.getInstance().getOutputDeviceManager().writeStarted.connect(
    lambda _dev: _install_gcodewriter_patch())
```

---

## Verification checklist

After applying the patches and restarting Cura:

1. Load a model, slice, then **File → Save to File** as `test.gcode`.
2. Open `test.gcode` in a text editor. First lines must contain, in order:
   ```
   ;simage:...
   ;;gimage:...
   ;MKSPREVIEWPROCESSED
   ; Postprocessed by [MKS WiFi plugin]...
   ; simage=100
   ; gimage=200
   ```
3. Open `%APPDATA%\cura\5.13\cura.log` and search for
   `using Snapshot.isometricSnapshot fallback`. Its presence confirms the
   fallback fired (and therefore the root fix is doing the work).
4. Send the same file over WiFi. LCD must show the model preview thumbnail
   next to the file name.
