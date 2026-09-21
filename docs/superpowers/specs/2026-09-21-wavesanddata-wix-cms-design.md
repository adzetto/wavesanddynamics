# wavesanddata.com — Wix CMS + Ricos tasarımı

Dr. Korkut Kaynardağ'ın sitesinin Wix üzerinde yeniden kurulması. UI ve backend değişiyor,
barındırma Wix'te kalıyor.

Tarih: 21 Eylül 2026
Durum: **onay bekliyor** — kod yazılmadı, canlı sitede hiçbir değişiklik yapılmadı

---

## 1. Neden bu tasarım

Hocanın üç şartı var, üçü de kendi cümlelerinden:

1. Sol tarafta sabit menü ("sol kısımda menü olacak hep")
2. `/research` sayfasında dört kutu, tıklanabilir, **altlarında Word indirme bağlantısı**
3. Yeni bölüm eklemek ve mevcutları düzenlemek kolay olsun — asıl şart, iki kez tekrarladı

Buna bir de sitenin varlık sebebi ekleniyor: eğitim bölümleri insanlar bulsun diye yazıldı,
yani **arama görünürlüğü** pazarlık konusu değil. Bugünkü site bunu sağlamıyor; sekiz blog
yazısının gövdesi ekran görüntüsü, metin Google'a hiç ulaşmıyor.

Karar: Wix'te kal, ama içeriği CMS'e taşı ve sayfaları koleksiyondan üret. Böylece "yeni bölüm
eklemek" bir satır eklemeye indirgeniyor ve içerik gerçek HTML olarak render ediliyor.

Wix'ten çıkış günü geldiğinde dönüştürücü ve içerik yapısı elimizde kalır; yeniden yazılacak
olan yalnız sayfa düzeni.

---

## 2. Doğrulanmış teknik temel

Bu bölümdeki her madde ya Wix'in kendi belgesinden ya da **hocanın canlı sitesinden** teyit
edildi. Hafızadan yazılmış hiçbir şey yok.

### 2.1 Canlı siteden doğrulananlar

Site id `36a33e18-0863-4d42-8bbd-70c189d86351`. Yapılan her çağrı salt okunur.

- **Wix Code açık.** `GET /wix-data/v2/collections` hatasız döndü. Wix Data API'leri sitenin
  kod düzenleyicisi açık olmadan çalışmıyor, dolayısıyla bu aynı zamanda Dev Mode'un
  kullanılabilir olduğunu gösteriyor.
- **`RICH_CONTENT` gerçek bir alan tipi.** Hocanın `Blog/Posts` koleksiyonunda birebir duruyor:
  `{"key":"richContent","displayName":"Rich Content","type":"RICH_CONTENT"}`.
- **Ricos düğüm yapısı.** `stationary-wavelet-package-transformation` yazısının gerçek
  `richContent` değeri çekildi:

  ```json
  { "nodes": [
      { "type":"PARAGRAPH","id":"foo",
        "nodes":[{"type":"TEXT","textData":{"text":"...","decorations":[]}}],
        "paragraphData":{"textStyle":{"textAlignment":"JUSTIFY"},"indentation":0} },
      { "type":"IMAGE","id":"38nq2",
        "imageData":{"containerData":{"width":{"size":"CONTENT"},"alignment":"CENTER","textWrap":true},
                     "image":{"src":{"id":"ce0a40_ebddb73eb53b42de8043e2ae2102f9b3~mv2.png"},
                              "width":1341,"height":1684}} }
    ],
    "metadata":{"version":1,...}, "documentStyle":{} }
  ```

- **Görsel referansı öneksiz id.** `imageData.image.src.id` içinde `ce0a40_…~mv2.png`,
  `wix:image://` değil. Yanında `width`/`height` zorunlu.
- **Yerel medya aynası birebir tutuyor.** Bu yazıdaki id'ler `reference/wix-media/` altındaki
  dosyalarla aynı. Zaten Medya Yöneticisi'nde olan görseller yeniden yüklenmeden
  referanslanabilir.
- **Mevcut koleksiyonlar:** `adi6LightHalfFull` (iletişim formu gönderileri, 2023'ten beri
  gerçek veri — **dokunulmayacak**), `Blog/*`, `Members/*`, `Locations/*`, `Marketing/Coupons`.

### 2.2 Belgelerden doğrulananlar

