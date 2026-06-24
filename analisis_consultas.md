# Análisis de Resultados — DataMart S.A.S.
## Pipeline ETL | Periodo: Diciembre 2009 — Diciembre 2011

---

## Pregunta central
**¿Qué está pasando con las ventas de DataMart y qué decisiones concretas debe tomar el equipo de producto para mejorar la rentabilidad?**

---

## Q1. Evolución mensual de ventas netas

### Resultados
| Periodo | Ventas Brutas | Devoluciones | Ventas Netas | % Devolución |
|---|---|---|---|---|
| 2009-12 | $822,269.58 | $25,816.45 | $796,453.13 | 3.14% |
| 2010-01 | $651,130.85 | $28,671.71 | $622,459.14 | 4.40% |
| 2010-02 | $551,871.92 | $20,612.93 | $531,258.99 | 3.74% |
| 2010-03 | $830,896.61 | $67,306.91 | $763,589.70 | 8.10% |
| 2010-04 | $678,863.40 | $36,793.28 | $642,070.12 | 5.42% |
| 2010-05 | $657,704.50 | $44,434.78 | $613,269.72 | 6.76% |
| 2010-06 | $749,514.33 | $71,196.23 | $678,318.10 | 9.50% |
| 2010-07 | $648,796.70 | $31,317.05 | $617,479.65 | 4.83% |
| 2010-08 | $695,189.24 | $40,477.52 | $654,711.72 | 5.82% |
| 2010-09 | $921,646.59 | $70,591.03 | $851,055.56 | 7.66% |
| 2010-10 | $1,161,827.24 | $80,805.25 | $1,081,021.99 | 6.96% |
| 2010-11 | $1,464,170.08 | $47,561.41 | $1,416,608.67 | 3.25% |
| 2010-12 | $820,994.87 | $74,634.62 | $746,360.25 | 9.09% |
| 2011-01 | $689,773.56 | $131,363.05 | $558,410.51 | **19.04%** |
| 2011-02 | $522,532.96 | $24,683.86 | $497,849.10 | 4.72% |
| 2011-03 | $715,704.01 | $33,885.98 | $681,818.03 | 4.73% |
| 2011-04 | $533,077.58 | $40,721.52 | $492,356.06 | 7.64% |
| 2011-05 | $769,267.11 | $46,812.43 | $722,454.68 | 6.09% |
| 2011-06 | $759,330.89 | $70,513.42 | $688,817.47 | 9.29% |
| 2011-07 | $718,068.71 | $37,909.77 | $680,158.94 | 5.28% |
| 2011-08 | $757,579.17 | $53,663.78 | $703,915.39 | 7.08% |
| 2011-09 | $1,056,356.67 | $38,838.51 | $1,017,518.16 | 3.68% |
| 2011-10 | $1,148,926.23 | $77,767.59 | $1,071,158.64 | 6.77% |
| 2011-11 | $1,502,309.96 | $46,967.74 | $1,455,342.22 | 3.13% |
| 2011-12 | $637,770.92 | $205,089.27 | $432,681.65 | **32.16%** |

### Análisis
El negocio muestra una **tendencia de crecimiento sostenida** entre 2009 y 2011. Las ventas netas de noviembre 2011 ($1,455,342) superan en un 2.7% las de noviembre 2010 ($1,416,608), confirmando crecimiento real año a año.

Se identifican dos **patrones estacionales claros:**
- **Pico de ventas:** Octubre y noviembre concentran los mayores volúmenes en ambos años, impulsados por la temporada navideña y Black Friday.
- **Valle post-navidad:** Enero y febrero registran caídas del 40-50% respecto al mes anterior.

**Alertas críticas:**
- **Enero 2011** tiene una tasa de devolución del 19.04% — casi 6 veces el promedio histórico (~5%). Corresponde a devoluciones de regalos navideños, lo que sugiere que algunos productos vendidos en diciembre generaron expectativas incorrectas.
- **Diciembre 2011** registra la tasa más alta del periodo (32.16%) con solo 24,829 transacciones de venta versus 81,993 en noviembre. Algo anómalo ocurrió ese mes que requiere investigación adicional.

