"""Czech glossary definitions and cheat-sheet text. Glossary terms stay in English (the industry vocabulary);
the Czech equivalent is given in italics where it differs."""

GLOSSARY = {
    "A/B test": "Randomizovaný experiment, který porovnává kontrolní a testovanou verzi, aby odhadl kauzální efekt změny.",
    "Aggregate function": "*Agregační funkce.* Funkce, která shrne mnoho řádků do jedné hodnoty, např. SUM, COUNT, AVG, MIN, MAX.",
    "Anomaly": "*Anomálie.* Pozorování, které se výrazně odchyluje od očekávané základny (se zohledněním trendu a sezónnosti).",
    "AOV (average order value)": "*Průměrná hodnota objednávky.* Tržby dělené počtem objednávek, počítané ze sečtených složek.",
    "Baseline model": "*Základní model.* Triviální model (nejčastější třída, průměr, poslední hodnota, sezónně naivní), který musí každý skutečný model překonat.",
    "Binding constraint": "*Vázající omezení.* Omezení, které je v optimu plně využité; jeho uvolnění by zlepšilo účelovou funkci.",
    "Bootstrap": "Opakované převzorkování dat s vracením za účelem odhadu nejistoty statistiky.",
    "Calibration": "*Kalibrace.* Shoda mezi předpovězenými pravděpodobnostmi a pozorovanými četnostmi.",
    "Cardinality (relationship)": "*Kardinalita (relace).* Kolik řádků na každé straně relace si odpovídá: 1:1, 1:N, M:N.",
    "CASE expression": "*Výraz CASE.* Logika když/pak/jinak v SQL pro vytváření kategorií nebo podmíněných agregací.",
    "Censoring (right-censoring)": "*Cenzorování (zprava).* Situace, kdy výsledek u některých jednotek ještě nebyl pozorován (např. noví zákazníci, kteří mohou ještě odejít).",
    "Churn rate": "*Míra odchodu.* Podíl zákazníků, kteří zruší službu během období nebo v pevné době od registrace.",
    "Cohort": "*Kohorta.* Skupina zákazníků se společnou počáteční událostí, například měsícem registrace.",
    "Confidence interval": "*Interval spolehlivosti.* Rozsah věrohodných hodnot neznámého parametru spočítaný s uvedenou hladinou spolehlivosti (např. 95 %).",
    "Confounder": "*Matoucí proměnná.* Proměnná, která ovlivňuje domnělou příčinu i výsledek, a vytváří tak zdánlivou souvislost.",
    "Confusion matrix": "*Matice záměn.* Tabulka skutečně/falešně pozitivních a negativních případů klasifikátoru při daném prahu.",
    "Contribution analysis": "*Analýza příspěvků.* Měření, jak velkou částí přispívá změna každého segmentu k celkové změně.",
    "Cross-validation": "*Křížová validace.* Opakované trénování a validace modelu na různých částech (foldech) dat pro odhad výkonu.",
    "CTE (common table expression)": "Pojmenovaný poddotaz definovaný pomocí WITH ... AS (...), díky kterému je SQL čitelné krok za krokem.",
    "DAX": "Data Analysis Expressions, jazyk vzorců pro míry a počítané sloupce v Power BI.",
    "Data drift": "*Drift dat.* Změna rozdělení vstupů modelu po nasazení.",
    "Concept drift": "*Drift konceptu.* Změna vztahu mezi vstupy a výsledkem v čase.",
    "Data leakage": "*Únik informací.* Informace v trénovacích datech, která by v okamžiku predikce nebyla k dispozici a nafukuje skóre vyhodnocení.",
    "Decision variable": "*Rozhodovací proměnná.* Veličina, kterou rozhodovatel v optimalizačním modelu ovládá.",
    "Dimension": "*Dimenze.* Atribut používaný k seskupení nebo filtrování metrik (region, měsíc, kategorie produktu).",
    "Dimension table": "*Dimenzní tabulka.* Tabulka popisující entity (produkty, zákazníky, data), na které se fakta odkazují.",
    "Difference-in-differences": "*Rozdíl v rozdílech.* Porovnání změny v čase u ovlivněné skupiny se změnou u srovnávací skupiny za účelem odhadu efektu.",
    "Elasticity": "*Elasticita.* Procentní změna jedné proměnné spojená se změnou jiné o 1 % (např. cenová elasticita poptávky).",
    "EOQ": "Ekonomické objednací množství: velikost objednávky, která minimalizuje náklady na objednávání a držení zásob.",
    "Fact table": "*Faktová tabulka.* Tabulka měřitelných událostí (položky prodejů) na definované granularitě, propojená s dimenzními tabulkami.",
    "Feature engineering": "*Tvorba příznaků.* Vytváření informativních vstupů modelu ze surových dat.",
    "Filter context": "*Kontext filtru.* V Power BI množina filtrů platných při vyhodnocení míry.",
    "Funnel": "*Trychtýř.* Posloupnost kroků, kterými uživatelé procházejí, s měřením konverze mezi kroky.",
    "Grain": "*Granularita.* Co představuje jeden řádek tabulky (jedna objednávka, jedna položka objednávky, jeden zákazník za měsíc).",
    "HAVING": "Klauzule SQL, která filtruje skupiny po agregaci.",
    "Hypothesis test": "*Test hypotézy.* Postup pro posouzení, zda jsou data v souladu s nulovou hypotézou.",
    "IQR (interquartile range)": "*Mezikvartilové rozpětí.* Q3 minus Q1; používá se v robustních pravidlech pro odlehlé hodnoty.",
    "Join": "*Spojení.* Kombinování řádků ze dvou tabulek pomocí klíče: INNER, LEFT, RIGHT, FULL.",
    "KPI": "Klíčový ukazatel výkonnosti: přesně definovaná metrika vázaná na byznysový cíl a vlastníka.",
    "LOD expression": "*Výraz LOD.* Výpočet úrovně detailu v Tableau, který počítá hodnoty na zadané granularitě ({ FIXED ... }).",
    "Linear programming": "*Lineární programování.* Optimalizace s lineární účelovou funkcí a lineárními omezeními.",
    "MAE": "Střední absolutní chyba: průměrná velikost chyb predikce.",
    "Measure (BI)": "*Míra (BI).* Výpočet vyhodnocovaný v okamžiku dotazu v aktuálním kontextu filtru.",
    "Metric": "*Metrika.* Veličina, která se agreguje a sleduje (tržby, objednávky, míra odchodu).",
    "Monte Carlo simulation": "*Simulace Monte Carlo.* Odhad rozdělení výsledků opakovaným losováním nejistých vstupů.",
    "NULL": "Značka SQL pro chybějící nebo neznámou hodnotu; nerovná se nule ani prázdnému textu.",
    "Overfitting": "*Přeučení.* Model, který se naučí šum v trénovacích datech a špatně generalizuje.",
    "p-value": "*p-hodnota.* Pravděpodobnost pozorování dat alespoň tak extrémních jako vzorek, pokud by platila nulová hypotéza.",
    "Pipeline (ML)": "Řetězec kroků předzpracování a modelu fitovaných společně, aby se zabránilo úniku informací.",
    "PivotTable": "*Kontingenční tabulka.* Interaktivní nástroj Excelu pro seskupení a agregaci (řádky, sloupce, hodnoty, filtry).",
    "Precision": "Z případů predikovaných jako pozitivní podíl těch, které jsou skutečně pozitivní.",
    "Prediction interval": "*Predikční interval.* Rozsah, který s danou pravděpodobností obsahuje budoucí pozorování.",
    "Recall": "Ze skutečně pozitivních případů podíl těch, které model odhalí.",
    "Retention": "*Retence.* Podíl kohorty, který je po určité době stále aktivní.",
    "RMSE": "Odmocnina střední kvadratické chyby: penalizuje velké chyby více než MAE.",
    "ROC-AUC": "Pravděpodobnost, že klasifikátor seřadí náhodný pozitivní případ nad náhodný negativní.",
    "Safety stock": "*Pojistná zásoba.* Zásoba navíc, která chrání před kolísáním poptávky a dodací lhůty.",
    "Seasonal naive forecast": "*Sezónně naivní předpověď.* Předpověď, která opakuje hodnotu ze stejné sezóny předchozího cyklu (např. stejný den v týdnu minulý týden).",
    "Segmentation": "*Segmentace.* Rozdělení dat do smysluplných skupin za účelem porovnání chování.",
    "Sensitivity analysis": "*Citlivostní analýza.* Zkoumání, jak se výstupy mění při změně vstupů nebo předpokladů.",
    "Shadow price": "*Stínová cena.* Změna optimální hodnoty účelové funkce na jednotku uvolnění omezení.",
    "Simpson's paradox": "*Simpsonův paradox.* Trend, který se objevuje v souhrnu, ale v podskupinách mizí nebo se obrací kvůli měnícím se velikostem skupin.",
    "Star schema": "*Hvězdicové schéma.* Datový model s centrální faktovou tabulkou obklopenou dimenzními tabulkami.",
    "Statistical significance": "*Statistická významnost.* Důkaz dost silný k zamítnutí nulové hypotézy na zvolené hladině; není totéž co praktická důležitost.",
    "SUMIFS": "Funkce Excelu, která sčítá hodnoty splňující několik kritérií.",
    "Survivorship bias": "*Zkreslení přeživších.* Vyvozování závěrů jen z jednotek, které „přežily“ výběrový proces.",
    "Threshold (classification)": "*Práh (klasifikace).* Pravděpodobnost, nad kterou je případ označen jako pozitivní.",
    "Window function": "*Okenní funkce.* Funkce SQL počítaná nad množinou řádků souvisejících s aktuálním řádkem, aniž by je slučovala.",
    "XLOOKUP": "Vyhledávací funkce Excelu s přesnou shodou jako výchozí a flexibilními oblastmi výsledku.",
}


