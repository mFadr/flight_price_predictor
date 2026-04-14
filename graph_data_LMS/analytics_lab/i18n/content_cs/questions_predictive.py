"""Czech text for the Predictive Analytics questions. Options are (text, why) in the original order."""

TOPICS = {
    "Prediction vs inference": "Predikce vs. inference",
    "Temporal splits": "Časové rozdělení dat",
    "Target leakage": "Únik cílové proměnné",
    "Regression metrics": "Metriky regrese",
    "R-squared": "R-squared",
    "Coefficients": "Koeficienty",
    "Precision vs recall": "Precision vs. recall",
    "Thresholds": "Prahy",
    "Imbalanced classes": "Nevyvážené třídy",
    "ROC vs PR AUC": "ROC vs. PR AUC",
    "Overfitting": "Přeučení",
    "Pipelines": "Pipeline",
    "Model selection": "Výběr modelu",
    "Forecast baselines": "Baseliny předpovědí",
    "Time-series validation": "Validace časových řad",
    "Forecast uncertainty": "Nejistota předpovědí",
    "Leakage detection": "Odhalení úniku",
    "Drift": "Drift",
    "Feature importance": "Důležitost příznaků",
    "Responsible use": "Odpovědné použití",
    "Calibration": "Kalibrace",
}

