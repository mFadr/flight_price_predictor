"""Czech text for the Data Visualization questions. Options are (text, why) in the original order."""

TOPICS = {
    "Chart selection": "Výběr grafu",
    "Distributions": "Rozdělení",
    "Tables vs charts": "Tabulky vs. grafy",
    "Matplotlib API": "API Matplotlibu",
    "Annotations": "Anotace",
    "Small multiples": "Malé násobky",
    "Colour": "Barva",
    "Accessibility": "Přístupnost",
    "Clutter": "Nepořádek v grafu",
    "Truncated axes": "Oříznuté osy",
    "Dual axes": "Dvě osy",
    "Maps": "Mapy",
    "Dashboard design": "Návrh dashboardu",
    "Uncertainty": "Nejistota",
    "Storytelling": "Datové vyprávění",
    "Tableau fields": "Pole v Tableau",
    "Tableau LOD": "LOD v Tableau",
    "Looker Studio ratios": "Poměry v Looker Studio",
    "Data preparation for BI": "Příprava dat pro BI",
    "Composition": "Složení",
}

QUESTIONS = {
    "q_vz_001": {
        "stem": "Který graf nejlépe ukáže, jak se měsíční tržby měnily během dvou let?",
        "options": [
            ("Spojnicový graf s měsíci na ose x", "Čáry zdůrazňují spojitost a trend v uspořádaném čase."),
            ("Koláčový graf tržeb podle měsíců", "Koláče ukazují části celku a skrývají časové pořadí."),
            ("Bodový graf tržeb vs. region", "Neukazuje čas."),
            ("Histogram měsíčních tržeb", "Ukazuje rozdělení a ztrácí časové pořadí."),
        ],
        "explanation": "Otázky na trend -> spojnicové grafy.",
    },
    "q_vz_002": {
        "stem": "Chcete ukázat, že většina objednávek je malá, ale několik je velmi velkých. Který graf je nejvhodnější?",
        "options": [
            ("Histogram (nebo krabicový graf) hodnoty objednávek", "Grafy rozdělení odhalí zešikmení a odlehlé hodnoty."),
            ("Sloupcový graf průměrné hodnoty objednávky", "Průměr skryje tvar rozdělení."),
            ("Spojnicový graf hodnoty objednávky podle ID objednávky", "ID objednávky nemá smysluplné pořadí."),
            ("Koláčový graf pásem hodnot objednávek s 12 výsečemi", "Příliš mnoho výsečí; špatně se čte."),
        ],
        "explanation": "Když záleží na tvaru, ukazujte rozdělení, ne jen souhrnné statistiky.",
    },
    "q_vz_003": {
        "stem": "Finanční kontrolor potřebuje přesné měsíční hodnoty za 40 nákladových středisek k odsouhlasení účetních knih. Co mu poskytnete?",
        "options": [
            ("Dobře formátovanou tabulku (s podmíněným formátováním výjimek)", "Přesné vyhledání hodnot je silnou stránkou tabulky."),
            ("Spojnicový graf se 40 čarami", "Nečitelné „špagety“ pro přesné hodnoty."),
            ("Treemapu", "Dobrá pro složení, ne pro přesné hodnoty."),
            ("Slovní mrak", "Není kvantitativní."),
        ],
        "explanation": "Grafy ukazují vzorce; tabulky ukazují přesné hodnoty.",
    },
    "q_vz_004": {
        "stem": "Který kód nastaví popisek osy s jednotkou pomocí objektově orientovaného API Matplotlibu?",
        "options": [
            ("ax.set_ylabel('Revenue (EUR)')", "Metody objektu Axes začínají v OO API předponou set_."),
            ("ax.ylabel('Revenue (EUR)')", "ylabel je funkce pyplot, ne metoda Axes."),
            ("plt.axes.label = 'Revenue (EUR)'", "Neplatný Matplotlib."),
            ("fig.set_ylabel('Revenue (EUR)')", "Figure nemá popisky osy y; ty mají Axes."),
        ],
        "explanation": "Dávejte přednost fig, ax = plt.subplots() a metodám ax.set_*.",
    },
    "q_vz_005": {
        "stem": "Proč anotovat výpadek zásob přímo ve spojnicovém grafu tržeb, a ne ho vysvětlit v poznámce pod čarou?",
        "options": [
            ("Vysvětlení je tam, kam se čtenář už dívá, a brání chybné interpretaci propadu", "Přímá anotace snižuje kognitivní zátěž."),
            ("V byznysových grafech nejsou poznámky pod čarou povoleny", "Povoleny jsou; jen jsou pro klíčový kontext méně účinné."),
            ("Anotace mění podkladová data", "Přidávají jen kontext."),
            ("Matplotlib neumí vykreslit poznámky pod čarou", "Umí (fig.text)."),
        ],
        "explanation": "Kontext umístěte vedle dat, která vysvětluje.",
    },
    "q_vz_006": {
        "stem": "Proč při porovnání trendů tržeb pěti regionů v malých násobcích použít sdílenou osu y (sharey=True)?",
        "options": [
            ("Aby byly výšky panelů porovnatelné; různé škály by malé regiony ukázaly stejně velké jako velké", "Sdílené škály umožňují poctivé srovnání."),
            ("Sdílené osy se vykreslují rychleji", "Rychlost je nepodstatná."),
            ("Matplotlib to u subplots vyžaduje", "Je to volitelné."),
            ("Skryje to rozdíly mezi regiony", "Odhalí je."),
        ],
        "explanation": "Kdykoli se mají panely porovnávat, používejte konzistentní škály.",
    },
    "q_vz_007": {
        "stem": "Jaký typ palety se hodí pro mapu míry odchodu (0 % až 40 %) podle regionu?",
        "options": [
            ("Sekvenční (od světlé po tmavou jednoho odstínu)", "Uspořádané velikosti odpovídají uspořádanému jasu."),
            ("Kategoriální (odlišné odstíny)", "Odlišné odstíny naznačují neuspořádané skupiny."),
            ("Duhová", "Duhové palety vytvářejí falešné hranice a nejsou vhodné pro barvoslepé."),
            ("Divergentní se středem v 0 %", "Divergentní palety potřebují smysluplný střed (např. cíl)."),
        ],
        "explanation": "Paletu přizpůsobte datům: kategoriální, sekvenční nebo divergentní.",
    },
    "q_vz_008": {
        "stem": "Které postupy zlepšují přístupnost grafů? (Vyberte všechny správné.)",
        "options": [
            ("Používat palety bezpečné pro barvoslepé a nespoléhat jen na rozlišení červené a zelené", "Poruchy rozlišení červené a zelené jsou nejčastější."),
            ("Přidat přímé popisky, aby význam nezávisel jen na barvě", "Redundantní kódování pomáhá všem."),
            ("Zajistit dostatečný kontrast textu vůči pozadí", "WCAG doporučuje alespoň 4,5:1."),
            ("Používat světle šedý text, aby graf vypadal moderně", "Nízký kontrast snižuje čitelnost."),
        ],
        "explanation": "Přístupné grafy jsou srozumitelnější pro všechny čtenáře.",
    },
    "q_vz_009": {
        "stem": "Který prvek je v jednoduchém sloupcovém grafu pěti hodnot nejspíš „grafickým balastem“?",
        "options": [
            ("3D perspektivní efekt sloupců", "Nepřidává informaci a zkresluje porovnání."),
            ("Popisek osy s jednotkami", "Nezbytný."),
            ("Název uvádějící závěr", "Hodnotný."),
            ("Popisky hodnot na sloupcích", "Často užitečné, zvlášť bez mřížky."),
        ],
        "explanation": "Odstraňte dekorace, které nic nesdělují.",
    },
    "q_vz_010": {
        "stem": "Osa y sloupcového grafu začíná na 95 a ukazuje hodnoty 96 a 98. Jaký dojem vytváří?",
        "options": [
            ("Druhý sloupec vypadá třikrát větší, přestože rozdíl je asi 2 %", "Délka sloupce kóduje hodnotu jen od nulové základny."),
            ("Přesný dojem, protože hodnoty jsou popsané", "Čtenáři posuzují nejprve délku."),
            ("Žádný, pokud je zobrazena mřížka", "Mřížka úměrnost neobnoví."),
            ("Sloupce vypadají stejně", "Vypadají velmi odlišně."),
        ],
        "explanation": "Sloupce začínají na nule; pokud musíte přiblížit, použijte body nebo čáry.",
    },
    "q_vz_011": {
        "stem": "Proč jsou spojnicové grafy se dvěma osami často zavádějící?",
        "options": [
            ("Obě škály jsou libovolné, takže sklony a průsečíky lze manipulovat", "Změna měřítka kterékoli osy změní zdánlivý vztah."),
            ("Umí ukázat jen dvě řady", "To není podstata problému."),
            ("Vyžadují logaritmickou škálu", "Nic takového nevyžadují."),
            ("Vždy začínají na nule", "Často nezačínají."),
        ],
        "explanation": "Dávejte přednost zarovnaným panelům nebo indexovaným řadám (základ = 100).",
    },
    "q_vz_012": {
        "stem": "Kartogram celkového počtu stížností podle zemí zbarví nejlidnatější země nejtmavěji. Jaká je oprava?",
        "options": [
            ("Zobrazit míru (stížnosti na 1 000 zákazníků) místo součtů", "Normalizace odstraní vliv velikosti populace."),
            ("Použít duhovou paletu", "Problém neřeší."),
            ("Přejít na 3D mapu", "Přidá zkreslení."),
            ("Odstranit legendu", "Zhorší to."),
        ],
        "explanation": "Když součty určuje plocha nebo populace, počty normalizujte.",
    },
    "q_vz_013": {
        "stem": "Co by mělo určovat rozvržení manažerského dashboardu?",
        "options": [
            ("Rozhodnutí, která jeho uživatelé dělají: nejprve KPI, pak trendy, rozpady a detail", "Navrhujte podle použití."),
            ("Zobrazení všech dostupných metrik", "Přehlcení skryje to důležité."),
            ("Typy vizuálů, které nástroj podporuje", "Nástroje slouží účelu, ne naopak."),
            ("Abecední pořadí metrik", "Libovolné."),
        ],
        "explanation": "Návrh zaměřený na rozhodnutí vytváří užitečné dashboardy.",
    },
    "q_vz_014": {
        "stem": "Konverze podle zařízení: tablet (n = 1 400) má 12,0 %, desktop (n = 9 000) má 11,2 %. Jak to vizualizovat pro rozhodovatele?",
        "options": [
            ("Bodové odhady s intervaly spolehlivosti a velikostmi vzorků", "Ukáže, že odhad pro tablet je mnohem méně jistý."),
            ("Sloupcový graf jen s mírami", "Naznačuje stejnou přesnost."),
            ("Koláčový graf konverzí podle zařízení", "Míchá objem a míru."),
            ("Tablet vynechat, protože je malý", "Skrývání dat není poctivé; ukažte jeho nejistotu."),
        ],
        "explanation": "Zviditelněte přesnost, aby publikum výsledky nepřeceňovalo.",
    },
    "q_vz_015": {
        "stem": "Který název grafu nejlépe podporuje datový příběh?",
        "options": [
            ("„Zákazníci z Paid Social odcházejí dvakrát častěji - většinu nárůstu vysvětluje posun mixu“", "Věta uvádějící zjištění posouvá příběh."),
            ("„Odchod podle zdroje“", "Popisuje obsah, ne poznatek."),
            ("„Obrázek 3“", "Nic neříká."),
            ("„Zajímavé vzorce odchodu!!!“", "Vágní a neprofesionální."),
        ],
        "explanation": "Akční názvy nesou vyprávění.",
    },
    "q_vz_016": {
        "stem": "Co v Tableau vytvoří umístění spojitého (zeleného) data do Columns?",
        "options": [
            ("Spojitou časovou osu", "Spojitá pole vytvářejí osy; diskrétní pole záhlaví."),
            ("Jedno záhlaví pro každé různé datum", "To je diskrétní (modré) datum."),
            ("Chybu", "Jde o standardní použití."),
            ("Filtr", "Police definují strukturu; filtry jsou zvlášť."),
        ],
        "explanation": "Diskrétní -> záhlaví; spojité -> osy.",
    },
    "q_vz_017": {
        "stem": "Který výraz v Tableau spočítá datum první objednávky každého zákazníka bez ohledu na úroveň detailu pohledu?",
        "options": [
            ("{ FIXED [Customer Id] : MIN([Order Date]) }", "FIXED LOD počítá na zadané granularitě."),
            ("MIN([Order Date])", "Agreguje na úrovni detailu pohledu."),
            ("WINDOW_MIN([Order Date])", "Tabulkový výpočet závislý na pohledu."),
            ("FIRST()", "Vrací posun, ne datum."),
        ],
        "explanation": "Výrazy LOD oddělují granularitu výpočtu od granularity pohledu.",
    },
    "q_vz_018": {
        "stem": "Jak v Looker Studio definovat hrubou marži %, aby byla správná i při filtrování podle regionu?",
        "options": [
            ("Počítané pole (SUM(revenue) - SUM(cost)) / SUM(revenue)", "Poměry spočítané z agregovaných složek zůstanou správné při jakémkoli filtru."),
            ("Nahrát předem spočítaný sloupec marže % a použít Průměr", "Průměr poměrů po řádcích váží řádky stejně."),
            ("Použít SUM sloupce marže %", "Sčítání procent nedává smysl."),
            ("Použít COUNT marže %", "Počty nejsou poměry."),
        ],
        "explanation": "V každém BI nástroji definujte poměry ze součtů.",
    },
    "q_vz_019": {
        "stem": "Proč laboratoř pro Looker Studio poskytuje plochý, předem spojený soubor „jeden řádek na položku dokončené objednávky“?",
        "options": [
            ("Ploché, uspořádané tabulky s jasnou granularitou zabrání dvojímu započtení a problémům s typy v nástrojích s omezeným modelováním", "Před vizualizací připravte data na správné granularitě."),
            ("Looker Studio neumí číst CSV soubory", "Umí."),
            ("Spojené soubory jsou vždy menší", "Obvykle jsou větší."),
            ("Aby se zrušené objednávky před analytiky natrvalo skryly", "Filtr je zdokumentovaný, ne skrytý."),
        ],
        "explanation": "Dobré dashboardy začínají dobře tvarovanými daty.",
    },
    "q_vz_020": {
        "stem": "Potřebujete ukázat, jak se mezi lety 2023 a 2024 změnil podíl osmi kategorií na tržbách. Který graf funguje nejlépe?",
        "options": [
            ("100% skládané sloupce pro každý rok, nebo sklonový graf podílů", "Oba porovnávají složení ve dvou obdobích."),
            ("Dva koláčové grafy s osmi výsečemi", "Úhly ve dvou koláčích se špatně porovnávají."),
            ("3D prstencový graf", "Zkreslení a nepořádek."),
            ("Histogram", "Špatný typ otázky."),
        ],
        "explanation": "Volte grafy složení, ve kterých se změny podílů snadno porovnávají.",
    },
}
