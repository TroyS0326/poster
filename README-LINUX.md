# 🧠 auto40 Script Suite - Linux (Ubuntu) Setup Guide

Follow this guide to install and run the `auto40` scripts on **Ubuntu or Linux**. Super beginner-friendly!

---

## ✅ Minimum System Requirements

- Ubuntu 20.04 or later
- CPU: Intel i5 / Ryzen 5 or better
- RAM: 8 GB minimum (16 GB recommended)
- GPU: NVIDIA GTX 1660 or better
- Python 3.10 or later
- 5+ GB free space

---

## 📦 Step-by-Step Instructions

### 1. Install Python & Pip

```bash
sudo apt update
sudo apt install python3 python3-pip -y
```

### 2. Install unzip if needed

```bash
sudo apt install unzip -y
```

### 3. Extract Project Files

```bash
unzip auto40.zip
cd auto40/auto40
```

### 4. Install Required Python Libraries

```bash
pip3 install -r requirements.txt
```

### 5. Configure `.env`

```bash
nano .env
```

- Add your keys and configuration
- Save with `CTRL+O`, exit with `CTRL+X`

### 6. Run the Script

```bash
python3 main.py
```

---

## ✅ Script Summary

| Script         | What It Does                                          |
|----------------|-------------------------------------------------------|
| `main.py`      | Starts the full process: caption + image + post      |
| `text_ai.py`   | Generates captions using AI                          |
| `image_ai.py`  | Creates AI-generated images                          |
| `meta_poster.py`| Posts to Instagram/Facebook                         |
| `uploader.py`  | Uploads image assets                                 |
| `scheduler.py` | Schedules auto-posting                               |
| `dashboard.py` | Optional interface (GUI)                             |
| `config.py`    | Holds default settings                               |
| `.env`         | Stores your keys and secrets                         |