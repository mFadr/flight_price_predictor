"""Czech text for the capstone projects and their graded exercises."""

LV = ["Chybí nebo je chybné", "Kritérium splněno částečně", "Solidní a téměř úplné", "Výborné, přesné a dobře zdůvodněné"]


def _r(name: str, description: str) -> dict:
    return {"name": name, "description": description, "levels": LV}


CAPSTONES = {
    "cap1": {
        "title": "Analýza výkonnosti maloobchodu",
        "brief": """
**Klient:** vedení firmy Northwind Living. **Termín:** výroční hodnocení výkonnosti.

Vedení chce úplný obraz výkonnosti v roce 2024 oproti roku 2023: tržby, marže, ekonomika objednávek, výkon regionů, mix kategorií a vratky - a navíc specifikaci dashboardu v Power BI, který budou regionální manažeři používat každý měsíc.

Zkombinujete SQL (výpočty), Excel (auditovatelný sešit pro finance), deskriptivní statistiku a návrh dashboardu. Výsledkem je krátký report KPI s byznysovými dopady, ne jen čísla.
""",
        "requirements": [
            "Karty definic KPI pro tržby, hrubou marži %, AOV, míru vratek a meziroční růst.",
            "Regionální scorecard spočítaný v SQL (automatická kontrola).",
            "Sešit Excelu, který reprodukuje dvě KPI pomocí SUMIFS a projde kontrolou sešitu.",
            "Datový model a specifikace dashboardu v Power BI (faktové/dimenzní tabulky, relace, 5+ měr DAX, rozvržení stránky).",
            "Jednostránkové manažerské shrnutí se třemi dopady a jedním doporučeným krokem.",
        ],
        "milestones": [
            {"title": "Definujte KPI", "description": "Napište karty definic KPI (vzorec, filtry, granularita, vlastník, cíl, výhrady) pro pět KPI.",
             "rubric": [_r("Přesnost", "Vzorce a filtry jsou jednoznačné (např. dokončené objednávky, práce se slevami)."),
                        _r("Byznysová relevance", "Každé KPI má vlastníka, cíl a rozhodnutí, které podporuje."),
                        _r("Výhrady", "Známá úskalí dat jsou přiznána.")]},
            {"title": "Regionální scorecard (SQL)", "description": "Sestavte dotaz pro regionální scorecard."},
            {"title": "Sešit Excelu", "description": "Dokončete workshop Excelu (Cvičebna a programování -> Workshopy nástrojů) a nahrajte sešit ke kontrole.",
             "checklist": ["Vstupy, výpočty a kontroly jsou v oddělených, popsaných oblastech", "Výsledky SUMIFS odpovídají kontrole",
                           "Ve vzorcích nejsou pevně zadaná čísla", "Kontrola odsouhlasení porovnává součet v sešitu se součtem ve zdroji"]},
            {"title": "Specifikace Power BI", "description": "Napište specifikaci datového modelu a dashboardu.",
             "rubric": [_r("Model", "Faktová tabulka na granularitě položky objednávky; dimenze produkt, zákazník, kalendář; relace 1:N s jednosměrným filtrem."),
                        _r("Míry", "Alespoň pět správných měr DAX, včetně marže % a YTD."),
                        _r("Rozvržení", "Karty KPI, trend, rozpad a detail s rozumnými průřezy a procházením.")]},
            {"title": "Manažerské shrnutí", "description": "Jedna stránka: hlavní sdělení, tři dopady, jedno doporučení, omezení.",
             "rubric": [_r("Nejprve odpověď", "Hlavní sdělení odpoví na otázku „jak se nám dařilo?“ jednou větou s čísly."),
                        _r("Dopady", "Vysvětluje, co čísla znamenají pro byznys (např. náklady výpadku v regionu West, mix marží)."),
                        _r("Proveditelnost", "Konkrétní doporučení s vlastníkem a dalším krokem."),
                        _r("Poctivost", "Jsou uvedena omezení a výhrady k datům.")]},
        ],
        "evaluation": ["Správnost výpočtů (automatická kontrola SQL, kontrola sešitu)", "Přesnost definic KPI", "Kvalita BI modelu a měr", "Byznysový vhled a srozumitelnost manažerského shrnutí"],
        "strong_example": """
**Hlavní sdělení:** Tržby v roce 2024 vzrostly o ~5 % na přibližně 3,15 mil. EUR, zatímco hrubá marže se udržela na ~Y %; růst přinesl vyšší počet objednávek (+~7,5 %), zatímco AOV klesla o ~2 %.

**Dopady**
1. *Výpadek zásob Electronics v regionu West (srpen-září) stál přibližně 42 tis. EUR* oproti stejným měsícům roku 2023 (~50 tis. -> ~8 tis. EUR); jinak region rostl v souladu s firmou. Rizikem je spolehlivost dodávek, ne poptávka.
2. *Míra vratek u Apparel (~12,6 %) je zhruba dvojnásobkem firemního průměru* a refundace ubírají z marže odhadem N tis. EUR.
3. *Posun mixu k Electronics* zvyšuje tržby, ale mírně ředí marži v %.

**Doporučení:** Provoz zavede upozornění na pojistnou zásobu pro 20 nejprodávanějších SKU kategorie Electronics v každém regionu (vlastník: vedoucí zásobování, do Q2).

**Omezení:** tržby nezahrnují dopravu; 0,5 % položek má neznámou slevu (bráno jako 0 %); 30 duplicitních záznamů zákazníků bylo pro počty zákazníků sloučeno.

**Model Power BI:** Fakta `order_items` (granularita: položka objednávky) -> `orders` (jako degenerovaná dimenze nebo sloučeno), `products` (se sloučenou kategorií), `customers`, `Calendar`. Míry: Revenue (SUMX), Cost, Margin % (DIVIDE), Orders (DISTINCTCOUNT), AOV, Revenue YTD (TOTALYTD), Revenue PY (SAMEPERIODLASTYEAR), YoY %.
""",
    },
    "cap2": {
        "title": "Šetření retence zákazníků",
        "brief": """
**Klient:** vedení CloudNest. **Otázka:** *Proč klesla retence zákazníků a co s tím máme dělat?*

Nedávné kohorty v prvních šesti měsících odcházejí znatelně více. Produkt viní kampaň marketingu na Paid Social; marketing viní červencové zdražení tarifu Basic; finance podezírá onboarding. Musíte tato vysvětlení oddělit pomocí důkazů, rozlišit podložené závěry od hypotéz a doporučit další kroky.
""",
        "requirements": [
            "Kohortní analýza šestiměsíčního odchodu (SQL nebo Python) při stejné délce vztahu.",
            "Porovnání segmentů podle akvizičního zdroje, tarifu a raného zapojení.",
            "Vyčíslení efektu mixu kanálů (složení).",
            "Odhad efektu ceny metodou rozdílu v rozdílech (automatická kontrola).",
            "Memo se zjištěními, které odděluje podložené závěry, hypotézy k ověření a doporučení.",
        ],
        "milestones": [
            {"title": "Kohortní pohled", "description": "Dokončete cvičení kohortního odchodu (podle čtvrtletí a tarifu)."},
            {"title": "Efekt složení", "description": "Vyčíslete, jaká část nárůstu je způsobena mixem kanálů."},
            {"title": "Efekt ceny", "description": "Izolujte efekt ceny tarifu Basic metodou rozdílu v rozdílech."},
            {"title": "Memo se zjištěními", "description": "Napište memo: zjištění (s důkazy), hypotézy (s tím, jak je ověřit), doporučení.",
             "rubric": [_r("Důkazy", "Každé zjištění cituje číslo z vašich analýz."),
                        _r("Kalibrovaná tvrzení", "Jasně odděluje podložená zjištění od neověřených hypotéz; žádné kauzální přehánění."),
                        _r("Alternativy", "Rozebírá alternativní vysvětlení a proč jsou s daty více či méně v souladu."),
                        _r("Doporučení", "Konkrétní, testovatelné další kroky (např. experiment s onboardingem pro uživatele z Paid Social).")]},
        ],
        "evaluation": ["Správné definice kohort a odchodu (stejná délka vztahu)", "Vyčíslené efekty složení a ceny", "Kvalita úvah: matoucí proměnné, předpoklady, omezení", "Proveditelná, kalibrovaná doporučení"],
        "strong_example": """
**Zjištění 1 (podložené):** Šestiměsíční odchod vzrostl z ~25 % (kohorty 2023-Q1 2024) na ~32 % (kohorty Q2-Q3 2024).
**Zjištění 2 (podložené):** Podíl Paid Social na registracích vyskočil z ~15 % na ~40 % a Paid Social má odchod ~50 % oproti ~20 % jinde. Převážení na starý mix odstraní většinu nárůstu - jde hlavně o **efekt složení**.
**Zjištění 3 (podložené, s předpoklady):** Bez Paid Social vzrostl po zdražení odchod zákazníků tarifu Basic více než u ostatních tarifů (rozdíl v rozdílech o několik procentních bodů), za předpokladu paralelních trendů.
**Hypotéza (zatím neověřená):** Uživatelé z Paid Social mají nižší zapojení v prvním měsíci, což naznačuje špatný soulad nebo slabý onboarding pro toto publikum. *Test:* randomizovaná varianta onboardingu pro registrace z Paid Social.
**Nepodloženo:** obecné selhání onboardingu - odchod v zavedených kanálech je stabilní.
**Doporučení:** (1) Hodnotit Paid Social podle udržených tržeb za 6 měsíců, ne podle registrací; (2) spustit experiment s onboardingem; (3) měsíčně sledovat odchod u tarifu Basic a zvážit zachování původní ceny stávajícím zákazníkům.
**Omezení:** observační data; předpoklad paralelních trendů; u mnoha tiketů chybí data o spokojenosti.
""",
    },
    "cap3": {
        "title": "Předpovídání prodejů",
        "brief": """
**Klient:** plánovací tým Meridian Supply. **Otázka:** *S jakou poptávkou máme počítat v příštích osmi týdnech a jak moc si jsme jistí?*

Sestavíte reprodukovatelný postup předpovídání: stanovíte baseliny, porovnáte alespoň dva přístupy na časově odložených datech, vyčíslíte nejistotu a vysvětlíte, kdy by se předpovědi nemělo věřit.
""",
        "requirements": [
            "Časové odložení posledních 56 dní; k trénování se nepoužije žádná informace z odložených dat.",
            "Alespoň dva přístupy porovnané se sezónně naivním modelem.",
            "80% predikční interval s ověřeným pokrytím (automatická kontrola).",
            "Krátká poznámka k modelu: zvolená metoda, přesnost, nejistota, omezení, monitoring.",
        ],
        "milestones": [
            {"title": "Baseliny", "description": "Dokončete cvičení s baseliny předpovědí."},
            {"title": "Předpověď s intervaly", "description": "Překonejte sezónně naivní model na 56denním odložení s kalibrovaným 80% intervalem."},
            {"title": "Poznámka k modelu", "description": "Vysvětlete plánovacímu týmu volbu finálního modelu.",
             "rubric": [_r("Srovnání", "Porovnává alespoň dvě metody na stejném odložení a se stejnou metrikou."),
                        _r("Nejistota", "Vysvětluje interval, jeho pokrytí a jak ho mají plánovači používat."),
                        _r("Omezení", "Zmiňuje cenzorovanou poptávku, akce, drift a kdy přetrénovat.")]},
        ],
        "evaluation": ["Návrh vyhodnocení bez úniku", "Zlepšení oproti silnému baselinu", "Kalibrovaná nejistota", "Srozumitelné sdělení omezení"],
        "strong_example": """
**Metoda:** aditivní Holt-Winters s týdenní sezónností, trénovaný na období 2023-01-01 až 2024-11-05.
**Přesnost (56denní odložení):** MAE ~X kusů/den oproti ~Y u sezónně naivního modelu (-Z %).
**Nejistota:** empirický 80% interval z reziduí za poslední rok pokryl 79 % dní odložených dat. Personál plánujte na horní mez v pondělí (den s nejvyšší poptávkou).
**Omezení:** poptávka ve dnech výpadku zásob je odhadnutá; akce nejsou modelovány (v týdnech akcí bude předpověď podstřelená); přetrénovávejte měsíčně a upozorněte, pokud týdenní MAE přesáhne 1,3násobek MAE z odložení.
""",
    },
    "cap4": {
        "title": "Optimalizace alokace zdrojů",
        "brief": """
**Klient:** marketingová ředitelka, čtvrtletní plánování rozpočtu. **Otázka:** *Jak rozdělit marketingový rozpočet na příští čtvrtletí, aby byl očekávaný zisk maximální v rámci omezení rozpočtu, kanálů a rizika?*

Definujte účelovou funkci a omezení, implementujte model, proveďte scénářovou a citlivostní analýzu a napište doporučení, které uvádí předpoklady a podmínky, za nichž by se změnilo.
""",
        "requirements": [
            "Výslovně formulujte rozhodovací proměnné, účelovou funkci a omezení.",
            "Optimální alokace se stínovou cenou rozpočtu (automatická kontrola).",
            "Mřížka scénářů pro rozpočet a rizikovou politiku (automatická kontrola).",
            "Memo s doporučením, předpoklady, vázajícími omezeními a podmínkami změny.",
        ],
        "milestones": [
            {"title": "Základní model", "description": "Vyřešte základní alokaci s rizikovou politikou."},
            {"title": "Scénáře", "description": "Sestavte mřížku scénářů rozpočet x riziková politika."},
            {"title": "Doporučení", "description": "Napište doporučení pro marketingovou ředitelku.",
             "rubric": [_r("Rozhodnutí", "Uvádí alokaci srozumitelně a v číslech."),
                        _r("Předpoklady", "Lineární marže v rozsazích, riziková skóre, minimální závazky."),
                        _r("Citlivost", "Pomocí stínových cen / scénářů říká, kdy se doporučení mění."),
                        _r("Kompromisy", "Vysvětluje, kolik zisku stojí riziková politika.")]},
        ],
        "evaluation": ["Správná formulace", "Optimální, přípustná řešení", "Přínosná citlivostní a scénářová analýza", "Jasné doporučení s ohledem na předpoklady"],
        "strong_example": """
**Rozhodnutí:** Financujte Search (120 tis. EUR), Social (90 tis. EUR), Email (25 tis. EUR) a Affiliate (50 tis. EUR) až po jejich stropy, Display na 60 tis. EUR a Video na ~53 tis. EUR - celkem asi 398 tis. EUR.
**Očekávaný zisk:** ~143 tis. EUR.
**Vázající omezení:** riziková politika 0,35, ne rozpočet. Optimalizátor nechá ~2 tis. EUR nevyčerpané; stínová cena rozpočtu je nulová, takže žádat o víc peněz je při současné politice zbytečné. Uvolnění rizikového stropu na 0,40 přidá ~1,4 tis. EUR při 400 tis. EUR a ~6 tis. EUR při 500 tis. EUR; zpřísnění na 0,30 stojí ~16 tis. EUR.
**Poznatek ze scénářů:** při 300 tis. EUR je vázající rozpočet a riziková politika je irelevantní (zisk ~124 tis. EUR pro každý strop).
**Předpoklady:** marže jsou lineární mezi min/max výdaji (za stropy klesající výnosy), riziková skóre jsou subjektivní.
**Změní se, pokud:** se přehodnotí riziková politika, marže e-mailu klesne pod marži Search, nebo se znovu vyjedná minimální závazek u Video.
""",
    },
    "cap5": {
        "title": "Manažerské analytické portfolio",
        "brief": """
**Klient:** výkonné vedení skupiny. **Otázka:** *Jaké jsou tři nejdůležitější věci, které by vedení mělo vědět a udělat v příštím čtvrtletí?*

Proveďte byznysovou otázku od definice přes přípravu dat, analýzu a vizualizaci až k doporučení. Sestavte vizualizační portfolio odpovídající na pět byznysových otázek vhodnými grafy, zkritizujte zavádějící dashboard a dodejte manažerské shrnutí.
""",
        "requirements": [
            "Pět byznysových otázek, každá zodpovězená vhodným a poctivým grafem.",
            "Manažerský přehledový obrázek (automatická kontrola).",
            "Kritika dashboardu (workshop Kritika dashboardu).",
            "Manažerské shrnutí: kontext, komplikace, řešení, s uvedenou nejistotou.",
        ],
        "milestones": [
            {"title": "Definice otázek a příprava dat", "description": "Definujte pět přesných, měřitelných byznysových otázek a data/metriky pro každou.",
             "checklist": ["Každá otázka je konkrétní a měřitelná", "U každé je uvedena metrika, dimenze a filtry",
                           "Problémy s kvalitou dat jsou zkontrolované a zdokumentované", "Typ grafu je pro každou otázku zvolen a zdůvodněn"]},
            {"title": "Manažerský přehledový obrázek", "description": "Sestavte manažerský obrázek 2x2."},
            {"title": "Kritika dashboardu", "description": "Dokončete workshop Kritika dashboardu (Cvičebna a programování -> Workshopy nástrojů).",
             "checklist": ["Identifikoval(a) jsem všechny zavádějící prvky", "Vysvětlil(a) jsem vliv každého na interpretaci", "Navrhl(a) jsem pro každý konkrétní opravu"]},
            {"title": "Manažerské shrnutí", "description": "Napište závěrečné shrnutí a doporučení.",
             "rubric": [_r("Dějová linka", "Kontext -> komplikace -> řešení, nejprve odpověď."),
                        _r("Důkazy", "Každé tvrzení je podloženo grafem nebo číslem."),
                        _r("Nejistota", "Poctivě uvádí míru jistoty a omezení."),
                        _r("Doporučení", "Tři prioritizované kroky s vlastníky.")]},
        ],
        "evaluation": ["Kvalita otázek", "Volba grafů a poctivost", "Vyprávění a komunikace s vedením", "Poctivé zacházení s nejistotou"],
        "strong_example": """
**Kontext:** Oba byznysy v roce 2024 rostly (tržby maloobchodu ~+5 %, registrace předplatného výrazně nahoru).
**Komplikace:** Kvalita růstu klesá - noví zákazníci CloudNest odcházejí více a Northwind ztratil ~42 tis. EUR kvůli regionálnímu výpadku zásob.
**Řešení / kroky:**
1. Cílit Paid Social podle udržených tržeb; spustit experiment s onboardingem (vlastník: CMO).
2. Zavést upozornění na pojistnou zásobu u nejprodávanějších SKU Electronics (vlastník: vedoucí zásobování).
3. Přepracovanou pokladnu zatím nenasazovat; prodloužit test - pozorované zlepšení je v rámci šumu (vlastník: Produkt).
**Míra jistoty:** zjištění 1-2 jsou daty dobře podložena; výsledek A/B testu je z podstaty nepřesvědčivý.
""",
    },
}

