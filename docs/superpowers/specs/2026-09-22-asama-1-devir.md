# Aşama 1 devir notu — docx → Ricos dönüştürücüsü

Tarih: 22 Eylül 2026
Durum: **bitti.** 29 + 5 commit, 171 test, çıktı Wix'in kendi doğrulayıcısından geçiyor.
Spec: `docs/superpowers/specs/2026-09-21-wavesanddata-wix-cms-design.md`
Plan: `docs/superpowers/plans/2026-09-21-docx2ricos.md`

---

## 1. Ne var elimizde

```
tools/ricos/blocks.py      ara model (Run, Para, Figure, Table, Callout) + walk()
tools/ricos/docx_read.py   .docx XML -> ara model. Wix'i bilmez.
tools/ricos/emit.py        ara model -> Ricos düğümleri. Word'ü bilmez.
tools/ricos/split.py       başlığa göre bölme + bayt ölçümü
tools/docx2ricos.py        komut satırı
```

```
python tools/docx2ricos.py                    content/source/ altındaki hepsi
python tools/docx2ricos.py <dosya.docx> ...   yalnız bunlar
```

Çıktı `build/ricos/<slug>/` altına: `part-NN.json`, `figures/`, `manifest.json`.
Ağ erişimi yok, Wix'e bağlanmıyor.

**Çıkış kodu:** `0` temiz · `1` rapor bulgu içeriyor (hata değil) · `2` bir belge çevrilemedi.

---

## 2. Ölçüm

Bayt = `len(json.dumps(doc, ensure_ascii=False).encode("utf-8"))`, yani Wix'in sakladığı hal.
Kayıt sınırı 500.000.

| belge | tek kayıt | bölüm | en büyük bölüm |
|---|---:|---:|---:|
| Machine Learning - The Complete Picture and Guide_5 | 362.379 (%72,5) | 12 | 56.454 (%11,3) |
| Signal Processing, System Identification… | 121.622 | 11 | 52.525 |
| Dynamical_Behavior_of_Engineering_Structures… | 98.156 | 11 | 25.375 |
| Understanding_SHM_and_NDT | 45.546 | 7 | 14.190 |
| Sound Detection and Tracking | 26.333 | 4 | 10.161 |
| Brochure - SHM and NDT - 2 pages | 18.627 | 1 | — |
| From_Bridges_to_Photons | 12.322 | 1 | — |
| **toplam** | **684.985** | **47** | 56.454 |

İçerik: 101 şekil (55 altyazılı), 25 veri tablosu, 12 callout, 107 liste öğesi, 48 başlık.

**Sonuç:** hiçbir belge bölünmek zorunda değil. Bölme kararı SEO ve büyüme payı için;
maliyeti korpus genelinde +555 bayt (%0,08).

---

## 3. Manifest şeması — Aşama 2'nin okuyacağı sözleşme

Bu bölüm bilerek var: şema şimdiye kadar yalnızca kodda ve üretilen dosyada belgeliydi.

```
source                    kaynak .docx dosya adı
slug                      çıktı dizininin adı, kayıt id'si için aday
title_candidates          [str] — Title stilli paragrafların metni; CMS kaydının başlığı
                          buradan seçilecek. Word'de Title stili yoksa boş.
records[]                 part          1'den başlayan parça numarası, part-NN.json ile eşleşir
                          titles        [str] — bu kaydın kapsadığı bölüm başlıkları.
                                        titles[0] == "" başlıksız önsöz demek; yalnız ilk
                                        kayıt taşıyabilir.
                          bytes         part-NN.json'un diskteki boyutu
                          over_limit    500.000'i aşıyor mu
figures[]                 number        okuma sırası. SAYFAYA BASILMAZ — yazarın kendi
                                        altyazı metni kendi numarasını taşıyor ve ikisi
                                        ML rehberinde kayıyor.
                          filename      figures/ altındaki dosya adı; Ricos IMAGE düğümünün
                                        src.id'si de budur
                          width/height  piksel. Ricos IMAGE düğümünde ZORUNLU.
                          caption       yoksa ""
media_files[]             figures/ altına gerçekten yazılan dosyalar
missing_media[]           bir şeklin referans verdiği ama yazılamayan dosya. **Boş değilse
                          Aşama 2 yüklemede patlar** — harici hedef ya da word/media/ dışı.
unreferenced_media[]      .docx'te duran ama hiçbir şeklin referans vermediği dosya
counts.*                  blocks, figures, figures_without_caption, figures_without_file,
                          tables, callouts, media_in_zip, drawings,
                          drawings_without_picture, drawings_without_picture_kinds,
                          headings, untitled_preamble_bytes
```

