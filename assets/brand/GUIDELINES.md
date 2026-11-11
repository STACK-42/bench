# bench logo guidelines

## 1. The logo

- Idea: a bench seen from the side is also the letter b. The back post is the stem; the seat, front leg and stretcher close the bowl. The mark is the first letter of the name, so the icon and the wordmark are one idea.
- Versions:
  - horizontal (`bench-horizontal.svg`): the wordmark with a green b. The primary version.
  - stacked (`bench-stacked.svg`): the symbol above the wordmark.
  - symbol (`bench-symbol.svg`) for 64 px and up.
  - small symbol (`bench-symbol-small.svg`) for 16 to 48 px.
  - wordmark (`bench-wordmark.svg`): all ink.
- Files: SVG for screens and print. `bench-horizontal-dark.svg` keeps the green b for dark backgrounds. The web icons are in `icons/`, the presentation slides in `board/`, the workflow diagram is `loop.svg`, and `notes.css` themes learning notes.

## 2. Clear space

Keep a clear zone of one wordmark stroke width on all sides: the thickness of the b's stem, which is 28 of the wordmark's 256-unit height. It scales with the logo.

## 3. Minimum size

| Version | Screen |
| --- | --- |
| Horizontal | 96 px wide |
| Symbol | 64 px; below that use the small symbol, down to 16 px |

## 4. Colour

| Name | HEX | RGB | Use |
| --- | --- | --- | --- |
| Signal green | #0B7A4B | 11, 122, 75 | the b, app icon tile, "keep" |
| Ink | #15181C | 21, 24, 28 | wordmark letters, text |
| Ground | #F6F7F5 | 246, 247, 245 | light backgrounds |
| Muted | #5B636B | 91, 99, 107 | secondary text |
| Caution | #B45309 | 180, 83, 9 | uploads and warnings in diagrams, never in the logo |

Green on white has a contrast of 5.4:1 and ink on white 17.8:1, so both pass for text.

Approved pairs: green b and ink on white or Ground; all white on green; all white on Ink; all black on white.

## 5. Typography

The wordmark is drawn, not typed: one 28-unit stroke and the bench seat's rounded top-right corner on every letter. For text next to it, use Space Grotesk 700 for headings, Inter for body and JetBrains Mono for numbers and commands. All three are open licence (SIL OFL) from Google Fonts.

## 6. Don'ts

- Don't stretch, rotate, outline or add shadows or gradients.
- Don't recolour outside the palette, and don't make the b any colour but green or the one-colour version.
- Don't type "bench" in a font in place of the wordmark.
- Don't use the large symbol below 64 px; use the small one.

## 7. Notes

- Trademark: no search was done. Check before any public launch.
- Made with the logo-design skill (github.com/kaankiziltug/logo-design-skill): SVG audit 100/100 on every file, renders checked at 16 to 512 px.
