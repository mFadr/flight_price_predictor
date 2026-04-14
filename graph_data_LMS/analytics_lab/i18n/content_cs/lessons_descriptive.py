"""Czech text for the Descriptive Analytics lessons (code stays as in the English source)."""

REVENUE_NOTE = "Tržby se v celé laboratoři počítají jako `quantity * unit_price * (1 - COALESCE(discount_pct, 0))` z položek objednávek se stavem **Completed** (dokončeno)."

LESSONS = {
    "ds1": {
        "title": "Základy SQL: výběr, filtrování a shrnutí",
        "objectives": [
            "Přečíst schéma tabulky a vybrat sloupce, které odpovídají na otázku.",
            "Filtrovat řádky pomocí WHERE, včetně dat, textu a více podmínek.",
            "Řadit a omezovat výsledky pomocí ORDER BY a LIMIT; odstraňovat duplicity pomocí DISTINCT.",
            "Shrnout celou tabulku pomocí COUNT, SUM, AVG, MIN a MAX.",
        ],
        "concept": """
SQL je *deklarativní* jazyk: popíšete, **jaký** výsledek chcete, a databáze sama zjistí, **jak** ho spočítat.
Dotaz se vyhodnocuje v logickém pořadí, které se liší od pořadí, v jakém ho píšete:

| Logický krok | Klauzule | Co dělá |
|---|---|---|
| 1 | `FROM` | vybere tabulku/tabulky |
| 2 | `WHERE` | ponechá jen řádky splňující podmínku |
| 3 | `GROUP BY` | vytvoří skupiny (další lekce) |
| 4 | `HAVING` | filtruje skupiny (další lekce) |
| 5 | `SELECT` | spočítá výstupní sloupce |
| 6 | `ORDER BY` | seřadí výstup |
| 7 | `LIMIT` | ponechá prvních *n* řádků |

Klíčové myšlenky:

* `WHERE status = 'Completed'` porovnává text přesně (v DuckDB záleží na velikosti písmen). Pro seznamy použijte `IN ('A','B')`, pro rozsahy `BETWEEN` nebo `>=`/`<`.
* U dat dávejte přednost polootevřeným intervalům: `order_date >= DATE '2024-01-01' AND order_date < DATE '2025-01-01'`. Fungují i s časovými razítky.
* `COUNT(*)` počítá řádky; `COUNT(col)` počítá hodnoty **různé od NULL**; `COUNT(DISTINCT col)` počítá unikátní hodnoty různé od NULL.
* `AVG`, `SUM`, `MIN` a `MAX` ignorují NULL, což může nenápadně změnit význam průměru.
* `DISTINCT` se vztahuje na **celý vybraný řádek**, ne jen na první sloupec.
""",
        "business_context": """
Finanční oddělení firmy Northwind Living se ptá: *„Kolik dokončených objednávek jsme v roce 2024 vyřídili, od kolika zákazníků a kolik zákazníci v průměru zaplatili za dopravu?“*
Tato souhrnná čísla otevírají každé měsíční obchodní hodnocení. Chyba v nich (například započítání zrušených objednávek) podkopává důvěru ve všechna další čísla.
""",
        "worked_example": {"explanation": """
1. `FROM orders` - hlavičky objednávek, jeden řádek na objednávku (granularitu ověřte v panelu schématu).
2. `WHERE` ponechá jen dokončené objednávky z roku 2024 pomocí polootevřeného datového intervalu.
3. `COUNT(*)` počítá objednávky; `COUNT(DISTINCT customer_id)` počítá unikátní kupující - zákazník s pěti objednávkami se započítá jednou.
4. `ROUND(AVG(...), 2)` zpřehlední výstup, aniž by změnil samotný výpočet.

**Ověření:** odstraňte filtr `status` a porovnejte - rozdíl tvoří zrušené a čekající objednávky, které jste záměrně vyloučili.
"""},
        "extra_examples": [{"explanation": "`ORDER BY ... DESC LIMIT 10` je standardní vzor *top-N*. Bez ORDER BY vrátí LIMIT libovolných 10 řádků."}],
        "summary": [
            "SQL se vyhodnocuje v pořadí FROM -> WHERE -> GROUP BY -> HAVING -> SELECT -> ORDER BY -> LIMIT.",
            "U KPI používejte polootevřené datové intervaly a výslovné filtry stavu.",
            "COUNT(*), COUNT(col) a COUNT(DISTINCT col) odpovídají na různé otázky.",
            "Agregace ignorují NULL - ověřte, zda to odpovídá byznysovému významu.",
        ],
        "common_mistakes": [
            "Počítání všech objednávek místo dokončených.",
            "Použití `order_date BETWEEN '2024-01-01' AND '2024-12-31'` na časových razítkách a vynechání posledního dne.",
            "Použití LIMIT bez ORDER BY v domnění, že jde o „nejlepší“ řádky.",
        ],
        "revision": "Vraťte se k tabulce pořadí klauzulí a spusťte řešený příklad znovu, pokaždé bez jedné klauzule.",
    },
    "ds2": {
        "title": "Seskupování, podmíněná logika a práce s NULL",
        "objectives": [
            "Agregovat podle jedné či více dimenzí pomocí GROUP BY.",
            "Filtrovat skupiny pomocí HAVING a řádky pomocí WHERE - a znát rozdíl.",
            "Vytvářet byznysové kategorie pomocí výrazů CASE.",
            "Záměrně pracovat s NULL pomocí COALESCE, IS NULL a NULLIF.",
        ],
        "concept": f"""
`GROUP BY` sloučí řádky se stejnými hodnotami do jednoho řádku na skupinu a agregace pak každou skupinu shrnou.
Každý vybraný sloupec musí být buď **seskupený**, nebo **agregovaný**.

* `WHERE` filtruje **řádky před** seskupením; `HAVING` filtruje **skupiny po** agregaci (`HAVING SUM(x) > 1000`).
* `CASE WHEN podmínka THEN hodnota ... ELSE hodnota END` převádí surové hodnoty na byznysové kategorie (cenová pásma, úrovně slev, velikostní segmenty). Podmínky se testují shora dolů; platí první shoda.
* NULL znamená *neznámé*, ne nulu. `NULL + 1` je NULL, `NULL = NULL` není pravda a `WHERE col = NULL` nenajde nic - použijte `IS NULL`.
* `COALESCE(discount_pct, 0)` nahradí NULL nulou - ale dělejte to jen tehdy, když byznys potvrdí, že chybějící hodnota znamená nulu, a zdokumentujte to.
* `NULLIF(jmenovatel, 0)` zabrání chybám dělení nulou u poměrů.
* Podmíněná agregace spočítá více metrik najednou: `SUM(CASE WHEN status='Cancelled' THEN 1 ELSE 0 END)` nebo v DuckDB `COUNT(*) FILTER (WHERE status='Cancelled')`.

{REVENUE_NOTE}
""",
        "business_context": """
Obchodní ředitel chce vědět, zda si firma slevami „kupuje“ tržby. Prvním krokem je shrnout položky a tržby podle pásem slev a ponechat položky s *neznámou* slevou viditelné, místo aby se potichu braly jako položky za plnou cenu.
""",
        "worked_example": {"explanation": """
* Podmíněná agregace (`SUM(CASE ...)`) spočítá zrušené objednávky v rámci každé skupiny regionu.
* `100.0 *` vynutí desetinné dělení; celočíselné dělení by zaokrouhlilo dolů na 0.
* `HAVING COUNT(*) > 100` vyřadí malé skupiny, jejichž míry by byly zašuměné - běžné pravidlo reportingu.
* **Interpretace:** region s vyšší mírou zrušení je stopa k prošetření, ne závěr. Před akcí ověřte objemy a spolehlivost.
"""},
        "summary": [
            "Každý vybraný sloupec musí být seskupený nebo agregovaný.",
            "WHERE filtruje řádky; HAVING filtruje skupiny.",
            "CASE vytváří byznysové kategorie; větve WHEN řaďte pečlivě.",
            "NULL je neznámá hodnota: IS NULL, COALESCE a NULLIF používejte záměrně a předpoklady dokumentujte.",
        ],
        "common_mistakes": [
            "Agregační podmínka umístěná do WHERE.",
            "Celočíselné dělení, které vede k mírám 0 %.",
            "Nahrazení NULL nulou bez ověření, co NULL znamená.",
        ],
        "revision": "Pokud není jasný rozdíl mezi HAVING a WHERE, vraťte se k logickému pořadí dotazu v lekci ds1.",
    },
    "ds3": {
        "title": "Spojování tabulek, CTE a poddotazy",
        "objectives": [
            "Zvolit INNER, LEFT, RIGHT a FULL JOIN podle toho, které řádky se musí zachovat.",
            "Předpovědět granularitu spojeného výsledku a vyhnout se dvojímu započtení.",
            "Najít nespárované záznamy pomocí anti-joinu.",
            "Strukturovat vícekrokovou logiku pomocí CTE (common table expressions) a poddotazů.",
        ],
        "concept": """
Spojení (join) kombinuje řádky ze dvou tabulek pomocí klíče.

| Join | Zachová |
|---|---|
| `INNER JOIN` | jen řádky se shodou v obou tabulkách |
| `LEFT JOIN` | všechny řádky levé tabulky; NULL tam, kde pravá nemá shodu |
| `RIGHT JOIN` | všechny řádky pravé tabulky (zřídka potřeba - prohoďte pořadí a použijte LEFT) |
| `FULL JOIN` | všechny řádky z obou stran |

**Granularita je všechno.** Spojení `orders` (jeden řádek na objednávku) s `order_items` (jeden řádek na položku) dá jeden řádek na *položku*. Když pak sečtete `SUM(o.shipping_cost)`, přičtete poplatek za dopravu každé objednávky jednou za každou položku - klasické dvojí započtení. Agregujte na správnou granularitu *před* spojením, nebo agregujte každou míru na její vlastní granularitě.

**Anti-join:** `LEFT JOIN ... WHERE right.key IS NULL` vrátí řádky bez shody (např. zákazníky, kteří nikdy nenakoupili). `NOT EXISTS (poddotaz)` je ekvivalentní, často srozumitelnější zápis.

**CTE** (`WITH name AS (...)`) pojmenují mezivýsledky, takže se dotaz čte shora dolů jako recept. Usnadňují ověřování: spusťte každé CTE samostatně a zkontrolujte počty řádků.

**Poddotazy** se mohou objevit ve `WHERE` (`customer_id IN (SELECT ...)`), ve `FROM` (odvozená tabulka) nebo v `SELECT` (skalární poddotaz).
""",
        "business_context": """
Finance chce hrubou marži podle kategorie. Tržby jsou v `order_items`, stav v `orders`, náklady v `products` a názvy kategorií v `categories` - čtyři tabulky, tři spojení. Marketing navíc chce vědět, kolik nedávno získaných zákazníků zatím nic nekoupilo, podle akvizičního kanálu.
""",
        "worked_example": {"explanation": """
1. `completed_lines` - granularita: jeden řádek na položku dokončené objednávky, tržby spočítané jednou.
2. `by_product` - agreguje na jeden řádek na produkt **před** připojením dimenzí, takže nic nemůže být započteno dvakrát.
3. Závěrečný SELECT připojí produkt -> kategorie -> oddělení a znovu agreguje.

**Kontrola:** součet `revenue` se musí rovnat celkovým tržbám dokončených objednávek z jednoduchého dotazu nad `order_items` + `orders`. Odsouhlasení součtů je nejrychlejší způsob, jak odhalit chyby ve spojeních.
"""},
        "extra_examples": [{"explanation": "`NOT EXISTS` skončí u první shody pro každý produkt a bezpečně pracuje s NULL (na rozdíl od `NOT IN`, pokud seznam obsahuje NULL)."}],
        "summary": [
            "Typ spojení zvolte podle toho, které řádky musí přežít.",
            "U každého mezivýsledku si ujasněte granularitu; když se granularity liší, agregujte před spojením.",
            "Anti-joiny (LEFT JOIN ... IS NULL / NOT EXISTS) najdou chybějící vztahy.",
            "CTE dělají vícekrokové dotazy čitelnými a samostatně testovatelnými.",
        ],
        "common_mistakes": [
            "Sčítání hodnot na úrovni objednávky po spojení s tabulkami na úrovni položek.",
            "Filtrování pravé tabulky LEFT JOINu ve WHERE, které ho potichu změní na INNER JOIN (podmínku dejte do ON).",
            "Použití NOT IN s poddotazem, který může vrátit NULL.",
        ],
        "revision": "Před psaním spojení si nakreslete granularitu každé tabulky. Pokud si nejste jistí s GROUP BY, vraťte se k ds2.",
    },
    "ds4": {
        "title": "Okenní funkce, pořadí a porovnání období",
        "objectives": [
            "Vysvětlit, čím se okenní funkce liší od GROUP BY.",
            "Řadit položky v rámci skupin pomocí ROW_NUMBER, RANK a DENSE_RANK.",
            "Počítat průběžné součty a klouzavé průměry pomocí rámců (frame).",
            "Porovnávat období pomocí LAG/LEAD a datových funkcí (DATE_TRUNC, EXTRACT).",
        ],
        "concept": """
**Okenní funkce** spočítá hodnotu pro každý řádek z množiny souvisejících řádků (*okna*), **aniž by je slučovala**:

```sql
function(...) OVER (PARTITION BY group_cols ORDER BY sort_cols ROWS BETWEEN ... )
```

* `PARTITION BY` začne výpočet znovu pro každou skupinu (jako GROUP BY, ale řádky zůstanou).
* `ORDER BY` uvnitř OVER určuje pořadí pro pořadí (ranking), průběžné součty a LAG/LEAD.
* Rámec určuje, které řádky se zahrnou: `ROWS BETWEEN 2 PRECEDING AND CURRENT ROW` dá klouzavý průměr ze 3 období.

| Potřeba | Funkce |
|---|---|
| Unikátní pořadí ve skupině | `ROW_NUMBER()` |
| Pořadí s mezerami po shodách (1,1,3) | `RANK()` |
| Pořadí bez mezer (1,1,2) | `DENSE_RANK()` |
| Předchozí / následující období | `LAG(x)`, `LEAD(x)` |
| Průběžný součet | `SUM(x) OVER (ORDER BY month)` |
| Podíl na celku | `x / SUM(x) OVER ()` |

Okna se vyhodnocují **po** WHERE/GROUP BY, takže podle nich nelze filtrovat ve WHERE. Zabalte dotaz do CTE, nebo použijte klauzuli `QUALIFY` z DuckDB (`QUALIFY rnk <= 3`).

**Datové funkce:** `DATE_TRUNC('month', order_date)` převede každé datum na první den jeho měsíce; `EXTRACT(year FROM order_date)` nebo `YEAR(order_date)` vytáhne části data; `order_date - INTERVAL 1 YEAR` posune data pro meziroční porovnání.
""",
        "business_context": """
Měsíční obchodní hodnocení potřebuje meziměsíční růst, kumulované tržby od začátku roku a nejprodávanější produkty v každé kategorii. Jsou to nejžádanější čísla v každém maloobchodním reportu - a zároveň nejčastěji chybně spočítaná, když se dělají ručně v tabulkovém procesoru.
""",
        "worked_example": {"explanation": """
* `monthly` nejprve agreguje na jeden řádek na měsíc; okenní funkce pak pracují s těmito 24 řádky.
* `LAG(revenue, 12)` se dívá o 12 řádků zpět = stejný měsíc loňského roku (platí jen proto, že je přesně jeden řádek na měsíc a žádné mezery - tento předpoklad vždy ověřte).
* Tříměsíční klouzavý průměr vyhlazuje šum; první dva měsíce průměrují méně než 3 hodnoty.
* **Interpretace:** meziroční porovnání odstraní sezónnost (prosinec vs. prosinec), meziměsíční ne.
"""},
        "summary": [
            "Okenní funkce řádky zachovávají; GROUP BY je slučuje.",
            "PARTITION BY = pro každou skupinu, ORDER BY = pořadí, rámec = které řádky.",
            "DENSE_RANK/RANK/ROW_NUMBER volte záměrně podle toho, jak chcete řešit shody.",
            "Meziroční růst očišťuje sezónnost; LAG předpokládá řadu bez mezer.",
        ],
        "common_mistakes": [
            "Filtrování výsledku okenní funkce ve WHERE (použijte CTE nebo QUALIFY).",
            "Použití LAG na řadě s chybějícími měsíci.",
            "Zapomenuté PARTITION BY při počítání průběžných součtů za jednotlivé roky.",
        ],
        "revision": "Sestavte řešený příklad znovu sloupec po sloupci. Pokud je struktura matoucí, zopakujte si CTE v ds3.",
    },
    "ds5": {
        "title": "Excel pro analytiky: vzorce, vyhledávání, kontingenční tabulky a citlivostní analýza",
        "objectives": [
            "Správně používat relativní, absolutní a smíšené odkazy.",
            "Aplikovat IF/IFS, SUMIFS/COUNTIFS a XLOOKUP na byznysové otázky.",
            "Shrnovat data kontingenčními tabulkami a vysvětlit odpovídající logiku v SQL/pandas.",
            "Vytvořit tabulku scénářů (what-if) a auditovatelné uspořádání sešitu.",
        ],
        "concept": """
**Odkazy.** `A1` je relativní (při kopírování se posune), `$A$1` je absolutní (nikdy se neposune), `$A1`/`A$1` jsou smíšené. Předpoklady (sazba daně, cílová marže) dávejte do popsaných vstupních buněk a odkazujte na ně absolutně: `=B2*$H$1`.

**Logika a podmíněná agregace**

| Vzorec | Účel | Ekvivalent v SQL |
|---|---|---|
| `=IF(C2>100,"High","Low")` | binární pravidlo | `CASE WHEN ... END` |
| `=IFS(C2>=500,"A",C2>=100,"B",TRUE,"C")` | více pravidel | `CASE` s několika WHEN |
| `=SUMIFS(Rev, Region,"West", Year,2024)` | podmíněný součet | `SUM(...) WHERE ... GROUP BY` |
| `=COUNTIFS(Status,"Cancelled")` | podmíněný počet | `COUNT(*) FILTER (WHERE ...)` |
| `=XLOOKUP(id, Products[id], Products[price], "not found")` | vyhledání | `LEFT JOIN` |

`XLOOKUP` nahrazuje `VLOOKUP` (ten se rozbije při vložení sloupce a ve výchozím stavu hledá přibližnou shodu). Ve starším Excelu použijte `INDEX(oblast_výsledku, MATCH(klíč, oblast_hledání, 0))`.

**Text a data:** `TEXT`, `LEFT`, `TRIM`, `PROPER`, `DATE`, `EOMONTH`, `YEAR`, `NETWORKDAYS`.

**Tabulky a kontingenční tabulky.** Převeďte data na tabulku Excelu (Ctrl+T), aby vzorce používaly strukturované odkazy a oblasti se automaticky rozšiřovaly. Kontingenční tabulka je GROUP BY s rozhraním „táhni a pusť“: *Řádky* a *Sloupce* jsou dimenze seskupení, *Hodnoty* jsou agregace, *Filtry/Průřezy* jsou klauzule WHERE.

**Citlivostní analýza (what-if).** *Data -> Citlivostní analýza -> Tabulka dat* přepočítá výstup (např. zisk) pro mřížku vstupních hodnot (cena x objem). *Hledání řešení* najde vstup, který dosáhne cíle.

**Auditovatelnost.** Oddělte listy *Vstupy*, *Výpočty* a *Výstupy*; vstupní buňky barvěte konzistentně; nevkládejte do vzorců pevná čísla; přidejte oblast *Kontroly* (např. součty odsouhlasené se zdrojem).
""",
        "business_context": """
Regionální manažeři žijí v Excelu. Potřebují kontingenční tabulku tržeb podle regionu a segmentu a jednoduchý model, jak zisk reaguje na změny ceny. Vaším úkolem je udělat sešit správný **a** auditovatelný, aby ho mohl ověřit jiný analytik.
""",
        "worked_example": {"explanation": """
* Dvojice kritérií v `SUMIFS` se kombinují pomocí AND; datová kritéria se skládají jako `">="&DATE(...)`.
* `Inputs!$H$1` je absolutní, takže každý řádek používá stejný cíl.
* `IFERROR` chrání před dělením nulou, ale může skrýt i skutečné chyby - používejte ho střídmě a jen tam, kde víte, jakou chybu čekáte.
* Stejná logika v pandas je níže; po spuštění dostanete čísla, která by měl váš sešit reprodukovat.
"""},
        "extra_examples": [{"explanation": "`pd.pivot_table` odpovídá kontingenční tabulce Excelu: `index` = Řádky, `columns` = Sloupce, `values`+`aggfunc` = Hodnoty, `margins` = Celkové součty."}],
        "summary": [
            "Absolutní odkazy ukotvují předpoklady; vstupy držte v popsaných buňkách.",
            "SUMIFS/COUNTIFS jsou podmíněné GROUP BY; XLOOKUP je bezpečné vyhledání (LEFT JOIN).",
            "Kontingenční tabulky = GROUP BY s Řádky/Sloupci/Hodnotami/Filtry.",
            "Oddělte vstupy, výpočty, výstupy a kontroly, aby váš sešit mohli ostatní auditovat.",
        ],
        "common_mistakes": [
            "VLOOKUP s přibližnou shodou (výchozí), který potichu vrací chybné hodnoty.",
            "Pevná čísla ve vzorcích místo odkazů na vstupní buňky.",
            "Kontingenční tabulky postavené na pevné oblasti, která se s novými daty nerozšiřuje.",
        ],
        "revision": "Dokončete workshop Excelu a porovnejte své výsledky SUMIFS s výstupem z pandas.",
    },
    "ds6": {
        "title": "Power BI: hvězdicová schémata, relace a míry v DAX",
        "objectives": [
            "Navrhnout hvězdicové schéma s faktovými a dimenzními tabulkami.",
            "Správně nastavit relace (kardinalita, směr filtru).",
            "Napsat základní míry DAX pro tržby, marži, růst a YTD.",
            "Vysvětlit kontext filtru, průřezy, procházení hierarchií (drill-down) a křížové filtrování.",
        ],
        "concept": """
**Power Query** (Načíst data -> Transformovat) je místo, kde data čistíte a tvarujete: měníte typy, odstraňujete sloupce, slučujete a připojujete dotazy. Každý krok se zaznamená a při aktualizaci přehraje - stejný princip reprodukovatelnosti jako u skriptu.

**Hvězdicové schéma.** Centrální **faktová** tabulka obsahuje události a číselné míry na definované granularitě (`order_items`: jeden řádek na položku objednávky). **Dimenzní** tabulky fakta popisují (`products`, `customers`, `calendar`). Relace vedou *jedna* (dimenze) -> *mnoho* (fakta) a filtry tečou z dimenzí do faktů.

* Upřednostňujte jednosměrné filtrování; obousměrné filtry vytvářejí nejednoznačnost a zpomalují modely.
* Vždy přidejte samostatnou **tabulku kalendáře** (označenou jako tabulka kalendáře) pro časové funkce.
* Sněhové vločky (produkt -> kategorie) fungují, ale sloučení do jedné dimenze produktu bývá jednodušší.

**Míry vs. počítané sloupce.** *Počítaný sloupec* se spočítá řádek po řádku při aktualizaci a uloží se (používá se pro průřezy/seskupení, např. cenové pásmo). *Míra* se počítá v okamžiku dotazu v aktuálním **kontextu filtru** (používá se pro agregace, jako jsou tržby). Většina KPI by měly být míry.

```DAX
Revenue      = SUMX(order_items, order_items[quantity] * order_items[unit_price] * (1 - order_items[discount_pct]))
Cost         = SUMX(order_items, order_items[quantity] * RELATED(products[unit_cost]))
Margin %     = DIVIDE([Revenue] - [Cost], [Revenue])
Revenue YTD  = TOTALYTD([Revenue], 'Calendar'[Date])
Revenue PY   = CALCULATE([Revenue], SAMEPERIODLASTYEAR('Calendar'[Date]))
YoY %        = DIVIDE([Revenue] - [Revenue PY], [Revenue PY])
```

**Kontext filtru** je množina filtrů (průřezy, osy vizuálů, filtry stránky) platných při vyhodnocení míry. `CALCULATE` kontext filtru mění; `DIVIDE` ošetří dělení nulou.

**Interakce:** průřezy filtrují stránku; výběr sloupce *křížově filtruje* ostatní vizuály; procházení (drill-down) vede v hierarchii z roku -> čtvrtletí -> měsíc.

**Aktualizace a výkon:** režim importu je nejrychlejší; odstraňte nepoužívané sloupce, vyhněte se textovým sloupcům s vysokou kardinalitou ve faktech a dávejte přednost mírám před počítanými sloupci.
""",
        "business_context": """
Northwind chce prodejní dashboard v Power BI. Před tvorbou vizuálů musíte navrhnout model: která tabulka je faktová, které jsou dimenze, jak spolu souvisejí a jaké míry dashboard potřebuje. Chybná relace vytvoří čísla, která *vypadají* věrohodně, ale jsou chybná v každém vizuálu.
""",
        "worked_example": {"explanation": """
`TOTALYTD` začíná každý rok znovu - ekvivalentem v SQL je průběžný SUM s `PARTITION BY year`.
Profesionální BI vývojáři před publikováním dashboardu odsouhlasí klíčové míry s nezávislým dotazem, jako je tento.
"""},
        "summary": [
            "Fakta obsahují měřitelné události na definované granularitě; dimenze je popisují.",
            "Výchozí jsou relace 1:N s jednosměrným filtrem z dimenze do faktů.",
            "Míry reagují na kontext filtru; počítané sloupce jsou pro každý řádek statické.",
            "Míry v dashboardu ověřte nezávislým výpočtem v SQL nebo pandas.",
        ],
        "common_mistakes": [
            "Implicitní součty sloupců místo explicitních měr.",
            "Obousměrné relace všude, „aby to fungovalo“.",
            "Chybějící tabulka kalendáře, takže se časové funkce chovají nečekaně.",
        ],
        "revision": "Projděte workshop Návrh modelu Power BI a kontrolu měr DAX.",
    },
    "ds7": {
        "title": "Návrh KPI a byznysový reporting",
        "objectives": [
            "Přesně definovat KPI (vzorec, filtry, granularita, vlastník, cíl).",
            "Rozlišovat metriky, dimenze, předpoklady a omezení.",
            "Sestavit měsíční report KPI a odsouhlasit ho.",
            "Vysvětlit byznysové dopady pohybů KPI, nejen samotná čísla.",
        ],
        "concept": """
KPI je užitečné jen tehdy, když ho všichni počítají stejně. Pro každé napište **kartu definice KPI**:

| Pole | Příklad: průměrná hodnota objednávky (AOV) |
|---|---|
| Byznysová otázka | Kolik nám vydělá typická objednávka? |
| Vzorec | tržby z dokončených objednávek / počet dokončených objednávek |
| Filtry | status = Completed; bez poplatků za dopravu |
| Granularita a období | měsíčně, podle regionu |
| Vlastník | manažer e-commerce |
| Cíl / práh | >= 165 EUR |
| Výhrady | citlivé na velké objednávky; sledujte i medián |

**Metriky vs. dimenze.** Metriky jsou čísla, která agregujete (tržby, objednávky). Dimenze jsou atributy, podle kterých data členíte (region, měsíc). **Předpoklady** jsou vaše rozhodnutí (sleva NULL = 0). **Omezení** určují, co je možné (data až od roku 2023).

**Dobré sady KPI** kombinují *výsledkové* metriky (tržby, marže) s *hnacími* metrikami (objednávky, AOV, konverze, míra vratek), aby šlo změnu vysvětlit: Tržby = Objednávky x AOV.

**Poměry vyžadují péči:** počítejte je ze sečtených složek (`SUM(revenue) / SUM(orders)`), nikdy průměrováním předem spočtených poměrů.

**Disciplína reportingu:** odsouhlaste součty se zdrojem, ukazujte srovnávací období, anotujte známé události a začínejte odpovědí na otázku „co z toho plyne“.

**Čitelnost a výkon dotazů:** používejte CTE se smysluplnými názvy, jeden sloupec na řádek, konzistentní aliasy; filtrujte co nejdříve, vybírejte jen potřebné sloupce a pokud možno nepoužívejte funkce na filtrovaných sloupcích (mohou zabránit prořezávání podle indexů/zón).
""",
        "business_context": """
Generální ředitel chce jednostránkový měsíční report KPI za rok 2024: objednávky, tržby, AOV a hrubou marži v %, plus pohled na vratky podle kategorie. Musíte dodat čísla **a** říct, co znamenají pro byznys.
""",
        "worked_example": {"explanation": """
* AOV se počítá ze **sečtených složek**, ne průměrováním hodnot objednávek po regionech a dalším průměrováním.
* Když tržby rostou, rozklad ukáže, zda díky více objednávkám, větším objednávkám, nebo obojímu - to je začátek diagnostického příběhu.
* Vedle čísla vždy uveďte definici (dokončené objednávky, bez dopravy).
"""},
        "summary": [
            "Každé KPI definujte vzorcem, filtry, granularitou, vlastníkem, cílem a výhradami.",
            "Výsledkové metriky párujte s hnacími, aby šlo pohyby vysvětlit.",
            "Poměry počítejte ze sečtených složek.",
            "Reporty začínejte dopady a čísla odsouhlaste se zdrojem.",
        ],
        "common_mistakes": [
            "Průměrování průměrů.",
            "KPI bez uvedených filtrů, takže různé týmy dostanou různá čísla.",
            "Reportování čísel bez srovnání a kontextu.",
        ],
        "revision": "Napište karty definic KPI pro tržby, AOV a míru vratek a pak začněte závěrečný projekt 1.",
    },
}