**Tablo destekleniyor.** `TABLE → TABLE_ROW → TABLE_CELL` gerçek düğümler. Hücre içine
`PARAGRAPH`, `HEADING`, `BULLETED_LIST`, `ORDERED_LIST`, `IMAGE`, `BLOCKQUOTE` girebiliyor.
İç içe tablo giremiyor. `tableData.rowHeader` / `columnHeader` bayrakları var.
`RichContentViewer`'da "Show plugin content" açık olmalı.

**SEO çalışıyor.** Wix'in kendi belgesi: *"Database content that is loaded into page elements
using a dataset (instead of code) is included in the SSR version of your page and will be seen
by search engines."* Ajan bunu canlı bir Ricos sayfasını Googlebot kimliğiyle, JavaScript
çalıştırmadan çekerek de doğruladı: makale metni ham HTML'de var ve hiçbir `<script>` bloğunun
içinde değil; başlıklar gerçek `<h1>/<h2>/<h3>`, görsellerin hepsi `alt` taşıyor, `canonical`
ve `og:*` ilk yanıtta.

**Ama önizleme hiçbir şey kanıtlamaz.** *"Rendering never occurs server-side when previewing a
site."* Test yalnız yayındaki sitede yapılır.

**Dışarıdan yazma mümkün.** Hesap düzeyinde API anahtarı, `Authorization: <API_KEY>`
(Bearer öneki yok) ve `wix-site-id: <SITE_ID>` başlıkları. Tek siteye kısıtlanabiliyor ve tek
tıkla iptal edilebiliyor.

### 2.3 Kritik ayrım: görsel kimliği üç ayrı biçimde yazılıyor

En sık kırılma sebebi bu. Karıştırılmayacak:

| Nereye | Ne yazılır |
|---|---|
| CMS `IMAGE` alanı | `wix:image://v1/<file.id>/<dosyaadı>#originWidth=<W>&originHeight=<H>` |
| CMS `MEDIA_IMAGE` alanı | nesne: `{"id":…,"url":…,"width":…,"height":…,"altText":…}` |
| **Ricos `IMAGE` düğümü** | **öneksiz**: `imageData.image.src = {"id":"<file.id>"}` |

Ricos düğümüne `wix:image://` yazmak render'ı bozuyor. Bu ayrım hem Wix'in kendi tarifinde
yazılı hem de hocanın canlı verisinde görüldü.

---

## 3. Bu tasarımı şekillendiren sınır: kayıt başına 500 KB

Wix geliştirici belgesi 500 kb, yardım merkezi 512 KB diyor. **500 KB'a göre planlanacak.**
Aşıldığında `WDE0009: Document is too large` ile başarısız oluyor.

Önemli olan şu: medya alanları (image, document, video, audio, gallery) bu sınıra **dahil
değil**, ama **Rich Content dahil**. Yani Ricos JSON'unun tamamı 500 KB'a sığmak zorunda.

**Ölçüldü (22 Eylül 2026).** Dönüştürücü yazıldı, yedi belgenin tamamı gerçek Ricos'a
çevrildi ve çıktı **Wix'in kendi doğrulayıcısından** geçirildi (`POST /ricos/v1/ricos-document/validate`
→ `valid: true`, sıfır ihlal). Bu paragrafın ilk hali "ML rehberi tek kayda büyük ihtimalle
sığmaz" diyordu; ölçüm aksini söylüyor.

**Tek kayıt olarak:**

| belge | bayt | sınıra oranı |
|---|---:|---:|
| Machine Learning - The Complete Picture and Guide_5 | **362.379** | **%72,5** |
| Signal Processing, System Identification… | 121.622 | %24 |
| Dynamical_Behavior_of_Engineering_Structures… | 98.156 | %20 |
| Understanding_SHM_and_NDT | 45.546 | %9 |
| Sound Detection and Tracking | 26.333 | %5 |
| Brochure - SHM and NDT - 2 pages | 18.627 | %4 |
| From_Bridges_to_Photons | 12.322 | %2 |
| **toplam** | **684.985** | |

Yani **hiçbir belge bölünmek zorunda değil.** Ricos tablo JSON'u konuşkan (büyüme hücre
sayısını takip ediyor: ML ×2,35, Signal Processing ×1,88, tablosuz Sound Detection ×1,25) ama
en büyüğü bile sınırın altında.

**Bölüm başına bir kayıt olarak:**

