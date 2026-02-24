from app.models.scenario import ExportPressure, MacroParameters, ScenarioPreset

PRESETS: dict[str, ScenarioPreset] = {
    "stabil_tillvaxt": ScenarioPreset(
        id="stabil_tillvaxt",
        name="Stabil tillväxt (2017)",
        description="Low inflation, moderate growth, low interest rates. A calm and predictable negotiation round.",
        flavor_text=(
            "The Swedish economy is humming along nicely. Inflation is below target, "
            "growth is steady, and the labor market is balanced. The Riksbank is still "
            "in negative rate territory. There is no crisis, no urgency — just the "
            "routine machinery of the Swedish model. Both sides expect a modest, "
            "uncontroversial settlement."
        ),
        parameters=MacroParameters(
            inflation=1.8, unemployment=6.7, gdp_growth=2.4, policy_rate=-0.5,
            political_climate=3, export_pressure=ExportPressure.MEDIUM, previous_agreement=2.2,
        ),
    ),
    "inflationschock": ScenarioPreset(
        id="inflationschock",
        name="Inflationschock (2023)",
        description="Surging inflation, rising rates, cost-of-living crisis. The hardest round in decades.",
        flavor_text=(
            "Inflation has surged past 10% for the first time since the 1990s. "
            "Energy prices, food costs, and mortgage rates are crushing households. "
            "Workers demand compensation for lost purchasing power. Employers warn "
            "that a wage-price spiral would be catastrophic. The Riksbank has raised "
            "rates aggressively. This is the most contentious round in a generation."
        ),
        parameters=MacroParameters(
            inflation=10.6, unemployment=7.5, gdp_growth=0.3, policy_rate=4.0,
            political_climate=4, export_pressure=ExportPressure.HIGH, previous_agreement=2.5,
        ),
    ),
    "90talskrisen": ScenarioPreset(
        id="90talskrisen",
        name="90-talskrisen",
        description="Deep recession, mass unemployment, fiscal emergency. Survival mode.",
        flavor_text=(
            "Sweden is in the worst economic crisis since the 1930s. Banks are failing, "
            "unemployment has tripled in two years, and the government is running massive "
            "deficits. The krona has been floated and is falling. There is a genuine fear "
            "that the Swedish model itself is at stake. Unions are on the defensive, "
            "employers push for structural reform."
        ),
        parameters=MacroParameters(
            inflation=4.5, unemployment=12.0, gdp_growth=-3.5, policy_rate=8.0,
            political_climate=4, export_pressure=ExportPressure.HIGH, previous_agreement=3.0,
        ),
    ),
    "hogkonjunktur": ScenarioPreset(
        id="hogkonjunktur",
        name="Högkonjunktur",
        description="Economic boom, labor shortage, record profits. Unions push hard.",
        flavor_text=(
            "The economy is overheating. Companies report record profits and can't find "
            "enough workers. Unemployment is at historic lows. Workers see their leverage "
            "and unions push for aggressive wage increases. Employers can afford it but "
            "worry about overheating and the Riksbank's reaction. The mood is confident "
            "but the stakes are high."
        ),
        parameters=MacroParameters(
            inflation=3.0, unemployment=3.5, gdp_growth=4.5, policy_rate=2.0,
            political_climate=2, export_pressure=ExportPressure.LOW, previous_agreement=2.8,
        ),
    ),
    "gron_omstallning": ScenarioPreset(
        id="gron_omstallning",
        name="Grön omställning",
        description="Green transition reshaping industries. New competence demands, structural upheaval.",
        flavor_text=(
            "The green transition is in full swing. Northern Sweden is booming with "
            "battery factories and green steel. Traditional industries face massive "
            "restructuring. The demand for skilled workers is enormous but in new areas. "
            "Unions want reskilling guarantees and transition security. Employers want "
            "flexibility to hire globally and restructure quickly. The old categories "
            "are breaking down."
        ),
        parameters=MacroParameters(
            inflation=2.5, unemployment=5.5, gdp_growth=3.0, policy_rate=2.0,
            political_climate=2, export_pressure=ExportPressure.MEDIUM, previous_agreement=2.5,
        ),
    ),
    "pandemi_aterhamtning": ScenarioPreset(
        id="pandemi_aterhamtning",
        name="Pandemiåterhämtning",
        description="Post-pandemic recovery. Private sector bounces back while public sector is exhausted and broke.",
        flavor_text=(
            "The pandemic is over but the scars remain. The private sector has recovered "
            "strongly — tech and manufacturing are booming. But the public sector is "
            "exhausted. Healthcare workers are burned out and leaving in droves. "
            "Municipal finances are strained after years of emergency spending. "
            "The gap between private and public sector working conditions has never "
            "been wider. Vårdförbundet is furious."
        ),
        parameters=MacroParameters(
            inflation=3.5, unemployment=8.0, gdp_growth=4.0, policy_rate=0.5,
            political_climate=3, export_pressure=ExportPressure.LOW, previous_agreement=2.0,
        ),
    ),
}
