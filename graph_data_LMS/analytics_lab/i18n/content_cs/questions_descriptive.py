"""Czech text for the Descriptive Analytics questions. Options are (text, why) in the original order."""

TOPICS = {
    "SQL clause order": "Pořadí klauzulí SQL",
    "COUNT variants": "Varianty COUNT",
    "Date filtering": "Filtrování podle data",
    "WHERE vs HAVING": "WHERE vs. HAVING",
    "NULL handling": "Práce s NULL",
    "CASE expressions": "Výrazy CASE",
    "Join grain": "Granularita spojení",
    "LEFT JOIN filters": "Filtry u LEFT JOIN",
    "Anti-joins": "Anti-joiny",
    "Window vs GROUP BY": "Okenní funkce vs. GROUP BY",
    "Ranking functions": "Funkce pořadí",
    "Period comparisons": "Porovnání období",
    "Cell references": "Odkazy na buňky",
    "Lookups": "Vyhledávání",
    "PivotTables": "Kontingenční tabulky",
    "Star schema": "Hvězdicové schéma",
    "Measures vs calculated columns": "Míry vs. počítané sloupce",
    "Filter context": "Kontext filtru",
    "KPI definition": "Definice KPI",
    "Ratio aggregation": "Agregace poměrů",
    "Metrics vs dimensions": "Metriky vs. dimenze",
    "Interpreting KPI changes": "Interpretace změn KPI",
    "Query performance": "Výkon dotazů",
    "What-if analysis": "Citlivostní analýza",
}