| belge | bölüm | en büyük bölüm | sınıra oranı |
|---|---:|---:|---:|
| Machine Learning | 12 | 56.454 | **%11,3** |
| Signal Processing | 11 | 52.525 | %10,5 |
| Dynamical Behavior | 11 | 25.375 | %5,1 |
| Understanding_SHM_and_NDT | 7 | 14.190 | %2,8 |
| Sound Detection and Tracking | 4 | 10.161 | %2,0 |
| Brochure / From_Bridges | 1 | — | |
| **korpus** | **47** | 56.454 | |

**Bölmenin maliyeti korpus genelinde +555 bayt, yani %0,08.** ML'de maliyet negatif bile
çıkıyor (−712): on bir fazladan sarmal, kısalan düğüm id'leriyle fazlasıyla karşılanıyor.

**Sonuç: bölüm başına bir kayıt — ama gerekçesi teknik değil.**

Bölme kararı iki sebeple ayakta:

- **SEO ve okunabilirlik.** 44 sayfalık tek dev sayfa yerine 12 indekslenebilir sayfa.
  Sitenin varlık sebebi arama görünürlüğü olduğuna göre bu kayıp değil kazanç.
- **Büyüme payı.** Belge 15-21 Eylül arasında 9.246'dan 18.192 kelimeye çıktı. Tek kayıtta
  kalan pay yaklaşık 7.000 kelime; altı günde 9.000 kelime ekleyen biri için ince bir pay.
  Bölünmüş halde en büyük bölüm sınırın yalnızca %11,3'ü, yani bu sorun tamamen kalkıyor.

ML rehberinde bir uyarı: gövdede on bir `Heading1` var ama yazarın kendi içindekiler listesi
on iki bölüm sayıyor. **"1. What is Machine Learning?" başlığı belgede hiç yok**, o yüzden o
bölüm 43.751 baytlık başlıksız bir önsöz olarak çıkıyor. Uydurma başlık konulmadı; hocaya
sorulacak.

Her yazımdan önce `JSON.stringify(ricos).length` ölçülecek ve 500 KB'ın altında olduğu
doğrulanacak; aşarsa bölüm daha küçük parçalara ayrılacak.

---

## 4. Veri modeli

Tek koleksiyon: **`Sections`**.

