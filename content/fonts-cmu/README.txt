cmu-serif-*.woff2: Computer Modern Unicode Serif (SIL Open Font License, OFL.txt), the
type of every figure (tools/numfig/engine.js) and of the slides.

figure-math.woff2, family "Figure Math": the mathematical symbols CMU Serif does not
carry (less or equal, approximately, partial, infinity, proportional to, arrows ...),
subset with fontTools from Latin Modern Math (B. Jackowski, P. Strzelczyk, P. Pianowski,
for the TeX user groups; MiKTeX fonts/opentype/public/lm-math/latinmodern-math.otf) and
renamed as a modified version. License: GUST Font License, GUST-FONT-LICENSE.txt. It
stands right after CMU Serif in the figures' font stack, so a symbol is set in Computer
Modern's own design instead of a system face such as Cambria Math.

site-math.woff2 and site-math-bold.woff2, family "Site Math" (regular, and bold at
weights 600 to 900): the face of every formula on the document and blog pages
(site/mathtex.py, round 13), made from the same Latin Modern Math 1.959 and renamed as a
modified version under the GUST Font License, GUST-FONT-LICENSE.txt. What was changed:
- cut down to the characters in site/mathtex.py's REPERTOIRE (351: his words in \text,
  the Latin and Greek letters in math italic, the operators, relations, arrows and
  delimiters of his fields), keeping the OpenType MATH table with its constants, italic
  corrections and the size variants and parts of every stretchy delimiter and large
  operator, so fractions, radicals, scripts and \left...\right take the font's own
  metrics in Chrome, Safari and Firefox;
- the script-size glyphs (ssty) and dotless letters (dtls) left out: Latin Modern files
  them under the script tag "math", which only Firefox reads;
- in the bold face each letter and figure is Latin Modern's own mathematical bold (bold
  italic for the italic letters), as LaTeX's \boldmath sets them; operators and
  delimiters have no bold in the font and stay as they are. Nothing is synthesized;
- CFF hints and subroutines removed (39 KB each as WOFF2); names and the CFF font name
  changed to Site Math.
site-math-metrics.json, written beside them: each character's advance and each italic
letter's italic correction, read from the regular face's MATH table, so the build can
measure a formula and add TeX's italic correction without a font library.
Remake all three with: python site/mathtex.py font