QUESTIONS = {
    "q_ds_001": {
        "stem": "V jakém logickém pořadí databáze vyhodnocuje tyto klauzule?",
        "options": [
            ("FROM -> WHERE -> GROUP BY -> SELECT -> ORDER BY", "Správně: řádky se načtou, vyfiltrují, seskupí, vyberou sloupce a pak seřadí."),
            ("SELECT -> FROM -> WHERE -> GROUP BY -> ORDER BY", "To je pořadí, v jakém klauzule *píšete*, ne v jakém se vyhodnocují."),
            ("FROM -> SELECT -> WHERE -> ORDER BY -> GROUP BY", "WHERE musí proběhnout před SELECT; proto nelze ve WHERE použít alias ze SELECT."),
            ("WHERE -> FROM -> SELECT -> GROUP BY -> ORDER BY", "WHERE potřebuje tabulku, kterou filtruje, takže FROM musí být první."),
        ],
        "explanation": "Znalost logického pořadí vysvětluje běžné chyby, například že aliasy nejsou ve WHERE viditelné a že tam nejsou povoleny agregace.",
    },
    "q_ds_002": {
        "stem": "Tabulka `customers` má 1 000 řádků; `birth_year` je u 80 z nich NULL a má 55 různých hodnot různých od NULL. Co vrátí `SELECT COUNT(birth_year) FROM customers`?",
        "options": [
            ("920", "COUNT(sloupec) počítá hodnoty různé od NULL: 1 000 - 80."),
            ("1,000", "To je COUNT(*), které počítá řádky bez ohledu na NULL."),
            ("55", "To je COUNT(DISTINCT birth_year)."),
            ("56", "COUNT(DISTINCT ...) nepočítá NULL jako samostatnou hodnotu."),
        ],
        "explanation": "COUNT(*), COUNT(col) a COUNT(DISTINCT col) odpovídají na tři různé otázky. Volte záměrně.",
    },
    "q_ds_003": {
        "stem": "`order_ts` je TIMESTAMP. Který filtr spolehlivě vrátí všechny objednávky z roku 2024?",
        "options": [
            ("order_ts >= TIMESTAMP '2024-01-01' AND order_ts < TIMESTAMP '2025-01-01'", "Polootevřený interval zahrne všechny časy 31. prosince a funguje pro data i časová razítka."),
            ("order_ts BETWEEN '2024-01-01' AND '2024-12-31'", "Horní mez je půlnoc na začátku 31. 12., takže pozdější objednávky toho dne se ztratí."),
            ("order_ts LIKE '2024%'", "LIKE pracuje s textem; spoléhat na implicitní převod je křehké a brání efektivnímu filtrování."),
            ("order_ts > '2024-01-01' AND order_ts < '2024-12-31'", "Vyloučí objednávky o půlnoci 1. ledna a vše z 31. prosince."),
        ],
        "explanation": "Polootevřené datové intervaly (>= začátek AND < další začátek) jsou profesionální standard.",
    },
    "q_ds_004": {
        "stem": "Potřebujete regiony, jejichž **celkové tržby** přesahují 1 mil. EUR, přičemž se berou v úvahu jen dokončené objednávky. Kam patří obě podmínky?",
        "options": [
            ("status do WHERE; SUM(revenue) > 1000000 do HAVING", "Filtry řádků patří do WHERE (před seskupením), filtry agregací do HAVING (po seskupení)."),
            ("Obě do WHERE", "Agregace ve WHERE nejsou k dispozici, protože seskupení ještě neproběhlo."),
            ("Obě do HAVING", "V některých databázích to funguje, ale filtruje se pozdě a zamlžuje to záměr; status je podmínka na úrovni řádku."),
            ("status do HAVING; SUM(revenue) do WHERE", "Obráceně: WHERE nesmí obsahovat agregační funkce."),
        ],
        "explanation": "WHERE filtruje řádky, HAVING filtruje skupiny.",
    },
    "q_ds_005": {
        "stem": "Která tvrzení o NULL v SQL jsou pravdivá? (Vyberte všechny správné.)",
        "options": [
            ("`WHERE discount = NULL` nevrátí žádné řádky", "Porovnání s NULL dává UNKNOWN, nikdy TRUE; použijte IS NULL."),
            ("AVG(discount) ignoruje hodnoty NULL", "Agregace NULL přeskakují, což mění jmenovatel průměru."),
            ("COALESCE(discount, 0) by se mělo standardně použít na každý sloupec", "Nahrazení NULL nulou je byznysový předpoklad, který je třeba zdůvodnit; chybějící není totéž co nula."),
            ("NULL + 5 se vyhodnotí jako 5", "Aritmetika s NULL vrací NULL."),
        ],
        "explanation": "NULL znamená neznámé. Pracujte s ním explicitně a volbu zdokumentujte.",
    },
    "q_ds_006": {
        "stem": "Jaký popisek přiřadí tento výraz CASE řádku s amount = 250?",
        "options": [
            ("'Medium'", "Větve WHEN se testují shora dolů; 250 nesplní > 500 a splní > 100."),
            ("'Large'", "250 není větší než 500."),
            ("'Small'", "ELSE se použije jen tehdy, když nevyhověla žádná předchozí větev."),
            ("'Medium' i 'Small'", "CASE vrací právě jednu hodnotu: první shodu."),
        ],
        "explanation": "Větve CASE řaďte od nejkonkrétnější po nejobecnější; vyhrává první pravdivá podmínka.",
    },
    "q_ds_007": {
        "stem": "Spojíte `orders` (jeden řádek na objednávku, obsahuje `shipping_cost`) s `order_items` (jeden řádek na položku) a spočítáte `SUM(o.shipping_cost)`. Co se stane?",
        "options": [
            ("Doprava je nadhodnocená: poplatek každé objednávky se započte jednou za každou položku", "Spojení změní granularitu na položky, takže hodnoty na úrovni objednávky se opakují."),
            ("Výsledek je správný, protože SUM odstraňuje duplicity", "SUM sčítá každý řádek; duplicity nikdy neodstraňuje."),
            ("Dotaz selže, protože se granularity liší", "SQL ho klidně spustí - právě proto je ta chyba nebezpečná."),
            ("Doprava je podhodnocená, protože se ignorují NULL", "Problémem tu nejsou NULL, ale zdvojení."),
        ],
        "explanation": "Každou míru agregujte na její vlastní granularitě, nebo agregujte před spojením.",
    },
    "q_ds_008": {
        "stem": "`customers c LEFT JOIN orders o ON o.customer_id = c.customer_id WHERE o.status = 'Completed'`. Proč tento dotaz už nevrací zákazníky bez objednávek?",
        "options": [
            ("Podmínka WHERE je pro NULL v o.status nepravdivá, takže se nespárovaní zákazníci odstraní", "Filtrování pravé tabulky ve WHERE změní LEFT JOIN na vnitřní spojení; podmínku přesuňte do ON."),
            ("LEFT JOIN nikdy nevrací nespárované řádky", "Vracet nespárované levé řádky je přesně to, co LEFT JOIN dělá."),
            ("Protože status je textový sloupec", "Datový typ je nepodstatný."),
            ("DuckDB nepodporuje LEFT JOIN s WHERE", "Podporuje; problémem je logika."),
        ],
        "explanation": "Podmínky na volitelné straně vnějšího spojení patří do klauzule ON.",
    },
    "q_ds_009": {
        "stem": "Proč je `NOT EXISTS` obvykle bezpečnější než `NOT IN (SELECT customer_id FROM orders)` při hledání zákazníků bez objednávek?",
        "options": [
            ("Pokud poddotaz vrátí jakékoli NULL, NOT IN nevrátí vůbec žádné řádky", "x NOT IN (..., NULL) je pro každé x UNKNOWN, takže se výsledek potichu vyprázdní."),
            ("NOT EXISTS je vždy rychlejší", "Výkon závisí na databázi; klíčovým rozdílem je chování NULL."),
            ("NOT IN nelze použít s poddotazy", "Lze; jen se s NULL chová překvapivě."),
            ("NOT EXISTS ignoruje duplicity, NOT IN ne", "Duplicity nemění ani jeden výsledek."),
        ],
        "explanation": "Pro anti-joiny dávejte přednost NOT EXISTS nebo LEFT JOIN ... IS NULL.",
    },
    "q_ds_010": {
        "stem": "Jaký je hlavní rozdíl mezi `SUM(revenue) OVER (PARTITION BY region)` a `SUM(revenue) ... GROUP BY region`?",
        "options": [
            ("Okenní verze zachová každý vstupní řádek a ke každému připojí součet za region", "Okenní funkce řádky neslučují."),
            ("Vracejí stejné výsledky", "GROUP BY vrací jeden řádek na region; okenní funkce jeden řádek na každý vstupní řádek."),
            ("Okenní verze je platná jen s ORDER BY", "ORDER BY je volitelné; bez něj je oknem celá partition."),
            ("GROUP BY neumí spočítat součty podle regionu", "Přesně to GROUP BY dělá."),
        ],
        "explanation": "Okenní funkce použijte, když potřebujete detail řádku spolu s kontextem skupiny (podíly, pořadí, průběžné součty).",
    },
    "q_ds_011": {
        "stem": "Tři produkty mají tržby 900, 900 a 800. Co přiřadí DENSE_RANK() (řazeno podle tržeb DESC)?",
        "options": [
            ("1, 1, 2", "DENSE_RANK dá shodám stejné pořadí a nepřeskakuje čísla."),
            ("1, 1, 3", "To je RANK(), které po shodách nechá mezeru."),
            ("1, 2, 3", "To je ROW_NUMBER(), které shody rozhoduje libovolně."),
            ("2, 2, 3", "Pořadí začíná od 1."),
        ],
        "explanation": "Funkci pořadí volte podle toho, jak se mají podle byznysového pravidla chovat shody.",
    },
    "q_ds_012": {
        "stem": "V tabulce měsíčních tržeb chybí řádek za měsíc s nulovými prodeji. Jaké je riziko `LAG(revenue, 12)` pro meziroční růst?",
        "options": [
            ("LAG počítá řádky, ne měsíce, takže pozdější porovnání použijí špatný měsíc", "Při mezeře už „12 řádků zpět“ není „stejný měsíc loni“."),
            ("LAG vrátí NULL pro každý řádek", "NULL vrátí jen prvních 12 řádků."),
            ("Žádné riziko; LAG rozumí kalendářním měsícům", "LAG je čistě poziční."),
            ("Dotaz skončí chybou", "Proběhne potichu - v tom je nebezpečí."),
        ],
        "explanation": "Před použitím pozičních okenních funkcí sestavte úplný kalendář (nebo spojujte přes month - INTERVAL 1 YEAR).",
    },
    "q_ds_013": {
        "stem": "Zkopírujete `=B2*$H$1` z C2 dolů do C3. Jaký vzorec se objeví v C3?",
        "options": [
            ("=B3*$H$1", "Relativní odkaz se posune o řádek; absolutní zůstane pevný."),
            ("=B2*$H$1", "Relativní odkazy se při kopírování posouvají."),
            ("=B3*$H$2", "$H$1 je absolutní v řádku i sloupci."),
            ("=C3*$H$1", "Kopírování dolů mění řádky, ne sloupce."),
        ],
        "explanation": "Předpoklady ukotvěte absolutními odkazy, aby každý řádek používal stejný vstup.",
    },
    "q_ds_014": {
        "stem": "Proč se dává přednost `XLOOKUP` (nebo INDEX/MATCH) před `VLOOKUP(id, A:D, 3)`?",
        "options": [
            ("VLOOKUP ve výchozím stavu hledá přibližnou shodu a rozbije se při vložení sloupců", "Vynechání 4. argumentu znamená přibližnou shodu a pevně zadané číslo sloupce se potichu posune."),
            ("VLOOKUP neumí vracet čísla", "Vrátí jakoukoli hodnotu."),
            ("XLOOKUP je rychlejší na každé datové sadě", "Rychlost není hlavním důvodem; jde o správnost a robustnost."),
            ("VLOOKUP funguje jen na seřazeném textu", "S přesnou shodou (FALSE) funguje i na neseřazených datech."),
        ],
        "explanation": "Vyhledávání jsou spojení; dělejte je přesná a odolná vůči změnám rozvržení.",
    },
    "q_ds_015": {
        "stem": "Která konstrukce SQL nejvíce odpovídá přetažení *Region* do Řádků a *Součet tržeb* do Hodnot v kontingenční tabulce?",
        "options": [
            ("SELECT region, SUM(revenue) ... GROUP BY region", "Řádky jsou dimenze seskupení; Hodnoty jsou agregace."),
            ("SELECT DISTINCT region, revenue", "DISTINCT odstraní duplicitní řádky; neagreguje."),
            ("SELECT region, revenue ORDER BY region", "Řazení neagreguje."),
            ("SELECT * WHERE region IS NOT NULL", "Filtr, ne souhrn."),
        ],
        "explanation": "Kontingenční tabulka je vizuální GROUP BY; Filtry a Průřezy fungují jako WHERE.",
    },
    "q_ds_016": {
        "stem": "Která tabulka by měla být faktovou tabulkou v hvězdicovém schématu maloobchodních prodejů?",
        "options": [
            ("order_items (jeden řádek na položku objednávky s množstvím a cenou)", "Fakta zaznamenávají měřitelné události na definované granularitě."),
            ("products", "Produkty fakta popisují; je to dimenze."),
            ("categories", "Popisný číselník (dimenze nebo součást dimenze produktu)."),
            ("customers", "Zákazníci popisují, kdo nakoupil - dimenze."),
        ],
        "explanation": "Fakta jsou události s mírami; dimenze poskytují atributy, podle kterých data členíte.",
    },
    "q_ds_017": {
        "stem": "Potřebujete `Margin %`, která správně reaguje na průřezy regionu a měsíce. Co vytvoříte?",
        "options": [
            ("Míru: DIVIDE([Revenue] - [Cost], [Revenue])", "Míry se vyhodnocují v aktuálním kontextu filtru, takže se poměr přepočítá pro jakýkoli výřez."),
            ("Počítaný sloupec s marží % každého řádku a ten zprůměrovat", "Průměr poměrů po řádcích váží každý řádek stejně a dá chybnou celkovou marži."),
            ("Počítaný sloupec sčítaný ve vizuálech", "Sčítání procent nedává smysl."),
            ("Krok v Power Query", "Power Query běží při aktualizaci a na průřezy reagovat nemůže."),
        ],
        "explanation": "Poměry mají být míry spočítané ze sečtených složek.",
    },
    "q_ds_018": {
        "stem": "Vizuál ukazuje [Revenue] po měsících, zatímco průřez vybírá Region = West. Co vrátí `CALCULATE([Revenue], ALL(Region))` za březen?",
        "options": [
            ("Celkové březnové tržby za všechny regiony", "ALL odstraní filtr Region, zatímco filtr měsíce z osy zůstane."),
            ("Tržby regionu West za březen", "ALL(Region) přebije výběr v průřezu."),
            ("Celkové tržby za všechny měsíce a regiony", "Odstraní se jen filtr Region; kontext měsíce zůstává."),
            ("Chybu, protože průřezy nelze přebít", "CALCULATE existuje právě proto, aby měnila kontext filtru."),
        ],
        "explanation": "CALCULATE mění kontext filtru; tento vzor se používá u měr typu „podíl na celku“.",
    },
    "q_ds_019": {
        "stem": "Dva týmy hlásí za stejný měsíc různé „měsíční tržby“. Jaká je nejúčinnější dlouhodobá náprava?",
        "options": [
            ("Písemná definice KPI (vzorec, filtry, granularita, vlastník), kterou používají oba týmy", "Sdílené, přesné definice odstraní nejasnosti ohledně filtrů stavu, slev a načasování."),
            ("Zprůměrovat obě čísla", "Průměr dvou nekonzistentních čísel vytvoří třetí, nevysvětlené číslo."),
            ("Použít to vyšší", "Výběrové reportování ničí důvěru."),
            ("Požádat oba týmy o zaokrouhlení na miliony", "Zaokrouhlení rozdíl skryje, ale nevyřeší."),
        ],
        "explanation": "Metriky potřebují správu: jedna definice, jeden vlastník, zdokumentované výhrady.",
    },
    "q_ds_020": {
        "stem": "Region A: 10 objednávek, AOV 300 EUR. Region B: 990 objednávek, AOV 100 EUR. Jaká je celková AOV?",
        "options": [
            ("EUR 102", "(10*300 + 990*100) / 1000 = 102 000 / 1000."),
            ("EUR 200", "To je prostý průměr dvou AOV, který ignoruje objemy objednávek."),
            ("EUR 300", "To je jen region A."),
            ("EUR 150", "K tomuto číslu nevede žádné platné vážení."),
        ],
        "explanation": "Nikdy neprůměrujte průměry; poměry přepočítejte ze sečtených čitatelů a jmenovatelů.",
    },
    "q_ds_021": {
        "stem": "Které z následujících jsou v prodejním reportu **dimenze**? (Vyberte všechny správné.)",
        "options": [
            ("Region", "Atribut, podle kterého se metriky člení."),
            ("Měsíc objednávky", "Časové atributy jsou dimenze."),
            ("Tržby", "Tržby jsou metrika (agregované číslo)."),
            ("Průměrná hodnota objednávky", "AOV je odvozená metrika."),
        ],
        "explanation": "Metriky se agregují; dimenze jsou atributy, podle kterých seskupujete a filtrujete.",
    },
    "q_ds_022": {
        "stem": "Tržby meziročně vzrostly o 8 %, zatímco počet objednávek o 12 %. Co z toho plyne a co byste měli zkontrolovat dál?",
        "options": [
            ("AOV klesla přibližně o 3,6 %; zkontrolujte posun mixu, slevy a změny ve velkoodběrech", "Tržby = Objednávky x AOV, takže AOV = 1,08/1,12 - 1 = -3,6 %. Před závěrem prozkoumejte faktory."),
            ("AOV vzrostla o 4 %", "Více objednávek s pomalejším růstem tržeb znamená menší průměrné objednávky."),
            ("Nic; růst tržeb je kladný, takže výkon je v pořádku", "Klesající AOV může signalizovat erozi marže kvůli slevám."),
            ("Data musí být chybná", "Tento vzorec je běžný a věrohodný; prošetřete ho, místo abyste ho odmítli."),
        ],
        "explanation": "Výsledková KPI rozkládejte na faktory, abyste vysvětlili jejich pohyby.",
    },
    "q_ds_023": {
        "stem": "Která změna nejspíš zrychlí pomalý analytický dotaz nad velkou tabulkou?",
        "options": [
            ("Vybírat jen potřebné sloupce a filtrovat co nejdříve", "Sloupcové databáze jako DuckDB čtou jen použité sloupce; časné filtry snižují práci."),
            ("Nahradit výčet sloupců za SELECT *", "SELECT * čte všechny sloupce a zvyšuje I/O."),
            ("Přidat ORDER BY do každého CTE", "Řazení mezivýsledků stojí čas a optimalizátor ho obvykle stejně ignoruje."),
            ("Obalit filtrovaný sloupec funkcí, např. YEAR(order_date) = 2024", "Funkce na filtrovaných sloupcích mohou zabránit prořezávání; dejte přednost rozsahu na původním sloupci."),
        ],
        "explanation": "Čitelné, minimalistické dotazy bývají zároveň rychlejší.",
    },
    "q_ds_024": {
        "stem": "Manažer se ptá: „Jakou jednotkovou cenu potřebujeme k zisku 50 000 EUR při stejném objemu?“ Který nástroj Excelu na to odpoví nejpříměji?",
        "options": [
            ("Hledání řešení (Goal Seek)", "Hledání řešení mění jeden vstup, dokud vzorec nedosáhne cílové hodnoty."),
            ("Podmíněné formátování", "Formátování zvýrazňuje hodnoty; vstupy nedopočítá."),
            ("Kontingenční tabulka", "Kontingenční tabulky shrnují data; rovnice neřeší."),
            ("Odebrat duplicity", "Nástroj pro čištění dat."),
        ],
        "explanation": "Tabulky dat ukazují výstupy pro mřížku vstupů; Hledání řešení najde vstup pro cílovou hodnotu.",
    },
}