Denge kuralı: `drawings − drawings_without_picture == figures`. Tutmuyorsa bu bir
**dönüştürücü kusurudur** ve araç öyle söyler. Diğer bütün uyarılar belgeye dair bulgudur.

---

## 4. Aşama 2'ye taşınan bilinmesi gerekenler

**Eklenti şartı.** Wix doğrulayıcısı eklenti listesi olmadan `IMAGE` ve `TABLE` düğümlerini
reddediyor. `RichContentViewer`'da **"Show plugin content" açık olmazsa sitedeki 101 görsel
ve 25 tablo hiç görünmez.**

**Her yazımdan önce doğrula.** `POST /ricos/v1/ricos-document/validate`, `fixDocument: true`,
eklentiler: `IMAGE, TABLE, LINK, HEADING, TEXT_COLOR, DIVIDER, CODE_BLOCK, INDENT,
LINE_SPACING, TEXT_HIGHLIGHT, FONT_FAMILY, COLLAPSIBLE_LIST`. Bu projede iki kez
üretilmiş tip tanımlarına güvenip yanlış karar verdik; tek yetkili kaynak çalışan doğrulayıcı.
Wix dönen belgeye `tableData.cellPadding: []` ekliyor — bilinen ve zararsız.

**Görsel kimliği üç ayrı biçimde yazılıyor.** Ricos düğümüne çıplak id, CMS `IMAGE` alanına
`wix:image://v1/<id>/<ad>#originWidth=…`. Karıştırmak en sık render bozma sebebi.

**Bilinen sadakat sınırı.** Paragraf stilinden miras alınan kalın/italik `rpr.find()` ile
görünmüyor; korpusta 340 doğrudan kalın işareti var, yani doğrudan biçimlendirme baskın ve
bu sınır hiç tetiklenmedi. Stil zincirini yürümek gerekirse ayrı iş.

**Callout şekli doğrulanmış ama tek çocukla sınırlı.** `BLOCKQUOTE` tek paragraf alıyor;
çok paragraflı aside'lar `"\n"` metin düğümüyle birleştiriliyor. Bu Wix'in kendi
`fixDocument` çıktısının birebir aynısı.

**`_style_means` yalnız 1-4 başlık seviyesi tanıyor.** Korpusta `Heading3` ve üstü yok.
Karar tek yerde ve yorumlu; genişletmek bir satır.

---

## 5. Hocaya sorulacaklar — belgelerden çıkan bulgular

1. **ML rehberinde dört altyazının görseli yok.** "Figure 1.", "Figure 3.", "Figure 5." ve
   "Table 1." altyazı satırları var ama önlerinde resim yok. Silinmiş ya da hiç eklenmemiş.
2. **ML rehberinin 1. bölüm başlığı gövdede yok.** Kendi içindekiler listesi on iki bölüm
   sayıyor, gövdede on bir `Heading1` var; "1. What is Machine Learning?" hiçbir yerde
   başlık değil. O bölüm 43.751 baytlık başlıksız önsöz olarak çıkıyor.
3. **Signal Processing'de 26 şeklin 23'ünde altyazı yok.** Dönüştürücü kusuru değil, yazılmamış.
   Yedisi kitap kapağı sırası ve fiilî açıklamaları "Left to right: …" paragrafları.
4. `From_Bridges_to_Photons.docx` nereye girecek? Ne PPT'de ne taslakta yeri var.
5. 196 MB'lık sunum nasıl servis edilecek?
6. Taslakta "coming soon" yazan her şey: CV, e-posta, ofis, Scholar/ResearchGate/ORCID.
7. Blog: sekiz yazı taşınacak mı? Görsel id'leri elimizde, OCR ile kurtarılabilir.
8. Galeri ne olacak? PPT metni belgelerin orada duracağını söylüyor, mevcut galeri 27 fotoğraf.

---

## 6. Bilerek bırakılanlar

Hiçbiri bu korpusta tetiklenmiyor:

- İki bütün-sözlük düğüm testi üretilmiş id'leri (`n1`/`n2`/`n3`) sabitliyor; id sırası
  değişirse düğüm şekliyle alakasız bir sebepten kırmızı olur.
- `emit.py` alıntı paragrafında `style` alanını temizliyor ama `role`'ü temizlemiyor.
  `_para` şu an `role` okumuyor, o yüzden zararsız.
- `w:numPr` içinde `w:ilvl` olup `w:numId` olmayan paragraf: `list_id=""` ile gruplanır,
  iki alakasız liste birleşebilir. Korpusta 107 `w:numPr`'ın hiçbiri böyle değil.
- İç içe tablo düzleştirmesi her derinlikte boş paragraf enjekte ediyor; korpusta iç içe
  tablo yok.
- `pack` bölüm sayısında karesel; 47 bölümde 0,17 sn. Birkaç yüz bölümde değiştirilecek.
