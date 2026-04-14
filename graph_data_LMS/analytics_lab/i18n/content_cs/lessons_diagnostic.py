"""Czech text for the Diagnostic Analytics lessons."""

LESSONS = {
    "dg1": {
        "title": "Kontrola kvality dat a explorativní analýza",
        "objectives": [
            "Před analýzou systematicky projít kontrolní seznam kvality dat.",
            "Vyčíslit chybějící hodnoty a rozhodnout, jak s nimi naložit.",
            "Odhalit duplicitní entity, nejen duplicitní řádky.",
            "Identifikovat odlehlé hodnoty robustními pravidly (IQR, mediánová absolutní odchylka) a posoudit, zda jde o chyby.",
        ],
        "concept": """
Diagnostika začíná důvěrou v data. Rychlý, opakovatelný **kontrolní seznam kvality dat**:

1. **Tvar a granularita** - kolik je řádků; co představuje jeden řádek; je klíč unikátní?
2. **Typy** - jsou data načtena jako data a čísla jako čísla?
3. **Chybějící hodnoty** - kolik jich je v každém sloupci a *proč* (nesbíralo se, netýká se, nepovedené spojení)?
4. **Duplicity** - shodné řádky i duplicitní *entity* s různými ID (stejný e-mail, stejné jméno a adresa).
5. **Platnost** - nemožné hodnoty (záporná množství, datum odeslání před datem objednávky, věk nad 120 let).
6. **Konzistence** - kategorie zapsané různě (`'west'`, `'West '`), součty, které nesedí.
7. **Rozdělení a odlehlé hodnoty** - porovnejte průměr a medián; prohlédněte si extrémy.

**Mechanismy chybějících dat.** *MCAR* (chybí zcela náhodně) je kromě ztráty přesnosti neškodné; *MAR* (závisí na pozorovaných proměnných) a *MNAR* (závisí na samotné chybějící hodnotě, např. nespokojení zákazníci nevyplní dotazník) mohou výsledky zkreslit. Vyřazení řádků je bezpečné jen při MCAR.

**Pravidla pro odlehlé hodnoty.** Pravidlo IQR označí hodnoty pod Q1 - 1,5*IQR nebo nad Q3 + 1,5*IQR. Robustní pravidla mají přednost před průměrem +/- 3 SD, protože průměr i SD jsou odlehlými hodnotami samy zkreslené. Odlehlá hodnota je *otázka*, ne chyba: velké B2B objednávky jsou skutečné; množství 99 999 je nejspíš překlep.

**EDA** pak shrnuje rozdělení (histogramy, krabicové grafy), vztahy (bodové grafy, korelace) a segmenty (souhrny podle skupin). Zapište si, co vás překvapilo - to jsou hypotézy na později.
""",
        "business_context": """
Než začnete zkoumat propad regionálních tržeb firmy Northwind, vedoucí analytiky vás požádá o certifikaci tabulek `customers` a `order_items`. Marketing tvrdí „3 030 zákazníků“, ale vy tušíte duplicitní záznamy a několik extrémních objednávek.
""",
        "worked_example": {"explanation": """
* `customer_id` je unikátní, ale některé hodnoty `email_hash` se opakují: **klíč** je čistý, ale **entita** je zdvojená. Počítání zákazníků podle ID nadhodnocuje zákaznickou základnu.
* `birth_year` má chybějící hodnoty. Analýza podle věku by pokryla jen zákazníky, kteří ho chtěli sdělit - pravděpodobně ne náhodnou podmnožinu.
* Rozdělení množství je velmi zešikmené. Protože většina položek má 1-2 kusy, hranice IQR je nízko; před rozhodnutím prohlédněte extrémy (20-60 kusů) - vypadají jako legitimní velkoodběry, takže je ponechte, ale vedle průměrů uvádějte i mediány.
"""},
        "summary": [
            "Nejprve zkontrolujte granularitu, typy, chybějící hodnoty, duplicity, platnost, konzistenci a rozdělení.",
            "Unikátní klíče nezaručují unikátní entity.",
            "Chybějící data mohou nést informaci (MNAR); vyřazení řádků může výsledky zkreslit.",
            "Odlehlé hodnoty vyžadují úsudek: prošetřete je, pak ponechte, ořízněte nebo vyřaďte - a zdokumentujte to.",
        ],
        "common_mistakes": [
            "Vyřazení všech řádků s jakýmkoli NULL.",
            "Automatické mazání odlehlých hodnot.",
            "Brát počet záznamů jako počet entit.",
        ],
        "revision": "Projděte kontrolní seznam znovu na tabulce `subscription.support_tickets` a ke každé kontrole napište jednu větu.",
    },
    "dg2": {
        "title": "Segmentace a analýza příčin (root cause)",
        "objectives": [
            "Formulovat hledání příčiny jako strom testovatelných hypotéz.",
            "Rozpadem KPI podle dimenzí lokalizovat změnu.",
            "Oddělit efekt mixu od efektu míry.",
            "Rozlišit podložená zjištění od hypotéz, které potřebují další důkazy.",
        ],
        "concept": """
Analýza příčin (RCA) je strukturované vylučování.

**1. Ověřte, že změna je skutečná.** Nejde o problém s daty (zpoždění datového toku, změna definice, dvojí načtení)? Porovnejte s nezávislým zdrojem.

**2. Rozložte KPI.** Tržby = Objednávky x AOV; Objednávky = Návštěvníci x Konverze. Který faktor se pohnul?

**3. Lokalizujte rozpadem.** Rozdělte změnu podle regionu, kategorie, kanálu, zákaznického segmentu a času. Hledejte segment, který vysvětluje největší část změny (*příspěvek*), ne ten s největší procentní změnou (malé segmenty divoce kolísají).

```
příspěvek segmentu = změna v segmentu / celková změna
```

**4. Mix vs. míra.** Celková míra se může změnit proto, že se změnily míry v segmentech (*efekt míry*), nebo proto, že se změnily podíly segmentů (*efekt mixu*). Příklad: celková marže klesne, protože rostly nízkomaržové kategorie, přestože marže každé kategorie zůstala stejná.

**5. Formulujte a testujte hypotézy.** U každé možné příčiny uveďte, jaký důkaz by ji potvrdil nebo vyvrátil (např. *„pokud jde o výpadek zásob, prodané kusy té kategorie v daném regionu by měly klesnout, zatímco ostatní kategorie zůstanou normální, a propad by měl skončit, jakmile se zásoby vrátí“*).

**6. Komunikujte kalibrovaným jazykem.** „Data ukazují...“, „to je v souladu s...“, „zatím jsme nevyloučili...“ Oddělujte **zjištění** (podložená důkazy) od **hypotéz** (věrohodné, neověřené).
""",
        "business_context": """
Tržby firmy Northwind v regionu West v srpnu a září 2024 prudce klesly a v říjnu se zotavily. Regionální viceprezident viní akci konkurence. Dřív, než někdo zareaguje snížením cen, musíte propad lokalizovat.
""",
        "worked_example": {"explanation": """
* Kategorie Electronics vysvětluje (více než) celý pokles, zatímco ostatní kategorie jsou zhruba stabilní nebo rostou - propad je **lokalizovaný**, ne celoregionální.
* Akce konkurence by obvykle zasáhla více kategorií; téměř úplný kolaps jedné kategorie v jednom regionu přesně na dva měsíce je spíš v souladu s problémem na **straně nabídky** (výpadek zásob, chyba v nabídce).
* **Zjištění:** pokles vysvětluje West Electronics. **Hypotéza (ověřit s provozem):** výpadek zásob. Podíly nad 100 % vznikají, když ostatní segmenty rostly.
"""},
        "summary": [
            "Než změnu vysvětlíte, ověřte, že je skutečná.",
            "Rozložte KPI na faktory a lokalizujte podle příspěvku, ne podle procentní změny.",
            "Oddělte efekt mixu od efektu míry.",
            "Zjištění a hypotézy reportujte zvlášť, s důkazy potřebnými k ověření každé hypotézy.",
        ],
        "common_mistakes": [
            "Honba za segmentem s největší procentní změnou, i když je zanedbatelně malý.",
            "Přijetí prvního věrohodného příběhu (konfirmační zkreslení).",
            "Prezentování hypotéz jako závěrů.",
        ],
        "revision": "Napište strom hypotéz pro propad v regionu West s alespoň třemi větvemi a důkazy pro každou.",
    },
    "dg3": {
        "title": "Trychtýře, kohorty a retence",
        "objectives": [
            "Sestavit konverzní trychtýř a najít největší odpad.",
            "Definovat kohorty a porovnávat je při stejné délce vztahu.",
            "Spočítat křivky retence a odchodu z dat o předplatném.",
            "Rozpoznat cenzorování zprava u nedávných kohort.",
        ],
        "concept": """
**Trychtýře** měří, kolik uživatelů projde uspořádanými kroky (návštěva -> registrace -> aktivace -> nákup). Uvádějte konverzi kroku (krok n / krok n-1) i kumulativní konverzi (krok n / krok 1). Zajistěte, aby byl každý uživatel v každém kroku započten jednou a kroky šly ve správném pořadí.

**Kohorty** seskupují zákazníky podle společné počáteční události, obvykle měsíce nebo čtvrtletí registrace. Porovnání kohort odpovídá na otázku: *chovají se noví zákazníci jinak než starší?*

**Retenční tabulka.** Řádky = kohorta, sloupce = měsíce od registrace (délka vztahu), buňky = % kohorty, které je stále aktivní. Čtením **dolů po sloupci** porovnáte kohorty při stejné délce vztahu; čtením **po řádku** uvidíte, jak jedna kohorta ubývá.

**Míra odchodu (churn)** = ztracení zákazníci za období / zákazníci na začátku období. *Šestiměsíční míra odchodu* = podíl kohorty, který zrušil předplatné do 6 měsíců od registrace.

**Cenzorování zprava.** Zákazník registrovaný minulý měsíc ještě nemohl odejít „do 6 měsíců“. Porovnání dosavadního odchodu nedávné kohorty s plným šestiměsíčním odchodem staré kohorty dělá nové kohorty lepšími, než jsou. Porovnávejte jen kohorty sledované po celé okno.

**Zkreslení přeživších.** Analýza jen aktuálně aktivních zákazníků skryje ty, kteří odešli - například „naši zákazníci milují funkci X“ na základě přeživších.
""",
        "business_context": """
Vedení CloudNest věří, že „retence klesla“. Musíte to ověřit kohortním pohledem na šestiměsíční odchod a určit, kdy zhoršení začalo.
""",
        "worked_example": {"explanation": """
* Odchod se u kohort 2023 Q1 - 2024 Q1 pohybuje kolem 23-26 % a od 2024 Q2 skočí nad 30 %.
* Protože je každá kohorta sledována celých 6 měsíců, srovnání je férové (žádné cenzorování zprava).
* **Další otázka:** co se změnilo u zákazníků získaných od Q2 2024? (Nápověda: podívejte se na `acquisition_source` a změnu ceny tarifu Basic.)
"""},
        "extra_examples": [{"explanation": "Každý řádek je kohorta; sloupce jsou měsíce od registrace. Prázdné buňky u nedávných kohort jsou cenzorované zprava - tuto délku vztahu ještě nedosáhly."}],
        "summary": [
            "Trychtýře potřebují uspořádané kroky bez duplicit; uvádějte konverzi kroku i kumulativní konverzi.",
            "Kohorty porovnávejte při stejné délce vztahu (čtěte retenční sloupce dolů).",
            "Kohorty, které nebyly sledovány po celé okno, vyřaďte nebo označte.",
            "Při analýze jen současných zákazníků si dejte pozor na zkreslení přeživších.",
        ],
        "common_mistakes": [
            "Porovnání dosavadního odchodu mezi kohortami různého stáří.",
            "Použití všech aktivních zákazníků jako jmenovatele odchodu uprostřed období.",
            "Vícenásobné započtení uživatelů v kroku trychtýře.",
        ],
        "revision": "Sestavte retenční matici znovu podle akvizičního zdroje a porovnejte Paid Social s Referral.",
    },
    "dg4": {
        "title": "Korelace, matoucí proměnné a Simpsonův paradox",
        "objectives": [
            "Spočítat a interpretovat korelaci a kovarianci (Pearson a Spearman).",
            "Vysvětlit, proč korelace neznamená kauzalitu.",
            "Identifikovat matoucí proměnné (confoundery) a efekty složení.",
            "Odhalit Simpsonův paradox porovnáním souhrnných výsledků a výsledků v rámci segmentů.",
        ],
        "concept": """
**Kovariance** měří, jak se dvě proměnné pohybují společně, ale závisí na jednotkách. **Pearsonova korelace** ji standardizuje na [-1, 1] a měří *lineární* souvislost; **Spearmanova** korelace používá pořadí, zachytí monotónní vztahy a je odolná vůči odlehlým hodnotám. r = 0 neznamená „žádný vztah“ - tvar U může mít r blízko 0.

**Proč korelace není kauzalita:**

* **Matoucí proměnná:** obě veličiny ovlivňuje třetí (prodej zmrzliny i utonutí rostou s teplotou).
* **Obrácená kauzalita:** nespokojení zákazníci zakládají víc tiketů, ne že by tikety způsobovaly nespokojenost.
* **Výběrové efekty:** analýza vyfiltrované populace (jen zákazníci, kteří odpověděli na dotazník).
* **Náhoda:** otestujete-li dost dvojic, některé budou korelovat náhodou.

**Simpsonův paradox / efekty složení.** Souhrnný trend se může lišit od trendu v každém segmentu - nebo být dokonce opačný -, protože se změnily *velikosti* segmentů. Klasický vzorec: odchod celkově roste, zatímco odchod *v každém kanálu* je stejný, protože se mix posunul ke kanálu s vysokým odchodem.

**Jak se bránit:** segmentujte podle věrohodných matoucích proměnných; porovnávejte srovnatelné (stratifikujte nebo standardizujte na pevný mix); uveďte, které proměnné jste *nekontrolovali*. Kauzální efekty čistě identifikují jen randomizované experimenty (další lekce); u observačních dat volte opatrný jazyk.
""",
        "business_context": """
Šestiměsíční odchod v CloudNest vzrostl z přibližně 25 % na více než 30 %. Produktový tým říká, že „nový onboarding něco rozbil“. Marketing od dubna 2024 spustil velkou kampaň na Paid Social. Kdo má pravdu?
""",
        "worked_example": {"explanation": """
* Celkový odchod znatelně vzrostl.
* Ve většině kanálů se odchod téměř nepohnul - ale **podíl** Paid Social na registracích vyskočil z ~15 % na ~40 % a Paid Social má zhruba dvojnásobný odchod než ostatní kanály.
* Převážení nových měr na starý mix ukáže, že většina nárůstu zmizí: jde o **efekt složení**. Hypotézu o onboardingu tyto důkazy nepodporují (zákazníci tarifu Basic ale v červenci 2024 zaznamenali i zdražení - ověřte to zvlášť).
"""},
        "summary": [
            "Pearson měří lineární souvislost; Spearman je založen na pořadí a je robustní.",
            "Korelace vytvářejí matoucí proměnné, obrácená kauzalita, výběr i náhoda.",
            "Porovnáním souhrnných výsledků a výsledků v segmentech odhalíte efekty složení.",
            "Standardizace na pevný mix vyčíslí, jaká část změny je způsobena mixem.",
        ],
        "common_mistakes": [
            "Doporučení akce jen na základě korelace.",
            "Ignorování změn mixu segmentů v čase.",
            "Závěr „žádný vztah“ z r blízko 0.",
        ],
        "revision": "Zopakujte standardizaci s tarifem místo akvizičního zdroje.",
    },
    "dg5": {
        "title": "Testování hypotéz, intervaly spolehlivosti a A/B testy",
        "objectives": [
            "Formulovat nulovou a alternativní hypotézu k byznysové otázce.",
            "Správně interpretovat p-hodnoty a intervaly spolehlivosti.",
            "Provést z-test dvou podílů a Welchův t-test.",
            "Rozlišit statistickou a praktickou významnost a ověřit předpoklady testu.",
        ],
        "concept": """
**Logika testu hypotéz.** Předpokládejte nulovou hypotézu H0 (žádný rozdíl). Spočítejte, jak překvapivá by pozorovaná data byla, kdyby H0 platila. **p-hodnota** je pravděpodobnost výsledku alespoň tak extrémního jako pozorovaný, *pokud by H0 platila*.

* p-hodnota **není** pravděpodobnost, že H0 platí, ani pravděpodobnost, že výsledek je dílem náhody.
* Volba alfa = 0,05 znamená přijmout 5% míru falešně pozitivních výsledků, když efekt ve skutečnosti neexistuje.
* „Nevýznamné“ znamená „nedostatek důkazů“, ne „žádný efekt“.

**Intervaly spolehlivosti** jsou informativnější než p-hodnoty: 95% IS pro zlepšení (lift) udává věrohodný rozsah velikostí efektu. Pokud IS nezahrnuje 0, je výsledek významný na hladině 5 %. Široký IS znamená, že potřebujete víc dat.

**Běžné testy**

| Otázka | Test |
|---|---|
| Rozdíl dvou konverzních měr | z-test dvou podílů (nebo chí-kvadrát) |
| Rozdíl dvou průměrů (nestejné rozptyly) | Welchův t-test |
| Zešikmená metrika, např. tržba na uživatele | Mannův-Whitneyův U test nebo bootstrapový IS |
| Souvislost dvou kategoriálních proměnných | chí-kvadrát test nezávislosti |

**Základy A/B testování:** randomizujte; primární metriku, minimální detekovatelný efekt a velikost vzorku stanovte *před* začátkem; nezastavujte test předčasně, jakmile p klesne pod 0,05 („nakukování“ zvyšuje falešně pozitivní výsledky); kontrolujte nepoměr velikosti vzorků (mají skupiny očekávanou velikost?); dejte si pozor na efekt novosti a vícenásobná porovnání napříč mnoha segmenty.

**Praktická významnost.** Při milionu uživatelů může být zlepšení o 0,05 procentního bodu „významné“, a přesto bezcenné. Porovnejte IS s nejmenším efektem, který by ospravedlnil náklady na změnu.

**Předpoklady a omezení.** Nezávislost pozorování, dostatečné velikosti vzorků (očekávané četnosti >= 5-10 v buňce) a žádné vzájemné ovlivňování skupin. Uvádějte je.
""",
        "business_context": """
Sesterský e-commerce tým CloudNest otestoval přepracovanou pokladnu na 20 000 uživatelích. Konverze vzrostla zhruba z 10,1 % na 10,7 %. Produktový manažer ji chce nasadit. Je zlepšení skutečné, jak velké může být a vyplatí se?
""",
        "worked_example": {"explanation": """
* Absolutní zlepšení je asi 0,6 procentního bodu (~6 % relativně). p-hodnota je kolem 0,15 a 95% IS zahrnuje 0, takže důkazy **nejsou** dost silné na tvrzení o efektu na hladině 5 %.
* První týden ukazuje větší výhodu testované varianty než pozdější týdny - v souladu s efektem novosti.
* **Doporučení:** nevyhlašujte vítězství. Buď test prodlužte (IS je široký), nebo rozhodněte, zda věrohodný rozsah zlepšení ospravedlní náklady na nasazení.
"""},
        "summary": [
            "p-hodnota měří překvapení za platnosti H0 - ne pravděpodobnost, že H0 platí.",
            "Intervaly spolehlivosti ukazují věrohodnou velikost efektu; v reportech jim dávejte přednost.",
            "Metriku a velikost vzorku stanovte předem; nenakukujte a nezastavujte předčasně.",
            "Statistická významnost není byznysová významnost.",
        ],
        "common_mistakes": [
            "Tvrzení „s 95% pravděpodobností je efekt skutečný“.",
            "Testování 20 segmentů a reportování toho jediného s p < 0,05.",
            "Použití t-testu na silně zešikmené tržby bez ověření robustnosti.",
        ],
        "revision": "Spočítejte IS podle zařízení a vysvětlete, proč jsou IS na úrovni segmentů širší.",
    },
    "dg6": {
        "title": "Detekce anomálií a komunikace důkazů",
        "objectives": [
            "Odhalovat anomálie v časových řadách pomocí klouzavých statistik a sezónních základen.",
            "Odlišit anomálie od očekávané sezónnosti a známých událostí.",
            "Napsat diagnostické memo se zjištěními, důkazy, omezeními a alternativami.",
        ],
        "concept": """
**Detekce anomálií** se ptá: je toto pozorování neobvyklé *ve srovnání s tím, co jsme očekávali*?

* **Pevné prahy** (tržby < 10 tis. EUR) jsou jednoduché, ale ignorují sezónnost.
* **Klouzavé z-skóre:** porovnejte každou hodnotu s průměrem a SD předchozího okna (např. předchozích 28 dní). Označte |z| > 3. Použijte *předcházející* okno, aby dnešní hodnota neovlivnila vlastní základnu.
* **Sezónní základny:** porovnejte se stejným dnem v týdnu v předchozích týdnech, nebo modelujte trend + sezónnost a označte velká rezidua.
* **Robustní statistiky** (medián, MAD) odolávají zkreslení dřívějšími anomáliemi.

Každý detektor vyvažuje falešné poplachy a přehlédnuté incidenty. Prahy laďte podle historických incidentů a zvažte cenu každé chyby.

**Komunikace důkazů - diagnostické memo**

1. **Nejprve otázka a odpověď** - „Tržby regionu West klesly v srpnu-září meziročně o ~39 %; kolaps kategorie Electronics (-42 tis. EUR) to více než vysvětluje, zatímco ostatní kategorie rostly.“
2. **Důkazy** - 2-3 analýzy, které to podporují, s čísly a grafy.
3. **Míra jistoty a omezení** - mezery v datech, neověřené předpoklady, možné matoucí proměnné.
4. **Zvážená alternativní vysvětlení** - a proč jsou s daty méně v souladu.
5. **Další kroky** - co by hypotézu potvrdilo (např. skladové záznamy) a doporučené akce.

Používejte kalibrovaný jazyk: *ukazuje*, *je v souladu s*, *naznačuje*, *nemůžeme vyloučit*.
""",
        "business_context": """
Provoz chce automatické upozornění, když je denní poptávka po určité skladové položce (SKU) abnormální, a vedení chce krátké memo vysvětlující incident s tržbami v regionu West. Obojí vyžaduje oddělit skutečné signály od běžného kolísání.
""",
        "worked_example": {"explanation": """
* Předcházející okno (`shift(1)`) zajistí, že se každý den posuzuje jen vůči minulosti.
* Poptávka má silnou týdenní sezónnost (víkendy jsou slabé), takže prosté klouzavé z-skóre označí dny, které jsou prostě nedělemi blízko svátků. Poměr zohledňující den v týdnu bývá lepší základnou.
* Před odesláním upozornění ověřte, zda označené dny nesouvisejí se známými událostmi (akce, svátky).
"""},
        "summary": [
            "Anomálie jsou odchylky od očekávané základny - základnu volte pečlivě.",
            "Používejte předcházející okna a robustní statistiky; zohledněte sezónnost.",
            "Memo začíná odpovědí, pak následují důkazy, omezení, alternativy a další kroky.",
            "Jazyk přizpůsobte síle důkazů.",
        ],
        "common_mistakes": [
            "Centrovaná okna, která propustí aktuální hodnotu do její vlastní základny.",
            "Označování běžných sezónních špiček jako anomálií.",
            "Memo, které vyjmenuje analýzy, ale nikdy neodpoví na otázku.",
        ],
        "revision": "Napište pětivěté memo o výsledku A/B testu podle struktury mema.",
    },
    "dg7": {
        "title": "R pro diagnostickou analýzu",
        "objectives": [
            "Pracovat v R s vektory a datovými rámci (data frame).",
            "Seskupovat a shrnovat v základním R (aggregate, tapply) a v dplyr.",
            "Vizualizovat rozdělení v ggplot2 (volitelný balíček).",
            "Spouštět v R t-testy a chí-kvadrát testy a číst jejich výstup.",
        ],
        "concept": """
R je navrženo pro statistiku; mnoho testů je jediné volání funkce. Hlavní rozdíly oproti Pythonu:

* Indexuje se od **1**, ne od 0. `x[1]` je první prvek.
* Základním typem jsou vektory: `x <- c(3, 5, 8)`; operace jsou vektorizované: `x * 2`.
* Datové rámce: `df$column`, `df[rows, cols]`, `nrow(df)`, `summary(df)`, `str(df)`.
* Chybějící hodnoty jsou `NA`; většina funkcí potřebuje `na.rm = TRUE`: `mean(x, na.rm = TRUE)`.
* Přiřazení se píše `<-` (funguje i `=`).

**Seskupování v základním R**

```r
aggregate(churned_6m ~ acquisition_source, data = cf, FUN = mean)
tapply(cf$churned_6m, cf$plan, mean)
table(cf$plan, cf$churned_6m)          # kontingenční tabulka
```

**dplyr (tidyverse)** - čitelné řetězce operací:

```r
library(dplyr)
cf |>
  group_by(acquisition_source) |>
  summarise(customers = n(), churn = mean(churned_6m)) |>
  arrange(desc(churn))
```

**ggplot2** - gramatika grafiky:

```r
library(ggplot2)
ggplot(cf, aes(x = logins_first_month, fill = factor(churned_6m))) +
  geom_histogram(bins = 30, position = "identity", alpha = 0.5) +
  labs(x = "Logins in first month", fill = "Churned")
```

**Testy:** `t.test(y ~ group, data = df)` ve výchozím stavu provede Welchův t-test; `chisq.test(table(a, b))`; `prop.test(x = c(k1, k2), n = c(n1, n2))`; `cor.test(x, y, method = "spearman")`.

V laboratoři používají hodnocená cvičení v R **jen základní R**, takže fungují bez dalších balíčků. `load_table("subscription.churn_features")` načte data jako datový rámec (data přicházejí jako text - převeďte je pomocí `as.Date()`).
""",
        "business_context": """
Tým datových vědců CloudNest pracuje v R. Máte v R zopakovat souhrn odchodu podle zdroje a otestovat, zda se rané zapojení liší mezi odcházejícími a zůstávajícími zákazníky.
""",
        "worked_example": {"explanation": """
* `aggregate(y ~ g, data, FUN)` je GROUP BY základního R.
* `t.test` ve výchozím stavu používá Welchovu korekci (`var.equal = FALSE`). Přečtěte si průměry obou skupin, IS rozdílu a p-hodnotu.
* `chisq.test` na kontingenční tabulce testuje, zda se míry odchodu liší mezi tarify.
* Vyžaduje lokální instalaci R; pokud R není nainstalováno, laboratoř zobrazí instrukce k instalaci a tento příklad nelze spustit.
"""},
        "summary": [
            "R indexuje od 1, pro chybějící hodnoty používá NA a je vektorizované.",
            "Seskupené souhrny vytvoříte pomocí aggregate()/tapply() v základním R a group_by()/summarise() v dplyr.",
            "t.test(), chisq.test(), prop.test() a cor.test() pokryjí většinu diagnostických testů.",
            "Python a R dají stejné statistiky, pokud použijete stejnou metodu a volby - kontrolujte výchozí nastavení.",
        ],
        "common_mistakes": [
            "Zapomenuté na.rm = TRUE a výsledky NA.",
            "Předpoklad, že výchozí nastavení t.test v R odpovídá scipy (ttest_ind ve scipy předpokládá stejné rozptyly, pokud nenastavíte equal_var=False).",
            "Práce s textovými daty jako s daty bez as.Date().",
        ],
        "revision": "Přepište příklad Simpsonova paradoxu v Pythonu (dg4) do R.",
    },
}