### Conclusión
Los 3 meses de octubre, noviembre y diciembre generan aproximadamente el 35% del revenue anual. Los problemas de calidad que se manifiestan como devoluciones en enero tienen impacto desproporcionado en la rentabilidad del negocio.

---

## Q2. Revenue por categoría y tasa de devoluciones

### Resultados
| Categoría | Revenue Bruto | Devoluciones | Revenue Neto | % Devolución | % del Total |
|---|---|---|---|---|---|
| Hogar | $5,439,206.31 | $196,112.39 | $5,243,093.92 | 3.61% | 26.58% |
| Varios | $4,933,711.23 | $806,959.86 | $4,126,751.37 | 16.36% | 24.11% |
| Cocina | $3,679,703.23 | $120,940.08 | $3,558,763.15 | 3.29% | 17.98% |
| Papelería | $1,998,648.44 | $211,390.48 | $1,787,257.96 | 10.58% | 9.77% |
| Ropa | $1,690,789.56 | $28,686.75 | $1,662,102.81 | 1.70% | 8.26% |
| Electrónica | $1,679,975.92 | $67,355.90 | $1,612,620.02 | 4.01% | 8.21% |
| Fiesta | $720,480.58 | $10,400.99 | $710,079.59 | 1.44% | 3.52% |
| Juguetes | $224,005.41 | $4,928.89 | $219,076.52 | 2.20% | 1.09% |
| Deportes | $99,053.01 | $1,660.75 | $97,392.26 | 1.68% | 0.48% |

### Análisis
**Hogar** es el motor del negocio con el 26.58% del revenue total ($5.4M bruto) y una tasa de devolución controlada del 3.61%. Es la categoría más saludable y sobre la que DataMart debe concentrar su estrategia de crecimiento.

**La categoría "Varios" es una señal de alerta crítica.** Con el 24.11% del revenue y una tasa de devolución del 16.36% — 4.5 veces la de Hogar — agrupa productos que el sistema de clasificación no pudo categorizar. Hay dos problemas simultáneos: alta concentración de revenue en una categoría sin nombre claro, y una tasa de devolución que indica problemas de calidad o descripción en productos específicos que están "escondidos" dentro de esta categoría.

**Papelería** genera $2M en revenue bruto pero con una tasa de devolución del 10.58% — anómala para su tipo de producto. Los artículos de papelería (bolígrafos, cuadernos, sellos) históricamente tienen tasas muy bajas; algo específico de este catálogo está fallando.

**Ropa** (1.70%), **Fiesta** (1.44%) y **Deportes** (1.68%) son las categorías más eficientes con las menores tasas de devolución, indicando alta satisfacción del cliente.

### Conclusión
Dos categorías requieren atención inmediata: **Varios** (por su tamaño y alta tasa de devolución que oculta productos problemáticos) y **Papelería** (tasa anómala para su tipo). Las categorías pequeñas muestran ratios saludables y tienen potencial de crecimiento.

---

## Q3. Top 10 productos — Revenue neto y mayor tasa de devolución

