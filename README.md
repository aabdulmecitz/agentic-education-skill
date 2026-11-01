# agentic-education-skill

Eğitim videoları üreten [Claude Code](https://claude.com/claude-code) skill'leri.

## matematik-reels

Matematik öğretmeninin dikey videosunu veya ses kaydını Instagram Reels ve YouTube Shorts için hazır bir videoya çevirir.

- Konuşmayı kelime kelime yazıya döker (faster-whisper).
- Formül, grafik, sayı doğrusu, kesir ve geometri animasyonlarını öğretmenin yanına, söylediği kelimeye göre yerleştirir.
- Gerektiğinde tam ekran animasyonlu b-roll ve küçük öğretmen penceresi kullanır.
- Altyazı yazar, duraklamaları kırpar ve videoyu Remotion ile oluşturur.
- Videoda gösterilen işlemleri SymPy ile kontrol eder; hatalı işlemde durur.
- Yayın metinlerini hazırlar. **Otomatik yayın yapmaz.**

Kayıt yoksa konu veya kazanımdan hook ve çekim senaryosu yazar.

> **Durum:** Geliştirme aşamasında. Akış, yapay sesli deneme videosuyla test edildi; gerçek öğretmen videosuyla henüz test edilmedi.

### Kurulum

Gerekenler: Node.js 18+, Python 3.10+, ffmpeg. GPU isteğe bağlıdır; yoksa yazı dökümü CPU'da çalışır.

```bash
git clone https://github.com/aabdulmecitz/agentic-education-skill.git
ln -s "$PWD/agentic-education-skill/skills/matematik-reels" ~/.claude/skills/matematik-reels
~/.claude/skills/matematik-reels/scripts/setup.sh
```

Kurulum Python ortamını, Node paketlerini, Remotion'ın tarayıcısını `~/.local/share/matematik-reels` altına indirir. Whisper modeli ilk kullanımda iner.

Yayın metni adımı `ig-caption`, `ig-human`, `ig-reel`, `yt-package` ve `yt-seo` skill'lerini kullanır. Bunlar bu repoya dahil değildir.

### Kullanım

Claude Code'da videonun yolunu verip şöyle yaz:

```text
/matematik-reels ~/videolar/uslu-ifadeler.mp4 yanıma animasyon koy
```

Sonuç, `video.mp4`, `kapak.png` ve `paket.md` olarak teslim klasörüne yazılır. Klasörü `MATEMATIK_REELS_OUT` ile değiştirebilirsin.

### Yapı

```text
skills/matematik-reels/
├── SKILL.md       İş akışı
├── references/    Plan biçimi, öğretim kuralları, yayın paketi
├── scripts/       Hazırlama, plan derleme, render ve kalite kontrol
└── engine/        Remotion animasyon motoru
```

### Lisanslar

Remotion, şirketler için ücretli lisans gerektirebilir: [remotion.dev/license](https://remotion.dev/license).
