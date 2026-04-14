"""Czech text for the business-case assessments.

Rubric indicators are Czech word stems, so the advisory keyword coverage also works for answers written in Czech.
"""

LEVELS = ["0 - Chybí nebo je chybné", "1 - Částečné", "2 - Solidní", "3 - Výborné"]

# Same order as cases.STANDARD_RUBRIC.
STANDARD_RUBRIC = [
    {"name": "Metodická správnost", "description": "Používá vhodné metody a vyhýbá se analytickým chybám (např. míchání granularit, kauzální přehánění).",
     "levels": LEVELS, "indicators": ["porovn", "segment", "baselin", "kontrol", "stejné období", "srovn"]},
    {"name": "Důkazy", "description": "Cituje konkrétní čísla z podkladů a spojuje je s tvrzením.",
     "levels": LEVELS, "indicators": ["%", "eur", "tis", "míra"]},
    {"name": "Úvaha", "description": "Zvažuje alternativní vysvětlení, předpoklady a omezení.",
     "levels": LEVELS, "indicators": ["alternativ", "předpokl", "omezen", "nicméně", "vylouč", "v souladu"]},
    {"name": "Komunikace", "description": "Začíná odpovědí; jasná, stručná, přiměřená publiku.", "levels": LEVELS},
    {"name": "Byznysová relevance", "description": "Končí konkrétním, proveditelným doporučením s vlastníkem.",
     "levels": LEVELS, "indicators": ["doporuč", "měli bychom", "další krok", "vlastník", "akce", "krok"]},
]

