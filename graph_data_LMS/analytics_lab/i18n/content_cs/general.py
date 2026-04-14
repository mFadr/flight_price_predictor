"""Czech module names, module questions and competency descriptions."""

MODULES = {
    "descriptive": "Deskriptivní analytika",
    "diagnostic": "Diagnostická analytika",
    "predictive": "Prediktivní analytika",
    "prescriptive": "Preskriptivní analytika",
    "visualization": "Vizualizace dat",
}

MODULE_QUESTIONS = {
    "descriptive": "Co se stalo, co se právě děje a jak shrnout výkon firmy?",
    "diagnostic": "Proč se něco stalo a jaké důkazy vysvětlení podporují?",
    "predictive": "Co se pravděpodobně stane a jak spolehlivá je tato předpověď?",
    "prescriptive": "Co bychom měli udělat vzhledem k důkazům, omezením, rizikům a zdrojům?",
    "visualization": "Jak data sdělit jasně, přesně a přesvědčivě?",
}

COMPETENCIES = {
    "sql_basics": {"name": "Základy dotazování v SQL", "description": "Správně vybírat, filtrovat, řadit a agregovat řádky."},
    "sql_aggregation": {"name": "Agregace a podmíněná logika", "description": "GROUP BY/HAVING, CASE a práce s NULL pro byznysové souhrny."},
    "sql_joins": {"name": "Spojování, CTE a poddotazy", "description": "Kombinovat tabulky bez zdvojování či ztráty řádků; strukturovat vícekrokové dotazy."},
    "sql_window": {"name": "Okenní funkce a časová srovnání", "description": "Pořadí, průběžné součty, srovnání období."},
    "excel_analysis": {"name": "Analýza v tabulkovém procesoru", "description": "Vzorce, vyhledávání, kontingenční tabulky a auditovatelný návrh sešitu."},
    "bi_modeling": {"name": "BI datové modelování a DAX", "description": "Hvězdicová schémata, relace, míry a kontext filtru."},
    "kpi_reporting": {"name": "Návrh KPI a reporting", "description": "Definovat, počítat a interpretovat byznysové KPI."},
    "data_quality": {"name": "Kvalita dat a EDA", "description": "Odhalovat chybějící hodnoty, duplicity, odlehlé hodnoty a nekonzistentní záznamy."},
    "segmentation_rca": {"name": "Segmentace a analýza příčin", "description": "Rozkládat změny KPI a porovnávat segmenty pro lokalizaci příčin."},
    "cohort_funnel": {"name": "Kohorty, retence a trychtýře", "description": "Sestavovat kohortní tabulky, retenční křivky a trychtýře."},
    "statistical_inference": {"name": "Statistická inference a A/B testy", "description": "Testy hypotéz, intervaly spolehlivosti, praktická významnost."},
    "causal_reasoning": {"name": "Kauzální uvažování", "description": "Matoucí proměnné, Simpsonův paradox, korelace vs. kauzalita."},
    "r_programming": {"name": "R pro analýzu", "description": "Datové rámce, seskupování a statistické testy v R."},
    "ml_framing": {"name": "Formulace predikce a únik informací", "description": "Definovat cíle, rozdělení dat a baseliny; předcházet úniku informací."},
    "regression_modeling": {"name": "Regresní modelování", "description": "Fitovat a vyhodnocovat regresní modely pomocí MAE/RMSE/R²."},
    "classification_modeling": {"name": "Klasifikace a prahy", "description": "Klasifikátory, matice záměn, precision/recall, prahy."},
    "model_validation": {"name": "Validace, ladění a pipeline", "description": "Křížová validace, pipeline, ladění a přeučení/podučení."},
    "forecasting": {"name": "Předpovídání časových řad", "description": "Časová rozdělení, sezónní baseliny a přesnost předpovědí."},
    "responsible_ml": {"name": "Interpretace a odpovědné použití", "description": "Důležitost příznaků, nejistota, drift a férovost."},
    "optimization_modeling": {"name": "Optimalizační modelování", "description": "Rozhodovací proměnné, účelové funkce, omezení a řešení LP."},
    "simulation_risk": {"name": "Simulace a riziko", "description": "Simulace Monte Carlo a rozhodování s ohledem na riziko."},
    "decision_analysis": {"name": "Rozhodovací a citlivostní analýza", "description": "Scénáře, citlivost, analýza nákladů a přínosů a doporučení."},
    "chart_selection": {"name": "Výběr grafu", "description": "Přiřazovat typy grafů k analytickým otázkám a publiku."},
    "viz_coding": {"name": "Programování vizualizací (Matplotlib)", "description": "Vytvářet v kódu správné grafy s popisky."},
    "viz_integrity": {"name": "Design a poctivost", "description": "Přístupný, poctivý a nepřeplácaný vizuální design."},
    "storytelling": {"name": "Dashboardy a vyprávění", "description": "Dashboardy, manažerská shrnutí a komunikace nejistoty."},
}

# Rubric lines shared by many exercises (criterion text -> Czech).
RUBRIC = {
    "Result set matches the expected rows and values": "Výsledek odpovídá očekávaným řádkům a hodnotám",
    "Correct columns and names": "Správné sloupce a názvy",
    "Correct number of rows": "Správný počet řádků",
}
