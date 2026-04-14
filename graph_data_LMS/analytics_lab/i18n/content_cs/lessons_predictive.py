"""Czech text for the Predictive Analytics lessons."""

LESSONS = {
    "pr1": {
        "title": "Formulace predikčních úloh: cíle, rozdělení dat, základní modely a únik informací",
        "objectives": [
            "Odlišit predikci od inference.",
            "Definovat predikovanou veličinu, okamžik predikce a rozhodnutí, které podporuje.",
            "Správně rozdělit data na trénovací/validační/testovací, včetně časového rozdělení.",
            "Sestavit základní model (baseline) a rozpoznat únik cílové proměnné a časový únik.",
        ],
        "concept": """
**Predikce vs. inference.** *Inference* se ptá, jak a proč spolu proměnné souvisejí (souvisí cena s odchodem po zohlednění tarifu?). *Predikce* se ptá, jak přesně umíme předpovědět výsledek pro nové případy. Model může dobře předpovídat, aniž by byl kauzálně interpretovatelný - a naopak.

**Před modelováním úlohu formulujte:**

| Otázka | Příklad (odchod v CloudNest) |
|---|---|
| Podporované rozhodnutí | Které nové zákazníky má Customer Success ve 2. měsíci obvolat? |
| Cíl | `churned_6m` = zrušení do 182 dní od registrace |
| Okamžik predikce | Konec prvního měsíce po registraci |
| Povolené příznaky | Jen informace dostupné v okamžiku predikce |
| Cena chyb | Přehlédnutý odcházející = ztracené tržby; zbytečný hovor = ~15 EUR |

**Rozdělení dat.** *Trénovací* množina k fitování, *validační* k výběru modelů a hyperparametrů, *testovací* k jednorázovému odhadu finálního výkonu. Když jsou řádky seřazené v čase a budete předpovídat budoucnost, dělte podle **času** (trénujte na starších registracích, testujte na novějších). Náhodné rozdělení nechá model učit se z budoucnosti.

**Základní modely.** Vždy porovnávejte s triviálním modelem: nejčastější třída (klasifikace), průměr trénovacích dat (regrese) nebo poslední hodnota / stejné období minulý týden (předpovědi). Model je užitečný jen tehdy, když baseline překoná o rozdíl, na kterém záleží.

**Únik informací (leakage)** je informace v trénovacích datech, která v okamžiku predikce nebude k dispozici:

* *Únik cílové proměnné* - příznaky způsobené cílem (`cancellation_reason` se vyplní až po zrušení).
* *Časový únik* - příznaky spočítané z budoucích dat (např. „všechny tikety zákazníka“ k 1. měsíci).
* *Kontaminace trénovacích a testovacích dat* - fitování škálování/kódování na všech datech před rozdělením.

Podezřele vysoká přesnost je poplach kvůli úniku, ne důvod k oslavě.
""",
        "business_context": """
Tým Customer Success v CloudNest zvládne obvolat asi 30 % nových zákazníků. Chce skóre rizika odchodu na konci prvního měsíce každého zákazníka. Před jakýmkoli modelováním musíte definovat cíl, rozdělení dat a baseline, který musí model překonat.
""",
        "worked_example": {"explanation": """
* V testovacím období je odchod vyšší (posunul se akviziční mix) - časové rozdělení odhalí tento **posun rozdělení**; náhodné rozdělení by ho skrylo.
* Baseline s nejčastější třídou má přesnost ~68 %, a přesto je pro byznys k ničemu: přesnost je špatná metrika, když jsou třídy nevyvážené a záleží na menšinové třídě.
* `cancellation_reason` chybí právě tehdy, když zákazník neodešel: dokonale kóduje cíl a musí se vyřadit.
"""},
        "summary": [
            "Nejprve definujte rozhodnutí, cíl, okamžik predikce a povolené příznaky.",
            "Při předpovídání budoucnosti dělte data podle času; testovací množinu použijte jednou.",
            "Každý model musí překonat jednoduchý baseline v metrice, na které záleží.",
            "Únik informací vede ke skvělým offline skóre a k nepoužitelným modelům v provozu.",
        ],
        "common_mistakes": [
            "Náhodné rozdělení u časově uspořádaných úloh.",
            "Použití přesnosti u nevyvážených tříd.",
            "Zahrnutí polí vzniklých až po výsledku mezi příznaky.",
        ],
        "revision": "Vypište všechny sloupce v churn_features a označte, kdy se každý stává známým.",
    },
    "pr2": {
        "title": "Regresní modely a metriky chyb",
        "objectives": [
            "Nafitovat lineární regresi a interpretovat koeficienty.",
            "Vyhodnotit model pomocí MAE, RMSE a R-squared na odložených datech.",
            "Zvolit metriku odpovídající byznysové ceně chyb.",
            "Diagnostikovat nelinearitu a použít transformace.",
        ],
        "concept": """
**Lineární regrese** modeluje y = b0 + b1*x1 + ... + e a volí koeficienty minimalizující čtvercovou chybu. b1 je očekávaná změna y při změně x1 o jednotku *při konstantních ostatních příznacích* - jde o tvrzení o souvislosti, ne o kauzalitě, pokud data nepocházejí z experimentu.

**Metriky (vždy na odložených datech):**

| Metrika | Vzorec | Kdy použít |
|---|---|---|
| MAE | mean(abs(y - yhat)) | chyby stojí úměrně; snadno se vysvětlí („v průměru vedle o 3 tis. EUR“) |
| RMSE | sqrt(mean((y - yhat)^2)) | velké chyby jsou nepoměrně horší |
| R-squared | 1 - SSE/SST | podíl vysvětleného rozptylu oproti předpovědi průměrem; na testovacích datech může být záporný |
| MAPE | mean(abs(error / y)) | relativní chyba; selhává, když je y blízko 0 |

R-squared závisí na rozptylu y v testovací množině; místo honby za vysokým R-squared porovnávejte MAE/RMSE s baselinem (např. předpovědí průměrem trénovacích dat).

**Nelinearita.** Odezva na marketing má klesající výnosy: každé další euro přinese méně tržeb. Log-log model `log(revenue) = a + b*log(spend)` to zachytí; b je *elasticita* (zvýšení výdajů o 1 % -> zvýšení tržeb o b %). Grafy reziduí (rezidua vs. predikce) odhalí zakřivení a heteroskedasticitu.

**Ekvivalent v R:**

```r
fit <- lm(revenue ~ spend, data = train)
summary(fit)                     # koeficienty, R-squared, p-hodnoty
pred <- predict(fit, newdata = test)
mae <- mean(abs(test$revenue - pred))
```
""",
        "business_context": """
Marketing chce předpovídat týdenní tržby z kanálu Search z plánovaných výdajů jako podklad pro rozpočet na příští čtvrtletí. Ze dvou let týdenních dat nafitujete model na prvních 78 týdnech a otestujete ho na posledních 26.
""",
        "worked_example": {"explanation": """
* Oba modely jasně překonávají baseline s průměrem - výdaje nesou skutečný signál.
* Elasticita pod 1 potvrzuje **klesající výnosy**: zdvojnásobení výdajů zvýší tržby méně než dvojnásobně. To je důležité pro alokaci rozpočtu (modul 4).
* Lineární sklon je *průměrný* výnos v pozorovaném rozsahu výdajů; extrapolace daleko za něj je riskantní.
"""},
        "summary": [
            "Koeficienty popisují souvislosti při konstantních ostatních příznacích.",
            "MAE/RMSE vyhodnocujte na odložených datech vůči baselinu.",
            "Volte metriky odrážející byznysovou cenu chyb.",
            "Pro klesající výnosy používejte transformace (log-log); vyhněte se extrapolaci.",
        ],
        "common_mistakes": [
            "Uvádění R-squared z trénovacích dat jako kvality modelu.",
            "Kauzální interpretace koeficientů z observačních dat.",
            "Použití MAPE, když mohou být skutečné hodnoty blízko nuly.",
        ],
        "revision": "Vykreslete rezidua vs. predikované hodnoty lineárního modelu a popište vzorec.",
    },
    "pr3": {
        "title": "Klasifikace, matice záměn a prahy",
        "objectives": [
            "Nafitovat klasifikátor logistické regrese.",
            "Číst matici záměn a spočítat precision, recall a F1.",
            "Porovnat ROC-AUC a PR-AUC, zejména při nevyvážených třídách.",
            "Zvolit rozhodovací práh podle byznysových nákladů a kapacity.",
        ],
        "concept": """
**Logistická regrese** předpovídá pravděpodobnost p = 1 / (1 + e^-(b0 + b1x1 + ...)). Koeficienty jsou změny **log-šancí**.

**Matice záměn** při prahu t (odchod předpovídáme, pokud p >= t):

|  | Predikován odchod | Predikováno setrvání |
|---|---|---|
| **Skutečný odchod** | TP | FN |
| **Skutečné setrvání** | FP | TN |

* **Precision (přesnost pozitivních)** = TP / (TP + FP): kolik z obvolaných zákazníků by skutečně odešlo?
* **Recall (záchyt)** = TP / (TP + FN): kolik ze všech odcházejících jsme zastihli?
* **F1** = harmonický průměr precision a recall.
* **Accuracy (přesnost)** = (TP + TN) / všichni - při nevyváženosti zavádějící.

**Volba prahu je byznysové rozhodnutí.** Snížení prahu zvýší recall a sníží precision. Volte ho podle nákladů a kapacity: např. pokud hovor stojí 15 EUR a zachrání 20 % odcházejících v hodnotě 300 EUR, vyplatí se volat, když p x 0,2 x 300 > 15, tj. p > 0,25. Pokud tým zvládne obvolat jen 30 % zákazníků, zvolte práh, který označí 30 %.

**Metriky pořadí (bez prahu):**

* **ROC-AUC** - pravděpodobnost, že náhodný odcházející dostane vyšší skóre než náhodný zůstávající. 0,5 = náhoda.
* **PR-AUC** (průměrná precision) - zaměřuje se na pozitivní třídu; při silné nevyváženosti je informativnější. Jejím baselinem je podíl pozitivních, ne 0,5.

**Nevyvážené třídy:** používejte stratifikované rozdělení, vhodné metriky, `class_weight="balanced"` nebo převzorkování - a pamatujte, že převážení mění kalibraci pravděpodobností.
""",
        "business_context": """
Customer Success zvládne obvolat zhruba 30 % nových zákazníků. Potřebujete model odchodu a práh a musíte vysvětlit, co precision a recall znamenají z hlediska uskutečněných hovorů a zastižených odcházejících.
""",
        "worked_example": {"explanation": """
* Škálování je uvnitř pipeline, takže se fituje jen na trénovacích datech (žádná kontaminace).
* Při t = 0,5 model označí málo zákazníků: vysoká precision, nízký recall. Snížením t měníte precision za recall.
* Zvolte práh, jehož *podíl označených* odpovídá 30% kapacitě týmu, a pak uveďte očekávanou precision („přibližně X z každých 10 hovorů zastihne skutečné riziko odchodu“) a recall.
"""},
        "summary": [
            "Precision = kvalita označeného seznamu; recall = pokrytí skutečných pozitivních.",
            "Prahy mají vycházet z nákladů, přínosů a kapacity, ne z výchozí hodnoty 0,5.",
            "ROC-AUC měří pořadí; PR-AUC je informativnější při nevyváženosti.",
            "Předzpracování držte uvnitř pipeline, abyste se vyhnuli kontaminaci.",
        ],
        "common_mistakes": [
            "Uvádění accuracy u nevyvážené úlohy.",
            "Použití výchozího prahu 0,5 bez zdůvodnění.",
            "Porovnávání PR-AUC s 0,5 místo s podílem pozitivních.",
        ],
        "revision": "Spočítejte očekávanou čistou hodnotu obvolávání při třech prazích s použitím uvedených nákladů.",
    },
    "pr4": {
        "title": "Stromy, náhodné lesy, pipeline a křížová validace",
        "objectives": [
            "Vysvětlit rozhodovací stromy a náhodné lesy a jejich kompromisy.",
            "Sestavit pipeline předzpracování + model pomocí ColumnTransformer.",
            "Odhadnout výkon pomocí k-násobné křížové validace.",
            "Ladit hyperparametry bez přeučení na validačních datech.",
        ],
        "concept": """
**Rozhodovací stromy** dělí data pravidly „když/pak“, která nejlépe oddělí cílovou proměnnou. Zachytí nelinearity a interakce a potřebují málo předzpracování, ale hluboký strom si zapamatuje šum (**přeučení**).

**Náhodné lesy** průměrují mnoho stromů trénovaných na bootstrapových vzorcích s náhodnými podmnožinami příznaků. Průměrování snižuje rozptyl, takže lesy obvykle generalizují mnohem lépe než jednotlivé stromy. Gradient boosting (např. `HistGradientBoostingClassifier`) staví stromy postupně a bývá ještě silnější.

**Kompromis mezi vychýlením a rozptylem.** *Podučení* (vysoké vychýlení): slabé výsledky na trénovacích i testovacích datech. *Přeučení* (vysoký rozptyl): skvělé na trénovacích, slabé na testovacích. Učicí křivky a rozdíl mezi trénovacím a validačním skóre ukážou, o který případ jde.

**Pipeline** řetězí předzpracování a model tak, aby se každá transformace naučila jen z trénovací části:

```python
pre = ColumnTransformer([
    ("num", StandardScaler(), numeric_cols),
    ("cat", OneHotEncoder(handle_unknown="ignore"), categorical_cols),
])
model = Pipeline([("pre", pre), ("clf", RandomForestClassifier(random_state=0))])
```

**Křížová validace** rozdělí trénovací data na k částí (foldů), trénuje k-krát a skóre zprůměruje - stabilnější odhad než jedno validační rozdělení. Pro klasifikaci použijte `StratifiedKFold`; pro časová data `TimeSeriesSplit`.

**Ladění hyperparametrů** (`GridSearchCV`, `RandomizedSearchCV`) vybírá nastavení podle skóre z CV. Skóre CV vybraného modelu je opticky nadhodnocené; potvrďte ho na nedotčené testovací množině. Jednodušší modely, které jsou od nejlepšího v rámci šumu, bývají vhodnější (snáze se vysvětlují i udržují).

**Ekvivalenty v R:** `rpart` (stromy), `randomForest` nebo `ranger` (lesy), `caret` / `tidymodels` (pipeline a CV).
""",
        "business_context": """
Vedoucí datové vědy se ptá: „Stojí náhodný les u odchodu za svou složitost oproti logistické regresi?“ Musíte odpovědět férovým srovnáním - stejné příznaky, stejné foldy, stejná metrika.
""",
        "worked_example": {"explanation": """
* Neořezaný strom má na trénovacích foldech skóre ~1,0, ale na validačních mnohem nižší: učebnicové přeučení.
* Les a logistická regrese si v CV vedou podobně. Když složitý model jasně nepřekoná jednoduchý, dejte přednost jednoduššímu, lépe vysvětlitelnému modelu.
* `SimpleImputer` doplňuje chybějící skóre spokojenosti uvnitř pipeline, takže hodnoty pro doplnění se učí v každém trénovacím foldu zvlášť.
"""},
        "summary": [
            "Stromy zachytí nelinearitu, ale přeučují se; lesy rozptyl zprůměrují.",
            "Pipeline brání úniku informací z předzpracování.",
            "Křížová validace dává stabilní odhady; podle potřeby použijte stratifikované nebo časové foldy.",
            "Když jsou rozdíly ve výkonu v rámci šumu, dejte přednost jednodušším modelům.",
        ],
        "common_mistakes": [
            "Fitování škálování nebo kódování před rozdělením dat.",
            "Uvádění nejlepšího skóre CV po intenzivním ladění jako očekávaného výkonu v provozu.",
            "Porovnávání modelů na různých foldech nebo příznacích.",
        ],
        "revision": "Přidejte do srovnání HistGradientBoostingClassifier a interpretujte výsledek.",
    },
    "pr5": {
        "title": "Základy předpovídání časových řad",
        "objectives": [
            "Popsat trend, sezónnost a šum v časové řadě.",
            "Vyhodnocovat předpovědi časovým odložením dat a klouzavým počátkem.",
            "Sestavit naivní a sezónně naivní baseline.",
            "Nafitovat exponenciální vyrovnávání a komunikovat nejistotu předpovědi.",
        ],
        "concept": """
Časová řada kombinuje **trend** (dlouhodobý směr), **sezónnost** (opakující se vzorce - týdenní, roční) a **šum**. Před modelováním vykreslete řadu a její sezónní profil.

**Vyhodnocení musí respektovat čas.** Jako testovací množinu odložte nejnovější období (např. posledních 28 dní). Lépe: vyhodnocení s *klouzavým počátkem* - předpovídejte z několika dat uzávěrky a chyby zprůměrujte. Nikdy nemíchejte pořadí.

**Baseliny, které musíte překonat:**

* *Naivní:* zítřek = dnešek.
* *Sezónně naivní:* příští pondělí = minulé pondělí (pro denní data s týdenní sezónností).
* *Klouzavý průměr:* průměr posledních k období.

**Exponenciální vyrovnávání (ETS / Holt-Winters)** dává novějším pozorováním větší váhu a umí modelovat úroveň, trend i sezónnost:

```python
from statsmodels.tsa.holtwinters import ExponentialSmoothing
fit = ExponentialSmoothing(train, trend="add", seasonal="add", seasonal_periods=7).fit()
forecast = fit.forecast(28)
```

**Regrese s kalendářními příznaky** (den v týdnu, měsíc, akce, svátky) je flexibilní alternativa; zpožděné příznaky smí používat jen informace dostupné v okamžiku předpovědi.

**Nejistota.** Bodové předpovědi jsou vždy chybné; komunikujte predikční intervaly (např. 80% rozsah) nebo kvantily. Pro rozhodování o zásobách je často důležitější *horní* kvantil než průměr.

**Cenzorovaná poptávka.** Pokud jsou prodeje omezeny výpadky zásob, předpověď *prodejů* podhodnocuje *poptávku*.

**Ekvivalenty v R:** `forecast::ets()`, `forecast::snaive()`, `fable` (předpovědi v duchu tidyverse).
""",
        "business_context": """
Plánovači firmy Meridian Supply potřebují čtyřtýdenní denní předpověď celkové poptávky, aby mohli naplánovat personál skladu. Musíte ukázat, že vaše metoda na posledních čtyřech týdnech překonává jednoduché baseliny.
""",
        "worked_example": {"explanation": """
* Týdenní sezónnost je silná (víkendy jsou výrazně slabší), takže naivní předpověď je špatná a sezónně naivní baseline je mnohem lepší.
* Holt-Winters je třeba posuzovat vůči sezónně naivnímu modelu, ne vůči naivnímu. Pokud ho výrazně nepřekoná, jeho složitost není opodstatněná.
* Pro plánování personálu uveďte rozsah: např. 80% interval ze simulovaných chyb nebo z reziduí.
"""},
        "summary": [
            "Rozložte řadu na trend, sezónnost a šum.",
            "Používejte časové odložení nebo klouzavé počátky - nikdy náhodné rozdělení.",
            "U sezónních dat je sezónně naivní model baseline, který je třeba překonat.",
            "Komunikujte intervaly předpovědi, ne jen bodové předpovědi.",
        ],
        "common_mistakes": [
            "Porovnání sezónního modelu jen s nesezónním baselinem.",
            "Použití budoucích informací ve zpožděných příznacích.",
            "Předpovídání prodejů místo poptávky, když došlo k výpadkům zásob.",
        ],
        "revision": "Zopakujte vyhodnocení se třemi různými daty uzávěrky (klouzavý počátek).",
    },
    "pr6": {
        "title": "Interpretace, nejistota, drift a odpovědné použití",
        "objectives": [
            "Interpretovat modely pomocí permutační důležitosti a parciální závislosti.",
            "Odhalit únik informací podle podezřelé důležitosti a výkonu.",
            "Po nasazení sledovat drift dat a konceptu.",
            "Posoudit férovost, nejistotu a to, zda je model v praxi užitečný.",
        ],
        "concept": """
**Nástroje interpretace**

* *Koeficienty* (lineární/logistická regrese) - směr a velikost souvislosti po škálování.
* *Permutační důležitost* - pokles metriky, když se jeden příznak na odložených datech zamíchá. Nezávislá na modelu; korelované příznaky si důležitost dělí.
* *Grafy parciální závislosti / ICE* - jak se mění predikce při změně jednoho příznaku.
* *Hodnoty SHAP* - příspěvky k jednotlivým predikcím (volitelný balíček `shap`).

Důležitost ukazuje, co model **používá**, ne co výsledek **způsobuje**.

**Odhalení úniku.** Pokud jeden příznak dominuje důležitosti a testovací AUC je blízko 1,0, zeptejte se: *mohli bychom tuto hodnotu znát v okamžiku predikce?*

**Je model užitečný?** Porovnejte ho s baselinem a se současným byznysovým procesem; převeďte metriky na hodnotu (ušetřené hovory, předejité výpadky zásob); zvažte náklady na jeho údržbu.

**Nejistota.** Uvádějte rozptyl CV nebo bootstrapové intervaly metrik; kontrolujte kalibraci (odchází u předpovězeného 30% rizika skutečně ~30 % zákazníků?).

**Drift a monitoring**

* *Drift dat* - mění se rozdělení vstupů (více zákazníků z Paid Social).
* *Drift konceptu* - mění se vztah mezi vstupy a výsledkem (zdražení změní, kdo odchází).
* Sledujte rozdělení vstupů, rozdělení predikcí a skutečný výkon, jakmile dorazí štítky; nastavte spouštěče přetrénování.

**Odpovědné použití.** Kontrolujte výkon napříč skupinami (regiony, velikosti firem); vyhněte se zástupným proměnným za chráněné atributy; zamýšlené použití a omezení zdokumentujte v *kartě modelu*; u závažných rozhodnutí ponechte člověka ve smyčce.
""",
        "business_context": """
Juniorní analytik hrdě hlásí model odchodu s AUC 0,99. Váš manažer vás žádá o jeho revizi, než půjde do Customer Success - a o sepsání plánu monitoringu pro model, který bude nakonec nasazen.
""",
        "worked_example": {"explanation": """
* AUC blízko 1,0 a příznak `cancellation_reason_none` dominující důležitosti = **únik cílové proměnné**. Sloupec odstraňte a model přetrénujte; očekávejte mnohem nižší, ale poctivé AUC.
* Kontingenční tabulka ukazuje **drift dat**: podíl Paid Social se v testovacím období více než zdvojnásobí. Model trénovaný na zákaznících z roku 2023 bude čelit jiné populaci - sledujte ho.
"""},
        "summary": [
            "Důležitost vysvětluje chování modelu, ne kauzalitu.",
            "Dominantní příznak spolu s téměř dokonalým skóre signalizuje únik.",
            "Sledujte drift dat, drift konceptu a skutečný výkon.",
            "Kontrolujte kalibraci a výkon v podskupinách a omezení zdokumentujte v kartě modelu.",
        ],
        "common_mistakes": [
            "Oslava AUC 0,99 bez ověření dostupnosti příznaků.",
            "Nasazení bez monitoringu a spouštěčů přetrénování.",
            "Předpoklad, že jedna globální metrika znamená, že model funguje stejně dobře pro všechny skupiny.",
        ],
        "revision": "Napište jednostránkovou kartu modelu pro očištěný model odchodu a pak začněte závěrečný projekt 3.",
    },
}
