"""Czech text for the Data Visualization lessons."""

LESSONS = {
    "vz1": {
        "title": "Výběr správného grafu pro danou otázku",
        "objectives": [
            "Přiřadit analytickým otázkám (porovnání, trend, rozdělení, vztah, složení) typy grafů.",
            "Vědět, kdy je tabulka lepší než graf.",
            "Rozlišit jednorozměrné, dvourozměrné a vícerozměrné pohledy.",
            "Volit grafy podle publika a rozhodnutí.",
        ],
        "concept": """
Začněte od **otázky**, ne od galerie grafů.

| Typ otázky | Dobré volby | Vyhněte se |
|---|---|---|
| Porovnání kategorií | seřazený sloupcový graf (vodorovný pro dlouhé popisky), tečkový graf | koláč s mnoha výsečemi, 3D sloupce |
| Trend v čase | spojnicový graf; sloupcový pro málo období | neseřazené sloupce, koláč |
| Rozdělení (jedna proměnná) | histogram, krabicový graf, houslový graf, ECDF | sloupec jen s průměry |
| Vztah (dvě číselné) | bodový graf (+ trendová čára), hexbin pro mnoho bodů | spojnicové grafy se dvěma osami naznačující korelaci |
| Složení | skládaný sloupec (málo částí), 100% skládaný sloupec, treemapa | koláč s > 4-5 výsečemi |
| Geografie | kartogram (míry, ne součty), mapa se symboly | mapy tam, kde o polohu nejde |
| Přesné vyhledání hodnoty | tabulka s podmíněným formátováním | graf |
| Mnoho proměnných | malé násobky, teplotní mapa, matice bodových grafů | jeden přetížený graf |

**Jednorozměrné** pohledy popisují jednu proměnnou (histogram). **Dvourozměrné** dávají do vztahu dvě (bodový graf, krabicové grafy podle skupin). **Vícerozměrné** přidávají třetí pomocí barvy, velikosti nebo panelů (malé násobky bývají srozumitelnější než bublinové grafy).

**Publikum a rozhodnutí:** vedení potřebuje odpověď a její důsledek (jeden jasný, anotovaný graf); analytici potřebují prozkoumávat (interaktivní filtry, detail). Graf, který odpovídá na otázku „který region nesplňuje cíl?“, má cíl i rozdíl ukázat na první pohled.

**Excel a Power BI** nabízejí stejné základní vizuály: skupinový pruhový/sloupcový, spojnicový, bodový, histogram, krabicový graf (Excel 2016+), mapa, matice, karta KPI. Pravidla výběru jsou ve všech nástrojích stejná.
""",
        "business_context": """
Vedení firmy Northwind klade čtyři otázky: Které kategorie vydělávají nejvíc? Rostou tržby? Jsou hodnoty objednávek typicky malé, nebo velké? Vedou větší slevy k větším objednávkám? Každá vyžaduje jiný graf.
""",
        "worked_example": {"explanation": """
* **Trend** -> spojnicový graf s osou od nuly u částek.
* **Rozdělení** -> histogram; oříznutí na 2 000 zachová viditelný tvar (oříznutí uveďte v názvu).
* **Vztah** -> bodový graf; logaritmická škála zvládne zešikmení a průhlednost (`alpha`) překrývání bodů.
"""},
        "summary": [
            "Graf volte podle typu otázky: porovnání, trend, rozdělení, vztah, složení.",
            "Pro přesné vyhledání hodnot jsou lepší tabulky.",
            "Pro mnoho proměnných použijte malé násobky.",
            "Navrhujte pro publikum a rozhodnutí.",
        ],
        "common_mistakes": [
            "Koláčové grafy s mnoha výsečemi.",
            "Neseřazené sloupcové grafy.",
            "Zobrazení jen průměrů, když záleží na rozdělení.",
        ],
        "revision": "Ke každé z „navrhovaných otázek“ u pěti datových sad uveďte nejvhodnější graf a proč.",
    },
    "vz2": {
        "title": "Základy Matplotlibu: osy, škály, popisky a anotace",
        "objectives": [
            "Používat objektově orientované API Matplotlibu (fig, ax).",
            "Nastavovat názvy, popisky os s jednotkami, značky, rozsahy a škály.",
            "Anotovat klíčové události a hodnoty přímo v grafu.",
            "Vytvářet malé násobky pomocí subplots.",
        ],
        "concept": """
Matplotlib má dvě rozhraní; pro cokoli nad rámec rychlého náhledu dávejte přednost **objektově orientovanému**:

```python
fig, ax = plt.subplots(figsize=(9, 4))
ax.plot(x, y, color="#2563eb", linewidth=2, label="Revenue")
ax.set_title("Monthly revenue, 2023-2024")
ax.set_xlabel("Month")
ax.set_ylabel("Revenue (EUR thousands)")
ax.set_ylim(bottom=0)
ax.annotate("Holiday peak", xy=(x_peak, y_peak), xytext=(x_peak, y_peak * 1.1),
            arrowprops=dict(arrowstyle="->"), ha="center")
ax.legend(frameon=False)
fig.tight_layout()
```

**Kontrolní seznam základů**

* **Název**, který říká pointu („Tržby vrcholí každý prosinec“), nebo alespoň předmět a období.
* **Popisky os s jednotkami** (EUR, %, tisíce). Formátujte značky: `ax.yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1.0))` nebo `FuncFormatter`.
* **Škály:** sloupce musí začínat na nule; u čar lze přiblížit, když záleží na *změně*, ale řekněte to. Pro multiplikativní data použijte logaritmickou škálu a označte ji.
* **Anotace** vysvětlují události (akce, výpadky zásob) tam, kam se oko už dívá - lépe než legenda nebo poznámka pod čarou.
* **Legendy:** jen když jsou nutné; přímé popisky na koncích čar se čtou snáz.
* **Malé násobky:** `fig, axes = plt.subplots(2, 3, sharex=True, sharey=True)` - sdílené osy dělají panely porovnatelnými.
* **Odstraňte nepořádek:** `ax.spines[["top", "right"]].set_visible(False)`; světlá mřížka nebo žádná.

V laboratoři se vytvořené obrázky zachytí a zobrazí automaticky - `plt.show()` není potřeba (ale neuškodí).
""",
        "business_context": """
Prezentace k měsíčnímu hodnocení potřebuje graf trendu tržeb, který netechnické publikum přečte za pět sekund, s výslovně anotovaným výpadkem zásob v regionu West, aby nikdo propad nevyložil špatně.
""",
        "worked_example": {"explanation": """
* Název uvádí zjištění; vystínovaný úsek a anotace vysvětlují propad přímo na místě.
* `set_ylim(bottom=0)` zachová poctivou velikost propadu; formátovač dělá značky čitelnými (90k místo 90000).
* Odstranění horní a pravé osy ubere nepořádek bez ztráty informace.
"""},
        "summary": [
            "Použijte fig, ax = plt.subplots() a vše nastavujte explicitně.",
            "Názvy říkají pointu; popisky nesou jednotky.",
            "Události anotujte přímo v grafu.",
            "Malé násobky se sdílenými osami umožňují porovnání.",
        ],
        "common_mistakes": [
            "Chybějící jednotky na osách.",
            "Legendy, které nutí čtenáře těkat očima sem a tam.",
            "Nekonzistentní osy v malých násobcích.",
        ],
        "revision": "Převeďte řešený příklad na malé násobky: jeden panel na region se sdílenou osou y.",
    },
    "vz3": {
        "title": "Principy designu: barva, hierarchie, přístupnost a nepořádek",
        "objectives": [
            "Používat barvu účelně: kategoriální, sekvenční, divergentní, zvýraznění.",
            "Vytvářet vizuální hierarchii velikostí, tloušťkou, polohou a prázdným prostorem.",
            "Navrhovat pro poruchy barevného vidění a s dostatečným kontrastem.",
            "Odstraňovat nepořádek a snižovat kognitivní zátěž.",
        ],
        "concept": """
**Barva má tři úkoly:**

* *Kategoriální* - rozlišit skupiny (max. ~6-8 odlišných odstínů).
* *Sekvenční* - uspořádaná velikost (světlá -> tmavá jednoho odstínu), např. míra odchodu na mapě.
* *Divergentní* - odchylka od smysluplného středu (pod/nad cílem), dva odstíny s neutrálním středem.
* *Zvýraznění* - vše šedě, barevně jen to jedno důležité. V byznysových grafech často nejúčinnější volba.

**Přístupnost**

* ~8 % mužů má poruchu barevného vidění; nejčastějším problémem je rozlišení červené a zelené. Používejte palety bezpečné pro barvoslepé (např. Okabe-Ito, viridis) a redundantní kódování (popisky, tvary, poloha).
* Kontrast textu vůči pozadí >= 4,5:1 (WCAG AA). Vyhněte se světle šedému textu na bílé.
* Nespoléhejte na samotnou barvu; přidejte přímé popisky.
* Pro čtečky obrazovky uveďte alternativní text nebo jednu větu se závěrem.

**Hierarchie a prázdný prostor.** Nejdůležitější prvek má být nejvýraznější (poloha vlevo nahoře, větší, tučnější, barevný). Zarovnávejte prvky do mřížky; seskupujte související; mezi skupinami nechte prázdný prostor.

**Nepořádek a kognitivní zátěž (poměr dat k inkoustu).** Odstraňte, co neinformuje: těžké rámečky, výplně pozadí, 3D efekty, nadbytečné legendy, přemíru mřížek, desetinná místa, která nikdo nepotřebuje. Každý prvek si své místo musí zasloužit.

**Typografie:** jedna rodina písma, dvě až tři velikosti, velké písmeno jen na začátku věty, vodorovný text (raději otočte graf - použijte vodorovné sloupce - než popisky).
""",
        "business_context": """
Snímek retenčního týmu ukazuje odchod podle akvizičního zdroje v pěti křiklavých barvách s legendou. Vedení se pořád ptá: „Který je ten problém?“ Přepracujte ho tak, aby byla odpověď zřejmá a přístupná.
""",
        "worked_example": {"explanation": """
* **Zvýrazňující barva** směruje pozornost; šedá upozadí kontextové kategorie.
* Přímé popisky hodnot nahrazují legendu a graf je čitelný i bez barvy.
* Vodorovné sloupce udrží popisky kategorií vodorovně; seřazení dá porovnání pořádek.
* Název uvádí závěr, takže graf funguje, i když ho čtenář jen přelétne.
"""},
        "summary": [
            "Kategoriální, sekvenční, divergentní nebo zvýrazňující barvu volte záměrně.",
            "Navrhujte s ohledem na poruchy barevného vidění a kontrast; nikdy nespoléhejte jen na barvu.",
            "Hierarchii budujte polohou, velikostí a prázdným prostorem.",
            "Odstraňte inkoust, který nic nesděluje.",
        ],
        "common_mistakes": [
            "Duhové palety pro uspořádaná data.",
            "Červená/zelená jako jediné rozlišení.",
            "Legendy tam, kde by stačily přímé popisky.",
        ],
        "revision": "Vytvořte graf znovu se sekvenční paletou a vysvětlete, proč zde zvýraznění funguje lépe.",
    },
    "vz4": {
        "title": "Zavádějící vizualizace a jak je opravit",
        "objectives": [
            "Rozpoznat běžné zavádějící techniky.",
            "Kritizovat graf konkrétními, proveditelnými vylepšeními.",
            "Opravit v kódu oříznuté osy, zkreslené plochy a účelově vybrané rozsahy.",
        ],
        "concept": """
Grafy zavádějí designem stejně jako daty. Běžné problémy:

| Problém | Proč zavádí | Oprava |
|---|---|---|
| Oříznutá osa sloupců | délka sloupce už není úměrná hodnotě; malé rozdíly vypadají obrovské | sloupce od nuly, nebo body/čáry a uvedené přiblížení |
| Dvě osy s libovolnými měřítky | průsečík i sklony jsou artefakty měřítka | dva zarovnané panely, nebo obě řady indexované na 100 |
| Účelově vybrané časové okno | mimo okno se trend obrací | ukažte celé relevantní období nebo okno zdůvodněte |
| 3D efekty / plošné a objemové ikony | perspektiva zkresluje velikost; plocha roste se čtvercem poloměru | ploché 2D značky škálované délkou |
| Nekonzistentní nebo obrácené škály | čtenáři předpokládají nahoru = více a stejné intervaly | konvenční, konzistentní škály |
| Kumulativní grafy skrývající poklesy | kumulativní součty vždy rostou | ukažte hodnoty za období |
| Součty na mapách | velké regiony/populace dominují | normalizujte na míry na obyvatele |
| Chybějící nejistota | malé vzorky vypadají stejně přesně jako velké | chybové úsečky, intervaly, velikosti vzorků |
| Koláče s mnoha výsečemi / nedávající 100 % | úhly se špatně porovnávají | seřazené sloupce |

**Strukturovaná kritika** pojmenuje problém, vysvětlí jeho vliv na interpretaci a navrhne konkrétní opravu: *„Osa y začíná na 9,5 %, takže zlepšení testované varianty o 0,6 p. b. vypadá jako trojnásobný rozdíl. Začněte na 0 % a přidejte IS, které navíc ukážou, že rozdíl není významný.“*

Zavádějící grafy často vznikají nechtěně (výchozí nastavení softwaru), ale za dojem, který graf vytváří, odpovídá analytik.
""",
        "business_context": """
Snímek produktového manažera oslavuje test pokladny sloupcovým grafem, jehož osa y začíná na 9,8 %. Finanční ředitel se chystá nasazení schválit. Váš úkol: graf zkritizovat a vytvořit poctivou verzi.
""",
        "worked_example": {"explanation": """
* Vlevo vypadá rozdíl 0,6 procentního bodu, jako by byla testovaná varianta několikanásobně lepší.
* Vpravo osa od nuly ukazuje skutečný poměr a intervaly spolehlivosti nejistotu - vizuál nyní odpovídá statistickému závěru z lekce dg5.
"""},
        "summary": [
            "Sloupce začínají na nule; přiblížené osy potřebují výslovné zdůvodnění.",
            "Vyhněte se dvěma osám, 3D a zkreslení ploch; mapy normalizujte.",
            "Ukazujte nejistotu a velikosti vzorků.",
            "Kritika = problém + vliv na interpretaci + konkrétní oprava.",
        ],
        "common_mistakes": [
            "Přijetí výchozích rozsahů os ze softwaru.",
            "Grafy se dvěma osami naznačující korelace.",
            "Prezentace malých rozdílů bez nejistoty.",
        ],
        "revision": "Dokončete workshop Kritika dashboardu a každou vadu vysvětlete jednou větou.",
    },
    "vz5": {
        "title": "Dashboardy, datové vyprávění a komunikace nejistoty",
        "objectives": [
            "Navrhovat dashboardy kolem rozhodnutí a uživatelů.",
            "Rozvrhnout KPI, trendy a procházení do detailu s interaktivními filtry.",
            "Psát manažerská shrnutí a strukturovat datový příběh.",
            "Vizualizovat nejistotu pomocí intervalů a rozsahů.",
        ],
        "concept": """
**Dashboardy** podporují opakovaná rozhodnutí; **příběhy** podporují jednorázové rozhodnutí. Obojí začíná otázkou: *kdo to používá, pro jaké rozhodnutí a jak často?*

**Rozvržení dashboardu (zleva nahoře doprava dolů):**

1. **Karty KPI** - aktuální hodnota, srovnání (vs. cíl / minulý rok), mini graf trendu.
2. **Trend** - hlavní KPI v čase s čárou cíle.
3. **Rozpad** - podle dimenzí, podle kterých lidé jednají (region, kategorie).
4. **Detail** - tabulka pro procházení do hloubky.

Interaktivní **filtry** (datum, region) patří nahoru nebo doleva; **procházení** (rok -> měsíc) a **křížové filtrování** (klik na sloupec filtruje ostatní) umožní prozkoumávat bez dalších stránek. Omezte každý pohled na 5-9 vizuálů; používejte konzistentní barvy (jedna barva = jeden význam v celém dashboardu).

**Datové vyprávění** - klasická struktura:

1. **Kontext** - co publikum už ví a co ho zajímá.
2. **Komplikace** - co se změnilo nebo co je v sázce.
3. **Řešení** - vaše zjištění a doporučení.

**Manažerské shrnutí pište jako první**: tři až pět vět s odpovědí, důkazy a žádostí. Název každého grafu je věta, která posouvá příběh.

**Nejistota** - ukazujte ji vždy, když na ní rozhodnutí závisí:

* chybové úsečky nebo pásy intervalů (`ax.fill_between`) u odhadů a předpovědí;
* velikosti vzorků vedle měr;
* rozsahy scénářů (nízký/základní/vysoký) u projekcí;
* slova odpovídající důkazům („pravděpodobně“, „v rozmezí“).

**Poznámky k nástrojům:** dashboardy v Power BI a Tableau podporují popisky (tooltips), přechod na detail (drill-through) a záložky; Looker Studio podporuje ovládací prvky (období, rozbalovací filtry) a propojené zdroje dat. Principy jsou ve všech nástrojích stejné.
""",
        "business_context": """
Generální ředitel chce jednostránkový přehled: je byznys zdravý, kde jsou problémy a co s nimi děláme? Potřebujete specifikaci dashboardu a krátký příběh pro správní radu.
""",
        "worked_example": {"explanation": """
* Body s intervaly ukazují odhady **i** jejich přesnost; malý vzorek tabletů vede k širokým intervalům.
* Velikosti vzorků jsou vypsané, aby čtenář mohl posoudit spolehlivost.
* Název říká publiku, jaký závěr je (a není) podložený.
"""},
        "summary": [
            "Dashboardy navrhujte kolem uživatelů a rozhodnutí: KPI -> trend -> rozpad -> detail.",
            "Příběhy mají strukturu kontext -> komplikace -> řešení; shrnutí pište jako první.",
            "Nejistotu ukazujte intervaly, rozsahy a velikostmi vzorků.",
            "Význam barev držte v celém dashboardu konzistentní.",
        ],
        "common_mistakes": [
            "Dashboardy, které ukazují všechno a neodpovídají na nic.",
            "Názvy grafů, které jen pojmenují metriku.",
            "Bodové odhady bez nejistoty u rozhodnutí, která na ní závisí.",
        ],
        "revision": "Napište čtyřvěté manažerské shrnutí šetření odchodu a pak začněte závěrečný projekt 5.",
    },
    "vz6": {
        "title": "Práce v Tableau: data, pole, výpočty a dashboardy",
        "objectives": [
            "Připojit Tableau k CSV datům a definovat relace.",
            "Rozlišit dimenze/míry a diskrétní/spojitá pole.",
            "Psát počítaná pole včetně výrazů LOD.",
            "Sestavit interaktivní dashboard s filtry a akcemi.",
        ],
        "concept": """
> Tato lekce je **řízené zadání** pro Tableau Desktop nebo Tableau Public (zdarma). Laboratoř samotné Tableau spustit neumí; poskytuje data, úkoly, očekávaná čísla k ověření práce a rubriku pro sebekontrolu.

**Připojení dat.** *Connect -> Text file* a vyberte `orders.csv`. Přetáhněte `order_items.csv`, `products.csv`, `categories.csv` a `customers.csv` na plátno a vytvořte **relace** (logická vrstva Tableau drží každou tabulku na její vlastní granularitě, což zabrání dvojímu započtení, ke kterému mohou vést fyzická spojení).

**Role polí.** *Dimenze* (modré, když jsou diskrétní) data člení; *míry* (zelené, když jsou spojité) se agregují. Diskrétní pole vytvářejí záhlaví; spojitá pole vytvářejí osy. Data mohou být diskrétní (MONTH jako záhlaví) nebo spojitá (časová osa).

**Počítaná pole** (Analysis -> Create Calculated Field):

```
Revenue        = [Quantity] * [Unit Price (Order Items)] * (1 - ZN([Discount Pct]))
Completed Rev  = IF [Status] = "Completed" THEN [Revenue] END
Margin %       = (SUM([Completed Rev]) - SUM([Line Cost])) / SUM([Completed Rev])
Customer First Order = { FIXED [Customer Id] : MIN([Order Date]) }      // výraz LOD
```

`ZN()` převede NULL na nulu (předpoklad uveďte). **Výrazy LOD** počítají hodnoty na zadané granularitě nezávisle na pohledu - např. datum první objednávky zákazníka pro kohortní analýzu.

**Tvorba pohledů:** přetahujte pole na police *Rows/Columns*; kartu *Marks* použijte pro barvu, velikost, popisek a tooltip; *Show Me* navrhuje typy grafů (použijte pravidla výběru z lekce vz1).

**Dashboardy:** spojte listy; přidejte *filtry* (aplikované na všechny listy se stejným zdrojem dat), *filtrační akce* (klik na sloupec filtruje jiné pohledy), *zvýrazňovací akce* a *parametry* (vstupy ovládané uživatelem, např. cílová marže). Použijte pevnou velikost (např. 1200 x 800) a jasnou mřížku rozvržení.
""",
        "business_context": """
Regionální manažeři firmy Northwind používají Tableau Server. Sestavte sešit „Retail Performance“: trend tržeb, marže podle kategorií a procházení podle regionů s interaktivními filtry.
""",
        "worked_example": {"explanation": "Ve workshopu Tableau si stáhněte CSV soubory a zadání a pak svůj sešit ověřte podle očekávaných součtů, které jsou tam uvedeny."},
        "summary": [
            "Relace drží tabulky na jejich vlastní granularitě; dávejte jim přednost před fyzickými spojeními.",
            "Dimenze člení, míry agregují; diskrétní = záhlaví, spojité = osy.",
            "Počítaná pole a výrazy LOD kódují byznysovou logiku.",
            "Dashboardy spojují listy s filtry, akcemi a parametry.",
        ],
        "common_mistakes": [
            "Fyzická spojení, která zdvojí hodnoty na úrovni objednávky.",
            "Agregace poměrů pomocí SUM místo jejich výpočtu ze součtů.",
            "Filtry, které nečekaně působí jen na jeden list.",
        ],
        "revision": "Dokončete workshop Tableau a zaznamenejte svou sebekontrolu.",
    },
    "vz7": {
        "title": "Práce v Looker Studio: zdroje dat, metriky a interaktivní reporty",
        "objectives": [
            "Připravit data z CSV/Tabulek Google pro Looker Studio.",
            "Nastavit dimenze, metriky, agregace a počítaná pole.",
            "Vytvořit grafy, přehledové karty a interaktivní ovládací prvky.",
            "Odpovědně sdílet a dokumentovat report.",
        ],
        "concept": """
> Tato lekce je **řízené zadání** pro Looker Studio (dříve Google Data Studio; zdarma, v prohlížeči, vyžaduje účet Google). Laboratoř se ke Googlu nepřipojuje; poskytuje připravená data, postup krok za krokem a očekávaná čísla k ověření reportu.

**Připravte data.** Looker Studio funguje nejlépe s jednou plochou, uspořádanou tabulkou na zdroj dat. Workshop poskytuje `looker_retail_lines.csv` - jeden řádek na položku dokončené objednávky s tržbami, náklady, kategorií, regionem a datem už spojenými (bez dvojího započtení). Nahrajte ho přes *Vytvořit -> Zdroj dat -> Nahrání souboru*, nebo ho nejprve importujte do Tabulek Google.

**Nastavte pole.** V editoru zdroje dat zkontrolujte u každého pole **typ** (Datum, Číslo, Text, Geo) a **výchozí agregaci** (Součet, Průměr, Počet jedinečných). `order_date` nastavte na *Datum (YYYYMMDD)*, `revenue` a `cost` na *Měna (EUR)* se Součtem, `order_id` na *Počet jedinečných*, když slouží jako metrika.

**Počítaná pole:**

```
Gross margin %   = (SUM(revenue) - SUM(cost)) / SUM(revenue)
AOV              = SUM(revenue) / COUNT_DISTINCT(order_id)
Revenue band     = CASE WHEN revenue >= 200 THEN "High" WHEN revenue >= 50 THEN "Medium" ELSE "Low" END
```

Poměry musí agregovat čitatel a jmenovatel zvlášť - definujte je se SUM uvnitř vzorce.

**Sestavte report:** *přehledové karty* pro KPI (se srovnávacím obdobím pro změnu v %), *časová řada* tržeb, *sloupcový graf* kategorií, *geografický graf* nebo tabulka regionů. Přidejte **ovládací prvky**: výběr období, rozbalovací seznam regionů a zapněte *křížové filtrování* grafů.

**Sdílejte odpovědně:** ve výchozím stavu přístup jen pro čtení, textové pole s definicemi a aktuálností dat a žádné osobní údaje ve sdílených reportech.
""",
        "business_context": """
Marketing firmy Northwind používá Google Workspace a chce samoobslužný report v Looker Studio o výkonu za rok 2024 podle regionu a kategorie.
""",
        "worked_example": {"explanation": "Ve workshopu Looker Studio si stáhněte připravené CSV a zadání; své přehledové karty porovnejte s očekávanými hodnotami."},
        "summary": [
            "Looker Studiu dodejte plochou, uspořádanou tabulku se správnými typy.",
            "Nastavte výchozí agregace; poměry definujte ze součtů.",
            "Přehledové karty se srovnáním, časové řady a ovládací prvky dělají reporty interaktivními.",
            "Definice a aktuálnost dat dokumentujte přímo v reportu.",
        ],
        "common_mistakes": [
            "Průměrování předem spočítaného sloupce marže.",
            "Špatné typy polí (data jako text), které rozbijí časové řady.",
            "Sdílení s možností úprav jako výchozí.",
        ],
        "revision": "Dokončete workshop Looker Studio a rubriku sebekontroly.",
    },
}