def cheatsheets() -> dict[str, str]:
    """Czech cheat sheets, derived from the current English ones (called while the English text is in place)."""
    from analytics_lab.curriculum.reference import CHEATSHEETS

    out = {}
    excel = CHEATSHEETS["Excel"]
    for a, b in [
        ("| Need | Formula |", "| Potřeba | Vzorec |"),
        ("| Absolute reference |", "| Absolutní odkaz |"),
        ("(F4 toggles)", "(F4 přepíná)"),
        ("| Conditional sum |", "| Podmíněný součet |"),
        ("| Conditional count / average |", "| Podmíněný počet / průměr |"),
        ("| Lookup |", "| Vyhledání |"),
        ('"not found")` or `', '"not found")` nebo `'),
        ("| Logic |", "| Logika |"),
        ("| Text / dates |", "| Text / data |"),
        ("| Tables |", "| Tabulky |"),
        ("structured references", "strukturované odkazy"),
        ("| What-if |", "| Citlivostní analýza |"),
        ("Data -> What-If Analysis -> Data Table / Goal Seek / Scenario Manager", "Data -> Citlivostní analýza -> Tabulka dat / Hledání řešení / Správce scénářů"),
        ("| Audit |", "| Audit |"),
        ("Formulas -> Trace Precedents / Evaluate Formula; separate Inputs / Calc / Output / Checks sheets",
         "Vzorce -> Předchůdci / Vyhodnotit vzorec; oddělené listy Vstupy / Výpočty / Výstupy / Kontroly"),
    ]:
        excel = excel.replace(a, b)
    out["Excel"] = excel
    out["Power BI / DAX"] = CHEATSHEETS["Power BI / DAX"].replace(
        "Model: star schema, one-to-many single-direction relationships, marked Calendar table, measures over calculated columns, hide foreign keys.",
        "Model: hvězdicové schéma, relace 1:N s jednosměrným filtrem, označená tabulka Calendar, míry místo počítaných sloupců, skryté cizí klíče.")
    out["Tableau"] = """
* Dimenze (modré = diskrétní) vytvářejí záhlaví; míry (zelené = spojité) vytvářejí osy.
* `ZN([x])` NULL -> 0; `IF ... THEN ... ELSEIF ... END`; `DATETRUNC('month', [Order Date])`.
* LOD: `{ FIXED [Customer Id] : MIN([Order Date]) }`, `{ INCLUDE ... }`, `{ EXCLUDE ... }`.
* Tabulkové výpočty: `RUNNING_SUM(SUM([Revenue]))`, `WINDOW_AVG(...)`, `RANK(...)` - počítají se nad pohledem.
* Pořadí filtrů: extrakt -> zdroj dat -> kontext -> dimenze -> míra -> tabulkový výpočet.
* Akce dashboardu: filtr, zvýraznění, URL, akce parametrů.
"""
    out["Looker Studio"] = """
* Nejlépe funguje jedna plochá, uspořádaná tabulka na zdroj dat; nastavte typy polí (Datum, Číslo, Měna) a výchozí agregaci.
* Počítaná pole: `SUM(revenue) / COUNT_DISTINCT(order_id)`, `CASE WHEN ... THEN ... ELSE ... END`.
* Přehledové karty se srovnávacím obdobím; časové řady s granularitou data; ovládací prvky (období, rozbalovací seznam).
* Propojení (blending) spojuje zdroje dat přes sdílené dimenze - kontrolujte granularitu.
* Sdílejte pro čtení; definice zdokumentujte v textovém poli.
"""
    return out

