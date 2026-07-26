# NOTICE

This project is a **modified redistribution** of the MKS WiFi Plugin for
Ultimaker Cura, released under the terms of the **GNU Affero General
Public License v3.0** (see [LICENSE](LICENSE)).

## Upstream project

- **Name:** MKS WiFi Plugin (MKS Plugin Connection)
- **Original repository:** https://github.com/PrintMakerLab/mks-wifi-plugin
- **Original authors:** Makerbase, Jeredian, Elkin-Vasily
- **Upstream license:** AGPL-3.0
- **Base version used in this fork:** `1.4.6-dev` (branch `master`)

The original copyright notice `# Copyright (c) 2021` is preserved in
every modified source file, as required by the license.

## Modifications made in this repository

Modified by **hobibilgisi** in **2026** to fix the missing LCD preview
thumbnail on Ultimaker Cura 5.13.0. Details:

> **AI-assisted development disclosure**  
> The root-cause analysis, code patches and documentation were produced
> through **AI-assisted "vibe coding"** (GitHub Copilot + Claude). The
> human contributor defined the problem, ran the tests on real hardware
> (MKS Robin Nano + Marlin 2.0 Bluer variant, Chitu 480×320 LCD), and
> validated every result. The AI drove code search, root-cause hypotheses
> and patch generation.

| File | Change |
| --- | --- |
| `MKSWifiPlugin/MKSPreview.py` | New fallback chain in `take_screenshot()` (`snapshot` → `isometricSnapshot` → `backend.getLatestSnapshot`); sensible defaults in `generate_preview()`; debug logging in `add_preview()`. |
| `MKSWifiPlugin/MKSOutputDevice.py` | Direct call to `MKSPreview.add_preview(self)` inside `requestWrite()` so WiFi uploads inject the preview too. |
| `MKSWifiPlugin/MKSOutputDevicePlugin.py` | Lazy monkey-patch of `GCodeWriter.write` as a belt-and-suspenders injection path. |

Full technical breakdown: [README_DETAILED.md](README_DETAILED.md) and
[PATCH_NOTES.md](PATCH_NOTES.md).

## Trademarks

- **"MKS"** and **"MKS Robin Nano"** are trademarks of **Makerbase / MakerBase**.
- **"Ultimaker Cura"** is a trademark of **Ultimaker B.V.**
- **"Marlin"** is a trademark of the Marlin Firmware project.

These names are used here solely to describe the software this project is
compatible with (nominative fair use). **This project is not affiliated
with, sponsored by, or endorsed by any of the above parties.**

## No warranty

As stated in the AGPL-3.0 license, this software is provided "AS IS",
without warranty of any kind. Use at your own risk. The author is not
liable for any damage to your 3D printer, computer, or workflow.