QUESTIONS = {
    "q_pr_001": {
        "stem": "Která otázka je primárně **predikční** úlohou, a ne úlohou inference?",
        "options": [
            ("Kteří zákazníci nejspíš příští měsíc zruší předplatné?", "Cílem jsou přesné předpovědi pro jednotlivé případy."),
            ("Způsobuje zdražení, že zákazníci ruší předplatné?", "Kauzální otázka / otázka inference o efektu ceny."),
            ("Jak silně souvisí délka vztahu s útratou po zohlednění tarifu?", "Odhad souvislosti je inference."),
            ("Je rozdíl v odchodu mezi dvěma tarify statisticky významný?", "Testování hypotéz je inference."),
        ],
        "explanation": "Predikce optimalizuje přesnost mimo vzorek; inference vysvětluje vztahy.",
    },
    "q_pr_002": {
        "stem": "Nové zákazníky budete skórovat každý měsíc. Proč by testovací množina měla obsahovat nejnovější registrace, a ne náhodných 20 %?",
        "options": [
            ("Napodobuje nasazení, kdy model předpovídá zákazníky přicházející po trénování, a odhalí drift", "Časové rozdělení testuje výkon na budoucnosti včetně změn v populaci."),
            ("scikit-learn nepodporuje náhodné rozdělení", "Podporuje; jen se sem nehodí."),
            ("Nové zákazníky je vždy snazší předpovídat", "Kvůli driftu často naopak."),
            ("Zrychlí to trénování", "Rychlost není důvodem."),
        ],
        "explanation": "Vyhodnocujte model tak, jak bude používán.",
    },
    "q_pr_003": {
        "stem": "Který příznak je únikem cílové proměnné při predikci odchodu na konci prvního měsíce zákazníka?",
        "options": [
            ("Důvod z odchodového dotazníku zaznamenaný při zrušení", "Existuje až po odchodu (a kvůli němu)."),
            ("Počet přihlášení v prvním měsíci", "Je znám v okamžiku predikce."),
            ("Tarif zvolený při registraci", "Je znám při registraci."),
            ("Akviziční zdroj", "Je znám při registraci."),
        ],
        "explanation": "U každého příznaku se ptejte: věděl bych to v okamžiku predikce?",
    },
    "q_pr_004": {
        "stem": "Podcenění poptávky o 1 000 kusů je desetkrát horší než deset chyb po 100 kusech, protože velké výpadky zastaví výrobu. Která metrika to nejlépe vystihuje?",
        "options": [
            ("RMSE, protože umocnění na druhou nepoměrně penalizuje velké chyby", "RMSE váží velké chyby více než MAE."),
            ("MAE, protože se nejsnáze vysvětluje", "MAE bere jednu chybu o 1 000 kusů stejně jako deset chyb o 100 kusech."),
            ("R-squared, protože nezávisí na měřítku", "R-squared nevyjadřuje nákladovou strukturu chyb."),
            ("Accuracy", "Accuracy je klasifikační metrika."),
        ],
        "explanation": "Volte metriky, které odrážejí byznysovou cenu chyb.",
    },
    "q_pr_005": {
        "stem": "Testovací R-squared modelu je -0,15. Co to znamená?",
        "options": [
            ("Model předpovídá hůř než prosté použití průměru cílové proměnné", "Záporné R-squared na testovacích datech znamená, že SSE převyšuje rozptyl kolem průměru."),
            ("Chybu ve výpočtu, protože R-squared nemůže být záporné", "Na odložených datech záporné být může."),
            ("15 % rozptylu je vysvětleno opačným směrem", "Takhle se R-squared neinterpretuje."),
            ("Model se přeučuje méně, než se čekalo", "Signalizuje špatnou generalizaci."),
        ],
        "explanation": "Na odložených datech vždy porovnávejte s baselinem.",
    },
    "q_pr_006": {
        "stem": "V log-log modelu tržeb na výdajích je koeficient 0,75. Jaká je správná interpretace?",
        "options": [
            ("Zvýšení výdajů o 1 % souvisí se zvýšením tržeb přibližně o 0,75 % (klesající výnosy)", "Koeficienty log-log modelu jsou elasticity."),
            ("Každé euro výdajů navíc vrátí 0,75 eura", "To by byl koeficient na lineární škále."),
            ("Výdaje způsobují 75 % tržeb", "Není to ani kauzalita, ani podíl."),
            ("Tržby rostou rychleji než výdaje", "Elasticita pod 1 znamená pomalejší růst."),
        ],
        "explanation": "Transformace mění způsob čtení koeficientů.",
    },
    "q_pr_007": {
        "stem": "Model podvodů označí 200 transakcí; 150 z nich jsou podvody. Celkem bylo 600 podvodů. Jaké jsou precision a recall?",
        "options": [
            ("Precision 75 %, recall 25 %", "Precision = 150/200; recall = 150/600."),
            ("Precision 25 %, recall 75 %", "Obráceně."),
            ("Precision 75 %, recall 75 %", "Recall má ve jmenovateli všech 600 skutečných podvodů."),
            ("Precision 33 %, recall 25 %", "Precision je TP / označené = 150/200."),
        ],
        "explanation": "Precision = TP/(TP+FP); recall = TP/(TP+FN).",
    },
    "q_pr_008": {
        "stem": "Retenční hovor stojí 10 EUR a zabrání odchodu u 25 % skutečně odcházejících, z nichž každý má hodnotu 400 EUR. Nad jakou předpovězenou pravděpodobností odchodu se vyplatí volat (bez dalších efektů)?",
        "options": [
            ("0.10", "Očekávaný přínos p x 0,25 x 400 = 100p musí přesáhnout 10, tedy p > 0,10."),
            ("0.50", "Výchozí práh ignoruje strukturu nákladů a přínosů."),
            ("0.25", "To je úspěšnost hovorů, ne pravděpodobnost bodu zvratu."),
            ("0.04", "To by ignorovalo 25% úspěšnost."),
        ],
        "explanation": "Prahy odvozujte z nákladů a přínosů, ne z konvence.",
    },
    "q_pr_009": {
        "stem": "Pozitivních je jen 2 % případů. Model hlásí přesnost (accuracy) 98 %. Jaký je nejdůležitější další krok?",
        "options": [
            ("Zkontrolovat recall, precision a PR-AUC; 98 % lze dosáhnout předpovídáním samých negativních", "Při silné nevyváženosti accuracy nic nevypovídá."),
            ("Nasadit, protože 98 % je výborné", "Nemusí odhalit vůbec žádné pozitivní."),
            ("Zvětšit testovací množinu na 50 % dat", "Velikost problém s metrikou nevyřeší."),
            ("Přejít na R-squared", "R-squared je pro regresi."),
        ],
        "explanation": "Používejte metriky zaměřené na menšinovou třídu.",
    },
    "q_pr_010": {
        "stem": "Při podílu pozitivních 3 % má model ROC-AUC 0,85 a PR-AUC 0,20. Jak číst PR-AUC?",
        "options": [
            ("Asi 7x lepší než náhoda (baseline = 0,03), ale většina označených případů budou stále falešně pozitivní", "Náhodný baseline PR-AUC se rovná podílu pozitivních."),
            ("Horší než náhoda, protože je pod 0,5", "0,5 je baseline pro ROC, ne pro PR."),
            ("Odporuje ROC-AUC, takže jedna je špatně spočítaná", "Obě mohou být správně; zdůrazňují různé věci."),
            ("Nepodstatné; záleží jen na ROC-AUC", "Při nevyváženosti je PR-AUC často informativnější."),
        ],
        "explanation": "Znejte baseline každé metriky.",
    },
    "q_pr_011": {
        "stem": "Trénovací AUC = 0,99, AUC z křížové validace = 0,68. Jaká je diagnóza a rozumná náprava?",
        "options": [
            ("Přeučení; regularizovat (např. omezit hloubku stromu, min_samples_leaf) nebo použít ensemble", "Velký rozdíl mezi trénovacím a validačním skóre signalizuje vysoký rozptyl."),
            ("Podučení; přidat složitější příznaky", "Podučení se projeví i slabým trénovacím výkonem."),
            ("Únik dat ve validačních foldech", "Únik obvykle validační skóre zvyšuje, ne snižuje."),
            ("Nic; 0,68 je dost blízko 0,99", "Rozdíl je velký."),
        ],
        "explanation": "Porovnáním trénovacího a validačního skóre diagnostikujete vychýlení vs. rozptyl.",
    },
    "q_pr_012": {
        "stem": "Proč by StandardScaler měl být uvnitř Pipeline předané do cross_val_score, a ne nafitovaný předem na všech datech?",
        "options": [
            ("Aby se scaler fitoval jen na každém trénovacím foldu a do něj neunikly informace z validačních foldů", "Předzpracování se musí učit uvnitř foldů."),
            ("Pipeline zrychlují škálování", "O rychlost nejde."),
            ("cross_val_score nepřijme škálovaná data", "Přijme; ale předchozí škálování propouští informace."),
            ("Škálování není potřeba u žádného modelu", "Záleží na něm u modelů založených na vzdálenosti a gradientu."),
        ],
        "explanation": "Každá naučená transformace patří do pipeline.",
    },
    "q_pr_013": {
        "stem": "Náhodný les má CV AUC 0,741 +/- 0,012 a logistická regrese 0,736 +/- 0,011. Co je lepší výchozí volba?",
        "options": [
            ("Logistická regrese: rozdíl je v rámci šumu a snáze se vysvětluje i udržuje", "Když je výkon statisticky nerozlišitelný, dejte přednost jednoduchosti."),
            ("Náhodný les, protože 0,741 > 0,736", "Rozdíl je mnohem menší než kolísání mezi foldy."),
            ("Ani jeden; AUC pod 0,8 je k ničemu", "Užitečnost závisí na baselinu a byznysové hodnotě."),
            ("Zprůměrovat jejich predikce bez testování", "Ensemble může pomoci, ale musí se ověřit."),
        ],
        "explanation": "Zvažte nejistotu, interpretovatelnost a náklady na údržbu.",
    },
    "q_pr_014": {
        "stem": "Denní poptávka je každý víkend nízká. S jakým baselinem by se měl porovnat nový předpovědní model?",
        "options": [
            ("Sezónně naivní: každý den se rovná stejnému dni v týdnu minulý týden", "Zachytí týdenní sezónnost s nulovými náklady."),
            ("Naivní: každý den se rovná včerejšku", "Pondělí by se předpovídalo z neděle - slabý, nefér baseline."),
            ("Celkový historický průměr", "Ignoruje sezónnost i aktuální úroveň."),
            ("U časových řad baseline není potřeba", "Baseliny jsou nezbytné."),
        ],
        "explanation": "Zvolte nejsilnější triviální baseline, ne ten nejslabší.",
    },
    "q_pr_015": {
        "stem": "Jaký přístup k vyhodnocení se hodí pro týdenní předpověď prodejů?",
        "options": [
            ("Vyhodnocení s klouzavým počátkem: opakovaně trénovat na datech do data uzávěrky a testovat na následujících týdnech", "Respektuje časové pořadí a průměruje přes několik období."),
            ("Pětinásobná křížová validace s promícháním", "Promíchání trénuje na budoucnosti."),
            ("Vyhodnotit na trénovacích datech", "Chyba uvnitř vzorku je optimistická."),
            ("Leave-one-out s náhodným pořadím", "Stále propouští informace z budoucnosti."),
        ],
        "explanation": "Nikdy nedovolte modelu při vyhodnocení vidět budoucnost.",
    },
    "q_pr_016": {
        "stem": "Pojistnou zásobu skladu nastavujete podle předpovědi poptávky. Co byste měli kromě bodové předpovědi sdělit?",
        "options": [
            ("Predikční interval nebo horní kvantil, protože výpadky zásob závisejí na dnech s vysokou poptávkou", "Rozhodnutí o zásobách závisí na rozdělení, ne jen na průměru."),
            ("Jen bodovou předpověď, zaokrouhlenou", "Ignoruje riziko."),
            ("Trénovací R-squared modelu", "Pro rozhodnutí nepodstatné."),
            ("Počet parametrů modelu", "Pro rozhodnutí nepodstatné."),
        ],
        "explanation": "Rozhodnutí závisí na nejistotě; sdělujte ji.",
    },
    "q_pr_017": {
        "stem": "Model odchodu má testovací AUC 0,995 a jeden příznak tvoří téměř celou permutační důležitost. Jaké je nejpravděpodobnější vysvětlení?",
        "options": [
            ("Tento příznak propouští cílovou proměnnou (je znám až po výsledku nebo kvůli němu)", "Téměř dokonalé skóre s dominantním příznakem je klasický znak úniku."),
            ("Model je mimořádně dobrý a měl by se nasadit", "Skutečný odchod je zřídka takto předvídatelný."),
            ("Permutační důležitost je nespolehlivá", "Zde naopak problém odhaluje."),
            ("Testovací množina je příliš velká", "Velikost nafouknuté AUC nezpůsobí."),
        ],
        "explanation": "Nevěrohodně dobré výsledky považujte za chyby, dokud se neprokáže opak.",
    },
    "q_pr_018": {
        "stem": "Po nasazení se podíl zákazníků z Paid Social zdvojnásobí. O jaký typ driftu jde a co byste měli sledovat?",
        "options": [
            ("Drift dat (kovariát); sledovat rozdělení vstupů a skutečný výkon, jakmile dorazí štítky", "Změnilo se rozdělení vstupů; výkon se může, ale nemusí zhoršit."),
            ("Drift konceptu; okamžitě přetrénovat", "Drift konceptu je změna vztahu mezi vstupy a výsledkem."),
            ("Únik štítků", "Nesouvisí."),
            ("Žádný drift, protože příznaky jsou stejné", "Změnilo se rozdělení."),
        ],
        "explanation": "Sledujte vstupy, predikce i výsledky.",
    },
    "q_pr_019": {
        "stem": "Permutační důležitost ukazuje, že „logins“ je nejdůležitější příznak odchodu. Co můžete usoudit?",
        "options": [
            ("Model se při predikcích silně opírá o přihlášení", "Důležitost popisuje chování modelu."),
            ("Zvýšení počtu přihlášení sníží odchod", "Důležitost není kauzální důkaz."),
            ("Ostatní příznaky jsou pro odchod nepodstatné", "Korelované příznaky si mohou důležitost dělit nebo ji maskovat."),
            ("Model je férový", "Důležitost o férovosti nic neříká."),
        ],
        "explanation": "Bez dalších důkazů z důležitosti příznaků nedělejte kauzální doporučení.",
    },
    "q_pr_020": {
        "stem": "Které kroky patří k odpovědnému nasazení modelu odchodu? (Vyberte všechny správné.)",
        "options": [
            ("Zkontrolovat výkon zvlášť pro klíčové skupiny zákazníků", "Souhrnné metriky mohou skrýt slabý výkon v podskupinách."),
            ("Zdokumentovat zamýšlené použití, data, omezení a monitoring v kartě modelu", "Transparentnost podporuje správné použití."),
            ("Definovat spouštěče přetrénování podle sledovaného výkonu", "Modely stárnou."),
            ("Skrýt omezení modelu, aby mu uživatelé důvěřovali", "Uživatelé omezení potřebují znát, aby se dobře rozhodovali."),
        ],
        "explanation": "Odpovědné ML zahrnuje vyhodnocení, dokumentaci, monitoring a lidský dohled.",
    },
    "q_pr_021": {
        "stem": "Zákazníci se skórem pravděpodobnosti odchodu 0,30 ve skutečnosti odcházejí v 55 % případů. V čem je problém?",
        "options": [
            ("Model je špatně kalibrovaný: při tomto skóre riziko podceňuje", "Kalibrace porovnává předpovězené pravděpodobnosti s pozorovanými četnostmi."),
            ("Model má nízké AUC", "AUC měří pořadí a může být vysoké, i když jsou pravděpodobnosti špatně kalibrované."),
            ("Nic; pravděpodobnosti nemusí odpovídat výsledkům", "Prahy založené na nákladech spoléhají na kalibrované pravděpodobnosti."),
            ("Práh je příliš vysoký", "Volba prahu je od kalibrace oddělená."),
        ],
        "explanation": "Když pravděpodobnosti vstupují do rozhodnutí, kontrolujte kalibraci (křivky spolehlivosti).",
    },
}
