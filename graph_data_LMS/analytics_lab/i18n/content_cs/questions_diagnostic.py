"""Czech text for the Diagnostic Analytics questions. Options are (text, why) in the original order."""

TOPICS = {
    "Missing data": "Chybějící data",
    "Duplicates": "Duplicity",
    "Outliers": "Odlehlé hodnoty",
    "Root-cause analysis": "Analýza příčin",
    "Contribution analysis": "Analýza příspěvků",
    "Mix vs rate": "Mix vs. míra",
    "Right-censoring": "Cenzorování zprava",
    "Funnels": "Trychtýře",
    "Survivorship bias": "Zkreslení přeživších",
    "Simpson's paradox": "Simpsonův paradox",
    "Correlation": "Korelace",
    "Pearson vs Spearman": "Pearson vs. Spearman",
    "p-values": "p-hodnoty",
    "Confidence intervals": "Intervaly spolehlivosti",
    "A/B testing practice": "Praxe A/B testování",
    "Practical significance": "Praktická významnost",
    "Anomaly detection": "Detekce anomálií",
    "Seasonal baselines": "Sezónní základny",
    "Communicating evidence": "Komunikace důkazů",
    "R basics": "Základy R",
    "R tests": "Testy v R",
    "Hypotheses vs findings": "Hypotézy vs. zjištění",
}