### Top 10 por mayor revenue neto
| Código | Producto | Categoría | Revenue Bruto | Devoluciones | Revenue Neto | Unidades |
|---|---|---|---|---|---|---|
| 22423 | REGENCY CAKESTAND 3 TIER | Cocina | $330,564.83 | $16,545.30 | $314,019.53 | 26,477 |
| DOT | DOTCOM POSTAGE | Papelería | $309,854.11 | $10.01 | $309,844.10 | 1,415 |
| 85123A | WHITE HANGING HEART T-LIGHT HOLDER | Electrónica | $261,153.98 | $9,387.10 | $251,766.88 | 94,714 |
| 85099B | JUMBO BAG RED RETROSPOT | Cocina | $182,680.98 | $2,168.82 | $180,512.16 | 97,176 |
| 47566 | PARTY BUNTING | Hogar | $148,307.49 | $1,238.55 | $147,068.94 | 28,199 |
| 84879 | ASSORTED COLOUR BIRD ORNAMENT | Varios | $129,310.97 | $774.07 | $128,536.90 | 80,074 |
| 22086 | PAPER CHAIN KIT 50'S CHRISTMAS | Papelería | $117,760.29 | $1,461.70 | $116,298.59 | 35,084 |
| POST | POSTAGE | Papelería | $125,682.42 | $15,168.37 | $110,514.05 | 5,363 |
| 79321 | CHILLI LIGHTS | Electrónica | $80,528.42 | $635.75 | $79,892.67 | 15,840 |
| 22197 | SMALL POPCORN HOLDER | Hogar | $79,516.88 | $616.58 | $78,900.30 | 88,497 |

### Top 10 por mayor tasa de devolución
| Código | Producto | Categoría | Ventas | Devoluciones | Rev. Bruto | Devuelto | Tasa |
|---|---|---|---|---|---|---|---|
| PADS | PADS TO MATCH ALL CUSHIONS | Hogar | 17 | 1 | $0.02 | $36.60 | 215,294% |
| BANKCHARGES | BANK CHARGES | Varios | 33 | 62 | $519.24 | $34,338.33 | 6,613% |
| 20879 | TREE OF NOAH FESTIVE SCENTED CANDLE | Hogar | 11 | 3 | $67.80 | $201.60 | 297% |
| M | MANUAL | Varios | 823 | 511 | $330,480.60 | $415,496.38 | **125.72%** |
| 79323B | BLACK CHERRY LIGHTS | Electrónica | 58 | 53 | $1,565.70 | $1,557.20 | 99.46% |
| 23166 | MEDIUM CERAMIC TOP STORAGE JAR | Hogar | 250 | 10 | $81,700.92 | $77,479.64 | **94.83%** |
| 23113 | PANTRY CHOPPING BOARD | Cocina | 57 | 7 | $5,868.50 | $4,803.06 | 81.84% |
| 20952 | PORCELAIN CHERUB BELL SMALL | Varios | 24 | 3 | $150.72 | $119.16 | 79.06% |
| 47587A | PINK FAIRY CAKE COASTER | Cocina | 26 | 3 | $1,099.88 | $864.00 | 78.55% |
| 10138 | ASSORTED COLOUR JUMBO PEN | Papelería | 21 | 7 | $111.22 | $81.90 | 73.64% |

### Análisis
**Productos estrella:** `REGENCY CAKESTAND 3 TIER` lidera con $314,019 de revenue neto y 26,477 unidades. `WHITE HANGING HEART T-LIGHT HOLDER` destaca por volumen (94,714 unidades). `JUMBO BAG RED RETROSPOT` también sobresale con 97,176 unidades y tasa de devolución del 1.19%. Estos tres productos son el núcleo del negocio.

**Caso crítico — MANUAL (código M):** Revenue neto **negativo de -$85,015.78**. Se devuelven $415,496 sobre $330,480 de ventas — una tasa del 125.72%. Con alta probabilidad es un código de ajuste contable interno que no representa un producto real. Su presencia contamina todos los análisis de revenue.

**PADS y BANKCHARGES:** Tasas extremas (215,294% y 6,613%) pero con muy pocas transacciones — son outliers estadísticos producto de errores de carga o ajustes contables, no productos reales con problemas de calidad.

**MEDIUM CERAMIC TOP STORAGE JAR (23166):** Con 250 ventas reales y una tasa del 94.83%, prácticamente todo lo que se vende se devuelve. Este sí es un problema de producto real que requiere acción inmediata.

