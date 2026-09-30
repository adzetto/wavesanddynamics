# Round 2 — the client's verdict, and what has to change

Read `CONTRACT.md` first; it still binds on scoping, deliverable shape, accessibility,
motion discipline and the Wix constraints. This file **overrides** its palette and
typography sections, and adds the work for this round.

The site is live. The client — a professional building it for Dr. Korkut Kaynardag — looked
at it and said, in his words:

> *"renkler fontlar vs çok generic"* — the colours and fonts are very generic.
> *"explore the topics kısmındaki iconlar vs hala çok kötü"* — the icons are still bad.
> *"renkler mavi mouse ile gelince renkler vs hala çok kötü ferah araştırmacı websitesi
> hissi vermiyor"* — the blues and the hover colours are bad; it does not feel like an
> airy researcher's website.
> *"about me butonu mesela o renk olmamış"* — the About me button's colour is wrong.
> *"my research areas kısmındaki okun stilini değiştir animasyonlu bir şeyler ekle"* —
> change the arrow style on My Research Areas, add something animated.
> *"ana ekranda hem ekranda hem de sol menüde hocanın resmi var mesela bu tür dizayn
> decisionları vs araştır"* — his photo is in the hero **and** in the left menu; research
> that kind of design decision.

Take the criticism at face value. The current work is competent and unremarkable. The bar
is a site that a senior researcher would be proud to put on a grant application, and that a
designer would look at twice.

## The palette is not sacred — this is new information

Earlier rounds treated `#104862` and `#80350E` as the professor's chosen brand colours,
measured out of his own slide deck. That reading was too literal. The deck's theme block is:

```
dk2=0E2841  lt2=E8E8E8  accent1=156082  accent2=E97132
accent3=196B24  accent4=0F9ED5  accent5=A02B93  accent6=4EA72E
```

`#104862` is `accent1` at 75% luminance and `#80350E` is `accent2` at 50%. **Verify whether
that accent set is simply Microsoft Office's current default theme** rather than anything he
picked. If it is — and the evidence points that way — then what he actually chose was
*"a deep blue navigation column with a warm accent for the current page"*, not those two
hexes. The structure is his decision and stays. The exact hues are ours to get right, and
right now they are PowerPoint-default and they look it.

Whatever you propose must still read as the same idea at a glance: deep blue column, warm
accent, white page. Do not turn it into a different site.

## What this round must deliver

1. **A palette that looks considered.** Refined hues, proper hover/pressed/active steps,
   and a stated reason for every value. Include contrast ratios you actually computed.
2. **A typographic system that is not the default.** Inter + Source Serif 4 is the safe
   pairing every AI-built site reaches for. Justify keeping it or replace it. Anything you
   choose must be on Google Fonts and must load in two weights at most, for page weight.
3. **Icons that survive scrutiny.** The three topic icons and the four document icons.
   Specific to vibration, signal processing, machine learning, structural monitoring,
   acoustic tracking and a research presentation. Drawn, consistent, and unmistakably not
   from a generic icon pack.
4. **Hover states worth hovering.** Currently they are a colour swap and a 2px lift. Find
   the response that suits a research site: precise, quiet, and telling you something.
5. **The arrow on My Research Areas** gets a real treatment with motion.
6. **A ruling on the duplicated portrait**, with reasoning from how comparable sites handle
   identity in a persistent sidebar.
7. **"Airy".** Whatever else changes, the page must breathe more than it does now.

## Copy rules — absolute

- **Never touch the professor's own sentences.** Where he wrote the text, it ships verbatim.
- Where *we* write (labels, affordances, section furniture), **do not use em dashes.**
  They are the fingerprint of machine-written copy and the client has called them out.
  Use a colon, a full stop, a comma, or restructure the sentence.
- No invented facts, no invented contact details, no filler.

## Research is part of the job

Do not design from memory. Look at how excellent research and academic sites actually solve
these problems, and bring back specifics — measurements, hexes, ratios, named techniques —
not adjectives. Load `WebSearch` and `WebFetch` through `ToolSearch` and use them.

Cite what you found. If a claim is your own judgement rather than something you observed,
say so.
