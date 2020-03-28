
```
export DEBUG=True
export DATABASE_URL=sqlite:////Users/you/dev/carpool/db.sqlite3
```

https://codigofacilito.com/articulos/deploy-dajngo-heroku

# Precio del Fonobus

```python
from lxml import html


b = requests.get("https://compraonline.sittnet.net/ar/6338/Resultados.aspx?param=395/758/28-03-2020/0/28-03-2020")
tree = html.fromstring(b.text)
prices = tree.xpath('//div[@title="Precio"]/text()')
max(map(lambda s: s.strip(), prices))
```
