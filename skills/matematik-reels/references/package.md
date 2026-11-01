# Post package

Same `video.mp4` goes to both platforms. Write `paket.md` next to it in Turkish. Read each skill's
`SKILL.md` and follow it, except where `teaching.md` overrides it.

Note: these tools' word lists are mostly English. Their length and structure checks apply to Turkish;
treat their style scores as rough signals and read the text yourself.

## Instagram (`ig-caption`, `ig-human`)

- Job A caption: the Reel already hooked them. Write the context, one public ask and search terms.
- Check: `python3 ~/.claude/skills/ig-caption/caption.py caption.txt --keywords "lgs matematik,üslü ifadeler"`
- Clean: `python3 ~/.claude/skills/ig-human/humanize.py caption.txt --report`
- Ask: "yorumlara yaz" or "kaydet". Never a DM. Three hashtags.

## YouTube Shorts (`yt-package`, `yt-seo`)

- Title: `python3 ~/.claude/skills/yt-package/title.py --title "..."`. Words students actually search:
  "üslü ifadeler 8. sınıf LGS". A Short has no custom thumbnail in most feeds, so the title carries it.
- Description: first two lines say what it teaches, using searchable words, then a few plain tags.
- Audience setting: 8th grade general content is usually not "made for kids" but the teacher decides;
  5th-6th grade content aimed at children should be marked. State which applies and why.

## paket.md layout

```markdown
# <konu>
Video: video.mp4 (süre) · Kapak: kapak.png · Sınıf: 8

## Instagram
<caption>

## YouTube Shorts
Başlık: <...>
Açıklama: <...>
Etiketler: <...>
Kitle ayarı: <...>

## Kontrol
İşlem kontrolü: <checks sonucu>
Doğrulanamayan: <varsa>
```

Nothing here publishes. End by asking the teacher whether to change anything.
