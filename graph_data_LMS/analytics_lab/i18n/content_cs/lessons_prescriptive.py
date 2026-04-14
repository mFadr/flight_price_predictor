"""Czech text for the Prescriptive Analytics lessons."""

LESSONS = {
    "ps1": {
        "title": "Základy optimalizace: rozhodovací proměnné, cíle a omezení",
        "objectives": [
            "Převést byznysový problém na rozhodovací proměnné, účelovou funkci a omezení.",
            "Rozpoznat přípustné, nepřípustné a neomezené úlohy.",
            "Vyřešit úlohu lineárního programování pomocí scipy.optimize.linprog.",
            "Interpretovat aktivní (vázající) omezení a rezervy (slack).",
        ],
        "concept": """
Preskriptivní analytika doporučuje **akce**. Jejím hlavním nástrojem je optimalizace. Každý model má tři části:

| Část | Otázka | Příklad výrobního mixu |
|---|---|---|
| Rozhodovací proměnné | Co můžeme zvolit? | počet kusů každé sady sestavených za týden (x1..x4) |
| Účelová funkce | Co maximalizujeme nebo minimalizujeme? | celkový příspěvek na úhradu = 24x1 + 41x2 + 13x3 + 30x4 |
| Omezení | Co nás limituje? | hodiny montáže, testování, balení; stropy poptávky; smluvní minima; x >= 0 |

**Lineární programování (LP)** vyžaduje lineární účelovou funkci i lineární omezení. Úlohy LP se řeší rychle a s prokazatelnou optimalitou. **Přípustná oblast** je množina rozhodnutí splňujících všechna omezení; optimum leží v jejím vrcholu.

* *Nepřípustná* - žádné rozhodnutí nesplňuje všechna omezení (např. smluvní minima přesahují kapacitu). Uveďte, která omezení jsou v konfliktu.
* *Neomezená* - účelová funkce se může zlepšovat donekonečna: chybí omezení.
* *Aktivní (vázající) omezení* - v optimu je plně využité (nulová rezerva). Zisk limitují jen vázající omezení; uvolnění nevázajícího nic nezmění.
* *Celočíselné proměnné* (kusy, rozhodnutí ano/ne) vyžadují smíšené celočíselné programování (`scipy.optimize.milp` nebo PuLP). Zaokrouhlení řešení LP může být nepřípustné nebo neoptimální.

**Tvar ve scipy:** `linprog` **minimalizuje** c @ x za podmínek `A_ub @ x <= b_ub`, `A_eq @ x == b_eq` a mezí. Chcete-li maximalizovat zisk, minimalizujte **záporný** zisk.

**Ekvivalent v R:**

```r
library(lpSolve)
sol <- lp("max", objective.in = profit, const.mat = A, const.dir = rep("<=", nrow(A)), const.rhs = b)
sol$solution; sol$objval
```
""",
        "business_context": """
Meridian Supply sestavuje čtyři sady na sdílených zdrojích Montáž, Testování a Balení. Vedoucí závodu dnes plánuje „to, co se minulý týden dobře prodávalo“. Spočítáte týdenní mix maximalizující zisk a určíte, který zdroj je úzkým hrdlem.
""",
        "worked_example": {"explanation": """
* Meze kódují stropy poptávky (horní) a smluvní minima (dolní).
* `res.slack` ukazuje nevyužité hodiny: zdroj s nulovou rezervou je **vázající** úzké hrdlo. Hodiny navíc by tam zvýšily zisk; hodiny navíc jinde ne.
* **Komunikujte jako rozhodnutí:** „Sestavte X sad Pro Kit ... Úzkým hrdlem je kapacita testování; každá další hodina testování má hodnotu přibližně Y EUR (viz lekce o citlivosti).“
"""},
        "extra_examples": [{"explanation": "lpSolve vyjadřuje meze jako další řádky omezení (max. poptávka <=, min. závazek >=). Optimum odpovídá výsledku ze scipy."}],
        "summary": [
            "Model = rozhodovací proměnné + účelová funkce + omezení.",
            "linprog minimalizuje; pro maximalizaci účelovou funkci znegujte.",
            "Vázající omezení jsou úzká hrdla, která limitují účelovou funkci.",
            "Když musí být rozhodnutí celá čísla, použijte celočíselné programování.",
        ],
        "common_mistakes": [
            "Zapomenutá negace účelové funkce při maximalizaci.",
            "Vynechání nezápornosti nebo stropů poptávky (neomezená řešení).",
            "Zaokrouhlení řešení LP bez nové kontroly přípustnosti.",
        ],
        "revision": "Odstraňte stropy poptávky a sledujte, co se stane s řešením.",
    },
    "ps2": {
        "title": "Alokace zdrojů, přiřazovací úlohy a rozvrhování",
        "objectives": [
            "Modelovat přiřazovací úlohy a řešit je pomocí linear_sum_assignment.",
            "Formulovat plánování kapacit a alokaci zdrojů pomocí smíšeného celočíselného programování.",
            "Vyjádřit pravidla rozvrhování (pokrytí, max. hodiny) jako omezení.",
        ],
        "concept": """
**Přiřazovací úlohy** přiřazují n pracovníků k n úkolům s minimálními celkovými náklady (nebo maximální hodnotou), každý pracovník dělá jeden úkol. Maďarská metoda je řeší přesně: `scipy.optimize.linear_sum_assignment(cost_matrix)`. Povoleny jsou i obdélníkové matice (někteří pracovníci zůstanou nepřiřazeni).

**Alokace zdrojů** rozděluje omezený zdroj (rozpočet, hodiny personálu, nákladní auta) mezi využití tak, aby se maximalizovala hodnota. Při lineárních výnosech jde o LP; při klesajících výnosech se úloha stává nelineární - často se aproximuje po částech lineárně.

**Plánování kapacit** rozhoduje, kolik kapacity přidat (směny, stroje), obvykle s **celočíselnými** nebo **binárními** rozhodnutími (otevřít druhou směnu: ano/ne) a fixními náklady. Binární proměnné modelují i logiku: „pokud otevřeme sklad B (y = 1), můžeme z něj expedovat“ -> `shipments_B <= M * y`.

**Rozvrhování** přiřazuje lidi nebo úlohy do časových slotů podle pravidel:

* pokrytí: každá hodina potřebuje alespoň k pracovníků;
* limity: každý pracuje nejvýše 40 hodin a nejvýše 5 směn;
* posloupnost: úloha A před úlohou B.

Z nich se stávají celočíselné programy. `scipy.optimize.milp` je zvládne; PuLP (volitelně) nabízí přívětivější syntaxi modelování.

**Tipy k modelování:** začněte zmenšenou úlohou a ověřte ji ručně; pojmenujte proměnné a omezení; zkontrolujte řešení vůči každému byznysovému pravidlu; zeptejte se zainteresovaných, která pravidla jsou tvrdá (musí platit) a která měkká (preference) - měkká pravidla se stanou penalizacemi v účelové funkci.
""",
        "business_context": """
Vedoucí servisních techniků firmy Meridian musí přiřadit pět techniků k pěti naléhavým opravám. Kvůli cestování a rozdílným dovednostem jsou některá přiřazení mnohem dražší. Dnes se to dělá každé ráno ručně.
""",
        "worked_example": {"explanation": """
* `linear_sum_assignment` vrátí optimální dvojice řádek/sloupec; součet (zde 20 hodin) je prokazatelně minimální.
* Příklad s personálem je záměrně triviální: jen s omezeními pokrytí se počet lidí rovná potřebě. Přidáním pravidel (např. lidé pracují dvě po sobě jdoucí směny) se celočíselný program stane smysluplným.
* Vždy zkontrolujte: má každá zakázka přesně jednoho technika a lze výsledek vysvětlit dotčeným lidem?
"""},
        "summary": [
            "Přiřazovací úlohy mají přesná a rychlá řešení (maďarská metoda).",
            "Binární proměnné modelují rozhodnutí ano/ne a logická pravidla.",
            "Pravidla rozvrhování se převádějí na omezení pokrytí a limitů.",
            "Oddělte tvrdá omezení od měkkých preferencí (penalizací).",
        ],
        "common_mistakes": [
            "Hladová pravidla (nejlepší shoda první), která minou globální optimum.",
            "Ignorování celočíselnosti u počtu lidí nebo kusů.",
            "Zakódování preferencí jako tvrdých omezení, takže úloha je nepřípustná.",
        ],
        "revision": "Přidejte šestou zakázku a pravidlo, že technik 3 nemůže dělat zakázku 1 (náklady = velké číslo).",
    },
    "ps3": {
        "title": "Rozhodování o zásobách, objednávkách a cenách",
        "objectives": [
            "Spočítat ekonomické objednací množství (EOQ).",
            "Nastavit bod znovuobjednání a pojistnou zásobu pro cílovou úroveň služeb.",
            "Vyhodnotit cenové a slevové scénáře s explicitní reakcí poptávky.",
            "Provést analýzu nákladů a přínosů provozní změny.",
        ],
        "concept": """
**Kompromis u zásob:** časté objednávání stojí poplatky za objednávky; řídké objednávání znamená držet velké zásoby.

**EOQ** (ekonomické objednací množství) minimalizuje náklady na objednávání + držení zásob při ustálené poptávce:

```
EOQ = sqrt(2 * D * S / H)
D = roční poptávka (kusy), S = náklady na objednávku, H = roční náklady na držení kusu (= unit_cost * sazba držení)
```

**Bod znovuobjednání (ROP)** - když zásoba klesne na ROP, zadejte objednávku:

```
ROP = očekávaná poptávka během dodací lhůty + pojistná zásoba = d * L + z * sigma_d * sqrt(L)
```

kde d je průměrná denní poptávka, sigma_d denní směrodatná odchylka, L dodací lhůta ve dnech a z faktor úrovně služeb (z = 1,645 pro 95% úroveň služeb v cyklu, 2,054 pro 98 %). Vzorec předpokládá nezávislou denní poptávku a pevnou dodací lhůtu; proměnlivé dodací lhůty potřebují větší rezervu.

**Cenové scénáře.** Tržby a zisk reagují na cenu prostřednictvím poptávky. Při konstantní **cenové elasticitě** e platí `Q_new = Q * (P_new / P)^e`. Pro e = -1,5 zvýší 10% sleva objem o ~17 % - ale zisk může přesto klesnout, pokud jsou marže tenké:

```
profit = Q_new * (P_new - unit_cost)
```

**Analýza nákladů a přínosů:** vyjmenujte přírůstkové náklady a přínosy, převeďte je na společný časový základ (ročně nebo NPV), uveďte předpoklady a spočítejte hodnoty bodu zvratu („změna se vyplatí, pokud se dodací lhůta zkrátí alespoň o 2 dny“).
""",
        "business_context": """
Plánovači firmy Meridian objednávají, „když se jim zdá, že je toho málo“. U rychloobrátkového zboží dochází několikrát za měsíc k výpadkům, zatímco pomaloobrátkové váže hotovost. Nastavíte objednací množství a body znovuobjednání na základě dat a vyhodnotíte navrhovanou 10% slevu.
""",
        "worked_example": {"explanation": """
* SKU od dodavatelů s dlouhou dodací lhůtou potřebují pro stejnou úroveň služeb mnohem větší pojistné zásoby - argument pro diverzifikaci dodavatelů.
* Porovnejte vypočtené body znovuobjednání se současnými v tabulce `inventory` a najděte SKU ohrožené výpadkem.
* Cenový příklad ukazuje, že sleva, která zvýší počet kusů, může při tenkých maržích **snížit zisk**: rozhodnutí určují předpoklady o elasticitě, takže jich otestujte několik.
"""},
        "summary": [
            "EOQ vyvažuje náklady na objednávání a na držení zásob.",
            "Bod znovuobjednání = poptávka během dodací lhůty + pojistná zásoba; pojistná zásoba roste s variabilitou a dodací lhůtou.",
            "Cenová rozhodnutí závisí na elasticitě a marži - větší objem není vždy větší zisk.",
            "Předpoklady analýzy nákladů a přínosů uvádějte výslovně a počítejte body zvratu.",
        ],
        "common_mistakes": [
            "Použití jen průměrné poptávky (bez pojistné zásoby).",
            "Míchání časových jednotek (roční náklady na držení s denní poptávkou).",
            "Předpoklad, že se sleva zaplatí sama, protože vzroste objem.",
        ],
        "revision": "Přepočítejte pojistnou zásobu pro 98% úroveň služeb a porovnejte dodatečné náklady na držení.",
    },
    "ps4": {
        "title": "Simulace Monte Carlo a riziko",
        "objectives": [
            "Vyjádřit nejisté vstupy pravděpodobnostními rozděleními.",
            "Simulovat rozdělení výsledků metodou Monte Carlo.",
            "Shrnout riziko: očekávaná hodnota, pravděpodobnost ztráty, percentily (VaR).",
            "Porovnávat rozhodnutí za nejistoty, ne jen při průměrných vstupech.",
        ],
        "concept": """
Deterministické modely používají jediné „nejlepší odhady“. Ale **průměr výsledků není výsledkem průměrů**, když jsou modely nelineární nebo mají stropy a podlahy (např. prodej nemůže překročit zásobu).

**Simulace Monte Carlo**

1. Určete nejisté vstupy a zvolte rozdělení (normální; lognormální pro kladné zešikmené hodnoty; trojúhelníkové, když experti uvedou min/nejpravděpodobnější/max; rovnoměrné, když je znám jen rozsah).
2. Vylosujte tisíce scénářů pomocí generátoru s pevným semínkem (`np.random.default_rng(42)`).
3. Pro každý scénář spočítejte výsledek (vektorizovaně v NumPy, ne smyčkami v Pythonu).
4. Shrňte rozdělení: průměr, směrodatná odchylka, percentily, pravděpodobnost splnění cíle nebo ztráty.

**Míry rizika**

* P(ztráta) - pravděpodobnost, že zisk < 0.
* 5. percentil (Value at Risk na 95 %) - špatný, ale věrohodný výsledek.
* Očekávaný schodek (expected shortfall) - průměrný výsledek v nejhorších 5 %.

**Rozhodovací pravidlo.** Rizikově neutrální rozhodovatel zvolí nejvyšší očekávanou hodnotu; rizikově averzní může dát přednost mírně nižšímu průměru s mnohem menší šancí na ztrátu. Ochotu riskovat uveďte výslovně.

**Dobrá praxe:** rozdělení zdůvodněte daty nebo názorem expertů; zahrňte korelace mezi vstupy, pokud jsou důležité (např. poptávka a cena); uvádějte chybu Monte Carlo (klesá s sqrt(n)); proveďte citlivostní analýzu předpokladů o rozděleních.

**Ekvivalent v R:** `rnorm`, `runif`, `quantile(profit, 0.05)`, `mean(profit < 0)`.
""",
        "business_context": """
Marketing navrhuje jednorázovou akci s fixními náklady 5 000 EUR. Poptávka i jednotková marže jsou nejisté. Finanční ředitel se ptá: „Kolik očekáváme, že vyděláme, a jaká je šance, že prohrajeme peníze?“
""",
        "worked_example": {"explanation": """
* Simulované rozdělení ukazuje nezanedbatelnou pravděpodobnost ztráty, kterou jediný „průměrný“ výpočet skryje.
* Strop zásob ořezává horní scénáře: očekávaný zisk klesne pod deterministický odhad - příklad, proč průměry vstupů zavádějí.
* **Formulace doporučení:** „Očekávaný zisk přibližně X EUR; zhruba Y% šance na ztrátu; ve špatném případě (5. percentil) prohrajeme asi Z EUR. Pokračujte, pokud je toto riziko přijatelné.“
"""},
        "summary": [
            "Nejisté vstupy modelujte jako rozdělení; simulujte tisíce scénářů.",
            "Uvádějte očekávanou hodnotu i riziko (P(ztráta), percentily, očekávaný schodek).",
            "Nelinearity (stropy, podlahy) dělají „plánování podle průměrů“ zkresleným.",
            "Simulace pro reprodukovatelnost nasemínkujte a testujte předpoklady o rozděleních.",
        ],
        "common_mistakes": [
            "Plánování podle průměrných vstupů a ignorování variability.",
            "Použití smyček v Pythonu místo vektorizovaného losování (pomalé).",
            "Volba rozdělení bez zdůvodnění.",
        ],
        "revision": "Spusťte simulaci znovu s lognormální poptávkou a porovnejte P(ztráta).",
    },
    "ps5": {
        "title": "Citlivostní analýza, scénáře a doporučení",
        "objectives": [
            "Číst stínové ceny a redukované náklady z úlohy LP.",
            "Provádět jednorozměrnou citlivostní analýzu (tornádo) a scénářovou analýzu.",
            "Vyvažovat kompromisy mezi ziskem, náklady, úrovní služeb a rizikem.",
            "Napsat doporučení s předpoklady a podmínkami, kdy se mění.",
        ],
        "concept": """
Optimální odpověď je jen tak dobrá jako její předpoklady. **Citlivostní analýza** se ptá, jak se doporučení změní, když se změní vstupy.

**Stínová cena (duální hodnota)** omezení = změna optimální hodnoty účelové funkce při uvolnění omezení o jednotku, platná v určitém rozsahu. Má-li rozpočtové omezení stínovou cenu 0,22, přidá další euro rozpočtu přibližně 0,22 EUR zisku - o rozpočet navíc se tedy vyplatí žádat, jen pokud jsou jeho kapitálové náklady nižší. Ve scipy (HiGHS) dává `res.ineqlin.marginals` duální hodnoty omezení `<=` pro *minimalizační* úlohu; pokud jste maximalizovali minimalizací -zisku, otočte znaménko.

**Jednorozměrná citlivost:** měňte jeden vstup po druhém (např. +/-20 %) a zaznamenávejte účelovou funkci -> *tornádový graf* seřadí vstupy podle dopadu.

**Scénářová analýza:** konzistentně změňte několik vstupů („recese“: nižší marže, vyšší riziko) a optimalizujte znovu. Prezentujte základní / pesimistický / optimistický scénář vedle sebe.

**Kompromisy.** Mnoho rozhodnutí má více cílů (zisk vs. riziko vs. úroveň služeb). Možnosti:

* optimalizovat jeden cíl a ostatní omezit (maximalizovat zisk při průměrném riziku <= 0,35);
* spojit cíle do vážené účelové funkce (s vahami odsouhlasenými zainteresovanými);
* vykreslit *efektivní hranici* opakovaným řešením s různými limity.

**Struktura doporučení**

1. **Rozhodnutí:** co udělat, srozumitelně a v číslech.
2. **Očekávaný dopad** a jeho rozsah.
3. **Klíčové předpoklady** a zdroje dat.
4. **Vázající omezení** - co limituje výsledek a jakou hodnotu má jejich uvolnění.
5. **Kdy se doporučení mění** - prahy z citlivostní analýzy („pokud marže e-mailu klesne pod 0,30, přesuňte 10 tis. EUR do Search“).
6. **Rizika a plán monitoringu.**
""",
        "business_context": """
Marketingová ředitelka musí rozdělit čtvrtletní rozpočet 400 000 EUR mezi šest kanálů s minimálními závazky, kapacitními limity kanálů a rizikovou politikou (průměrné rizikové skóre <= 0,35). Potřebuje doporučení, ne jen výstup řešiče.
""",
        "worked_example": {"explanation": """
* Stínová cena rozpočtu je **nulová**: při rizikové politice 0,35 optimalizátor ani nevyčerpá celých 400 tis. EUR. Další rozpočet je bezcenný, dokud se politika nezmění - zjištění, které stojí za to říct ředitelce výslovně.
* **Rizikové omezení je vázající** (kladná duální hodnota): uvolnění rizikové politiky zvýší zisk. Jde o **kompromis v politice** pro vedení, ne o technický detail.
* Mřížka scénářů ukazuje, kde na které páce záleží: při 300 tis. EUR je vázající rozpočet a rizikový strop je irelevantní; při 400-500 tis. EUR rozhoduje rizikový strop. Vždy kontrolujte `res.status` - přísné politiky v kombinaci s minimálními závazky mohou scénář učinit nepřípustným.
* Lineární marže jsou aproximací platnou mezi minimálními a maximálními výdaji (klesající výnosy z modulu 3 stropy zdůvodňují).
"""},
        "summary": [
            "Stínové ceny oceňují uvolnění vázajících omezení.",
            "Tornádové grafy řadí vstupy; scénáře testují konzistentní alternativní budoucnosti.",
            "Kompromisy uvádějte výslovně (omezení, váhy nebo hranice).",
            "Doporučení uvádí rozhodnutí, dopad, předpoklady, omezení a podmínky změny.",
        ],
        "common_mistakes": [
            "Prezentace výstupu řešiče bez interpretace.",
            "Čtení stínových cen se špatným znaménkem po negaci účelové funkce.",
            "Ignorování nepřípustných scénářů.",
        ],
        "revision": "Sestavte tornádový graf pro změny marže každého kanálu o +/-20 % a pak začněte závěrečný projekt 4.",
    },
}
