"""Czech text for the Data Visualization exercises (code, solutions and check logic are unchanged)."""

NO_FIG = "'Nebyl vytvořen žádný obrázek. Použijte fig, ax = plt.subplots() a kreslete do ax.'"
NO_BARS = "'V grafu nejsou žádné sloupce. Použijte ax.bar nebo ax.barh.'"

EXERCISES = {
    "ex_py_vz1_bar": {
        "title": "Seřazený sloupcový graf tržeb podle kategorií",
        "topic": "Sloupcové grafy",
        "business_question": "Které kategorie v roce 2024 vydělaly nejvíce?",
        "requirements": [
            "`cat_rev`: Series tržeb z dokončených objednávek 2024 podle category_name, seřazená sestupně.",
            "Jeden sloupcový graf (svislý nebo vodorovný) s jedním sloupcem na kategorii, seřazený podle tržeb (u svislého největší první; u vodorovného je v pořádku největší nahoře).",
            "Název a popisek osy, který uvádí jednotku (EUR).",
        ],
        "expected_output": "Series a sloupcový graf s 8 sloupci.",
        "explanation": "Seřazené sloupce dělají pořadí okamžitě čitelným. Vodorovné sloupce udrží dlouhé názvy kategorií čitelné. Dělení 1 000 je v pořádku, pokud popisek uvádí jednotku.",
        "hints": [
            "groupby('category_name')['revenue'].sum().sort_values(ascending=False).",
            "ax.barh(names, values) kreslí vodorovné sloupce; obraťte pořadí, aby byl největší nahoře.",
            "Použijte ax.set_title a ax.set_xlabel / set_ylabel.",
        ],
        "checks": [
            {"name": "hodnoty cat_rev", "msgs": ["'Hodnoty cat_rev se liší - zkontrolujte filtry 2024 + Completed a chybějící slevy.'", "'cat_rev má být seřazená sestupně.'"]},
            {"name": "8 sloupců seřazených podle hodnoty", "msgs": [NO_FIG, NO_BARS, "f'Očekáváno 8 sloupců (jeden na kategorii), nalezeno {len(bars)}.'", "'Sloupce nejsou seřazeny podle hodnoty. Před vykreslením data seřaďte.'"]},
            {"name": "sloupce úměrné tržbám", "msgs": [NO_FIG, NO_BARS, "'Délky sloupců nejsou úměrné tržbám kategorií.'"]},
            {"name": "název a jednotka v popisku", "msgs": [NO_FIG, "'Přidejte název.'", "'Popisek osy má uvádět jednotku (EUR).'"]},
        ],
        "visible_tests": ["cat_rev je správná a seřazená", "8 seřazených sloupců úměrných tržbám", "Název a popisek s jednotkou jsou přítomné"],
        "rubric": [("Správná data", 30), ("Vhodný seřazený graf", 40), ("Popisky", 30)],
    },
    "ex_py_vz2_line": {
        "title": "Anotovaný trend měsíčních tržeb",
        "topic": "Spojnicové grafy a anotace",
        "business_question": "Ukažte trend měsíčních tržeb 2023-2024 a vyznačte měsíc s vrcholem.",
        "requirements": [
            "`monthly`: Series tržeb z dokončených objednávek za měsíc (24 hodnot, chronologicky).",
            "Spojnicový graf měsíčních tržeb s osou y začínající na 0.",
            "Název, popisek osy x a popisek osy y s jednotkou (EUR).",
            "Alespoň jedna anotace (ax.annotate nebo ax.text) označující měsíc s vrcholem.",
        ],
        "expected_output": "Series a anotovaný spojnicový graf.",
        "explanation": "Anotace umístí klíčový fakt tam, kam se oko dívá; osa od nuly drží sezónní výkyvy ve správném poměru.",
        "hints": [
            "Seskupte podle df['order_date'].dt.to_period('M').",
            "ax.set_ylim(bottom=0).",
            "ax.annotate('text', xy=(x, y), xytext=(x2, y2), arrowprops=dict(arrowstyle='->')).",
        ],
        "checks": [
            {"name": "měsíční hodnoty", "msgs": ["f'Očekáváno 24 měsíců, máte {len(m)}.'", "'Měsíční tržby se liší nebo nejsou v chronologickém pořadí.'"]},
            {"name": "čára s 24 body", "msgs": [NO_FIG, "'Nakreslete spojnicový graf pomocí ax.plot (24 měsíčních bodů).'", "'Čára má mít 24 bodů.'"]},
            {"name": "osa od nuly", "msgs": [NO_FIG, "f'Osa y začíná na {ax.get_ylim()[0]:.0f}; nastavte ax.set_ylim(bottom=0).'"]},
            {"name": "popisky a název", "msgs": [NO_FIG, "'Přidejte název.'", "'Popište osu x.'", "'Popisek osy y má obsahovat jednotku (EUR).'"]},
            {"name": "anotace je přítomná", "msgs": [NO_FIG, "'Přidejte anotaci měsíce s vrcholem (ax.annotate nebo ax.text).'"]},
        ],
        "visible_tests": ["24 měsíčních hodnot", "Čára s 24 body", "Osa y začíná na 0", "Název a popisky s jednotkou", "Alespoň jedna anotace"],
        "rubric": [("Správná data", 25), ("Poctivá škála", 25), ("Popisky", 25), ("Anotace", 25)],
    },
    "ex_py_vz3_highlight": {
        "title": "Zvýrazněte problémový kanál",
        "topic": "Zvýrazňující barva a přímé popisky",
        "business_question": "Udělejte zřejmým, který akviziční zdroj má nejvyšší odchod.",
        "requirements": [
            "Jeden sloupec na akviziční zdroj (5 sloupců) s šestiměsíční mírou odchodu.",
            "Právě jeden sloupec (Paid Social, nejvyšší) ve zvýrazňující barvě; všechny ostatní sloupce sdílejí jednu neutrální barvu.",
            "Žádná legenda. Názvy kategorií na ose. Název grafu.",
        ],
        "expected_output": "Sloupcový graf s 5 sloupci, jeden zvýrazněný.",
        "explanation": "Šedá pro kontext a jedna akcentní barva pro to podstatné je nejrychlejší způsob, jak nasměrovat pozornost, a ve spojení s popisky funguje i pro barvoslepé čtenáře.",
        "hints": [
            "Sestavte seznam barev: neutrální pro všechny, akcentní pro 'Paid Social'.",
            "Předejte color=colors do ax.bar/ax.barh.",
            "Nevolejte ax.legend().",
        ],
        "checks": [
            {"name": "pět sloupců", "msgs": [NO_FIG, NO_BARS, "f'Očekáváno 5 sloupců, nalezeno {len(bars)}.'"]},
            {"name": "právě jeden zvýrazněný sloupec", "msgs": [NO_FIG, NO_BARS, "f'Použijte právě dvě barvy (neutrální + zvýrazňující); nalezeno {len(cnt)}.'", "'Zvýrazňující barvu má mít právě jeden sloupec.'"]},
            {"name": "zvýrazněn je Paid Social (nejvyšší)", "msgs": [NO_FIG, NO_BARS, "'Zvýrazněný má být sloupec s nejvyšším odchodem.'", "f'Zvýrazněný sloupec má popisek {tick_text[i]!r}, očekáváno Paid Social.'"]},
            {"name": "bez legendy, s názvem", "msgs": [NO_FIG, "'Odstraňte legendu; kategorie raději popište na ose.'", "'Přidejte název, který uvádí závěr.'"]},
        ],
        "visible_tests": ["5 sloupců", "Právě jeden zvýrazněný sloupec", "Zvýraznění = nejvyšší odchod (Paid Social)", "Bez legendy, název přítomen"],
        "rubric": [("Správná data", 25), ("Účelná barva", 50), ("Čistý design", 25)],
    },
    "ex_py_vz4_fix": {
        "title": "Opravte zavádějící graf A/B testu",
        "topic": "Oříznuté osy",
        "business_question": "Připravený kód reprodukuje zavádějící snímek. Udělejte ho poctivým.",
        "requirements": [
            "Ponechte sloupcový graf míry konverze (%) pro control a treatment.",
            "Osa hodnot musí začínat na 0.",
            "Popisek osy hodnot musí uvádět jednotku (% nebo percent). Přidejte neutrální, přesný název (žádné „huge win“).",
            "Přidejte ke sloupcům popisky hodnot (ax.bar_label nebo ax.text).",
        ],
        "expected_output": "Opravený sloupcový graf se 2 sloupci.",
        "explanation": "Sloupce od nuly obnoví úměrné délky; popisky dají přesné hodnoty; název výsledek poctivě sděluje.",
        "hints": [
            "ax.set_ylim(0, ...) nebo jednoduše odstraňte vlastní meze.",
            "ax.set_ylabel('Míra konverze (%)').",
            "ax.bar_label(bars) přidá popisky hodnot.",
        ],
        "checks": [
            {"name": "dva sloupce", "msgs": [NO_FIG, NO_BARS, "f'Očekávány 2 sloupce, nalezeno {len(bars)}.'"]},
            {"name": "osa od nuly", "msgs": [NO_FIG, NO_BARS, "f'Osa hodnot začíná na {lo}; sloupce musí začínat na 0.'"]},
            {"name": "jednotka v popisku", "msgs": [NO_FIG, NO_BARS, "'Popište osu hodnot její jednotkou (%).'"]},
            {"name": "poctivý název", "msgs": [NO_FIG, "'Přidejte název.'", "'Název stále výsledek přeceňuje.'"]},
            {"name": "popisky hodnot", "msgs": [NO_FIG, "'Přidejte popisky hodnot k oběma sloupcům (ax.bar_label).'"]},
        ],
        "visible_tests": ["2 sloupce", "Osa hodnot začíná na 0", "Popisek s jednotkou", "Neutrální název", "Popisky hodnot"],
        "rubric": [("Úměrné sloupce", 40), ("Jasné popisky", 30), ("Poctivé podání", 30)],
    },
    "ex_py_vz5_uncertainty": {
        "title": "Ukažte nejistotu",
        "topic": "Chybové úsečky a intervaly spolehlivosti",
        "business_question": "Prezentujte konverzi A/B testu podle zařízení s poctivě vyjádřenou nejistotou.",
        "requirements": [
            "`ci_table`: DataFrame se sloupci device, variant, rate, ci_low, ci_high (95% Waldův IS: rate +/- 1.96*sqrt(rate*(1-rate)/n), jako zlomky). 6 řádků.",
            "Graf s chybovými úsečkami (ax.errorbar nebo yerr u sloupců) zobrazující všech 6 odhadů.",
            "Název a popisek osy y s jednotkou.",
        ],
        "expected_output": "DataFrame se 6 řádky a graf s chybovými úsečkami.",
        "explanation": "Šířka intervalů ukazuje, kde jsou důkazy slabé (tablet). Vizualizace nejistoty brání přeceňování malých rozdílů.",
        "hints": [
            "se = sqrt(p(1-p)/n) pro každou kombinaci zařízení x varianta.",
            "ax.errorbar(x, y, yerr=..., fmt='o', capsize=5).",
            "Pozice x pro obě varianty mírně posuňte.",
        ],
        "checks": [
            {"name": "hodnoty ci_table"},
            {"name": "chybové úsečky vykresleny", "msgs": [NO_FIG, "'Nebyly nalezeny chybové úsečky. Použijte ax.errorbar(...) nebo ax.bar(..., yerr=...).'", "f'Zobrazte všech 6 odhadů zařízení x varianta (nalezeno {max(n, bars_n)}).'"]},
            {"name": "popisky", "msgs": [NO_FIG, "'Přidejte název.'", "'Popište osu y metrikou a jednotkou.'"]},
        ],
        "visible_tests": ["ci_table odpovídá referenci", "Chybové úsečky pro všech 6 odhadů", "Název a popisek osy y"],
        "rubric": [("Správné intervaly", 40), ("Viditelná nejistota", 40), ("Popisky", 20)],
    },
}