### Conclusión
El núcleo de 5-6 productos estrella genera revenue neto sólido con tasas de devolución menores al 5%. En paralelo, existe un grupo pequeño de productos que destruyen valor activamente, liderado por el código M (MANUAL) con -$85,015 de revenue neto.

---

## Q4. Países y ticket promedio

### Resultados
| País | Facturas | Líneas Venta | Revenue Bruto | Ticket Promedio | % del Total |
|---|---|---|---|---|---|
| United Kingdom | 36,535 | 925,894 | $17,408,156.59 | $476.48 | **85.06%** |
| EIRE (Irlanda) | 626 | 17,153 | $657,551.19 | $1,050.40 | 3.21% |
| Netherlands | 228 | 5,085 | $554,038.09 | **$2,429.99** | 2.71% |
| Germany | 789 | 16,430 | $424,046.31 | $537.45 | 2.07% |
| France | 622 | 13,639 | $350,456.09 | $563.43 | 1.71% |
| Australia | 95 | 1,789 | $169,283.46 | $1,781.93 | 0.83% |
| Spain | 154 | 3,662 | $108,332.49 | $703.46 | 0.53% |
| Switzerland | 93 | 3,122 | $100,685.59 | $1,082.64 | 0.49% |
| Sweden | 105 | 1,336 | $91,869.82 | $874.95 | 0.45% |
| Denmark | 43 | 778 | $68,580.69 | $1,594.90 | 0.34% |
| Belgium | 149 | 3,055 | $65,387.82 | $438.84 | 0.32% |
| Portugal | 95 | 2,470 | $56,283.53 | $592.46 | 0.28% |
| Norway | 45 | 1,287 | $55,858.70 | $1,241.30 | 0.27% |
| Channel Islands | 55 | 1,551 | $44,623.33 | $811.33 | 0.22% |
| Japan | 33 | 468 | $43,023.91 | $1,303.75 | 0.21% |

### Análisis
El negocio es **altamente concentrado en UK** con el 85.06% del revenue total ($17.4M). Sin embargo, los mercados internacionales muestran tickets promedio significativamente más altos, indicando compradores mayoristas o distribuidores.

**Netherlands destaca como mercado mayorista premium:** Con solo 228 facturas genera $554,038 a un ticket promedio de $2,429.99 — 5.1 veces el ticket de UK ($476.48). Cada pedido holandés equivale en valor a más de 5 pedidos británicos.

**Mercados de alto ticket (>$1,000):** EIRE ($1,050), Australia ($1,782), Switzerland ($1,082), Denmark ($1,595), Norway ($1,241) y Japan ($1,304) conforman un segmento mayorista internacional de alto valor que opera con bajo volumen de facturas pero pedidos grandes.

**Mercados similares a UK (<$700):** Germany ($537), France ($563), Belgium ($439) y Portugal ($592) tienen tickets similares al mercado doméstico — probablemente compradores minoristas internacionales.

### Conclusión
La estrategia de internacionalización debería priorizar los mercados de ticket alto (Netherlands, Australia, Denmark) antes que los de ticket similar a UK. Un solo cliente mayorista holandés genera el mismo revenue que 5 clientes británicos típicos, con menor costo operativo por transacción.

---

## Q5. Clientes identificados vs. anónimos

### Resultados
| Tipo | Clientes | Facturas | Líneas | Revenue Bruto | Ticket Promedio | Facturas/Cliente |
|---|---|---|---|---|---|---|
| Identificado | 5,878 | 36,968 | 779,389 | $17,366,007.00 | $469.76 | 6.29 |
| Sin cliente | 1 (ANON.) | 3,109 | 228,371 | $3,099,566.69 | $996.97 | 3,109.00 |

### Análisis
El hallazgo más relevante: los clientes **sin identificar tienen un ticket promedio de $996.97 — más del doble** que los clientes registrados ($469.76). Esto contradice la intuición de que los anónimos serían compradores ocasionales de bajo valor.

