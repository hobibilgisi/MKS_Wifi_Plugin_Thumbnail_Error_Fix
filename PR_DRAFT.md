# Pull Request Draft (copy/paste to GitHub)

## Title

`Fix: LCD preview thumbnail never written on Cura 5.13 (SD save + WiFi upload)`

## Summary

The MKS preview block (`;simage:` / `;;gimage:`) is silently skipped on
**Cura 5.13** for both local save and WiFi upload paths. Root cause is
`cura.Snapshot.snapshot()` returning `None` after its 10‑attempt retry
loop, compounded by two secondary issues in the plugin. This PR fixes
all three defects with minimal, isolated changes.

## Reproduction (before this PR)

1. Cura 5.13.0, MKS WiFi Plugin `master`.
2. Any printer profile (tested MKS Robin Nano + Bluer/Blue Whale firmware).
3. Slice → Save to File or Print over WiFi.
4. Open the produced gcode → **no `;simage:` block**.
5. Printer LCD shows only file name, no thumbnail.

Cura log contains:
```
WARNING - cura.Snapshot.snapshot [200]: Failed to crop the snapshot even after 10 attempts!
DEBUG   - MKSWifiPlugin.MKSPreview.add_preview: Skipping adding screenshot
```

## Root cause

Four cascading defects — all four need to be addressed for the LCD
thumbnail to appear reliably:

1. **`cura.Snapshot.snapshot()` returns `None` on Cura 5.13** — OpenGL/QQuickView
   timing issue. `add_preview` bails out immediately.
2. **`CuraEngineBackend.getLatestSnapshot()` uses the same broken code** —
   not a valid fallback on its own.
3. **`MKSOutputDevice.requestWrite` only fires its own `writeStarted` signal**,
   not the `OutputDeviceManager.writeStarted` the plugin is subscribed to.
   Therefore `add_preview` is never called on the WiFi path.
4. **`mks_simage` / `mks_gimage` default to `0`** for profiles that don't
   declare them, producing an empty preview even when the snapshot succeeds.

## Changes

- **`MKSPreview.take_screenshot()`** — new fallback chain
  `snapshot → isometricSnapshot → backend.getLatestSnapshot`.
  `Snapshot.isometricSnapshot()` builds its own offscreen renderer and is
  independent of viewport state, so it works reliably on Cura 5.13.
- **`MKSPreview.generate_preview()`** — defaults `simage=100, gimage=200`
  (Chitu 480×320 LCD compatible) when the profile does not declare them or
  provides non-positive values.
- **`MKSOutputDevice.requestWrite()`** — direct `MKSPreview.add_preview(self)`
  call right after `self.writeStarted.emit(self)` so WiFi uploads inject
  the preview too.
- **`MKSOutputDevicePlugin`** — belt-and-suspenders monkey-patch on the
  resolved `GCodeWriter` instance that writes the preview block into the
  outgoing stream even if the `writeStarted → add_preview` path is ever
  bypassed by upstream changes.

## Verification

Cura log after the fix:
```
DEBUG - MKSWifiPlugin.MKSPreview.take_screenshot: MKS: using Snapshot.isometricSnapshot fallback
DEBUG - MKSWifiPlugin.MKSPreview.add_preview: plate 0 modified, new item[0] len=203022, starts with: ;simage:...
```

Produced gcode begins with:
```
;simage:0000...
;;gimage:0000...
;MKSPREVIEWPROCESSED
; Postprocessed by [MKS WiFi plugin]...
; simage=100
; gimage=200
```

Confirmed on real hardware: **thumbnail visible on the printer's LCD**
(MKS Robin Nano v1.x + Marlin 2.0 Bluer variant, Chitu 480×320 screen).

## Compatibility

- No breaking changes to public API.
- All fallbacks are guarded with `hasattr` / try/except and no-op on
  older Cura versions where `isometricSnapshot` is unavailable — behavior
  reverts to upstream in that case.
- No new dependencies.

## Files touched

- `MKSWifiPlugin/MKSPreview.py`
- `MKSWifiPlugin/MKSOutputDevice.py`
- `MKSWifiPlugin/MKSOutputDevicePlugin.py`

## Tested with

- OS: Windows 10/11
- Cura: 5.13.0
- Plugin base: v1.4.6-dev (`master` @ 2026-07-27)
- Printer: MKS Robin Nano v1.x (Blue Whale / Bluer Marlin 2.0 variant)