EXERCISES = {
    "ex_cap1_region_scorecard": {
        "title": "Závěrečný projekt 1 - Regionální scorecard",
        "topic": "Scorecard KPI",
        "business_question": "Vytvořte regionální scorecard pro výroční hodnocení výkonnosti.",
        "requirements": [
            "Dokončené objednávky. Jeden řádek na region.",
            "Sloupce: `region`, `revenue_2023`, `revenue_2024` (2 des. místa), `yoy_growth_pct` (1 des. místo), `margin_pct_2024` (1 des. místo), `aov_2024` (2 des. místa).",
            "margin_pct_2024 = 100 * (revenue - cost) / revenue za rok 2024; cost = quantity * products.unit_cost; aov_2024 = tržby 2024 / různé objednávky 2024.",
            "Seřaďte podle revenue_2024 sestupně.",
        ],
        "expected_output": "5 řádků x 6 sloupců.",
        "explanation": "Podmíněná agregace spočítá metriky více období v jednom průchodu; poměry se počítají z nezaokrouhlených součtů.",
        "hints": [
            "SUM(revenue) FILTER (WHERE yr = 2024) dá tržby 2024 na region.",
            "COUNT(DISTINCT order_id) FILTER (...) počítá objednávky na úrovni položek.",
            "Poměry spočítejte ve finálním SELECT z agregovaných složek.",
        ],
    },
    "ex_cap2_price_effect": {
        "title": "Závěrečný projekt 2 - Izolujte efekt ceny (rozdíl v rozdílech)",
        "topic": "Rozdíl v rozdílech",
        "business_question": "Cena tarifu Basic vzrostla v červenci 2024 souběžně s posílením Paid Social. Odhadněte efekt ceny na šestiměsíční odchod a odstraňte přitom efekt mixu kanálů.",
        "requirements": [
            "Vyřaďte zákazníky z Paid Social (odstraní posun mixu).",
            "`after` = signup_date >= 2024-04-01 (jejich prvních 6 měsíců zahrnuje červencovou změnu ceny); before = dřívější registrace.",
            "`rates`: DataFrame míry odchodu s indexem plan_group ('Basic', 'Other') a sloupci 'before', 'after'.",
            "`did` = (Basic after - Basic before) - (Other after - Other before).",
        ],
        "expected_output": "Tabulka 2x2 a jedna hodnota float.",
        "explanation": "Rozdíl v rozdílech porovnává změnu u zasažené skupiny (Basic) se změnou u nezasažené srovnávací skupiny (ostatní tarify) a odstraňuje společné časové trendy. Předpokládá, že by se obě skupiny jinak vyvíjely paralelně - tento předpoklad uveďte.",
        "hints": [
            "pivot_table(index='plan_group', columns='period', values='churned_6m', aggfunc='mean').",
            "did = změna u Basic minus změna u Other.",
        ],
        "checks": [
            {"name": "tabulka měr", "msgs": ["f'rates.loc[{g!r}, {p!r}] je nesprávně. Vyřadili jste Paid Social?'"]},
            {"msgs": ["'did = (Basic after - Basic before) - (Other after - Other before).'"]},
        ],
        "visible_tests": ["Tabulka odchodu 2x2", "Odhad rozdílu v rozdílech"],
        "rubric": [("Odstraněný efekt mixu", 30), ("Správné skupiny a období", 30), ("Správný odhad", 40)],
    },
    "ex_cap3_forecast": {
        "title": "Závěrečný projekt 3 - Osmitýdenní předpověď poptávky s intervaly",
        "topic": "Předpovídání s nejistotou",
        "business_question": "Předpovězte celkovou denní poptávku za posledních 56 dní roku 2024 jen z dřívějších dat, s 80% predikčním intervalem.",
        "requirements": [
            "`y`: celkové units_demanded za den; train = vše kromě posledních 56 dní.",
            "Jakákoli metoda (sezónně naivní, Holt-Winters, regrese s kalendářními příznaky...), trénovaná jen na train.",
            "`forecast`, `lower`, `upper`: pole délky 56 pro posledních 56 dní (80% interval).",
            "Předpověď musí překonat MAE sezónně naivního modelu; interval by měl pokrýt zhruba 80 % skutečných dní (přijímá se 60-95 %).",
        ],
        "expected_output": "Tři pole délky 56.",
        "explanation": "Holt-Winters s týdenní sezónností obvykle překoná sezónně naivní model, protože vyhladí šum. Kvantily reziduí z posledního roku dají jednoduchý empirický interval; ověřte jeho pokrytí na odložených datech.",
        "hints": [
            "Sezónně naivní = opakovat posledních 7 trénovacích dní.",
            "statsmodels ExponentialSmoothing(train, trend='add', seasonal='add', seasonal_periods=7).",
            "Interval z kvantilů reziduí: forecast + quantile(resid, 0.10/0.90).",
        ],
        "checks": [
            {"name": "tvary", "msgs": ["'forecast, lower a upper musí mít každé 56 hodnot.'", "'Musí platit lower <= forecast <= upper.'"]},
            {"name": "překonává sezónně naivní", "msgs": ["f'Vaše MAE {mae:.1f} nepřekonává sezónně naivní model ({mae_sn:.1f}).'"]},
            {"name": "pokrytí intervalu", "msgs": ["f'Interval pokrývá {cov:.0%} skutečných dní; cílem je asi 80 %.'"]},
        ],
        "visible_tests": ["Tři pole s 56 hodnotami a lower <= forecast <= upper", "MAE lepší než sezónně naivní", "Pokrytí intervalu mezi 60 % a 95 %"],
        "rubric": [("Trénování bez úniku", 25), ("Překonává silný baseline", 40), ("Kalibrovaná nejistota", 35)],
    },
    "ex_cap4_scenarios": {
        "title": "Závěrečný projekt 4 - Mřížka scénářů rozpočtu",
        "topic": "Scénářová analýza",
        "business_question": "Jak optimální zisk reaguje na celkový rozpočet a na rizikovou politiku?",
        "requirements": [
            "Stejný model jako v lekci ps5 (maximalizovat marže * výdaje; min/max výdaje; rozpočet; průměrné riziko <= strop).",
            "Vyřešte pro každou kombinaci rozpočtu z [300000, 400000, 500000] a rizikového stropu z [0.30, 0.35, 0.40].",
            "`scenarios`: DataFrame se sloupci budget, risk_cap, profit (NaN, pokud je úloha nepřípustná) - 9 řádků.",
        ],
        "expected_output": "9 řádků x 3 sloupce.",
        "explanation": "Mřížka scénářů ukazuje, kde se rozpočet navíc vyplatí a kolik zisku stojí riziková politika: při 300 tis. EUR je vázající rozpočet; nad 400 tis. EUR přidá zisk jen volnější rizikový strop. Nepřípustné buňky, pokud nastanou (přísné stropy s velkými minimálními závazky), jsou také informací důležitou pro rozhodnutí.",
        "hints": [
            "Napište funkci solve(budget, risk_cap), která vrátí zisk nebo NaN.",
            "res.status == 0 znamená, že bylo nalezeno optimální řešení.",
            "Použijte list comprehension přes oba seznamy.",
        ],
        "checks": [{"name": "mřížka scénářů"}],
        "visible_tests": ["9 scénářů s optimálním ziskem (NaN, pokud nepřípustné)"],
        "rubric": [("Správný model", 40), ("Úplná mřížka", 30), ("Ošetřená nepřípustnost", 30)],
    },
    "ex_cap5_overview_figure": {
        "title": "Závěrečný projekt 5 - Manažerský přehledový obrázek",
        "topic": "Malé násobky pro vedení",
        "business_question": "Vytvořte jednostránkový obrázek pro vedení, který odpoví na čtyři otázky: trend tržeb, mix kategorií, odchod podle zdroje, výsledek A/B testu.",
        "requirements": [
            "Jeden obrázek s mřížkou os 2x2 (plt.subplots(2, 2)).",
            "Každý panel má název, který uvádí zjištění (alespoň 4 slova), a popsané osy.",
            "Sloupcové panely začínají na nule. Alespoň jeden panel ukazuje nejistotu (chybové úsečky).",
            "Název celého obrázku (fig.suptitle).",
        ],
        "expected_output": "Obrázek 2x2.",
        "explanation": "Malé násobky s akčními názvy umožní vedení přečíst čtyři zjištění za necelou minutu. Poctivé osy a viditelná nejistota udrží stránku důvěryhodnou.",
        "hints": [
            "fig.suptitle('...') přidá celkový název.",
            "U sloupcových panelů nastavte spodní mez ylim/xlim na 0.",
            "ax.bar(..., yerr=1.96*se*100, capsize=5) přidá chybové úsečky.",
        ],
        "checks": [
            {"name": "rozvržení 2x2", "msgs": ["'Vytvořte obrázek.'", "f'Očekávány 4 panely, nalezeno {len(f.axes)}.'"]},
            {"name": "akční názvy a popisky", "msgs": ["f'Panel {i + 1} potřebuje název ve stylu zjištění (4+ slova).'", "f'Panel {i + 1} potřebuje popisky obou os.'"]},
            {"name": "sloupce od nuly", "msgs": ["f'Sloupce v panelu {i + 1} musí začínat na nule (osa začíná na {lo:.2f}).'"]},
            {"name": "nejistota zobrazena", "msgs": ["'Ukažte nejistotu alespoň v jednom panelu (chybové úsečky).'"]},
            {"name": "název obrázku", "msgs": ["'Přidejte fig.suptitle(...).'"]},
        ],
        "visible_tests": ["4 panely", "Názvy ve stylu zjištění a popisky os", "Sloupce od nuly", "Chybové úsečky", "Název obrázku"],
        "rubric": [("Odpovídá na čtyři otázky", 30), ("Poctivý design", 30), ("Vyprávějící názvy", 25), ("Nejistota", 15)],
    },
}