| alan | tip | ne işe yarıyor |
|---|---|---|
| `title` | TEXT | başlık |
| `slug` | TEXT | URL parçası, aynı zamanda kayıt id'si |
| `order` | NUMBER | menü ve liste sırası |
| `parentSlug` | TEXT | bölüm bir belgenin alt bölümüyse üst belgenin slug'ı, değilse boş |
| `subLabel` | TEXT | menüdeki alt etiket (yalnız Signal Processing'de dolu) |
| `inMenu` | BOOLEAN | sol menüde görünsün mü |
| `kind` | TEXT | `topic` \| `document` \| `chapter` \| `page` |
| `linkUrl` | TEXT | yalnız `kind="page"` satırlarında dolu; sabit sayfanın yolu |
| `summary` | TEXT | kart ve giriş metni |
| `icon` | IMAGE | PPT'den çıkan dört ikon |
| `body` | **RICH_CONTENT** | dönüştürülmüş gövde |
| `sourceFile` | DOCUMENT | indirilebilir .docx |
| `sourceHash` | TEXT | yeniden yüklemeyi tespit etmek için |
| `updatedAt` | DATETIME | |

İzinler: `{"insert":"ADMIN","update":"ADMIN","remove":"ADMIN","read":"ANYONE"}`. CLI, API
anahtarı yöneticisi kimliğiyle `ADMIN` karşılığını sağlıyor; ziyaretçi yalnız okuyor.

Bu tek koleksiyon dört şeyi besliyor: sol menü, ana sayfadaki üç kart, `/research`'teki dört
kutu, ve bölüm sayfalarının gövdesi. **Yeni bölüm eklemek = koleksiyona satır eklemek.**

### 4.1 Başlangıç içeriği

`kind = "topic"` (ana sayfadaki üç kart, sol menüde):

| slug | kaynak | kelime | şekil | tablo |
|---|---|---|---|---|
| `vibrations-waves` | Dynamical_Behavior_of_Engineering_Structures… | 7.260 | 26 | 2 |
| `signal-processing` | Signal Processing, System Identification, and Optimization | 7.108 | 26 | 1 |
| `machine-learning` | Machine Learning - The Complete Picture and Guide_5 | 18.192 | 30 | 28 |

`kind = "document"` (`/research`'teki dört kutu, PPT slayt 3'ün birebir karşılığı):

| kutu | kaynak | boyut |
|---|---|---|
| SHM/NDT (Short) | Brochure - SHM and NDT - 2 pages.docx | 587 kelime, 8 görsel, 6 tablo |
| SHM/NDT (Extended) | Understanding_SHM_and_NDT.docx | 4.037 kelime, 6 şekil |
| Sound Wave Tracking | Sound Detection and Tracking.docx | 2.531 kelime, 3 şekil |
| Extensive MSc/PhD ppt | PhD_MsC_entire_Review_ppt.pptx | 177 slayt, 196 MB |

Machine Learning rehberi 12 ayrı `kind = "chapter"` kaydına bölünecek — 500 KB sınırı yüzünden
değil (§3: tek kayıt olarak %72,5'te kalıyor), arama görünürlüğü ve büyüme payı için,
her birinde `parentSlug = "machine-learning"`. Üstteki `machine-learning` satırı `topic` olarak
kalıyor; gövdesinde yalnız giriş metni ve bölüm listesi bulunuyor, asıl içerik alt kayıtlarda.
Diğer iki eğitim belgesi ölçülüp gerekirse aynı şekilde bölünecek.

`kind = "page"` satırları koleksiyonda içerik tutmuyor, yalnız menüde yer alıyor ve `linkUrl`
ile sabit sayfaya işaret ediyor: Home, About Me, My Research Areas, Gallery, Blog, Contact.
Böylece menünün tamamı tek bir kaynaktan geliyor ve sıralaması tek yerden değişiyor.

`From_Bridges_to_Photons.docx` (~900 kelime, çift yarık deneyi) henüz yersiz — hocaya
sorulacak.

---

## 5. Sayfalar

**Sol menü (master sayfa).** `Sections` koleksiyonuna bağlı repeater, `inMenu` filtreli,
`order` sıralı. Hedef adres `kind="page"` satırlarında `linkUrl`'den, diğerlerinde `slug`'dan
türetiliyor. Üstte dairesel fotoğraf, serif isim, iki satır unvan. Etkin satır üç işaretle:
kenardan kenara koyulaşan zemin, sol kenara yapışık 3px bordo çubuk, koyulaşan yazı.

Menü sırası PPT'den (sekiz madde; "Home" PPT'de yok, Lovable eklemişti, koruyoruz):
Home · About Me · My Research Areas · Gallery · Vibrations and Waves ·
Signal Processing & Optimization *(alt etiket: System Identification · Estimation · Optimization)* ·
Machine Learning · Blog · Contact

**`/sections/{slug}`** — dinamik sayfa. Başlık, giriş, `RichContentViewer` (dataset'e bağlı,
kodla değil), altında "Download as Word". `parentSlug` doluysa üstte üst belgeye dönüş
bağlantısı, yanında kardeş bölümlerin listesi.

**`/research`** — dört kutu, `kind="document"` filtreli repeater, PPT ikonlarıyla. Kutu
tıklanınca kendi sayfasına gider; **kutunun altında ayrı Word indirme bağlantısı** durur.
Hocanın son mesajında istediği tam olarak bu.

**Ana sayfa, `/about`, `/contact`** — sabit sayfalar. Metinleri Lovable taslağından ve PPT'den
elimizde; `/about`'taki "At a glance" sayıları (12 makale, 2 patent, 8 ödül) PPT slayt 2'deki
kendi cümlesinden geliyor.

### 5.1 Renkler

PPT'nin içindeki dört ikon 1024×1024 sıkıştırılmamış PNG; renkler doğrudan pikselden okundu:

| jeton | değer |
|---|---|
| `--navy` | `#1B3A6B` |
| `--maroon` | `#8C1A1A` |
| `--rose` | `#A54C4B` |
| `--rose-light` | `#C48B8A` |
| `--slate` | `#8B9AB2` |
| `--white` | `#FDFCFB` |

Vurgu bordo, mavi değil. Tam çözünürlüklü vesikalık da PPT'nin içinden çıktı:
`content/source/ppt-icons/headshot-708.png`, 708×691.

---

## 6. docx → Ricos hattı

Ağır iş Wix'te dönmüyor. Velo backend'inde Python yok, npm sınırlı; dönüşüm yerelde yapılıyor,
sonuç API ile yazılıyor.

Adımlar:

1. **docx → HTML**, yerelde (mammoth veya pandoc). Belgelerde gerçek `Heading1`/`Heading2`
   stilleri kullanılmış, bu doğrulandı — stil eşlemesi çalışır.
2. **Şekilleri çıkar**, Medya Yöneticisi'ne yükle, `file.id` + genişlik/yükseklik sakla.
3. **Blok modeli → Ricos**, kendi yayıcımızla. Wix'in `POST /ricos/v1/ricos-document/convert/to-ricos`
   uç noktası var ama üç sebeple kullanılmıyor: ağ erişimi istiyor (Aşama 1 çevrimdışı çalışacak),
   girdisi **30.000 karakterle sınırlı**, ve genel bir dönüştürücü olduğu için bizim ihtiyacımız
   olan üç ayrımı yapamıyor — hangi tablonun aslında callout olduğu, hangi italik satırın hangi
   şeklin altyazısı olduğu, ve hangi paragrafın hangi başlık stilini taşıdığı. Hedef düğüm
   şekilleri hocanın canlı sitesinden birebir okunduğu için kendi yayıcımızı yazmak risk değil.
   Wix'in dönüştürücüsü yalnız çapraz kontrol için kullanılabilir.
4. **Şekil düğümlerini yamalar:** her `IMAGE` düğümünün `src`'sini `{"id":"<file.id>"}` yap,
   `width`/`height` doldur, `altText` ve `CAPTION` alt düğümünü ekle.
5. **Doğrula:** `POST /ricos/v1/ricos-document/validate` (`fixDocument: true`).
6. **Boyut kontrolü:** `JSON.stringify(ricos).length < 500_000`. Aşarsa bölümü ayır.
7. **Yaz:** `POST /wix-data/v2/items/save`, `dataItem.id` = slug. Yanıttaki `action` alanı
   `INSERTED` mi `UPDATED` mi söylüyor.

### 6.1 Dönüştürücünün uyması gereken kurallar

Hepsi doğrulandı, hepsi sessizce bozulma sebebi:

- Her düğümün benzersiz `id`'si zorunlu; harfle başlar, harf/rakam/tire/alt çizgi içerir.
- `TEXT` asla çıplak duramaz, hep `PARAGRAPH` içinde. Aksi halde
  `Expected a paragraph node but found TEXT`.
- Boş Word hücresi = TEXT'siz boş `PARAGRAPH`, `""` metinli TEXT değil.
- Şekil altyazısı ayrı `CAPTION` alt düğümü. `imageData.caption` kullanımdan kalkmış ama
  resmî örnekler ikisini birden yazıyor; biz de ikisini yazacağız.
- `colspan`/`rowspan` REST şemasında görünüyor ama Ricos referansında ve npm şemasında yok —
  güvenilmeyecek, birleşik hücreler düzleştirilecek.
- Hiçbir belgede OMML denklemi veya MathType nesnesi yok; 98 şeklin hepsi PNG. MathType
  dönüştürme adımı gerekmiyor.
- Tek hücreli Word tabloları callout kutusu; `<aside>` karşılığı `BLOCKQUOTE` veya
  `COLLAPSIBLE_LIST` olarak eşlenecek, `TABLE` olarak değil.
- Gruplanmış Word şekilleri hem pandoc'ta hem mammoth'ta sessizce kayboluyor. Dönüştürücü
  bunları sayıp uyaracak; o şekiller SVG olarak yeniden çizilecek.
- Metindeki "Figure 7" / "Section 5.3" göndermeleri çapaya bağlanacak.

---

## 7. CLI

`ingest <dosya.docx> [--section <slug>]`

Akış: aç → HTML'e çevir → şekilleri yükle (`filePath: /sections/<slug>/figures`) →
`operationStatus` `READY` olana kadar yokla → Ricos'a çevir → doğrula → boyutu ölç → kaydı yaz.

Yeniden çalıştırılabilir olacak: yüklenen dosyaların `file.id`'leri yerel bir manifestte
tutulacak, ikinci çalıştırmada aynı görseller yeniden yüklenmeyecek. Kayıt yazımı `save` ile
yapıldığı için önce okuma gerekmiyor — bu aynı zamanda Wix'in eventual consistency'sinden
kaynaklanan çift kayıt riskini ortadan kaldırıyor.

İşlenecek hatalar: `WDE0009` (kayıt çok büyük), `WDE0014` / 429 (dakikalık kota — 60 saniye
bekleyip tekrar dene), `SITE_QUOTA_EXCEEDED`, `FILE_SIZE_OVER_LIMIT`, `MISMATCH_MIME_TYPE`.
Toplu çağrılar HTTP 200 dönüp tek tek başarısızlıkları gövdede bildiriyor; yalnız durum koduna
bakmak yetmez.

Bir tuzak: `save` kaydın tamamını değiştiriyor, göndermediğin alan siliniyor. Tek alan
güncellemek gerekirse `POST /wix-data/v2/items/patch`.

Bir tuzak daha: koleksiyon şeması dayatılmıyor. Yanlış yazılmış bir alan adı hata vermeden
çöp yazıyor. Alan adları sabit bir listeden gelecek.

### 7.1 Güvenlik

API anahtarı yalnız CLI'nin bağımsız çalışması için gerekli (bkz. §11, Aşama 3). Geliştirme ve
doğrulama sırasında Wix MCP oturumunun mevcut yetkisi kullanılacak.

API anahtarını **hocanın kendisi** oluşturacak: hesap sahibi olarak
`manage.wix.com/account/api-keys`, SMS doğrulamalı. Anahtar tek siteye kısıtlanacak ve tek
tıkla iptal edilebiliyor.

Verilecek yetkiler yalnız şunlar:

- `SCOPE.DC-DATA.WRITE` — kayıt yazma
- `SCOPE.DC-DATA.DATA-COLLECTIONS-MANAGE` — koleksiyon ve alan oluşturma
- `SCOPE.DC-MEDIA.MANAGE-MEDIAMANAGER` — medya yükleme
- `SCOPE.DC-RICOS.MANAGE-DOCUMENTS` — Ricos dönüştürme/doğrulama

Anahtar yerelde açık metin durmayacak: parola ile türetilen anahtarla şifrelenmiş dosyada
tutulacak. Ama güvenliği asıl sağlayan şifreleme değil, **anahtarın dar ve iptal
edilebilir olması**. Parolayla açılan bir anahtar o makinede çözülebilen anahtardır; şifreleme
yalnız dosyanın tek başına çalınmasına karşı korur. Sızma halinde etki alanı "bu sitenin
CMS'ine yazılabilir" ile sınırlı kalır ve anahtar anında iptal edilir.

CLI ileride hocaya tek dosyalık çalıştırılabilir olarak paketlenebilir: parola → bölüm seç →
.docx seç → önizle → yayınla. Bu ikinci aşama.

---

## 8. SEO

- `RichContentViewer` editörde **dataset'e bağlanacak**, kodla doldurulmayacak. Wix'in açıkça
  SSR garantisi verdiği yol bu. Kodla doldurmak da render ediliyor ama async iş `onReady`den
  sonra çözülürse HTML'e yetişmiyor; promise'i `return` etmek gerekiyor. Dataset bağlaması bu
  tuzağı tamamen atlıyor.
- Sayfa başına başlık/açıklama/OG/şema, SEO Ayarları → sayfa tipine göre düzenle →
  `+ Add Variable` ile koleksiyon alanlarından beslenecek. Kod gerekmiyor.
- Dinamik sayfalar `/dynamic-{prefix}-sitemap.xml` altına düşüyor. Forumda "görünmüyor"
  şikayetleri var, Wix'ten resmî cevap yok — **yayın günü elle kontrol edilecek.**
- Eski URL'ler değişiyor, yönlendirme gerekiyor: `/personal-resume` → `/about`,
  `/research-portfolio` → `/research`, `/structural-dynamics-and-wave-propagation` →
  `/sections/vibrations-waves`, `/signal-processing-optimization-ml` ikiye bölünüyor,
  `/fullscreen-page` kalkıyor.
- Test **yalnız yayındaki sitede**. Önizleme sunucu tarafında render etmiyor.

---

## 9. Doğrulama denemesi (ilk iş)

Kobay: **`Brochure - SHM and NDT - 2 pages.docx`** — 587 kelime ama içinde 8 görsel ve 6 tablo
var. Küçük ama her bileşeni test ediyor.

Uçtan uca geçirilecek ve şunlar ölçülecek:

1. Tablolar `RichContentViewer`'da doğru render ediliyor mu
2. Kayıt boyutu ne çıkıyor — 500 KB bütçesini gerçek veriyle kalibre etmek için
3. Yayındaki sayfanın ham HTML'inde metin ve tablolar görünüyor mu (JavaScript çalıştırmadan,
   Googlebot kimliğiyle)
