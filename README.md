## 🚀 Yerelde LLM Test Etmek İçin Pratik Bir Yol Arayanlara 👇

Kendi makinende **Ollama + Docker** stack’i ile nasıl 5+ açık kaynak büyük dil modelini (LLM) nasıl test edersin?

---

### Neden Böyle Bir Akış Kurmaya Değer?

* 💡 **Model Karşılaştırması** — Mistral, Llama 3, Qwen, Phi‑mini ve Gemma gibi modelleri aynı senaryoda ölçüp hangisinin projenize uygun olduğunu test edebilirsiniz.
* 🛠️ **Araç & Şema Uyumluluğu** — Test betiği, fonksiyon çağrısı (tool call) ve JSON schema desteğini de kontrol ediyor. Yani model sadece “sohbet” edebiliyor mu değil; gerçek üretim akışına hazır mı, onu öğreniyorsunuz.
* 🌱 **Tamamen Açık Kaynak** — Dockerfile, docker‑compose, Python betiği ve gereksinimler GitHub’da. Çek, kur, çalıştır.

---

### 0️⃣ Hazırlık

| Gereklilik                   | Detay                                    |
| ---------------------------- | ---------------------------------------- |
| **Docker Desktop**           | Windows’ta WSL 2 / Hyper‑V açık olmalı.  |
| **Python ≥ 3.10**            | Betik asenkron `httpx` kullanıyor.       |
| **uv** (opsiyonel)           | Bağımlılıkları ışık hızında kurmak için. |
| **NVIDIA Container Toolkit** | GPU hızlandırma istiyorsan.              |

---

### 1️⃣ Ollama Sunucusunu Kaldır 🚢

```bash
# modelleri **konteyner içinde** çekmek için:
docker exec -it ollama ollama pull mistral:7b
docker exec -it ollama ollama pull llama3.2:latest
docker exec -it ollama ollama pull qwen3:14b
docker exec -it ollama ollama pull qwen3:8b
docker exec -it ollama ollama pull phi4-mini:3.8b-fp16
# opsiyonel
docker exec -it ollama ollama pull gemma3:12b
```

Bittiğinde \~10‑20 GB arası depolama kullanıyor, sonra tekrar indirmeye gerek yok.

---

### 3️⃣ Python Ortamı ⚙️

```bash
uv pip install httpx pydantic   # 2 sn
# Bu iki paket, betikteki **httpx** ve **pydantic** dışındaki tüm modüller
# (asyncio, sys, json, datetime, random, typing) Python standart kütüphanesidir.
# Dolayısıyla ek bir kurulum gerekmez.
```

Alternatif olarak klasik `pip`:

```bash
pip install httpx pydantic
```

---

### 4️⃣ Testi Çalıştır 🧪

```bash
uv run test_ollama_connection.py                # tüm modeller
uv run test_ollama_connection.py http://localhost:11434 llama3.2:latest  # tek model
```

Betiğin sonunda şöyle bir tablo geliyor:

```
Model           | Basic | Tools | Schema | Combo
mistral:7b      | ✅    | ✅    | ✅     | ✅
qwen3:14b       | ✅    | ❌    | ✅     | ❌
...
```

Eksik kalan hücre varsa betik ayrıntılı hatayı da listeliyor — debug süreniz kısalıyor.

---

### 5️⃣ Karşılaştığım Küçük Pürüzler

* **11434 portu meşgul** → eski konteyneri durdur/unpublish.
* **CUDA hatası** → NVIDIA Driver + Toolkit sürümü uyumlu mu diye bak.
* **`uv`**\*\* bulunamadı\*\* → `pip install uv` ya da `cargo install uv` yeterli.

---

### Son Söz 🎯

Yerelde LLM denemek için saatlerce ortam kurmaya gerek yok. Bu akışla **10 dakika içinde** model çek, test et, karar ver.

Beraber daha iyi test senaryoları geliştirebiliriz! Hataları iletmeyi unutmayın! 🚀