CASES = {
    "case_revenue_decline": {
        "title": "Vysvětlete náhlý pokles tržeb",
        "scenario": "Tržby regionu West v srpnu a září 2024 prudce klesly. Regionální viceprezident to připisuje akci konkurence a navrhuje plošné snížení cen v celém regionu. Do porady vedení máte 30 minut.",
        "objectives": [
            ("Které vysvětlení je s důkazy nejvíce v souladu?",
             ["Akce konkurence snížila poptávku v celém regionu", "Problém s dodávkami (např. výpadek zásob) u West Electronics", "Cenová chyba v celém regionu", "Běžná sezónnost"],
             "Pokles je soustředěný do jediné kategorie v jediném regionu přesně na dva měsíce a pak se zotaví - typický vzorec problému s dodávkami. Akce konkurence by obvykle zasáhla více kategorií."),
            ("Které další důkazy by vaše vysvětlení nejlépe potvrdily? (vyberte všechny správné)",
             ["Skladové záznamy / záznamy o výpadcích zásob u West Electronics", "Návštěvnost webu a míra přidání do košíku u Electronics v regionu West", "Ceny konkurence v ostatních kategoriích", "Celkový počet zaměstnanců firmy"],
             "Skladové záznamy přímo testují hypotézu o dodávkách; stabilní návštěvnost při klesajících prodejích ji podporuje; ceny konkurence v ostatních kategoriích pomohou vyloučit příběh o akci."),
            ("Měl by Northwind snížit ceny v celém regionu West?",
             ["Ano, okamžitě", "Ne - důkazy ukazují na dodávky, ne na cenu; nejprve opravte dostupnost", "Ano, ale jen u Electronics", "Jen pokud tržby příští měsíc znovu klesnou"],
             "Snížení cen by snížilo marži u kategorií, které si vedou normálně, a výpadek zásob by nevyřešilo."),
        ],
        "prompt": "Napište regionálnímu viceprezidentovi krátkou zprávu (5-8 vět): co se stalo, jak moc si jste jistí, co byste ověřili dál a co doporučujete.",
        "rubric": STANDARD_RUBRIC,
        "exemplar": "Tržby regionu West v srpnu-září 2024 meziročně klesly o ~39 % (~79 tis. -> ~49 tis. EUR), ale téměř celý pokles - a ještě víc - připadá na Electronics, které spadly z ~50 tis. na ~8 tis. EUR, zatímco všechny ostatní kategorie stagnovaly nebo rostly. Propad začíná náhle v srpnu, končí v říjnu a v jiných regionech se neobjevuje. Tento vzorec je spíše v souladu s problémem s dodávkami (výpadek zásob nebo chyba v nabídce) než s akcí konkurence, která by normálně zasáhla více kategorií. Skladové záznamy jsme zatím neviděli, takže jde o silnou hypotézu, ne o potvrzenou příčinu. **Další krok:** provoz potvrdí stav zásob Electronics v regionu West za srpen-září (dnes); já zkontroluji návštěvnost stránek Electronics. **Doporučení:** neplošně nesnižujte ceny v regionu - snížilo by to marži u zdravých kategorií a dostupnost by to nevyřešilo. Místo toho zaveďte upozornění na stav zásob u nejprodávanějších SKU Electronics.",
    },
    "case_churn_increase": {
        "title": "Zjistěte, proč vzrostl odchod zákazníků",
        "scenario": "Šestiměsíční odchod v CloudNest vzrostl přibližně o 7 procentních bodů u zákazníků registrovaných od dubna 2024. Produkt, marketing i finance mají každý jiné vysvětlení. Generální ředitel vás žádá o rozuzlení.",
        "objectives": [
            ("Co vysvětluje většinu nárůstu celkového odchodu?",
             ["Každý akviziční zdroj se podstatně zhoršil", "Mix se posunul k Paid Social, zdroji s vysokým odchodem", "Přepracovaný onboarding selhal u všech zákazníků", "Náhodné kolísání"],
             "Odchod v rámci zdrojů je zhruba stabilní, zatímco podíl Paid Social vyskočil z ~15 % na ~40 % - efekt složení."),
            ("Které tvrzení zobrazené důkazy NEPODPORUJÍ?",
             ["Zákazníci z Paid Social odcházejí přibližně dvakrát častěji než ostatní", "Přepracovaný onboarding způsobil nárůst odchodu", "Podíl Paid Social na registracích po dubnu 2024 vzrostl", "Odchod v rámci zdrojů se změnil poměrně málo"],
             "Kdyby onboarding selhal plošně, odchod by vzrostl i v zavedených zdrojích; to se nestalo."),
            ("Jaká je nejlepší další analýza pro samostatné vyhodnocení zdražení?",
             ["Porovnat Basic s ostatními tarify před a po červenci bez Paid Social (rozdíl v rozdílech)", "Porovnat celkový odchod v letech 2023 a 2024", "Udělat průzkum mezi současnými zákazníky o ceně", "Spočítat tikety podpory týkající se fakturace"],
             "Porovnání změn u zasažené skupiny se srovnávací skupinou při odstranění posunu mixu izoluje efekt ceny za předpokladu paralelních trendů."),
        ],
        "prompt": "Napište pro generálního ředitele krátké memo: co se stalo, co to vysvětluje, co je stále nejisté a co dělat.",
        "rubric": STANDARD_RUBRIC,
        "exemplar": "Odchod vzrostl z ~25 % na ~32 % u registrací z dubna-září 2024. Většinu nárůstu tvoří **efekt mixu**: Paid Social vzrostl z ~15 % na ~40 % registrací a má odchod ~50 % oproti ~20 % u ostatních zdrojů, zatímco odchod *uvnitř* jednotlivých zdrojů se změnil málo. To nepodporuje plošné selhání onboardingu. Červencové zdražení tarifu Basic může přidat menší efekt; odhadneme ho porovnáním Basic s ostatními tarify před a po červenci bez Paid Social. **Nejisté:** zda uživatelé z Paid Social odcházejí kvůli špatnému souladu, nebo slabému onboardingu - odpověď dá cílený experiment s onboardingem. **Kroky:** hodnotit Paid Social podle udržených tržeb za 6 měsíců (CMO), spustit test onboardingu pro uživatele z Paid Social (Produkt) a měsíčně reportovat odchod u tarifu Basic (Finance).",
    },
    "case_model_selection": {
        "title": "Vyberte a vyhodnoťte prediktivní model",
        "scenario": "Tým datové vědy porovnal modely odchodu. Sponzor projektu chce nasadit ten s „nejlepším číslem“.",
        "objectives": [
            ("Proč musí být model A zamítnut?",
             ["Je příliš pomalý", "Používá cancellation_reason, který je známý až po odchodu (únik cílové proměnné)", "Náhodné lesy nelze nasadit", "Jeho AUC je příliš nízké"],
             "Téměř dokonalé AUC tažené polem vzniklým po výsledku je únik; v provozu model selže."),
            ("Která volba mezi B a C je pro tento případ obhajitelnější?",
             ["B: podobné AUC v rámci šumu, mnohem lépe vysvětlitelný, menší rozdíl mezi tréninkem a testem", "C: vyhrává nejvyšší AUC", "Ani jeden: AUC pod 0,8 je k ničemu", "Zprůměrovat B a C bez testování"],
             "Rozdíl 0,012 AUC je v rámci směrodatných odchylek CV; pro account manažery je důležitá vysvětlitelnost; C vykazuje větší přeučení."),
            ("Která metrika nejlépe sdělí týmu Customer Success očekávané výsledky hovorů?",
             ["Precision při prahu, který označí 30 % zákazníků", "Trénovací přesnost", "R-squared", "Počet stromů"],
             "Precision při prahu podle kapacity jim řekne, kolik hovorů zastihne skutečné riziko odchodu."),
        ],
        "prompt": "Napište sponzorovi doporučení: který model nasadit, proč, jak nastavit práh a co sledovat.",
        "rubric": STANDARD_RUBRIC,
        "exemplar": "Nasaďte **model B (logistická regrese)**. AUC 0,995 modelu A pochází z `cancellation_reason`, který existuje až po zrušení předplatného - v provozu fungovat nemůže. B a C fungují stejně v rámci šumu (0,712 vs. 0,724, směrodatná odchylka ~0,015), ale B je vysvětlitelný account manažerům a méně se přeučuje (trénink 0,718 vs. CV 0,712). Práh nastavte tak, aby označil horních 30 % rizikových skóre podle kapacity hovorů, a uvádějte precision při tomto prahu (očekávaně ~4-5 z 10 hovorů zastihne skutečné riziko oproti ~3 z 10 náhodně). Sledujte drift vstupů (akviziční mix se posouvá), měsíční precision, jakmile dorazí výsledky, a kalibraci; přetrénujte čtvrtletně nebo když precision klesne o více než 5 bodů.",
    },
    "case_budget": {
        "title": "Doporučte alokaci rozpočtu",
        "scenario": "Optimalizační model marketingového rozpočtu na příští čtvrtletí byl spuštěn. Marketingová ředitelka chce dalších 100 tis. EUR a žádá vaše doporučení.",
        "objectives": [
            ("Které omezení v základním případě limituje zisk?",
             ["Celkový rozpočet", "Politika průměrného rizika", "Jen maximální výdaje na Email", "Žádné - zisk je neomezený"],
             "Duální hodnota rozpočtu je nulová a výdaje jsou pod 400 tis. EUR; rizikové omezení má kladnou duální hodnotu."),
            ("Co se stane, když rozpočet vzroste na 500 tis. EUR při stejné rizikové politice?",
             ["Zisk výrazně vzroste", "Zisk se nezmění", "Úloha se stane nepřípustnou", "Zisk klesne"],
             "Rozpočet navíc nelze ziskově utratit bez porušení rizikové politiky."),
            ("Co byste měli říct marketingové ředitelce?",
             ["Schválit dalších 100 tis. EUR", "Rozpočet navíc nic nepřidá, pokud se neuvolní riziková politika; diskutujte raději o politice", "Snížit rozpočet o 100 tis. EUR", "Utratit peníze navíc za nejrizikovější kanál"],
             "Vázajícím omezením je politika; rozhodnutí patří k ochotě vedení riskovat."),
        ],
        "prompt": "Napište doporučení pro marketingovou ředitelku (alokace, proč, co ji limituje a kdy by se změnila).",
        "rubric": STANDARD_RUBRIC,
        "exemplar": "Alokujte ~398 tis. EUR: Search 120 tis., Social 90 tis., Display 60 tis., Email 25 tis., Affiliate 50 tis. a Video ~53 tis., s očekávaným ziskem ~143 tis. EUR. Vázajícím omezením je **politika průměrného rizika (<= 0,35)**, ne rozpočet - model nechá ~2 tis. EUR nevyčerpané a dalších 100 tis. EUR by při současné politice nepřidalo **žádný** zisk. Pokud je vedení ochotné zvýšit rizikový strop na 0,40, zisk vzroste na ~145 tis. EUR při současném rozpočtu a na ~149 tis. EUR při 500 tis. EUR. **Doporučení:** rozpočet navíc zatím odmítněte a kompromis rizikové politiky přineste na poradu vedení. **Předpoklady:** lineární marže v limitech kanálů; subjektivní riziková skóre - přehodnoťte, pokud se marže Email nebo Search změní o více než ~20 %.",
    },
    "case_chart_critique": {
        "title": "Zkritizujte zavádějící graf",
        "scenario": "Níže uvedený dashboard regionu West byl předložen vedení v období výpadku zásob. Problému si nikdo nevšiml.",
        "objectives": [
            ("Jaké problémy dashboard má? (vyberte všechny správné)",
             ["Kumulativní křivka tržeb skrývá propad v srpnu a září", "Dvě osy s libovolnými měřítky naznačují vztah, který neexistuje",
              "Oříznutá osa sloupců zveličuje rozdíly v počtu objednávek", "Koláčový graf s osmi výsečemi v duhových barvách se špatně porovnává",
              "Chybějící popisky os a jednotky", "Koláčový graf používá tržby před slevami, což neodpovídá definici KPI",
              "Dashboard používá příliš málo barev", "Tržby jsou uvedeny v EUR místo v USD"],
             "Šest skutečných vad: kumulativní křivka, dvě osy, oříznuté sloupce, duhový koláč s osmi výsečemi, chybějící popisky a nekonzistentní definice tržeb. Počet barev a měna problémem nejsou."),
            ("Která jediná vada má pro rozhodovatele nejzávažnější důsledky?",
             ["Kumulativní křivka tržeb skryla 39% dvouměsíční pokles", "Barvy koláčového grafu", "Písmo názvu", "Natočení popisků osy x"],
             "Skryla právě tu událost, kterou vedení potřebovalo vidět."),
        ],
        "prompt": "Navrhněte přepracovaný dashboard: uveďte každý problém, jeho vliv na interpretaci a konkrétní opravu.",
        "rubric": STANDARD_RUBRIC,
        "exemplar": "1. **Kumulativní křivka** vždy roste a skryla propad v srpnu-září -> zobrazte měsíční tržby s osou od nuly a anotujte výpadek zásob. 2. **Dvě osy** s libovolnými měřítky naznačují, že objednávky a tržby se pohybují spolu -> dva zarovnané panely nebo indexovaný graf (březen = 100). 3. **Oříznutá osa sloupců** zveličuje meziměsíční změny objednávek -> sloupce od nuly. 4. **Duhový koláč s osmi výsečemi** -> seřazené vodorovné sloupce s přímými popisky a paletou bezpečnou pro barvoslepé. 5. **Chybějící popisky/jednotky** -> popište osy (EUR, objednávky). 6. **Tržby před slevami** v koláči odporují definici KPI -> použijte tržby z dokončených objednávek po slevách a definici uveďte v poznámce. Nakonec nahraďte oslavný název neutrálním názvem vycházejícím ze zjištění.",
    },
    "case_kpis": {
        "title": "Doporučte KPI pro manažerský dashboard",
        "scenario": "Vedení CloudNest vás žádá o přepracování měsíčního dashboardu, aby ukazoval zdraví byznysu a kde zasáhnout.",
        "objectives": [
            ("Která KPI patří na dashboard vedení? (vyberte všechny správné)",
             ["Měsíční opakované tržby (MRR) a jejich růst", "Šestiměsíční odchod podle kohorty registrace", "Čistá retence tržeb (net revenue retention)",
              "Míra aktivace v prvním měsíci (např. podíl s >= 5 přihlášeními)", "Celkový počet registrovaných uživatelů od počátku", "Zobrazení stránek webu", "Slovní mrak z textu tiketů"],
             "MRR, kohortní odchod, čistá retence tržeb a aktivace jsou výsledkové a hnací metriky, podle kterých může vedení jednat. Registrovaní uživatelé od počátku a zobrazení stránek jsou „marnivé“ metriky; slovní mraky nejsou kvantitativní."),
            ("Proč je „celkový počet registrovaných uživatelů (od počátku)“ špatné KPI pro vedení?",
             ["Může jen růst a ignoruje odchod, takže nemůže signalizovat problémy", "Je příliš těžké ho spočítat", "Je to poměr", "Je důvěrné"],
             "Kumulativní počet skrývá ztráty - jde o marnivou metriku."),
        ],
        "prompt": "Navrhněte 5-7 KPI, každé s jednořádkovou definicí (vzorec, filtr, vlastník, cíl), a vysvětlete, jak spolu souvisejí (výsledkové vs. hnací metriky).",
        "rubric": STANDARD_RUBRIC,
        "exemplar": "**Výsledkové:** (1) MRR = součet mrr aktivních zákazníků v měsíci (vlastník CFO; cíl +3 % meziměsíčně); (2) Čistá retence tržeb = MRR tento měsíc od zákazníků aktivních před 12 měsíci / jejich tehdejší MRR (CFO; >= 100 %). **Hnací:** (3) šestiměsíční odchod podle kohorty registrace a zdroje (vedoucí CS; <= 25 %); (4) aktivace = podíl nových zákazníků s >= 5 přihlášeními v 1. měsíci (Produkt; >= 60 %); (5) nové MRR podle akvizičního zdroje, hodnocené podle udržených tržeb za 6 měsíců (CMO); (6) CSAT podpory a mediánová doba vyřešení (vedoucí CS; >= 4,0, <= 24 h). Výsledkové metriky říkají vedení, *zda* je byznys zdravý; hnací metriky ukazují, *kde* zasáhnout. Odstraňte registrované uživatele od počátku a zobrazení stránek (marnivé metriky) a slovní mrak (pro rozhodování nepodstatný).",
    },
}