La explicación más probable es que los **clientes anónimos son compradores mayoristas** que realizan pedidos grandes sin necesidad de registrarse en la plataforma. Este segmento genera $3,099,566 — el **15.1% del revenue total** — siendo completamente invisible para el equipo comercial.

Los clientes identificados muestran una frecuencia de compra de 6.29 facturas por cliente, indicando buena retención y fidelidad. Sin embargo, su ticket promedio es significativamente menor.

### Conclusión
La decisión de incluir transacciones sin customer ID fue correcta y crítica: excluirlas habría eliminado el 15.1% del revenue del análisis. El equipo comercial debería implementar un programa de incentivos para identificar a estos compradores de alto valor, lo que permitiría hacer seguimiento, fidelización y oferta de condiciones especiales.

---

## Q6. Calidad del catálogo de productos

### Resultados
- **Total de códigos únicos de producto:** 5,072
- **Productos sin descripción recuperable:** 46 códigos (etiqueta "SIN DESCRIPCION")
- La mayoría tiene entre 1 y 2 transacciones — productos marginales o descontinuados

### Análisis
El catálogo tiene una **calidad general buena**: el 99.1% de los 5,072 productos tiene descripción asignada. Los 46 sin descripción son códigos que aparecieron en transacciones pero nunca tuvieron descripción en ninguna de las dos fuentes — estadísticamente insignificantes en revenue.

La oportunidad real de mejora está en la categoría **"Varios"** que agrupa productos clasificables con mayor precisión. Con el 24.11% del revenue y la mayor tasa de devolución (16.36%), una revisión manual del catálogo "Varios" podría revelar sub-categorías problemáticas específicas.

### Conclusión
La prioridad de calidad del catálogo no son los 46 productos sin descripción (impacto mínimo) sino la revisión y sub-clasificación de los productos en "Varios". Esto permitiría identificar con mayor precisión qué sub-categoría específica tiene el problema de devoluciones del 16.36%.

---

## Q7. Recomendación concreta al equipo de producto

### Productos críticos identificados
| Código | Producto | Revenue Bruto | Devuelto | Revenue Neto | Ventas | Dev. | Tasa |
|---|---|---|---|---|---|---|---|
| 22423 | REGENCY CAKESTAND 3 TIER | $330,564.83 | $16,545.30 | **$314,019.53** | 3,949 | 352 | 5.01% |
| M | MANUAL | $330,480.60 | $415,496.38 | **-$85,015.78** | 823 | 511 | 125.72% |
| 85123A | WHITE HANGING HEART T-LIGHT HOLDER | $261,153.98 | $9,387.10 | **$251,766.88** | 5,608 | 136 | 3.59% |
| POST | POSTAGE | $125,682.42 | $15,168.37 | $110,514.05 | 1,851 | 226 | 12.07% |
| 23166 | MEDIUM CERAMIC TOP STORAGE JAR | $81,700.92 | $77,479.64 | $4,221.28 | 250 | 10 | 94.83% |
| 21843 | RED RETROSPOT CAKE STAND | $64,918.30 | $5,270.25 | $59,648.05 | 1,529 | 159 | 8.12% |
| 22139 | RETROSPOT TEA SET CERAMIC 11 PC | $52,843.01 | $2,014.50 | $50,828.51 | 2,103 | 53 | 3.81% |
| 21731 | RED TOADSTOOL LED NIGHT LIGHT | $48,315.84 | $1,457.90 | $46,857.94 | 1,554 | 24 | 3.02% |
| 22138 | BAKING SET 9 PIECE RETROSPOT | $45,870.75 | $4,052.95 | $41,817.80 | 1,925 | 211 | 8.84% |
| 48185 | DOORMAT FAIRY CAKE | $45,709.41 | $4,678.68 | $41,030.73 | 987 | 9 | 10.24% |

