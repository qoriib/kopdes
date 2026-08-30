# 🌾 KOPDES — SIMKOPDES Analytics & MLOps Platform

[![GitHub Workflow](https://img.shields.io/badge/CI%2FCD-GitHub%20Actions-2088FF?style=for-the-badge&logo=githubactions&logoColor=white)](.github/workflows/main.yml)
[![MLOps](https://img.shields.io/badge/MLOps-DVC%20%2B%20Cloudflare%20R2-945DD6?style=for-the-badge&logo=dvc&logoColor=white)](https://dvc.org)
[![Backend](https://img.shields.io/badge/Backend-Cloudflare%20Workers%20%2B%20Hono-F38020?style=for-the-badge&logo=cloudflareworkers&logoColor=white)](https://workers.cloudflare.com)
[![Database](https://img.shields.io/badge/Database-Cloudflare%20D1%20(SQLite)-0051C3?style=for-the-badge&logo=sqlite&logoColor=white)](https://developers.cloudflare.com/d1/)
[![Frontend](https://img.shields.io/badge/Frontend-React%2019%20%2B%20Astryx-61DAFB?style=for-the-badge&logo=react&logoColor=black)](web/frontend)

**KOPDES** adalah platform analitik dan machine learning *end-to-end* yang menerapkan metodologi **CRISP-DM 1.0 (Cross-Industry Standard Process for Data Mining)** untuk mengumpulkan, memproses, mengelompokkan (clustering), mengevaluasi, dan mendiseminasikan data profil serta performa Koperasi Desa di seluruh Indonesia dari portal [SIMKOPDES](https://simkopdes.go.id).

---

## 📌 Daftar Isi

- [Arsitektur Sistem](#-arsitektur-sistem)
- [Teknologi & Stack](#-teknologi--stack)
- [Tahapan CRISP-DM](#-tahapan-crisp-dm)
- [Struktur Direktori](#-struktur-direktori)
- [Panduan Instalasi & Penggunaan Lokal](#-panduan-instalasi--penggunaan-lokal)
  - [Prasyarat](#prasyarat)
  - [1. Clone Repository & Konfigurasi Environment](#1-clone-repository--konfigurasi-environment)
  - [2. Setup Python & DVC Data Pipeline](#2-setup-python--dvc-data-pipeline)
  - [3. Menjalankan Backend (Cloudflare Workers + D1)](#3-menjalankan-backend-cloudflare-workers--d1)
  - [4. Menjalankan Frontend (React 19 + Vite)](#4-menjalankan-frontend-react-19--vite)
- [CI/CD & Otomatisasi GitHub Actions](#-cicd--otomatisasi-github-actions)
- [Lisensi & Kontributor](#-lisensi--kontributor)

---

## 🏛️ Arsitektur Sistem

```mermaid
flowchart TD
    subgraph INGESTION ["0. Data Ingestion"]
        A[SIMKOPDES Portal] -->|Playwright Headless Scraper| B[Raw CSV Data]
    end

    subgraph MLOPS ["1-5. CRISP-DM Pipeline (DVC & Papermill)"]
        B --> S1[1_understanding.ipynb]
        S1 --> S2[2_preparation.ipynb]
        S2 --> S3[3_modeling.ipynb - KMeans]
        S3 --> S4[4_evaluation.ipynb - Silhouette/CH]
        S4 --> S5[5_deployment.ipynb - AI Interpretation]
        S5 -->|Generate| SEED[seed.sql]
        S5 -->|Store Artifacts & Model| R2[(Cloudflare R2 Storage)]
    end

    subgraph BACKEND ["Cloudflare Serverless Backend"]
        SEED -->|D1 Migrations & Seed| D1[(Cloudflare D1 Database)]
        D1 <--> WORKER[Cloudflare Workers API - Hono / OpenAPI]
    end

    subgraph FRONTEND ["Web Presentation"]
        WORKER <--> UI[Cloudflare Pages - React 19 + Tailwind v4 + Recharts]
    end
```

---

## 🚀 Teknologi & Stack

### Data Pipeline & MLOps
- **Python 3.12+** & **Papermill**: Eksekusi notebook analitik modular secara terotomatisasi dan parametrik.
- **Playwright**: Web scraping dinamis untuk ekstraksi data tabel hierarki provinsi dan kabupaten/kota dari SIMKOPDES.
- **DVC (Data Version Control)** + **dvc-s3**: Versioning dataset, tracking dependensi pipeline (`dvc.yaml`), dan remote storage berbasis **Cloudflare R2 (S3-compatible)**.
- **Scikit-Learn**: Algoritma K-Means Clustering, Standard Scaling, dan evaluasi metrik (*Silhouette Score, Calinski-Harabasz Index, Davies-Bouldin Index*).
- **Cloudflare Workers AI (LLM)**: Ekstraksi insight eksekutif dan deskripsi profil cluster berbasis model AI terkelola (`@cf/openai/gpt-oss-120b`).

### Backend (Cloudflare Workers)
- **Runtime**: Cloudflare Workers (Serverless Edge Runtime).
- **Framework**: [Hono](https://hono.dev/) dengan `@hono/zod-openapi` untuk type-safety dan dokumentasi Swagger/OpenAPI otomatis.
- **Database**: Cloudflare D1 (Serverless Distributed SQLite).

### Frontend (Cloudflare Pages)
- **Framework**: React 19, TypeScript, Vite.
- **Design System**: Astryx Design System (`@astryxdesign/core`, `@astryxdesign/theme-neutral`), StyleX, Lucide Icons, Figtree Font, Dark/Light Mode.
- **Visualisasi**: Leaflet Map (Spatial Cluster Map), Astryx Markdown & Analytics Cards.

---

## 🔬 Alur Kerja & Penjelasan Step Tiap Notebook

Pipeline analitik KOPDES dibangun secara modular dalam 5 notebook Jupyter (`src/*.ipynb`) yang dijalankan otomatis secara parametrik menggunakan **Papermill** dan dipantau oleh **DVC**.

```
[0. Ingestion (Playwright)]
       │
       ▼
[1_understanding.ipynb] ──> cleaned_provinces.csv, cleaned_regencies.csv, feature_evaluation.json
       │
       ▼
[2_preparation.ipynb]   ──> prepared_regencies.csv, feature_selection.json
       │
       ▼
[3_modeling.ipynb]      ──> kmeans_model.pkl, agglomerative_model.pkl
       │
       ▼
[4_evaluation.ipynb]    ──> clustered_regencies.csv, model_comparison.json
       │
       ▼
[deploy_seed.py]        ──> seed.sql (Cloudflare D1 Seeder & AI Interpretation)
```

---

### 1. `src/1_understanding.ipynb` — Data Understanding
Notebook ini bertujuan memahami struktur, integritas, dan korelasi data mentah hasil scraping:
- **Pemuatan Data Mentah**: Memuat `scraped_provinces.csv` dan `scraped_regencies.csv`.
- **Pembersihan Teks & Parsing Numerik**: Standardisasi nama kolom dan konversi format string (mata uang, titik pemisah ribuan) menjadi tipe numerik (`float64`/`int64`).
- **Analisis Statistik Deskriptif**: Menghitung *mean, median, standard deviation, min, max,* serta persentase *missing values*.
- **Evaluasi Fitur & Multikolinearitas**:
  - Menghitung nilai **VIF (Variance Inflation Factor)** untuk mendeteksi multikolinearitas antar fitur.
  - Menghitung **CV (Coefficient of Variation)** untuk menilai variabilitas sebaran data.
  - Menghitung tingkat kemencengan data (**Skewness**).
- **Artefak Output**:
  - `artifact/1_understanding/cleaned_provinces.csv`
  - `artifact/1_understanding/cleaned_regencies.csv`
  - `artifact/1_understanding/feature_evaluation.json`

---

### 2. `src/2_preparation.ipynb` — Data Preparation
Notebook ini memproses data kabupaten/kota agar siap untuk pemodelan machine learning:
- **Injeksi Parameter**: `MAX_VIF` (default: `10.0`), `MIN_CV` (default: `10.0`), `SKEWNESS_THRESHOLD` (default: `2.0`).
- **Imputasi Nilai Hilang (Missing Values)**: Menggunakan algoritma **k-Nearest Neighbors Imputation (`KNNImputer`, $k=5$)** untuk menjaga pola kovarian data.
- **Rule-Based Feature Selection**:
  - Mengeliminasi fitur dengan multikolinearitas tinggi ($VIF \ge \text{MAX\_VIF}$) dan variabilitas rendah ($CV < \text{MIN\_CV}$) berdasarkan metadata `feature_evaluation.json`.
- **Transformasi Logaritmik**: Menerapkan transformasi $\log(1+x)$ (`np.log1p`) pada fitur yang memiliki skewness ekstrem ($|\text{skew}| > \text{SKEWNESS\_THRESHOLD}$).
- **Standardisasi Fitur**: Menggunakan `StandardScaler` untuk menghasilkan kolom fitur berskala baku (`scaled_*`).
- **Penyimpanan Gabungan Data**: Menggabungkan seluruh kolom awal terimputasi dengan kolom fitur terstandarisasi.
- **Artefak Output**:
  - `artifact/2_preparation/prepared_regencies.csv`
  - `artifact/2_preparation/feature_selection.json`

---

### 3. `src/3_modeling.ipynb` — Modeling
Notebook ini menentukan jumlah klaster optimal dan melatih model klasterisasi:
- **Injeksi Parameter**: `K_MIN` (default: `2`), `K_MAX` (default: `10`), `FALLBACK_K` (default: `4`), `RANDOM_STATE` (default: `42`).
- **Optimasi Nilai $K$ Optimal**:
  - **K-Means**: Menghitung WCSS (*Within-Cluster Sum of Squares* / Inersia) pada rentang $K \in [K\_MIN, K\_MAX]$ dan mendeteksi titik siku (*knee point*) dengan `kneed.KneeLocator`.
  - **Agglomerative Clustering**: Mengoptimalkan $K$ berdasarkan maksimasi nilai *Silhouette Score* serta matriks hierarki *Ward Linkage*.
- **Pelatihan & Penyimpanan Model Individual**:
  - Melatih model **K-Means** dan **Agglomerative Clustering** pada $K$ optimal masing-masing.
  - Menyimpan setiap model terlatih secara terpisah ke direktori `artifact/3_modeling/`.
- **Artefak Output**:
  - `artifact/3_modeling/kmeans_model.pkl`
  - `artifact/3_modeling/agglomerative_model.pkl`

---

### 4. `src/4_evaluation.ipynb` — Evaluation
Notebook ini memuat model terlatih, mengevaluasi perbandingan metrik, memilih model terbaik, dan menghasilkan data terklaster:
- **Pemuatan Model & Komparasi Metrik**:
  - Memuat model `artifact/3_modeling/kmeans_model.pkl` dan `artifact/3_modeling/agglomerative_model.pkl`.
  - Menghitung metrik validasi internal: *Silhouette Coefficient*, *Calinski-Harabasz Index*, dan *Davies-Bouldin Index*.
- **Pemilihan Model Terbaik & Penetapan Klaster**:
  - Memilih model dengan performa terbaik (*best model selection*).
  - Membentuk kolom `cluster_label` dan menyimpan dataset hasil klasterisasi.
  - Menyimpan ringkasan komparasi ke `model_comparison.json`.
- **Eksplorasi Visual & Distribusi**:
  - Proyeksi 2D Klaster menggunakan PCA (*Principal Component Analysis*).
  - Distribusi jumlah anggota per klaster (tabel dan grafik batang).
- **Artefak Output**:
  - `artifact/4_evaluation/clustered_regencies.csv`
  - `artifact/4_evaluation/model_comparison.json`

---

### 5. Modul Deployment (`src/deploy_*.py`)
Tahap deployment dibangun modular setara modul scraping, terdiri dari 3 modul spesifik:
- **`src/deploy_util.py`**:
  - Utilitas bersama untuk memuat dataset terintegrasi geospasial (`load_merged_deployment_data`) dan sanitasi SQL (`sql_val`).
- **`src/deploy_interpret.py`**:
  - Menganalisis profil rata-rata tiap klaster, menentukan label tipologi wilayah, dan menyusun laporan rekomendasi kebijakan.
  - Artefak Output: `artifact/deployment/interpretation.json` & `artifact/deployment/ai_report.md`.
- **`src/deploy_store.py`**:
  - Menyusun seluruh pernyataan DDL & INSERT SQL untuk tabel `provinces`, `regencies`, dan `ai_report` ke Cloudflare D1.
  - Artefak Output: `artifact/deployment/seed.sql`.

---

## 📂 Struktur Direktori

```text
kopdes/
├── .github/
│   ├── actions/               # Composite GitHub Actions (setup-pipeline, push-pipeline)
│   └── workflows/
│       └── main.yml           # CI/CD End-to-End Orchestration Workflow
├── .dvc/                      # Konfigurasi DVC & R2 Remote Storage
├── artifact/                  # Artifact storage per tahapan CRISP-DM
│   ├── scrape/                # Data mentah hasil scraping
│   ├── 1_understanding/       # Data bersih & metadata evaluasi fitur
│   ├── 2_preparation/         # Data terimputasi & fitur terstandarisasi
│   ├── 3_modeling/            # Model tersimpan (kmeans_model.pkl, agglomerative_model.pkl)
│   ├── 4_evaluation/          # Data hasil klasterisasi (clustered_regencies.csv) & model_comparison.json
│   └── deployment/            # Berkas seed.sql database D1 & data referensi geospasial
├── src/                       # Source code pipeline analitik
│   ├── scrape_util.py         # Modul utilitas scraping & parser tabel HTML
│   ├── scrape_provinces.py    # Script scraping data tingkat provinsi
│   ├── scrape_regencies.py    # Script scraping data tingkat kabupaten/kota
│   ├── 1_understanding.ipynb  # Notebook eksplorasi & pemahaman data
│   ├── 2_preparation.ipynb    # Notebook pra-pemrosesan data
│   ├── 3_modeling.ipynb       # Notebook pemodelan K-Means & Agglomerative
│   ├── 4_evaluation.ipynb     # Notebook evaluasi metrik & komparasi
│   ├── deploy_util.py         # Modul utilitas pemuatan data spasial & SQL escaping
│   ├── deploy_interpret.py    # Generator laporan interpretasi & metadata tipologi klaster
│   ├── deploy_store.py        # Generator seeder SQL database Cloudflare D1
│   ├── config.py              # Konfigurasi konstanta & fitur global
│   └── outs/                  # Output notebook hasil eksekusi Papermill
├── web/
│   ├── backend/               # Cloudflare Workers API (Hono + D1 Database)
│   │   ├── migrations/        # Skema migrasi database D1
│   │   ├── src/               # Controllers, routes, & model OpenAPI
│   │   └── wrangler.jsonc     # Konfigurasi Cloudflare Wrangler Worker
│   └── frontend/              # Cloudflare Pages React Dashboard
│       ├── src/               # Komponen React, visualisasi Recharts, hooks
│       └── wrangler.json      # Konfigurasi Cloudflare Pages
├── dvc.yaml                   # Definisi DAG Pipeline DVC
├── params.yaml                # Parameter hyperparameter pipeline
├── pyproject.toml             # Python package configuration
└── requirements.txt           # Python dependencies
```

---

## 💻 Panduan Instalasi & Penggunaan Lokal

### Prasyarat
- **Python** $\ge$ 3.10
- **Node.js** $\ge$ 20 & **npm**
- **Git** & **DVC**

---

### 1. Clone Repository & Konfigurasi Environment

```bash
git clone https://github.com/qoriib/kopdes.git
cd kopdes
```

Salin template environment variable dan isi kunci API yang diperlukan:

```bash
cp .env.example .env
```

Isi variabel pada file `.env`:
```ini
AWS_ACCESS_KEY_ID=<your_cloudflare_r2_access_key>
AWS_SECRET_ACCESS_KEY=<your_cloudflare_r2_secret_key>
CLOUDFLARE_ACCOUNT_ID=<your_cloudflare_account_id>
CLOUDFLARE_API_TOKEN=<your_cloudflare_api_token>
R2_BUCKET=kopdes
R2_PUBLIC_URL=https://<your_r2_public_url>
```

---

### 2. Setup Python & DVC Data Pipeline

```bash
# Buat dan aktifkan virtual environment
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

# Install dependencies Python
pip install -r requirements.txt
pip install -e .

# Install browser Chromium untuk scraping (Playwright)
playwright install chromium --with-deps

# Unduh dataset cache dari DVC remote (Cloudflare R2)
dvc pull

# Jalankan seluruh pipeline CRISP-DM
dvc repro
```

---

### 3. Menjalankan Backend (Cloudflare Workers + D1)

```bash
cd web/backend
npm install

# Terapkan skema database D1 secara lokal
npx wrangler d1 execute simkopdes_db --local --file=../../artifact/deployment/schema.sql

# Isi data awal database dari hasil pipeline
npx wrangler d1 execute simkopdes_db --local --file=../../artifact/deployment/seed.sql

# Jalankan server backend lokal
npm run dev
```
> API backend lokal akan berjalan di `http://localhost:8787` (Swagger Docs: `http://localhost:8787/api/doc`).

---

### 4. Menjalankan Frontend (React 19 + Vite)

Buka terminal baru:

```bash
cd web/frontend
npm install

# Jalankan server frontend lokal
npm run dev
```
> Dashboard frontend interaktif dapat diakses di `http://localhost:5173`.

---

## 🔄 CI/CD & Otomatisasi GitHub Actions

Workflow terpusat pada [`.github/workflows/main.yml`](.github/workflows/main.yml) menjalankan otomatisasi end-to-end setiap kali di-trigger via `workflow_dispatch`:

1. **Scrape Job**: Mengambil data terbaru dari portal SIMKOPDES via Playwright headless browser.
2. **Pipeline Job**:
   - Menjalankan `dvc repro` untuk memproses seluruh tahapan analitik & model training.
   - Mengonversi notebook ke laporan Markdown dan mempublikasikan visualisasi plot via **CML (Continuous Machine Learning)** langsung ke GitHub Actions Step Summary.
   - Menerapkan migrasi skema dan melakukan seeding database ke **Cloudflare D1 Remote**.
   - Menyimpan dan menyinkronkan data cache model ke remote storage via `dvc push`.
3. **Deploy Backend Job**: Membangun dan merilis API Worker ke **Cloudflare Workers** via `cloudflare/wrangler-action@v4`.
4. **Deploy Frontend Job**: Membangun dan menerbitkan web app dashboard ke **Cloudflare Pages**.

---

## 📄 Lisensi & Kontributor

Dikembangkan oleh **[Qoriib](https://github.com/qoriib)** untuk inovasi digitalisasi dan pemetaan analitik Koperasi Desa Indonesia.

Lisensi di bawah **MIT License**.
