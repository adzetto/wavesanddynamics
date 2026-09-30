# Aşama 1 devir notu — docx → Ricos dönüştürücüsü

Tarih: 22 Eylül 2026
Durum: **bitti.** 29 + 5 commit, 171 test, çıktı Wix'in kendi doğrulayıcısından geçiyor.
Aşama 1b (aynı gün, sadakat işi, commit yok): 299 test; iki yeni şekil doğrulayıcıya
sorulmadı — §7.7.
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

**Aşama 1b sonrası (22 Eylül, sadakat işi — §7):** toplam 698.245 bayt (+13.260, %1,9;
tamamı renk dekorasyonu). Şekil 101, tablo 25, liste öğesi 107, başlık 48 **değişmedi**.
Callout 12 → 18 (altı kutu paragraf kenarlığıyla çizilmişti, §7.4), 6 yatay çizgi (DIVIDER),
182 renkli run. Belge başına: Brochure 20.299 · Dynamical 99.636 · From_Bridges 12.959 ·
ML 368.354 (%73,7) · Signal 124.814 · Sound 26.552 · Understanding 45.631.

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
colors                    {"#rrggbb": run sayısı} — SAYFAYA ULAŞAN metin renkleri (§7.2'nin
                          süzgecinden geçenler). Aşama 2 site paletine eşlemek isterse
                          listesi budur; eşlemezse düğümlerdeki hex olduğu gibi kalır.
counts.*                  blocks, figures, figures_without_caption, figures_without_file,
                          tables, callouts, media_in_zip, drawings,
                          drawings_without_picture, drawings_without_picture_kinds,
                          headings, untitled_preamble_bytes
                          — Aşama 1b'de eklenenler (hepsi ekleyici, eski anahtarlar aynı):
                          rules               DIVIDER sayısı (paragraf kenarlığından çizgi)
                          equations           OMML (m:oMath) denklem sayısı; doğrusal metne
                                              çevrildi, sayfada okunmalı
                          objects             gömülü OLE nesnesi sayısı; HİÇBİRİ sayfaya
                                              ulaşmaz. MathType (Equation.DSMT4) bunlardan
                                              biri: Word'de OMML'e çevrilip yeniden dışa
                                              aktarılmalı
                          object_kinds        {ProgID: adet}
                          footnotes           dipnot + sonnot referansı; metne [n], gövdenin
                                              ardına "[n] …" paragrafı
                          internal_links      belge içine (yer imine) giden bağlantı; sözcük
                                              kalır, bağlantı kalmaz — hedef sayfa Aşama 2'nin
                          strikethrough_runs  üstü çizili run; düz metin olarak yayımlanır
                          unmapped_symbols    tabloda karşılığı olmayan w:sym; metinde U+FFFD
                          text_boxes          metin kutusu; paragrafları demirlendiği
                                              paragrafın ardına alınır
                          colored_runs        sayfaya renkli ulaşan run sayısı