### Recomendación 1 — URGENTE: Eliminar el código M (MANUAL) del catálogo
El producto con código `M` tiene un **revenue neto negativo de -$85,015.78**. Se devuelven $415,496 sobre $330,480 de ventas brutas — una tasa del 125.72%. Es casi seguro un código de ajuste contable interno que no representa un producto real. Su presencia distorsiona todas las métricas de revenue del negocio.

**Acción concreta:** Reclasificar o eliminar este código antes del próximo cierre financiero. Si es un ajuste contable, debe procesarse fuera del sistema de ventas o con un código diferente que no aparezca en el catálogo de productos.

**Impacto estimado:** Eliminar este código mejoraría el revenue neto total reportado en $85,015.

### Recomendación 2 — CRÍTICA: Revisar y suspender MEDIUM CERAMIC TOP STORAGE JAR
Con 250 ventas reales y una tasa de devolución del 94.83%, prácticamente todo lo que se vende de este producto se devuelve. El negocio pierde $77,479 de los $81,700 generados. Las causas más probables son:
- Las fotos o descripción en la tienda no representan el producto real
- El producto llega dañado por empaque insuficiente
- El precio no corresponde a la calidad percibida

**Acción concreta:** Suspender temporalmente las ventas, revisar empaque y material gráfico, recopilar feedback de los 250 clientes que lo compraron y los 10 que lo devolvieron.

### Recomendación 3 — ESTRATÉGICA: Potenciar los tres productos estrella
`REGENCY CAKESTAND 3 TIER` ($314K neto), `WHITE HANGING HEART T-LIGHT HOLDER` ($251K neto) y `JUMBO BAG RED RETROSPOT` ($180K neto) generan juntos $746,298 de revenue neto con tasas de devolución menores al 5%.

**Acción concreta:**
- Garantizar inventario permanente de estos tres SKUs — nunca deben quedar fuera de stock en temporada navideña.
- Usarlos como productos ancla en campañas de octubre-noviembre.
- Analizar qué tienen en común (precio, descripción, calidad visual) para aplicar esas características a nuevos productos.

### Recomendación 4 — OPORTUNIDAD: Programa de identificación para compradores mayoristas anónimos
Los clientes sin registro tienen ticket promedio de $996.97 — más del doble que los clientes identificados ($469.76). Representan $3,099,566 (15.1% del revenue total) de compradores completamente desconocidos para el equipo comercial.

**Acción concreta:** Implementar un incentivo para que se registren — descuento del 3-5% en el siguiente pedido, acceso anticipado a catálogo de temporada, o condiciones especiales de pago. Convertir este segmento opaco en clientes rastreables permitiría hacer seguimiento, fidelización y potencialmente duplicar sus pedidos mediante ofertas personalizadas.

---

## Conclusión general

DataMart S.A.S. tiene un negocio sólido con crecimiento sostenido (+2.7% en el pico de noviembre año a año) y una base de productos estrella bien establecida. Sin embargo, el pipeline ETL permitió identificar con precisión numérica tres problemas que antes eran invisibles:

**1. Contaminación del catálogo:** El código M (MANUAL) tiene revenue neto negativo de -$85,015. Eliminarlo mejoraría inmediatamente las métricas del negocio sin ningún cambio en las operaciones reales.

**2. Producto con falla sistémica:** MEDIUM CERAMIC TOP STORAGE JAR tiene una tasa de devolución del 94.83% sobre 250 transacciones reales — no es un outlier estadístico, es un problema real que cuesta $77,479 en devoluciones.

**3. Segmento de alto valor invisible:** $3.1M en revenue (15.1% del total) proviene de compradores anónimos con ticket promedio del doble que los clientes registrados. Sin identificarlos, el negocio no puede fidelizarlos ni hacerles ofertas personalizadas.

El pipeline transforma un proceso de consolidación manual de 3-5 días en un repositorio analítico disponible en tiempo real, permitiendo al equipo financiero cerrar reportes el mismo día y al equipo de producto tomar decisiones respaldadas en datos concretos.