4. `/dynamic-…-sitemap.xml` oluşuyor mu

Bu deneme **canlı sitede yazma** gerektiriyor. Yapılacak tek şey yeni bir `Sections`
koleksiyonu ve içine bir test kaydı; mevcut sayfalara, `adi6LightHalfFull` form verisine ve
blog içeriğine dokunulmayacak. Yine de ilk yazma işlemi **açık onay alınmadan
yapılmayacak.**

---

## 10. Açık maddeler

**Hocadan:**

- API anahtarı (yukarıdaki dört yetkiyle, tek siteye kısıtlı)
- `From_Bridges_to_Photons.docx` nereye girecek
- 196 MB'lık sunum nasıl servis edilecek — sıkıştırılmış sürüm mü, PDF mi, ayrı depo mu
- Taslakta "coming soon" yazan her şey: CV, yayımlanacak e-posta, ofis bilgisi,
  Google Scholar / ResearchGate / ORCID bağlantıları
- Blog: sekiz yazı taşınacak mı? Görsel id'leri elimizde, OCR ile gerçek metne çevirip düzgün
  Ricos belgesi olarak geri yazmak mümkün.
- Gallery ne olacak? PPT metni belgelerin Gallery'de duracağını söylüyor, oysa mevcut galeri
  27 fotoğraf. İki ayrı şey aynı adı taşıyor.
