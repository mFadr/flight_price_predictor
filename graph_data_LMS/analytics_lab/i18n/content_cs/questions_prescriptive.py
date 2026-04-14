"""Czech text for the Prescriptive Analytics questions. Options are (text, why) in the original order."""

TOPICS = {
    "Model components": "Složky modelu",
    "Binding constraints": "Vázající omezení",
    "linprog conventions": "Konvence linprog",
    "Assignment": "Přiřazovací úlohy",
    "Integer decisions": "Celočíselná rozhodnutí",
    "Hard vs soft constraints": "Tvrdá vs. měkká omezení",
    "EOQ": "EOQ",
    "Safety stock": "Pojistná zásoba",
    "Pricing": "Cenotvorba",
    "Monte Carlo": "Monte Carlo",
    "Risk measures": "Míry rizika",
    "Simulation practice": "Praxe simulací",
    "Shadow prices": "Stínové ceny",
    "Sensitivity": "Citlivost",
    "Recommendations": "Doporučení",
    "Trade-offs": "Kompromisy",
}

QUESTIONS = {
    "q_ps_001": {
        "stem": "V modelu, který volí, kolik kusů každého produktu vyrobit, aby se maximalizoval zisk v rámci strojových hodin, co jsou rozhodovací proměnné?",
        "options": [
            ("Počet kusů každého produktu", "To jsou veličiny, které rozhodovatel ovládá."),
            ("Celkový zisk", "Zisk je účelová funkce."),
            ("Dostupné strojové hodiny", "Kapacita je parametr omezení."),
            ("Zisk na kus", "Pevný vstup (koeficient)."),
        ],
        "explanation": "Proměnné = co volíte; účelová funkce = co optimalizujete; omezení = co vás limituje.",
    },
    "q_ps_002": {
        "stem": "V optimu má Balení 40 nevyužitých hodin a Testování 0. Manažer nabízí 10 hodin Balení navíc. Co se stane s optimálním ziskem?",
        "options": [
            ("Nic: Balení není vázající, takže hodiny navíc mají nulovou hodnotu", "Účelovou funkci limitují jen vázající omezení."),
            ("Vzroste úměrně hodinám navíc", "Balení už má rezervu."),
            ("Klesne kvůli dodatečným nákladům", "Jen pokud hodiny stojí peníze; hodnota hodin v modelu je nulová."),
            ("Úloha se stane nepřípustnou", "Uvolnění omezení nemůže přípustnou úlohu učinit nepřípustnou."),
        ],
        "explanation": "Investujte do uvolnění vázajících omezení, ne těch s rezervou.",
    },
    "q_ps_003": {
        "stem": "Zavoláte `linprog(c=profit, ...)` v naději, že maximalizujete zisk. Co se ve skutečnosti stane?",
        "options": [
            ("linprog minimalizuje, takže najde přípustný plán s nejnižším ziskem", "Pro maximalizaci předejte -profit a výsledek znegujte."),
            ("Při kladných koeficientech automaticky maximalizuje", "Takové chování neexistuje."),
            ("Vyhodí chybu", "Proběhne potichu - v tom je nebezpečí."),
            ("Vrátí v obou případech stejnou odpověď", "Minimalizace a maximalizace dávají různá řešení."),
        ],
        "explanation": "Znejte konvence svého řešiče.",
    },
    "q_ps_004": {
        "stem": "Proč může hladové pravidlo („každý technik si postupně vezme nejlevnější zbývající zakázku“) u přiřazovací úlohy selhat?",
        "options": [
            ("Dřívější volby mohou zablokovat levnější kombinace později, takže součet není minimální", "Hladové volby jsou lokálně, ale ne globálně optimální."),
            ("Hladová pravidla nedokážou vytvořit platné přiřazení", "Vytvoří platná, ale často neoptimální přiřazení."),
            ("Přiřazovací úlohy nemají přesnou metodu řešení", "Maďarská metoda je řeší přesně."),
            ("Hladová pravidla vždy najdou optimum", "Protipříklady se snadno sestrojí."),
        ],
        "explanation": "Pokud jsou k dispozici, používejte přesné metody (linear_sum_assignment).",
    },
    "q_ps_005": {
        "stem": "LP říká „otevřete 0,4 nového skladu“. Jaká je správná reakce při modelování?",
        "options": [
            ("Udělat z rozhodnutí otevřít/neotevřít binární proměnnou a vyřešit smíšený celočíselný program", "Rozhodnutí ano/ne vyžadují celočíselnost."),
            ("Zaokrouhlit na 0, protože je to pod 0,5", "Zaokrouhlení může být neoptimální nebo nepřípustné."),
            ("Pro jistotu zaokrouhlit na 1", "Může být daleko od optima."),
            ("Otevřít sklad na 40 % kapacity", "Zlomek nepředstavuje skutečné rozhodnutí."),
        ],
        "explanation": "Binární proměnné modelují diskrétní volby a fixní náklady.",
    },
    "q_ps_006": {
        "stem": "Model rozvrhování je po přidání tvrdého omezení „nikdo nepracuje dva víkendy po sobě“ nepřípustný. Jaký je rozumný postup?",
        "options": [
            ("Zjistit, zda jde o preferenci; pokud ano, modelovat ji jako penalizaci v účelové funkci", "Měkká omezení se vyvažují s ostatními cíli, místo aby vynutila nepřípustnost."),
            ("Smazat omezení pokrytí", "Pokrytí může být zákonným nebo servisním požadavkem."),
            ("Oznámit, že žádný rozvrh neexistuje", "Pro tvrdou verzi pravda, ale neužitečné, pokud je pravidlo vyjednatelné."),
            ("Použít náhodné rozvrhy", "Vzdává se optimalizace."),
        ],
        "explanation": "Se zainteresovanými rozlište nezbytnosti od přání.",
    },
    "q_ps_007": {
        "stem": "Roční poptávka se zčtyřnásobí, zatímco náklady na objednávku a držení zůstanou stejné. Co se stane s EOQ?",
        "options": [
            ("Zdvojnásobí se", "EOQ = sqrt(2DS/H); sqrt(4) = 2."),
            ("Zčtyřnásobí se", "EOQ roste s odmocninou poptávky."),
            ("Zůstane stejné", "Poptávka je ve vzorci."),
            ("Klesne na polovinu", "Vyšší poptávka EOQ zvyšuje."),
        ],
        "explanation": "EOQ roste s odmocninou poptávky.",
    },
    "q_ps_008": {
        "stem": "Dodací lhůta dodavatele se prodlouží ze 4 na 16 dní (variabilita denní poptávky beze změny). Jak se podle z * sd * sqrt(L) změní pojistná zásoba?",
        "options": [
            ("Zdvojnásobí se", "sqrt(16)/sqrt(4) = 2."),
            ("Zčtyřnásobí se", "Pojistná zásoba roste s sqrt(L), ne s L."),
            ("Nezmění se", "Dodací lhůta přímo ovlivňuje vystavení variabilitě poptávky."),
            ("Klesne", "Delší dodací lhůty vyžadují větší rezervu."),
        ],
        "explanation": "Delší a proměnlivější dodací lhůty vyžadují větší pojistnou zásobu.",
    },
    "q_ps_009": {
        "stem": "Cena 20 EUR, jednotkové náklady 15 EUR, elasticita -2. 10% sleva zvýší objem přibližně o 23 %. Co se stane se ziskem?",
        "options": [
            ("Klesne: marže na kus spadne z 5 na 3, takže zisk klesne z 5Q na přibližně 3,7Q", "1,23Q x 3 = 3,69Q < 5Q."),
            ("Vzroste, protože objem vzroste víc než sleva", "Při tenkých maržích ztráta marže převáží dodatečný objem."),
            ("Nezmění se", "Změní se podstatně."),
            ("Bez cen konkurence ho nelze spočítat", "Se zadanou elasticitou ho lze odhadnout."),
        ],
        "explanation": "Slevy posuzujte podle zisku, ne podle tržeb nebo objemu.",
    },
    "q_ps_010": {
        "stem": "Proč výsledek investice simulovat, místo abyste spočítali zisk při průměru každého vstupu?",
        "options": [
            ("Výsledky závisejí na vstupech nelineárně (stropy, podlahy, součiny), takže průměrný výsledek se liší od výsledku při průměrných vstupech, a simulace odhalí riziko", "Simulace zachytí celé rozdělení."),
            ("Simulace vždy dá vyšší zisk", "Může dát nižší očekávaný zisk."),
            ("U nejistých vstupů nelze průměry spočítat", "Lze; jen skrývají riziko."),
            ("Simulace odstraní nejistotu", "Nejistotu vyčíslí, neodstraní ji."),
        ],
        "explanation": "Modelujte rozdělení výsledků, ne jen jediný odhad.",
    },
    "q_ps_011": {
        "stem": "Projekt A: očekávaný zisk 100 tis. EUR, P(ztráta) 2 %. Projekt B: očekávaný zisk 110 tis. EUR, P(ztráta) 25 %. Rizikově averzní správní rada dává přednost A. Je to iracionální?",
        "options": [
            ("Ne: volba mírně nižšího průměru za mnohem nižší riziko odráží legitimní ochotu riskovat", "Rozhodnutí závisí na preferencích ohledně rizika, ne jen na očekávané hodnotě."),
            ("Ano: vždy volte nejvyšší očekávanou hodnotu", "To platí jen pro rizikově neutrální rozhodovatele."),
            ("Ano: P(ztráta) je nepodstatná", "Ztráty mohou mít závažné důsledky (úvěrové podmínky, pracovní místa)."),
            ("Ne, protože očekávaná hodnota B je chybná", "Nic nenaznačuje chybu ve výpočtu."),
        ],
        "explanation": "Ochotu riskovat uvádějte v doporučeních výslovně.",
    },
    "q_ps_012": {
        "stem": "Které postupy činí analýzu Monte Carlo důvěryhodnou? (Vyberte všechny správné.)",
        "options": [
            ("Nastavit semínko generátoru náhodných čísel, aby byly výsledky reprodukovatelné", "Reprodukovatelnost umožňuje revizi."),
            ("Zdůvodnit vstupní rozdělení daty nebo expertním úsudkem", "Výsledky jsou jen tak dobré jako vstupní předpoklady."),
            ("Otestovat citlivost na volbu rozdělení", "Ukáže, jak robustní je závěr."),
            ("Kvůli rychlosti použít co nejméně scénářů", "Příliš málo scénářů dává zašuměné odhady; vektorizovaný kód zvládne 100 tis. levně."),
        ],
        "explanation": "Vstupy simulace berte jako předpoklady, které je třeba dokumentovat a testovat.",
    },
    "q_ps_013": {
        "stem": "Stínová cena rozpočtového omezení je 0,22. Co to znamená?",
        "options": [
            ("Každé další euro rozpočtu zvýší optimální zisk přibližně o 0,22 EUR, v rámci platného rozsahu", "Stínové ceny jsou mezní hodnoty uvolnění omezení."),
            ("22 % rozpočtu je nevyužito", "Stínová cena není rezerva."),
            ("Rozpočet by se měl snížit o 22 %", "Nic takového z toho neplyne."),
            ("Zisk tvoří 22 % rozpočtu", "To je průměrný výnos, ne mezní."),
        ],
        "explanation": "Stínové ceny oceňují vázající omezení na okraji.",
    },
    "q_ps_014": {
        "stem": "Co ukazuje tornádový graf?",
        "options": [
            ("O kolik se změní výsledek, když se postupně mění jednotlivé vstupy, seřazeno podle dopadu", "Jednorozměrná citlivost seřazená podle rozpětí."),
            ("Pravděpodobnostní rozdělení zisku", "To je histogram ze simulace."),
            ("Korelace mezi vstupy", "V tornádovém grafu se neukazují."),
            ("Optimální rozhodnutí v každém scénáři", "To je scénářová analýza."),
        ],
        "explanation": "Tornádové grafy zaměří pozornost na nejdůležitější předpoklady.",
    },
    "q_ps_015": {
        "stem": "Které prvky patří do preskriptivního doporučení pro vedení? (Vyberte všechny správné.)",
        "options": [
            ("Doporučené rozhodnutí srozumitelně a v číslech", "Začněte akcí."),
            ("Klíčové předpoklady a omezení, která limitují výsledek", "Vedení potřebuje vědět, co odpověď určuje."),
            ("Podmínky, za kterých by se doporučení změnilo", "Prahy z citlivostní analýzy dělají radu robustní."),
            ("Kompletní log řešiče", "Technické detaily patří nanejvýš do přílohy."),
        ],
        "explanation": "Doporučení je rozhodnutí plus jeho předpoklady, limity a podmínky změny.",
    },
    "q_ps_016": {
        "stem": "Vedení chce maximalizovat zisk a zároveň udržet nízké riziko. Který přístup kompromis zviditelní?",
        "options": [
            ("Vyřešit model znovu pro několik limitů rizika a ukázat zisk vs. riziko (efektivní hranici)", "Umožní rozhodovatelům zvolit kompromis vědomě."),
            ("Vybrat řešení s nejvyšším ziskem a riziko zmínit později", "Skrývá kompromis."),
            ("Zprůměrovat řešení s maximálním ziskem a minimálním rizikem", "Zprůměrovaná rozhodnutí mohou být nepřípustná nebo dominovaná."),
            ("Riziko ignorovat, protože je subjektivní", "I subjektivní riziko lze vyčíslit odsouhlasenými skóre."),
        ],
        "explanation": "Kompromisy mezi více cíli zviditelněte, místo abyste je pohřbili.",
    },
}
