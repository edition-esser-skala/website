---
title: Quarterly update Q4/2022
date: 2022-12-31
categories: [editions, technical]
description: Adlgasser · Brixi · Caldara · Haydn M · Hofmann · Tůma · Werner · EES Tools v2022.12.0
---

## New editions

### Adlgasser, Anton Cajetan

- [Requiem](/scores/adlgasser.qmd#work-catad-2-01star) CatAd 2.01<br/>
  This edition reproduces the Viennese abridged version preserved in the archive of the Hofmusikkapelle.
- [Komm Heiliger Geist](/scores/adlgasser.qmd#work-catad-9-03) CatAd 9.03<br/>


### Brixi, František Xaver

- [Opus patheticum de septem doloribus Beatæ Virginis Mariæ](/scores/brixi.qmd#work-cz-pu-59-r-25) (CZ-Pu 59 R 25)<br/>
  Brixi was a popular Czech composer in the mid-18th century, who wrote a comprehensive body of sacral music. Although the tradition of his works is somewhat complex, the Opus patheticum is a certain attribution that is available from several libraries and archives. It features a highly chromatic alla breve fugue. Movements 5 and 3 have also been published as gradual and offertorium.


### Caldara, Antonio

- [Missa](/scores/caldara.qmd#work-a-ed-a-174) (A-Ed A 174)


### Haydn, Johann Michael

- The [Proprium Missæ](/scores/haydn.qmd) project now also includes MH 213, 361, 366, 388–390, 394, 401–403, 408, 409, 415, 494, 505f, 509–511, 513, 519–524, 588, 635, and 800. Moreover, MIDI files for all works are available.


### Hofmann, Leopold

- [Missa](/scores/hofmann.qmd#work-proh-27) ProH 27


### Tůma, František Ignác Antonín

- [Bonum est confiteri](/scores/tuma.qmd) (A-Wn Mus.Hs.15705)
- [De profundis](/scores/tuma.qmd) (A-Wn Mus.Hs.15723)
- [De profundis et Memento](/scores/tuma.qmd) (A-Wn Mus.Hs.15724)
- [Dixit Dominus](/scores/tuma.qmd) (A-Wn Mus.Hs.15679)
- [Dixit Dominus](/scores/tuma.qmd) (A-Wn Mus.Hs.15680)
- [Laudes Mariae](/scores/tuma.qmd) (A-Wn Mus.Hs.15719)


### Werner, Gregor Joseph

- [Symphoniæ sex senæque sonatæ](/scores/werner.qmd) (D-Dl Mus.2462-Q-1)  <br/>
  This collection of six three-part symphonies and six four-part sonatas was printed in 1734. Each sonata contains two sophisticated fugues preceded by slow introductions.


## Technical

We have released a new version of EES Tools ([v2022.12.0](https://github.com/edition-esser-skala/ees-tools/releases/tag/v2022.12.0)), which is based on LilyPond 2.24.0. The version contains several small improvements which are documented in the [changelog](https://github.com/edition-esser-skala/ees-tools/blob/v2022.12.0/CHANGELOG.md). Notably, LilyPond 2.24.0 greatly improves [rendering of bass figures](http://lilypond.org/doc/v2.24/Documentation/changes/index.html#chord-notation-improvements), from which our editions indeed will benefit.

We have also switched from Atom (whose development has been abandoned as of 2022-12-15) to [VSCodium](https://vscodium.com) as development environment for our scores. The README of EES Tools describes [our setup](https://github.com/edition-esser-skala/ees-tools#-using-a-manual-installation) in more detail. Syntax highlighting is done via a custom [language extension](https://github.com/skafdasschaf/vscode-lilypond-language).