```

`callouts` artık iki kaynaktan gelir: tek hücreli tablo (12) ve sol kenarlıklı paragraf
kutusu (6). `blocks` üst düzey blok sayısıdır; çizgiler ve not paragrafları dahil, kutuya
katlanan paragraflar hariç.

Denge kuralı: `drawings − drawings_without_picture == figures`. Tutmuyorsa bu bir
**dönüştürücü kusurudur** ve araç öyle söyler. Diğer bütün uyarılar belgeye dair bulgudur.
`objects > 0` da belgeye dair bulgudur ama **içerik kaybı** demektir: uyarı satırı ne
yapılacağını söyler.

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

**Sadakat sınırı kalktı (Aşama 1b).** Stil zinciri artık yürünüyor: docDefaults → paragraf
stili (basedOn boyunca) → karakter stili → doğrudan biçimlendirme. Ölçüm, eski notun
"hiç tetiklenmedi" yargısını yanlışladı: Sound Detection ve From_Bridges'in Title paragrafları
yalnız stil üzerinden kalındı ve sayfaya düz gitmişti. Ayrıntı §7.1.

**Callout şekli doğrulanmış ama tek çocukla sınırlı.** `BLOCKQUOTE` tek paragraf alıyor;
çok paragraflı aside'lar `"\n"` metin düğümüyle birleştiriliyor. Bu Wix'in kendi
`fixDocument` çıktısının birebir aynısı.

**`_style_means` 1-6 başlık seviyesi tanıyor** (Aşama 1b; Ricos'un çizdiği altı seviye).
Heading7-9 seviye 6'ya kırpılır: fazla derin bir başlık yine başlıktır. Korpusta `Heading3`
ve üstü yok.

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

Aşama 1b'de kapatılanlar: `w:numId`'siz `w:numPr` (stil zincirinden okunur, yoksa liste
değildir), iç içe tablonun boş paragraf enjeksiyonu (iç hücrenin boşları atılır), `pack`'in
karesel maliyeti (bölüm başına bir emit; sınırın onda birine yaklaşınca kesin ölçüm).

Hiçbiri bu korpusta tetiklenmiyor:

- İki bütün-sözlük düğüm testi üretilmiş id'leri (`n1`/`n2`/`n3`) sabitliyor; id sırası
  değişirse düğüm şekliyle alakasız bir sebepten kırmızı olur.
- `emit.py` alıntı paragrafında `style` alanını temizliyor ama `role`'ü temizlemiyor.
  `_para` şu an `role` okumuyor, o yüzden zararsız.
- **Tablo stili** (`w:tblStyle` / `w:tblStylePr firstRow`) üzerinden gelen kalın başlık satırı
  çözülmüyor; `header_row` yalnız run'ların (stil dahil) kalınlığına bakar. Korpusun 25
  tablosunun hiçbiri tablo stiliyle biçimlenmiş değil (ölçüldü: yalnız `TableGrid`, rPr'siz).
- **Başlık stilleri id ile** eşleniyor (`Heading1`), adla değil. Yerelleştirilmiş Word
  (Türkçe: id `Balk1`, ad `heading 1`) başlıkları kaybeder. Hyperlink stili için ad eşlemesi
  yapıldı (§7.1); başlıklar için aynı şey bir satır, korpusun yedisi de İngilizce Word.
- **Küçük büyük harf** (`w:smallCaps`) olduğu gibi kalır; düz metin karşılığı yok.
- **Üstü çizili** metin düz yayımlanır ve sayılır; Ricos'ta dekorasyonu yok, uydurulmadı.
- **Hücre gölgesi** (`w:shd` on `tcPr`) taşınmıyor; bu yüzden beyaz metin de taşınmıyor (§7.2).
- **Metin kutusunun** yeri kaybolur: paragrafları demirlendiği paragrafın ardına düşer.
- **Denklem düzeni** kaybolur: OMML tek satır metne iner (§7.5). MathType hiç okunmaz.
- **İç bağlantılar** ve "Section 5.3"/"Figure 7" göndermeleri bağlantıya çevrilmez; hedef
  sayfa/çapa Aşama 2'de doğar. Korpusta 52 iç bağlantının 51'i içindekiler satırı (atılır),
  biri (`Linear%20Programming`, Signal) belgede olmayan bir yer imine gidiyor — Word'de de kırık.
- Bir metin kutusu içindeki **ikinci** kutu, iç paragrafı üzerinden okunur; `mc:Choice` ile
  `mc:Fallback` kopyaları arasında seçimi yalnız dış kutuda yapıyoruz.

---

## 7. Aşama 1b — sadakat kuralları (22 Eylül)

Yedi belgede ölçülüp yapılanlar ve ölçülmediği halde ucuz olduğu için yapılanlar. Kural
"ölç, varsayma": her madde korpustaki sayısıyla.

### 7.1 Stil zinciri (korpusta var)

`Run` işaretleri artık çözümlenmiş değerdir: docDefaults → paragraf stili (basedOn boyunca)
→ karakter stili → doğrudan. Toggle özellikler (`b i caps smallCaps strike vanish`) ECMA-376
§17.7.3'e göre: doğrudan mutlak; paragraf stili VE karakter stili ikisi de açıksa **kapalı**
(XOR); yalnız biri söylüyorsa o. Diğerleri (u, color, highlight, vertAlign) yakın olan kazanır.
Word'ün `Hyperlink`/`FollowedHyperlink` karakter stili **ada göre** tanınıp yok sayılır:
korpusta 61 bağlantı run'ı bu stille mavi+altı çizili; hiçbiri yazarın işareti değil,
sayfada bağlantıyı site biçimler. `w:pPr/w:rPr` (paragraf işareti) okunmaz (korpusta 55).
Korpusta tetiklenen: Title kalınlığı (3 run, iki belge), Caption italik (18 run, altyazıya
katlanıyor), Hyperlink altı çizgisi (61, yok sayılıyor).

### 7.2 Renk (korpusta ~1.700 run)

`Run.color`, belgenin **gövde renginden sapma**dır. Gövde rengi: docDefaults rengi (Dynamical,
Signal: 222831) ve karakter sayısına göre çoğunluk rengi (ML: 262626 %85, Brochure: 1A1A1A
%74). `auto`/`000000` renk değil. Sayfaya çıkarken üç süzgeç daha (`emit.color_on_page`):
başlıkta renk yok (Word'ün başlık mavisi 2E74B5 her Heading1'de, tema karar verir); bağlantıda
renk yok; beyaza karşı kontrastı 3:1'in altındaki renk yok (koyu dolgulu hücrelerdeki 26 beyaz
run, ML'nin A6A6A6 başlık satırı) — hücre gölgesi taşınmadığından görünmez metin olurdu.
Vurgu (`w:highlight`, `w:shd`) → `colorData.background`; korpusta 0. Sonuç: 182 renkli run,
+13.260 bayt. `manifest.colors` sayfaya ulaşan listedir; Aşama 2 site paletine (`--maroon`
#8C1A1A, `--navy` #1B3A6B) eşlemek isterse yazarın koyu kırmızıları (7A0000, 8A0000, A30D0D,
8E0000) ve grileri (595959, 6B7280) buradan görülür. **Karar sahibi:** renkleri olduğu gibi mi
taşımalı, palete mi eşlemeli, hiç mi taşımamalı — bu araç "olduğu gibi, süzgeçle" yapar.

### 7.3 Üst/alt simge, üstü çizili, büyük harf

Ricos'ta dekorasyonu yok, uydurulmadı. Üst/alt simge metne iner: Unicode karşılığı olan her
karakter (rakam, işaret, parantez, alt simge harfleri, ⁿ ⁱ) glife (`10⁶`, `xᵢ`), olmayan
Word'ün doğrusal denklem notasyonuna (`P_A`, `e^(iωt)`). Korpusta 2 alt simge
(From_Bridges: `P = P_A + P_B`). `w:caps` metni büyük harfe çevirir (korpusta 0).
Üstü çizili: 0; REST referansının belgelediği `STRIKETHROUGH` dekorasyonuyla yazılır (§7.7), sayılır ve uyarılır. Gizli metin (`w:vanish`, `w:webHidden`) okunmaz:
korpusta 52 `webHidden` run, hepsi içindekiler sayfa numarası.

### 7.4 Paragraf kenarlıkları → BLOCKQUOTE / DIVIDER (korpusta 20 + 11 paragraf)

Sol kenarlıklı (gölgeli, girintili) paragraf yazarın tablo çizmeden yaptığı kutudur:
Dynamical 3, From_Bridges 1, Signal 2, Understanding 14. Ardışık olanlar tek `Callout` (tek
hücreli tabloyla aynı BLOCKQUOTE şekli, `\n` ile birleşik). Resim kutuyu böler; altyazı önce
katlanır. Alt/üst kenarlık → paragrafın altına/üstüne `Rule` → `DIVIDER` (imza satırları,
ML başlık satırı, Brochure kapanış satırı, Signal'in yalnız kenarlıktan ibaret boş
paragrafı: 6). **Başlıktaki kenarlık başlığın süsüdür**, çizgi de kutu da olmaz
(Understanding'in altı Heading1'i). Hücre içinde uygulanmaz (doğrulayıcının görmediği şekil).

### 7.5 Denklemler (korpusta 0; hocanın gelecek belgelerinde kesin)

`m:oMath` / `m:oMathPara` artık paragraf çocuğu olarak okunur — eskiden hiç bakılmayan çocuktu,
denklem cümleden **sessizce** düşüyordu. `omml.linear` OMML'i Word'ün "Linear" gösterimine
indirir: `a/b`, `(a+b)/2`, `x²`, `e^(iωt)`, `P_A`, `√(k/m)`, `∛x`, `∑ᵢ₌₁ⁿ a`, `sin θ`,
`lim_(x→0) f`, `[1 2; 3 4]`, `x̄`, eşitlik dizisi satır satır. Görüntü denklemi
(`oMathPara`) kendi paragrafı, varsayılan ortalı. `counts.equations` + uyarı.
MathType (`w:object`, ProgID `Equation.DSMT4`) **okunamaz**: sayılır, uyarı Word'de OMML'e
çevirmeyi söyler. Ölçüm: yedi belgede 0 oMath, 0 nesne, 0 EMF/WMF (PROJECT.md'nin "MathType
EMF'ye düşer" uyarısı bu dosyalar için geçersiz, yenileri için geçerli).

### 7.6 Dipnot/sonnot, metin kutusu, iç bağlantı, sembol (korpusta 0 / 0 / 1 / 2)

Dipnot: metne `[n]`, gövdenin ardına `[n] …` paragrafı; dipnot ve sonnot tek sıra. Metin
kutusu: `wps` kopyası okunur, VML `mc:Fallback` kopyası değil (ikisi aynı kutu); paragrafları
demirlendiği paragrafın ardına. İç bağlantı (`w:anchor`): `Run.anchor`'a yazılır, sayılır,
bağlantı üretilmez. `w:sym`: Symbol ve Wingdings tabloları (ML'deki iki Wingdings F0E0 oku
→ `→`; eskiden düşüyordu: "in your mind  explore"); tabloda olmayan → U+FFFD + sayım.
Word 2016 emoji (`w16se:symEx`) fallback'teki `w:t` ile okunur ("develop your own 😊."):
`_text` yalnız run'ın doğrudan çocuklarını okur, çizimin içindeki metni değil.
Satır içi kapsayıcılar (`fldSimple`, `sdt/sdtContent`, `ins`, `smartTag`, `customXml`)
saydam; `w:del` atılır. Alan kodu (`instrText`) okunmaz, alan sonucu okunur (Sound
Detection'ın REF/SEQ alanları; artık testle sabit).

### 7.7 Şekillerin dayanağı — doğrulayıcıya sorulmayanlar Aşama 2'de ilk iş

Bu oturumda Wix anahtarı yoktu; hiçbir yeni şekil `POST /ricos/v1/ricos-document/validate`'e
sorulmadı. Ama bellekten de yazılmadı: Aşama 1'in geçici dizinde bıraktığı üç kaynak bulundu
ve `reference/ricos-schema/` altına alındı (README'de kökeni var) — npm `ricos-schema@10.102.0`
tip tanımı ve JSON Type Definition'ı, bir de dev.wix.com "Ricos Document" REST referansının
metni. Şekil şekil:

- `COLOR` — `{"type": "COLOR", "colorData": {"foreground": "#7a0000", "background":
  "#ffff00"}}` (alanlar isteğe bağlı; yalnız olanı yazılır). **Hem npm şeması hem REST
  referansı** böyle. `colorDecoration` eklentisi gerekir; §4'teki listede `TEXT_COLOR` ve
  `TEXT_HIGHLIGHT` zaten var.
- `DIVIDER` — `{"type": "DIVIDER", "id": …, "nodes": [], "dividerData": {"lineStyle":
  "SINGLE", "width": "LARGE", "alignment": "CENTER"}}`. **Hem npm şeması hem REST referansı:**
  `lineStyle` SINGLE|DOUBLE|DASHED|DOTTED, `width` LARGE|MEDIUM|SMALL, `alignment`
  CENTER|LEFT|RIGHT; `nodes` IMAGE'daki gibi `never[]`, doğrulayıcı orada `[]` kabul etmişti.
- `STRIKETHROUGH` — `{"type": "STRIKETHROUGH", "strikethroughData": true}`. **Yalnız REST
  referansı**; npm şemasının `Decoration` birleşiminde yok. ITALIC/UNDERLINE'ın doğrulayıcının
  kabul ettiği kalıbı (`italicData: true`). Reddedilirse metin düz kalır, yani bugünkü hal;
  sayım ve uyarı olduğu için sessiz değil. Korpusta 0.
- `SUPERSCRIPT` / `SUBSCRIPT` — REST referansı belgeliyor (`superscriptData` /
  `subscriptData`: boolean), npm şeması yok. **Bilerek kullanılmadı:** görüntüleyici tanımazsa
  `10⁶` sessizce `106` olur ve bunu hiçbir doğrulayıcı yakalamaz. Metin çözümü (§7.3) her
  koşulda doğru okunur. Canlı sitede bir denemeyle (Aşama 1'in bir blog yazısını Data API'den
  okuma yöntemi) görüntüleyicinin çizdiği görülürse geçiş tek yer: `emit._text_nodes`,
  `script()` yerine dekorasyon.
- `Link.anchor` — REST referansı ve şema: "hedef düğüm id'si", `url` ile `anchor` birbirini
  dışlar. İç bağlantılar (§7.6) buna bağlanır; yer imi → başlık düğüm id'si eşlemesi ve
  kayıtlar arası hedef Aşama 2'nin işi.
- `TableCellData.cellStyle.backgroundColor` — şemada var (COLOR_HEX). Hücre gölgesi taşınmak
  istenirse yeri burası; o gün beyaz metin de taşınır (§7.2). Bugün doğrulayıcının gördüğü
  `tableCellData: {}` korunuyor.

Aşama 1'in dersi aynen geçerli: tip tanımına değil, çalışan doğrulayıcıya güven — ve REST
referansı ile npm şeması birbirini tutmuyor, ikisine de değil.

### 7.8 Test ve ölçüm

171 → 299 test; `ruff check` ve `ruff format --check` temiz (format bu turda bütün ağaca
uygulandı; başlangıçta 18 dosya biçimlenmemişti). Korpus: şekil 101, tablo 25, liste 107,
başlık 48 aynı; callout 12 → 18; DIVIDER 6; kalın/italik/altı çizili **karakter** sayıları
belge başına aynı (Title kalınlığı kazanılan iki belge dışında: +187, +127 karakter).
