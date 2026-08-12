#!/usr/bin/env bash
# Optimize plugin page images for weak networks: WebP/AVIF + multiple widths, fallback PNG.
set -e
cd "$(dirname "$0")/.."
ASSETS="assets"
TMP="/tmp/nekodeck-img"
mkdir -p "$TMP"

WEBP_Q=82
AVIF_Q=70

# Hero: 400w, 800w, 1200w (hero max-width 800px in CSS, 1.5x retina)
echo "Optimizing hero-banner..."
for W in 400 800 1200; do
  sips -Z "$W" "$ASSETS/hero-banner.png" -o "$TMP/hero-$W.png"
  cwebp -q $WEBP_Q "$TMP/hero-$W.png" -o "$ASSETS/hero-banner-${W}w.webp"
  avifenc -q $AVIF_Q -s 4 "$TMP/hero-$W.png" "$ASSETS/hero-banner-${W}w.avif"
done
# Fallback PNG (single size for old browsers)
cp "$TMP/hero-800.png" "$ASSETS/hero-banner-800w.png"

# Feature icons: 128w, 256w (display 64px, 2x = 128)
for name in import toggle tun kill-switch; do
  echo "Optimizing features/$name..."
  for W in 128 256; do
    sips -Z "$W" "$ASSETS/features/$name.png" -o "$TMP/feat-$name-$W.png"
    cwebp -q $WEBP_Q "$TMP/feat-$name-$W.png" -o "$ASSETS/features/$name-${W}w.webp"
    avifenc -q $AVIF_Q -s 4 "$TMP/feat-$name-$W.png" "$ASSETS/features/$name-${W}w.avif"
  done
  cp "$TMP/feat-$name-256.png" "$ASSETS/features/$name-256w.png"
done

rm -rf "$TMP"
echo "Done. Optimized files in $ASSETS/"
