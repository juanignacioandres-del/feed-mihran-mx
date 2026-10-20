"""Genera el feed de Google Shopping de Mihran México desde la API pública de VTEX.

No necesita credenciales: lee el catálogo publicado en www.mihran.com.mx.
Uso:  python generar_feed_mx.py [salida.xml]
"""
import json
import sys
import urllib.request
from xml.sax.saxutils import escape

SITE = "https://www.mihran.com.mx"
BRAND = "Mihran Alfombras México"
PAGE = 50  # máximo que acepta VTEX por request

# Taxonomía de Google: el número o la ruta completa en inglés son válidos.
# El primero que matchee en el título gana; lo que es de "Alfombras" en VTEX es siempre 598.
CATEGORIAS_DECO = [
    ("cojín", "Home & Garden > Decor > Throw Pillows"),
    ("manta", "Home & Garden > Linens & Bedding > Bedding > Blankets"),
    ("puff", "Furniture > Ottomans"),
    ("individual", "Home & Garden > Linens & Bedding > Table Linens > Placemats"),
    ("silla", "Furniture > Chairs > Kitchen & Dining Room Chairs"),
]


def google_category(p, titulo):
    # Va primero por el título: hay puffs cargados dentro de Alfombras en VTEX.
    t = titulo.lower()
    por_titulo = next((cat for clave, cat in CATEGORIAS_DECO if clave in t), None)
    if por_titulo:
        return por_titulo
    if any(c.startswith("/Category/Alfombras/") for c in p["categories"]):
        return "598"  # Home & Garden > Decor > Rugs
    return "Home & Garden > Decor"


def fetch_all():
    productos, desde = [], 0
    while True:
        url = f"{SITE}/api/catalog_system/pub/products/search?_from={desde}&_to={desde + PAGE - 1}"
        req = urllib.request.Request(url, headers={"User-Agent": "feed-mx"})
        with urllib.request.urlopen(req, timeout=60) as r:
            lote = json.load(r)
        productos += lote
        if len(lote) < PAGE:
            return productos
        desde += PAGE


def tag(nombre, valor):
    return f"      <{nombre}>{escape(str(valor))}</{nombre}>\n" if valor not in (None, "", []) else ""


def product_type(p):
    # Una sola ruta, la de la categoría principal del producto (Shake lo pidió así):
    # "/Category/Alfombras/Yute & Sisal/" -> "Hogar > Alfombras > Yute & Sisal".
    # categoriesIds va en el mismo orden que categories.
    rutas = dict(zip((c.strip("/").split("/")[-1] for c in p["categoriesIds"]), p["categories"]))
    ruta = rutas.get(str(p["categoryId"])) or max(p["categories"], key=len)
    partes = [x for x in ruta.strip("/").split("/") if x != "Category"]
    return " > ".join(["Hogar"] + partes)


def items(productos):
    for p in productos:
        material = ", ".join(p.get("COMPOSICIÓN", []))
        for it in p["items"]:
            oferta = next((s["commertialOffer"] for s in it["sellers"] if s.get("sellerDefault")), it["sellers"][0]["commertialOffer"])
            precio, lista = oferta["Price"], oferta["ListPrice"]
            if not precio:
                continue  # sin precio en la web: Google lo rechazaría
            sku = next((r["Value"] for r in it.get("referenceId") or [] if r["Key"] == "RefId"), it["itemId"])
            imgs = [i["imageUrl"].split("?")[0] for i in it["images"]]
            medida = ", ".join(it.get("Medidas", []))
            color = ", ".join(it.get("Colores", []))
            con_oferta = lista and lista > precio
            # nameComplete a veces repite el nombre del producto delante del de la variante;
            # el nombre de la variante ya viene completo y con la medida.
            titulo = " ".join(it["name"].split())
            x = "    <item>\n"
            x += tag("g:id", sku)
            x += tag("title", titulo)
            x += tag("description", p["description"].replace("<br/>", " ").strip())
            x += tag("g:google_product_category", google_category(p, titulo))
            x += tag("g:product_type", product_type(p))
            x += tag("link", f"{SITE}/{p['linkText']}/p?skuId={it['itemId']}")
            x += tag("g:image_link", imgs[0] if imgs else "")
            for extra in imgs[1:7]:
                x += tag("g:additional_image_link", extra)
            x += tag("g:condition", "new")
            x += tag("g:availability", "in_stock" if oferta["AvailableQuantity"] > 0 else "out_of_stock")
            x += tag("g:price", f"{(lista if con_oferta else precio):.2f} MXN")
            if con_oferta:
                x += tag("g:sale_price", f"{precio:.2f} MXN")
            x += tag("g:brand", BRAND)
            x += tag("g:identifier_exists", "no")
            x += tag("g:item_group_id", p["productId"])
            x += tag("g:color", color)
            x += tag("g:size", medida)
            x += tag("g:material", material)
            # pattern = la subcategoría principal, la misma hoja que product_type.
            x += tag("g:pattern", product_type(p).split(" > ")[-1])
            # Etiquetas base que pidió Shake (19/10/2026): SALE, NEW IN y Yute & Sisal como core category.
            x += tag("g:custom_label_0", "SALE" if con_oferta else "")
            x += tag("g:custom_label_1", "NEW IN" if any("New In" in c for c in p["productClusters"].values()) else "")
            x += tag("g:custom_label_2", "Core Category" if any("Yute & Sisal" in c for c in p["categories"]) else "")
            x += "    </item>\n"
            yield x


def main():
    salida = sys.argv[1] if len(sys.argv) > 1 else "mihran-mx-google-shopping.xml"
    productos = fetch_all()
    cuerpo = "".join(items(productos))
    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<rss version="2.0" xmlns:g="http://base.google.com/ns/1.0">\n'
        "  <channel>\n"
        "    <title>Mihran México - Google Shopping</title>\n"
        f"    <link>{SITE}</link>\n"
        "    <description>Product Feed</description>\n"
        f"{cuerpo}"
        "  </channel>\n"
        "</rss>\n"
    )
    with open(salida, "w", encoding="utf-8") as f:
        f.write(xml)
    print(f"{len(productos)} productos, {cuerpo.count('<item>')} variantes -> {salida}")


if __name__ == "__main__":
    main()
