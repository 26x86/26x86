# Tahoe SkyLight & WindowServer LUT Research

Deep technical analysis of the RenderBox compositor engine and SkyLight color transformation matrices in macOS 26 Tahoe.

## Architecture

Modern WindowServer instances composite surfaces in wide-gamut linear spaces before passing framebuffers to CoreDisplay. On older display pipelines lacking hardware HDR tone mapping, incorrect EOTF gamma curves produce noticeable yellow/amber saturation.
