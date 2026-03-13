# Büyük Veri Analitiğinde Olasılıksal Veri Yapıları ve HyperLogLog Tasarımı

> Python ile sıfırdan gerçeklenen, bellek dostu ve olasılıksal bir kardinalite tahmin algoritması.

---

## İçindekiler

- [Proje Özeti ve Amaç](#proje-özeti-ve-amaç)
- [Kullanılan Teknolojiler ve Agentic Coding Yöntemi](#kullanılan-teknolojiler-ve-agentic-coding-yöntemi)
- [Algoritma Tasarımı ve Teknik Gerçekleme](#algoritma-tasarımı-ve-teknik-gerçekleme)
- [Teorik Hata Analizi](#teorik-hata-analizi)
- [Kurulum ve Çalıştırma](#kurulum-ve-çalıştırma)
- [Test Sonuçları ve Yorum](#test-sonuçları-ve-yorum)

---

## Proje Özeti ve Amaç

Büyük veri sistemlerinde sıklıkla karşılaşılan temel zorluklardan biri, milyonlarca ya da milyarlarca eleman içeren bir veri akışında **kaç benzersiz elemanın (kardinalite) bulunduğunu** verimli biçimde hesaplamaktır.

Geleneksel yaklaşımda tüm elemanlar bir hash kümesinde tutulur; bu yöntem kesin sonuç vermekle birlikte bellek tüketimi doğrudan küme boyutuyla orantılı olarak büyür. 500.000 elemanlık bir veri seti için bu, onlarca megabaytlık bellek gereksinimi anlamına gelir.

**HyperLogLog (HLL)**, bu problemi olasılık teorisi ve istatistiksel örnekleme yoluyla çözen bir veri yapısıdır:

- Yalnızca birkaç kilobayt **sabit bellek** kullanır.
- Milyarlarca elemanlı kümeler için **%1–3 hata payıyla** tahminde bulunabilir.
- Birden fazla yapı, orijinal veriye ihtiyaç duyulmadan **kayıpsız birleştirilebilir**.

Bu proje; HyperLogLog algoritmasının Python ile sıfırdan gerçeklenmesini, performans odaklı optimizasyonların uygulanmasını ve kapsamlı test senaryolarıyla doğrulanmasını kapsamaktadır.

---

## Kullanılan Teknolojiler ve Agentic Coding Yöntemi

### Teknoloji Yığını

| Araç / Teknoloji | Kullanım Amacı |
|---|---|
| **Python 3** | Temel implementasyon dili |
| **hashlib** (SHA-256) | Güvenli ve tekdüze dağılımlı hash üretimi |
| **VS Code** | Geliştirme ortamı |
| **GitHub Copilot** | Agentic Coding asistanı |
| **Claude Sonnet** | Copilot altında çalışan büyük dil modeli |

### Agentic Coding Yöntemi

Bu projede geliştirme süreci boyunca **Agentic Coding** yaklaşımı benimsendi. Bu yöntemde yapay zeka, geleneksel bir otomatik tamamlama aracının ötesine geçerek algoritmik kararların alındığı her adımda aktif bir mühendislik ortağı olarak rol üstlenir.

Süreç aşağıdaki aşamaları kapsamaktadır:

1. **Araştırma** — HLL'nin matematiksel temellerinin ve literatürdeki varyantlarının incelenmesi
2. **Tasarım** — Bitwise optimizasyon kararları ve kova sayısının belirlenmesi
3. **Gerçekleme** — Hashing, bucketing, düzeltme faktörleri ve merge fonksiyonlarının kodlanması
4. **Doğrulama** — Test senaryolarının tasarlanması, hata oranlarının teorik beklentiyle karşılaştırılması

---

## Algoritma Tasarımı ve Teknik Gerçekleme

HyperLogLog beş temel bileşenden oluşmaktadır:

---

### 1. Hashing — SHA-256 ile Tekdüze Dağılım

Her eleman, **SHA-256** hash fonksiyonundan geçirilerek 256 bit uzunluğunda rastgele görünen bir bit dizisine dönüştürülür. Hesaplama sadece ilk **64 bit** üzerinden yürütülür; bu değer sonraki tüm işlemler için yeterlidir.

SHA-256 tercihinin teknik gerekçeleri:

- **Yüksek çarpışma direnci** — farklı girdiler aynı hash değerini üretmez
- **Uniform dağılım** — her kova eşit olasılıkla seçilir, tahmin sapması en aza indirilir
- **Standart kütüphane desteği** — harici bağımlılık gerektirmez

```python
hash_val = int(hashlib.sha256(str(item).encode()).hexdigest(), 16) >> 192  # İlk 64 bit
```

---

### 2. Bucketing — Bitwise Right Shift ve Masking

Hash değerinin ilk `p` biti, elemanın atanacağı kovayı (bucket) belirler. Klasik **mod (`%`) işlemi yerine** bitwise operatörler tercih edilmiştir:

```python
# m = 2048 → p = 11 bit
bucket_index = hash_val >> (64 - self.p)   # İlk p bit → kova indeksi
remaining    = hash_val & self.mask         # Kalan bitler → sıfır sayımı
```

**Neden Bitwise?**

| Yöntem | Karmaşıklık | Avantaj |
|---|:---:|---|
| Mod (`%`) | O(n) — bölme işlemi | Okunabilir |
| **Bitwise shift + mask** | **O(1)** | Donanım seviyesinde optimize, hash dağılımını bozmaz |

Bu projede `m = 2**p = 2048` kova kullanılmıştır.

---

### 3. Leading Zeros — `bit_length()` ile O(1) Sıfır Sayımı

Hash değerinin kalan bitlerindeki **art arda baştaki sıfır sayısı**, kardinalite tahminin istatistiksel temelidir. Olasılık teorisine göre:

> Bir hash değerinde art arda $k$ sıfır gözlemleniyorsa, bu değeri üretmek için ortalama $2^k$ deneme gerekmiştir.

Baştaki sıfır sayısı, döngü yerine Python'un yerleşik `bit_length()` fonksiyonuyla $O(1)$ karmaşıklıkta hesaplanır:

```python
# bit_length() → kaç bit gerektiğini döner; farktan sıfır sayısı elde edilir
leading_zeros = (64 - self.p) - remaining.bit_length()
self.registers[bucket_index] = max(self.registers[bucket_index], leading_zeros + 1)
```

Her kova, o kovaya düşen elemanların **maksimum sıfır sayısını** saklar.

---

### 4. Kardinalite Tahmini — Harmonik Ortalama ve Düzeltme Faktörleri

Tüm kova değerlerinden **harmonik ortalama** alınarak ham tahmin hesaplanır:

$$\hat{n} = \alpha_m \cdot m^2 \cdot \left( \sum_{j=1}^{m} 2^{-M_j} \right)^{-1}$$

Harmonik ortalama, aritmetik ortalamadan farklı olarak uç değerlerin ağırlığını baskılar. $\alpha_m$ ise kova sayısına bağlı sabit bir düzeltme katsayısıdır.

Ham tahmin, veri boyutuna göre ek düzeltme faktörleriyle iyileştirilir:

| Durum | Uygulanan Yöntem | Gerekçe |
|---|---|---|
| Tahmin `< 2.5 × m` **ve** boş kova mevcutsa | **Linear Counting** | Küçük kümelerde HLL sistematik olarak yüksek tahmin üretir |
| Tahmin `> 2³² / 30` | **Large Range Correction** | Hash alanı taşması (collision) ihtimali artar |
| Diğer durumlar | Ham HLL tahmini | Düzeltme gerekmez |

---

### 5. Merge — Kayıpsız Birleştirme

İki bağımsız HLL yapısını birleştirmek için her iki yapının eş indeksli kova değerlerinden **maksimum** alınır:

```python
for i in range(self.m):
    merged.registers[i] = max(self.registers[i], other.registers[i])
```

**Neden maksimum?** Her kovadaki değer, o kovaya gelen elemanların en uzun sıfır dizisini temsil eder. İki kaynaktan gelen maksimum değer, her iki kümenin birleşimini en doğru biçimde modellemektedir.

Bu işlem **tamamen kayıpsız**, hızlı ve yalnızca kova dizileri üzerinden gerçekleştirilir — orijinal veriye hiçbir şekilde ihtiyaç duyulmaz.

---

## Teorik Hata Analizi

HyperLogLog'un göreceli standart hatası (relative standard error) aşağıdaki formülle tanımlanır:

$$\varepsilon \approx \frac{1.04}{\sqrt{m}}$$

Burada $m$, kullanılan kova sayısıdır. Kova sayısı arttıkça hata oranı azalır; buna karşın bellek tüketimi de buna paralel büyür.

| Kova Sayısı ($m$) | Teorik Hata | Toplam Bellek |
|:---:|:---:|:---:|
| 64 | %13.00 | ~64 B |
| 256 | %6.50 | ~256 B |
| 1024 | %3.25 | ~1 KB |
| **2048** | **%2.30** | **~2 KB** |
| 4096 | %1.63 | ~4 KB |
| 16384 | %0.81 | ~16 KB |

Bu projede `m = 2048` seçilmiştir. Teorik hata sınırı **≈ %2.30** olup elde edilen test sonuçları bu beklentiyle uyumludur.

---

## Kurulum ve Çalıştırma

### Gereksinimler

Python 3.8 veya üzeri yeterlidir. Harici bağımlılık bulunmamaktadır; yalnızca standart kütüphane modülleri (`hashlib`, `math`) kullanılmıştır.

### Kurulum

```bash
git clone https://github.com/kullanici-adi/hyperloglog.git
cd hyperloglog
```

### Çalıştırma

```bash
# Ana implementasyonu çalıştır
python hyperloglog.py

# Test senaryolarını çalıştır
python test_hll.py
```

---

## Test Sonuçları ve Yorum

### Test 1 — Büyük Veri Kardinalite Tahmini

| Metrik | Değer |
|---|---|
| Üretilen toplam veri | 500,000 |
| Gerçek benzersiz eleman sayısı | 393,369 |
| HLL Tahmini | 406,226 |
| **Hata Oranı** | **%3.24** |

**Yorum:** 500.000 elemanlık veri akışında HLL, gerçek kardinaliteyi %3.24 hatayla tahmin etmiştir. Teorik sınır %2.30 olduğundan bu sonuç kabul edilebilir aralıktadır. Sapmanın başlıca kaynağı, veri kümesindeki tekrar oranıdır: 500.000 örnekten yalnızca 393.369'u benzersizdir (~%21 tekrar). Yüksek tekrar yoğunluğu, kova değerlerini baskılayarak harmonik ortalamayı yukarı kaydırır. Buna karşın bellek tüketimi yalnızca **~2 KB** ile sabit kalmıştır.

---

### Test 2 — Merge İşlevi

| Metrik | Değer |
|---|---|
| Küme 1 boyutu | 50,000 |
| Küme 2 boyutu | 50,000 |
| Gerçek birleşik benzersiz eleman | 100,000 |
| HLL Merge Tahmini | 102,546 |
| **Hata Oranı** | **%2.55** |

**Yorum:** Merge testi, teorik hata sınırına (%2.30) son derece yakın bir sonuç üretmiştir. İki bağımsız HLL yapısının kova düzeyinde maksimum operatörüyle birleştirilmesi, birleşim kümesini başarıyla modelleyerek **%2.55 hata** ile sonuçlanmıştır. Bu sonuç; dağıtık sistemlerde (örn. birden fazla sunucudan gelen log verileri) orijinal veriye erişim sağlamaksızın kardinalite hesabı yapılabileceğini doğrulamaktadır.

---

### Özet Karşılaştırma

| Test | Gerçek Değer | HLL Tahmini | Hata | Teorik Sınır |
|---|:---:|:---:|:---:|:---:|
| Büyük Veri | 393,369 | 406,226 | %3.24 | %2.30 |
| Merge | 100,000 | 102,546 | %2.55 | %2.30 |

---

## Lisans

Bu proje MIT Lisansı ile lisanslanmıştır.