- Türkçe karakterler: Kaynardag/Kaynardağ, Izmir/İzmir — Scholar indekslemesi için ikisi de
  geçmeli

**Teknik, ilk yazmadan önce kontrol:**

- Site **Harmony** mi? Harmony sitelerinde `IMAGE` ve `DOCUMENT` alan tipleri reddediliyor
  (`400 WDE0080`), `RICH_CONTENT` de reddedilebiliyor. Site 2021'de klasik Wix editörüyle
  kurulduğu için büyük ihtimalle değil, ama ilk koleksiyon oluşturmada teyit edilecek.
- Sitenin gerçek kotaları: `GET /wix-data/v1/site-data-usage/v1/site-data-usage`

**Bilinen belirsizlik:** Ricos referansı "Developer Preview" etiketli, Wix değiştirebilir.

---

## 11. Aşamalar

Sıra, dış bağımlılığı en aza indirecek şekilde kuruldu. API anahtarı en sona bırakıldı.

**Aşama 1 — dönüştürücü. Wix erişimi gerekmiyor.**
Girdi `content/source/` altındaki yedi .docx, çıktı bölüm bölüm Ricos JSON ve şekil manifesti.
Hedef yapı hocanın canlı verisinden birebir bilindiği için doğruluk yerelde denetlenebiliyor.
Buranın en kritik çıktısı **gerçek boyut ölçümü**: §3'teki "ML rehberi 12 bölüm" ifadesi bir
tahmindi. Ölçüldü (22 Eylül 2026): `python tools/docx2ricos.py` yedi belgeyi çeviriyor ve
her biri tek kayda sığıyor — en büyüğü 362.379 bayt, korpus 684.985. §3 bu ölçüme göre
güncellendi; bölüm başına bir kayıt kararı teknik zorunluluk değil, SEO gerekçeli.

**Aşama 2 — canlı doğrulama.** §9'daki deneme. `Sections` koleksiyonu kurulur ve tek test
kaydı yazılır; bunlar Wix MCP oturumunun mevcut yetkisiyle yapılabiliyor, API anahtarı
gerekmiyor. Canlı siteye ilk yazma olduğu için açık onay gerekiyor.

**Aşama 3 — CLI.** Aşama 1'deki dönüştürücünün kendi başına çalışan araca sarılması. API
anahtarı yalnız burada devreye giriyor.

---

## 12. Kapsam dışı

- Git entegrasyonu — istenmedi, Velo kodu Wix editörünün kod panelinden yazılacak
- Hocanın kendi kendine yükleyeceği panel — ikinci aşama
- Wix'ten tamamen çıkış — üyelik bitince, ayrı iş kalemi
- Blog yazılarının OCR ile kurtarılması — karar bekliyor