QUESTIONS = {
    "q_dg_001": {
        "stem": "Dotazníky spokojenosti většinou nevyplní nespokojení zákazníci. O jaký typ chybějících dat jde a jaké je riziko?",
        "options": [
            ("Chybějící ne náhodně (MNAR); průměry odpovědí nadhodnotí spokojenost", "Chybění závisí na samotné nepozorované hodnotě, což pozorovaný průměr zkresluje nahoru."),
            ("Chybějící zcela náhodně; žádné zkreslení, jen menší přesnost", "MCAR by znamenalo, že vynechání se spokojeností nesouvisí, což odporuje scénáři."),
            ("Chybějící náhodně; vyřazení řádků je vždy bezpečné", "Vyřazení je bezpečné jen při MCAR a tohle není ani MAR."),
            ("Vůbec nejde o chybějící data, protože dotazník byl dobrovolný", "I dobrovolná pole vytvářejí chybějící hodnoty, které mohou analýzu zkreslit."),
        ],
        "explanation": "Než zvolíte způsob ošetření, zeptejte se, *proč* data chybějí.",
    },
    "q_dg_002": {
        "stem": "`customer_id` je unikátní, ale 30 hashů e-mailů se vyskytuje dvakrát. Jaký je správný závěr?",
        "options": [
            ("Klíč je čistý, ale někteří lidé jsou zaznamenáni dvakrát; počty zákazníků podle ID jsou nadsazené", "Duplicitní entity se skrývají za unikátními umělými klíči."),
            ("Duplicity neexistují, protože primární klíč je unikátní", "Unikátnost klíče nic neříká o duplicitních entitách."),
            ("Sloupec s hashem e-mailu je poškozený a měl by se odstranit", "Opakované hashe jsou důkaz, ne poškození."),
            ("Smazat oba záznamy z každé dvojice", "Přišli byste o skutečné zákazníky; záznamy raději slučte nebo deduplikujte."),
        ],
        "explanation": "Unikátnost kontrolujte na úrovni entit, ne jen klíčů.",
    },
    "q_dg_003": {
        "stem": "Proč se k označení odlehlých hodnot často dává přednost pravidlu IQR před „průměr +/- 3 směrodatné odchylky“?",
        "options": [
            ("Kvartily jsou robustní; průměr a SD jsou samy nafouknuté právě hledanými odlehlými hodnotami", "Extrémní hodnoty táhnou průměr a rozšiřují SD, čímž se samy maskují."),
            ("Pravidlo IQR vždy označí méně bodů", "U zešikmených dat jich může označit mnohem víc."),
            ("Směrodatné odchylky nelze spočítat na zešikmených datech", "Spočítat je lze; jen mají menší vypovídací hodnotu."),
            ("Pravidlo IQR dokazuje, které body jsou chyby", "Žádné pravidlo chyby nedokazuje; odlehlé hodnoty vyžadují prošetření."),
        ],
        "explanation": "K detekci používejte robustní statistiky a před zásahem vše prošetřete.",
    },
    "q_dg_004": {
        "stem": "Tržby minulý měsíc klesly o 12 %. Co byste měli udělat **jako první**?",
        "options": [
            ("Ověřit, že pokles je skutečný (datový tok, změny definic, opožděná data)", "Mnoho „poklesů“ jsou problémy s daty; jejich vyloučení na začátku ušetří zbytečnou analýzu."),
            ("Sestavit model predikce odchodu", "Modelovat dřív, než změně rozumíte, je předčasné."),
            ("Předložit pokles správní radě s pravděpodobnými příčinami", "Bez důkazů byste předkládali dohady."),
            ("Porovnat pokles s tiskovými zprávami konkurence", "Vnější kontext může později pomoci; nejprve ověřte vlastní data."),
        ],
        "explanation": "Krok jedna analýzy příčin: ověřte signál.",
    },
    "q_dg_005": {
        "stem": "Segment A klesl o 60 % (z 10 tis. na 4 tis. EUR). Segment B klesl o 8 % (z 900 tis. na 828 tis. EUR). Který segment je důležitější pro vysvětlení celkového poklesu?",
        "options": [
            ("Segment B: ztratil 72 tis. EUR oproti 6 tis. EUR u A", "Příspěvek je o absolutní změně vůči celkové změně, ne o procentní změně."),
            ("Segment A, protože jeho procentní pokles je větší", "Malé základy dávají velká procenta s malým dopadem."),
            ("Oba stejně", "Jejich příspěvky se liší dvanáctinásobně."),
            ("Žádný; záleží jen na procentních změnách nad 50 %", "Takové pravidlo neexistuje."),
        ],
        "explanation": "Segmenty seřaďte podle příspěvku ke změně a pak se podívejte na míry.",
    },
    "q_dg_006": {
        "stem": "Marže % každé kategorie je meziročně beze změny, a přesto celková marže % klesla. Jaké je nejpravděpodobnější vysvětlení?",
        "options": [
            ("Prodejní mix se posunul k nízkomaržovým kategoriím", "Čistý efekt mixu: vážený průměr klesá, protože se změnily váhy."),
            ("Chyba v datech, protože celková marže se musí rovnat maržím kategorií", "Celková marže je vážený průměr; váhy se mohou měnit."),
            ("V každé kategorii vzrostly náklady", "Pak by klesly marže kategorií."),
            ("V každé kategorii vzrostly slevy", "To by také snížilo marže kategorií."),
        ],
        "explanation": "Oddělte efekty míry (změna uvnitř segmentu) od efektů mixu (změna vah).",
    },
    "q_dg_007": {
        "stem": "Lednová kohorta má šestiměsíční odchod 25 %; kohorta z minulého měsíce má „dosavadní odchod“ 8 %. Můžete usoudit, že se retence zlepšila?",
        "options": [
            ("Ne: nedávná kohorta měla na odchod teprve jeden měsíc", "Cenzorování zprava - porovnávejte kohorty při stejné délce vztahu."),
            ("Ano: 8 % je mnohem méně než 25 %", "Srovnání není srovnatelné."),
            ("Ano, pokud jsou kohorty podobně velké", "Velikost kohorty nerovné okno pozorování nevyřeší."),
            ("Ne, protože kohorty nelze nikdy porovnávat", "Lze, při stejné délce vztahu."),
        ],
        "explanation": "Retenční tabulky čtěte dolů po sloupcích délky vztahu.",
    },
    "q_dg_008": {
        "stem": "Trychtýř: 10 000 návštěv -> 2 000 registrací -> 1 200 aktivací -> 300 nákupů. Kde je největší (relativní) odpad mezi kroky?",
        "options": [
            ("Návštěva -> registrace (ztráta 80 %)", "Konverze kroků: 20 % (návštěva->registrace), 60 % (registrace->aktivace), 25 % (aktivace->nákup)."),
            ("Aktivace -> nákup", "Zde se ztratí 75 %, méně než 80 % v prvním kroku."),
            ("Registrace -> aktivace", "Zde se ztratí jen 40 %."),
            ("Všechny kroky ztrácejí stejný podíl", "Konverze kroků se liší."),
        ],
        "explanation": "Uvádějte konverzi kroků i kumulativní konverzi.",
    },
    "q_dg_009": {
        "stem": "Průzkum mezi současnými zákazníky zjistil, že 90 % miluje funkci X. Proč je to slabý důkaz, že funkce X podporuje retenci?",
        "options": [
            ("Zákazníci, kterým X nevyhovovala, už možná odešli, takže ve vzorku chybějí", "Zkreslení přeživších: vzorek je vyfiltrovaný podle výsledku."),
            ("Průzkumy nejsou nikdy platným důkazem", "Průzkumy mohou být užitečné; tento má problém s výběrem."),
            ("90 % je příliš vysoké, aby to bylo uvěřitelné", "Problémem není úroveň, ale vzorek."),
            ("Funkci X je nutné odstranit", "Takový závěr z toho neplyne."),
        ],
        "explanation": "Než uděláte závěry o faktorech retence, zahrňte i ty, kteří odešli (nebo porovnejte kohorty).",
    },
    "q_dg_010": {
        "stem": "Celkový odchod vzrostl z 25 % na 31 %, ale odchod v jednotlivých akvizičních kanálech je zhruba beze změny. Co to vysvětluje?",
        "options": [
            ("Vzrostl podíl zákazníků z kanálů s vysokým odchodem", "Efekt složení - typický znak Simpsonova paradoxu."),
            ("Chyba ve výpočtu, protože celkový odchod se musí rovnat průměru odchodu kanálů", "Celkový odchod je vážený průměr; váhy se posunuly."),
            ("Všechny kanály se zhoršily", "To odporuje tvrzení „v každém kanálu zhruba beze změny“."),
            ("Náhodný šum", "Posun o 6 bodů na tisících zákazníků je nepravděpodobně šum a mechanismus je jasný."),
        ],
        "explanation": "Vždy porovnávejte souhrnné trendy s trendy uvnitř segmentů.",
    },
    "q_dg_011": {
        "stem": "Zákazníci, kteří zakládají více tiketů podpory, více odcházejí. Která vysvětlení je nutné vyloučit, než usoudíte, že „tikety způsobují odchod“? (Vyberte všechny správné.)",
        "options": [
            ("Obrácená kauzalita: nespokojení zákazníci zakládají tikety a zároveň odcházejí", "Kauzální šipka může vést od nespokojenosti k tiketům."),
            ("Matoucí vliv problémů s produktem, které způsobují obojí", "Souvislost může vytvořit třetí proměnná."),
            ("Výběrové efekty v tom, kteří zákazníci jsou zaznamenáni", "Pokud se eviduje jen část tiketů, může být souvislost zkreslená."),
            ("Záporný korelační koeficient", "Zde je souvislost kladná; znaménko není alternativní vysvětlení."),
        ],
        "explanation": "Korelace může vzniknout z matoucích proměnných, obrácené kauzality, výběru nebo náhody.",
    },
    "q_dg_012": {
        "stem": "Dvě proměnné mají silný monotónní, ale zakřivený vztah a k tomu několik extrémních odlehlých hodnot. Která statistika souvislost nejlépe shrne?",
        "options": [
            ("Spearmanova pořadová korelace", "Je založena na pořadí, takže zachytí monotónní vztahy a odolá odlehlým hodnotám."),
            ("Pearsonova korelace", "Pearson měří lineární souvislost a je citlivý na odlehlé hodnoty."),
            ("Kovariance", "Kovariance závisí na jednotkách a je také citlivá na odlehlé hodnoty."),
            ("p-hodnota t-testu", "t-test porovnává průměry, ne sílu souvislosti."),
        ],
        "explanation": "Statistiku volte podle tvaru vztahu a kvality dat.",
    },
    "q_dg_013": {
        "stem": "A/B test dal p = 0,03. Která interpretace je správná?",
        "options": [
            ("Kdyby rozdíl ve skutečnosti neexistoval, výsledek alespoň takto extrémní by nastal asi ve 3 % případů", "To je definice p-hodnoty."),
            ("S pravděpodobností 97 % testovaná varianta funguje", "p-hodnota není pravděpodobnost, že hypotéza platí."),
            ("S pravděpodobností 3 % je výsledek dílem náhody", "Častá chybná interpretace; p-hodnota je podmíněná platností H0."),
            ("Efekt je velký a důležitý", "p-hodnoty nic neříkají o velikosti efektu ani o byznysové hodnotě."),
        ],
        "explanation": "Spolu s p-hodnotami uvádějte velikosti efektu a intervaly spolehlivosti.",
    },
    "q_dg_014": {
        "stem": "95% IS pro zlepšení konverze je [-0,2; +1,4] procentního bodu. Co byste měli usoudit?",
        "options": [
            ("Data jsou v souladu s nulovým efektem i se smysluplným kladným efektem; test je nepřesvědčivý", "IS zahrnuje 0, ale i hodnotná zlepšení - je potřeba víc dat nebo rozhodnutí za nejistoty."),
            ("Testovaná varianta nemá žádný efekt", "Absence důkazu není důkazem absence."),
            ("Testovaná varianta zvyšuje konverzi o 0,6 p. b.", "0,6 je bodový odhad; nejistota je velká."),
            ("Testovaná varianta konverzi zhoršuje", "Záporné hodnoty jsou možné, ale nejsou prokázané."),
        ],
        "explanation": "IS použijte k úvaze o věrohodných velikostech efektu a o rozhodnutích.",
    },
    "q_dg_015": {
        "stem": "Které postupy chrání A/B test před falešně pozitivními výsledky? (Vyberte všechny správné.)",
        "options": [
            ("Stanovit velikost vzorku a primární metriku před začátkem", "Předběžná registrace brání posouvání cílů."),
            ("Nezastavit test hned, jak poprvé platí p < 0,05", "Nakukování zvyšuje míru falešně pozitivních výsledků."),
            ("Korigovat mnoho porovnání segmentů nebo k nim přistupovat opatrně", "Vícenásobná porovnání činí náhodná zjištění pravděpodobnými."),
            ("Spustit test jen na uživatelích, kteří nejspíš konvertují", "To poškodí zobecnitelnost; falešně pozitivní výsledky to nesníží."),
        ],
        "explanation": "Návrh experimentu je stejně důležitý jako statistický test.",
    },
    "q_dg_016": {
        "stem": "Při 5 milionech uživatelů ukáže test statisticky významné zlepšení o 0,02 procentního bodu. Údržba změny stojí ročně 400 tis. EUR. Jaká je nejlepší reakce?",
        "options": [
            ("Před rozhodnutím posoudit, zda věrohodné zlepšení (IS) vytvoří hodnotu vyšší než 400 tis. EUR", "Statistická významnost není byznysová významnost; porovnejte hodnotu s náklady."),
            ("Okamžitě nasadit, protože p < 0,05", "Významnost říká, že efekt je pravděpodobně nenulový, ne že se vyplatí."),
            ("Výsledek zamítnout, protože efekt je malinký", "Malé efekty mohou být ve velkém měřítku hodnotné; spočítejte to."),
            ("Opakovat test, dokud nebude zlepšení větší", "Opakované testování kvůli žádoucí odpovědi je p-hacking."),
        ],
        "explanation": "Velikosti efektu převeďte na peníze a porovnejte s náklady a riziky.",
    },
    "q_dg_017": {
        "stem": "Proč by klouzavý průměr jako základna pro detekci anomálií měl používat jen *minulá* pozorování (např. `shift(1)` před `rolling`)?",
        "options": [
            ("Zahrnutí aktuální hodnoty dovolí anomálii nafouknout vlastní základnu a skrýt se", "Špička zvýší průměr i SD, se kterými se porovnává."),
            ("Pandas neumí centrovaná okna", "Umí (center=True); zde se jen nehodí."),
            ("Zrychlí to výpočet", "Rychlost není důvodem."),
            ("Okna jen z minulosti odstraní sezónnost", "Neodstraní; sezónnost je třeba ošetřit zvlášť."),
        ],
        "explanation": "Základny musí odrážet, co bylo známo před pozorováním.",
    },
    "q_dg_018": {
        "stem": "Klouzavé z-skóre za 28 dní označí každý státní svátek jako anomálii. Jaké je nejlepší zlepšení?",
        "options": [
            ("Použít základnu, která zohlední známou sezónnost a kalendářní události", "Očekávané vzorce mají být součástí základny, ne poplachy."),
            ("Zvýšit práh na |z| > 10", "To by skrylo i skutečné incidenty."),
            ("Svátky z dat natrvalo smazat", "Svátky nesou skutečnou informaci; raději je modelujte."),
            ("Přejít na okno 365 dní", "Dlouhé okno se pomalu přizpůsobuje a kalendářní efekty stále ignoruje."),
        ],
        "explanation": "Anomálie je odchylka od toho, co jste očekávali - takže modelujte, co očekáváte.",
    },
    "q_dg_019": {
        "stem": "Která věta nejlépe sděluje diagnostické zjištění?",
        "options": [
            ("„West Electronics vysvětluje více než celý pokles; vzorec je v souladu s výpadkem zásob, což ověřujeme na skladových datech.“", "Uvádí zjištění, hypotézu podloženou důkazy i další ověřovací krok."),
            ("„Pokles způsobil konkurent.“", "Kauzální tvrzení bez uvedených důkazů."),
            ("„Spustili jsme 14 dotazů a vytvořili 9 grafů.“", "Popisuje činnost, ne zjištění."),
            ("„Tržby klesly kvůli mnoha faktorům.“", "Vágní a nepoužitelné pro akci."),
        ],
        "explanation": "Začněte odpovědí, citujte důkazy, oddělte zjištění od hypotéz.",
    },
    "q_dg_020": {
        "stem": "V R platí `x <- c(10, 20, 30)`. Co vrátí `x[1]`?",
        "options": [
            ("10", "R indexuje od 1."),
            ("20", "To by bylo x[2] v R (nebo x[1] v Pythonu)."),
            ("Chybu", "x[1] je platné."),
            ("NULL", "Index 1 existuje."),
        ],
        "explanation": "Při převodu mezi Pythonem a R pamatujte na indexování od 1.",
    },
    "q_dg_021": {
        "stem": "`mean(df$satisfaction)` vrací `NA`. Jaká je nejpravděpodobnější příčina a oprava?",
        "options": [
            ("Sloupec obsahuje hodnoty NA; použijte mean(df$satisfaction, na.rm = TRUE) a uveďte, kolik hodnot bylo vyřazeno", "R šíří NA, pokud mu neřeknete, ať je odstraní."),
            ("Sloupec je překlepnutý; R vrací NA pro neznámé sloupce", "Neznámý sloupec vrátí NULL s varováním, ne NA."),
            ("R neumí spočítat průměr celých čísel", "Umí."),
            ("Převést sloupec na text", "Průměr vyžaduje čísla."),
        ],
        "explanation": "Na rozdíl od pandas R ve výchozím stavu chybějící hodnoty nepřeskakuje.",
    },
    "q_dg_022": {
        "stem": "Odchod vzrostl po zdražení (tarif Basic) i po posunu akvizice k Paid Social. Jaký je nejobhajitelnější další krok?",
        "options": [
            ("Odhadnout každý efekt zvlášť, např. porovnat Basic s ostatními tarify v každém kanálu před a po", "Stratifikace oddělí dvě současně působící vysvětlení."),
            ("Připsat nárůst zdražení, protože nastalo později", "Samotné načasování současné příčiny neoddělí."),
            ("Uvést, že každá z nich způsobila přesně polovinu nárůstu", "Libovolné rozdělení bez důkazů."),
            ("Obě ignorovat a vinit sezónnost", "Sezónnost je hypotéza k otestování, ne výchozí volba."),
        ],
        "explanation": "Když se vysvětlení časově překrývají, oddělte je stratifikací nebo experimenty.",
    },
}
