# SLM-Based Resource Efficient Log Analysis System 🛡️

![Python](https://img.shields.io/badge/Python-3.9%2B-blue)
![AI](https://img.shields.io/badge/AI-Hugging%20Face-yellow)
![Status](https://img.shields.io/badge/Status-Prototype-orange)

## 📖 Proje Özeti (Abstract)
Bu proje, modern yazılım sistemlerinde üretilen büyük hacimli log verilerini analiz etmek için **Küçük Dil Modelleri (SLM)** tabanlı, kaynak verimli bir **AIOps** mimarisi sunar.

[cite_start]Büyük Dil Modellerinin (LLM) yüksek gecikme (latency) ve maliyet sorunlarına [cite: 11] [cite_start]çözüm olarak geliştirilen bu sistem; log ayrıştırma (parsing), anomali tespiti, kök neden analizi (RCA) ve kestirimci bakım (Predictive Maintenance) süreçlerini uçtan uca tek bir boru hattında (pipeline) birleştirir[cite: 15].

## 🚀 Temel Özellikler (Key Features)

[cite_start]Makalede önerilen mimari tasarımına  dayanarak:

* [cite_start]**Micro-Batch Processing:** Logları tek tek değil, zaman veya boyut pencereleriyle (örn. 50 satır/1 dk) işleyerek API çağrı maliyetini düşürür[cite: 94].
* **RAG (Retrieval-Augmented Generation) Hafıza:** Geçmiş olayları ve çözülen incident kayıtlarını vektör veritabanında tutar. [cite_start]Yeni bir hata oluştuğunda geçmişteki benzer çözümleri "Context" olarak modele sunar[cite: 101].
* [cite_start]**SLM Odaklı Mimari:** GPT-4 gibi dev modeller yerine, operasyonel verimlilik için "TinyLlama", "Phi-2" gibi özelleştirilmiş küçük modeller (SLM) kullanır[cite: 41].
* **Predictive Maintenance (PdM):** Sadece hatayı bulmaz; [cite_start]"Sistem 2 saat içinde çökebilir" gibi erken uyarılar üretir[cite: 109].
* [cite_start]**Kanıta Dayalı RCA:** Yapay zeka halüsinasyonunu önlemek için log satırlarını kanıt olarak göstererek Kök Neden Analizi yapar[cite: 107].

## 🏗️ Mimari Tasarım (Architecture)

[cite_start]Sistem 4 ana modülden oluşur:

1.  **Data Ingestion & Preprocessing:** Logların akıştan alınması ve Template/Parametre olarak ayrıştırılması (Parsing).
2.  **Event Memory & Retrieval:** Vektör tabanlı hafıza kontrolü (RAG).
3.  **Analysis & Reasoning:** Anomali tespiti ve Durum Özeti çıkarma.
4.  **Output & Interaction:** Operatör için RCA raporu ve doğal dil sorgu katmanı.

*(Buraya makaledeki Şekil 1 görseli eklenecek: `![Architecture](architecture.png)`) *

## 🛠️ Kullanılan Teknolojiler

* **Dil:** Python
* **Yapay Zeka:** Hugging Face Transformers (SLM Entegrasyonu), PyTorch
* **Veri İşleme:** Pandas, NumPy
* **Vektör Veritabanı:** FAISS veya ChromaDB (Planlanan)
* **Yöntemler:** Micro-batching, Prompt Engineering, RAG

## 📊 Nasıl Çalışır? (Workflow)

| Aşama | İşlem | Çıktı Örneği |
| :--- | :--- | :--- |
| **1. Ingestion** | [cite_start]Loglar 1 dakikalık paketler (micro-batch) halinde toplanır[cite: 115]. | `Batch ID: #1024` |
| **2. Parsing** | Ham loglar şablonlara dönüştürülür. | `Template: Connection timeout at <IP>` |
| **3. Retrieval** | [cite_start]Geçmişte benzer 'timeout' hataları vektör veritabanından çağrılır[cite: 118]. | `Context: "Geçen ay bu hata DB kilidi yüzünden oldu."` |
| **4. Analysis** | Model, geçmiş veriyi ve şu anki hatayı birleştirip analiz eder. | `Anomaly Score: 0.95 (High Risk)` |
| **5. Output** | [cite_start]Operatöre özet ve aksiyon planı sunulur[cite: 122]. | `Root Cause: DB Pool Saturation. Action: Restart Service.` |

## 📅 Yol Haritası (Roadmap)
- [x] Literatür Taraması ve Mimari Tasarım (Review Paper Tamamlandı).
- [ ] Log Parsing Modülünün Kodlanması (Devam Ediyor).
- [ ] RAG (Vektör Veritabanı) Entegrasyonu.
- [ ] SLM Modelinin Fine-Tuning İşlemleri.
- [ ] Google Cloud üzerinde Dockerize edilmesi.

---
**Akademik Referans:**
[cite_start]Bu proje, *"SLM ile Kaynak Verimli Log Analiz Sistemi: Sistematik İnceleme ve Uçtan Uca SLM Tabanlı Mimari Önerisi"*  başlıklı lisans bitirme tezi kapsamında geliştirilmektedir.
