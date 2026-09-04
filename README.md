# Monitor Titik Panas Kabupaten Berau

Dashboard publik yang memantau sebaran titik panas (hotspot) di Kabupaten Berau, disaring dari data satelit BMKG Wilayah III Kalimantan Timur. Dibangun sebagai proyek portofolio profil lulusan **Data Analyst**: analisis deskriptif dan komunikasi temuan dari data yang bersumber otomatis.

Live: `https://<username>.github.io/<nama-repo>/` (isi setelah deploy)

## Sumber data

`https://kaltim.bmkg.go.id/api/koordinat-hotspot` — mengembalikan seluruh titik panas se-Kalimantan Timur hasil deteksi satelit (Himawari/VIIRS-MODIS via SNPP & NOAA20), lengkap dengan `kabupaten` dan `kecamatan`. Scraper menyaring baris dengan `kabupaten == "BERAU"` saja.

## Struktur

```
scripts/scrape.py         # fetch API -> filter Berau -> tulis data/
data/latest.json          # snapshot titik panas Berau terbaru
data/history.json         # ringkasan harian (upsert per tanggal), untuk grafik tren
data/history/<tanggal>.json  # arsip poin mentah per hari
index.html                # dashboard (peta Leaflet + grafik Chart.js)
.github/workflows/scrape.yml  # jadwal otomatis 3x/hari (01.30, 07.30, 13.30 WITA)
```

## Menjalankan scraper secara manual

```bash
python scripts/scrape.py
```

Untuk uji coba tanpa memanggil API asli:

```bash
python scripts/scrape.py scripts/sample_response.json
```

## Catatan jujur soal data historis

Saat pertama kali di-deploy, `data/history.json` hanya berisi hari saat scraper pertama dijalankan — grafik tren akan kosong/pendek di awal dan baru bermakna setelah beberapa minggu GitHub Actions berjalan otomatis. Ini disengaja: tidak ada data historis yang direkayasa, karena ini data kebencanaan yang bisa dibaca publik/BPBD.

## Batasan

Titik panas satelit adalah indikasi awal (anomali suhu permukaan), bukan konfirmasi kebakaran lahan/hutan di lapangan. Verifikasi lanjutan tetap menjadi kewenangan BPBD/Manggala Agni setempat.

## Deploy

1. Push repo ini ke GitHub, aktifkan GitHub Pages (branch `main`, folder root).
2. Pastikan Actions punya izin `contents: write` (Settings → Actions → General → Workflow permissions → Read and write).
3. Jalankan workflow sekali secara manual (`workflow_dispatch`) untuk mengisi data pertama.
