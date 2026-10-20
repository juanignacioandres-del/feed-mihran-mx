# Feed de Google Shopping — Mihran México

`mihran-mx-google-shopping.xml` se regenera todos los días a las 22:00 y a las 6:00 (Argentina) desde el
catálogo publicado en www.mihran.com.mx (API pública de VTEX, sin credenciales) y se publica
con GitHub Pages. Esa URL es la que lee Google Merchant Center.

- Generador: `generar_feed_mx.py`
- Tarea diaria: `.github/workflows/feed.yml` (también se puede correr a mano desde la pestaña Actions → Run workflow).
- Si la web devuelve menos de 300 ítems, no se publica y queda el feed del día anterior.

Provisorio hasta la integración por IURCO.
