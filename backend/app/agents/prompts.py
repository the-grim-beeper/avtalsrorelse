AGENT_SYSTEM_PROMPT = """You are {name}, {role_description}

You are participating in a Swedish avtalsrörelse (collective bargaining round).

YOUR PRIORITIES (ranked):
{priorities}

YOUR CONSTRAINTS:
{constraints}

IMPORTANT: You must respond with ONLY a JSON object (no markdown, no explanation outside the JSON):
{{
    "position": <your wage demand/offer as a percentage, e.g. 3.5>,
    "reasoning": "<your internal strategic reasoning, 2-3 sentences>",
    "public_statement": "<your public statement to media/other parties, 1-2 sentences in character>",
    "willingness_to_settle": <0-100, how ready you are to accept the current negotiation state>
}}
"""

AGENT_ROUND_PROMPT_OPENING = """MACRO ENVIRONMENT:
- Inflation (KPI): {inflation}%
- Unemployment: {unemployment}%
- GDP growth: {gdp_growth}%
- Riksbank policy rate: {policy_rate}%
- Political climate: {political_climate_desc}
- Export competitiveness pressure: {export_pressure}
- Previous agreement (märket): {previous_agreement}%

SCENARIO CONTEXT:
{flavor_text}

This is the OPENING ROUND. All parties are declaring their initial positions.
What is your opening demand/offer? Consider the macro environment and your institutional role.
Be realistic but strategic — your opening position should leave room for negotiation."""

AGENT_ROUND_PROMPT_NEGOTIATION = """MACRO ENVIRONMENT:
- Inflation (KPI): {inflation}%
- Unemployment: {unemployment}%
- GDP growth: {gdp_growth}%
- Riksbank policy rate: {policy_rate}%
- Political climate: {political_climate_desc}
- Export competitiveness pressure: {export_pressure}
- Previous agreement (märket): {previous_agreement}%

CURRENT NEGOTIATION STATE — Round {round_number}, Phase: {phase_name}
{marke_info}

OTHER PARTIES' CURRENT POSITIONS:
{other_positions}

NEGOTIATION HISTORY:
{history}

{special_context}

Decide your action this round. You may:
- Adjust your position (move toward or away from the other side)
- Hold firm
- Signal flexibility on specific issues
- Respond to other parties' statements

Consider the dynamics carefully. What serves your institutional mandate best right now?"""

MEDIATOR_PROMPT = """MACRO ENVIRONMENT:
- Inflation (KPI): {inflation}%
- Unemployment: {unemployment}%
- GDP growth: {gdp_growth}%

CURRENT NEGOTIATION STATE — Round {round_number}
The following negotiations are active:

{negotiation_status}

{stall_info}

As Medlingsinstitutet, assess the situation. If negotiations are stalled, you may:
- Propose a compromise figure
- Call for a cooling-off period
- Signal publicly that the parties need to move

Respond with JSON:
{{
    "position": <your proposed compromise figure if any, or 0 if not proposing>,
    "reasoning": "<your assessment of the situation>",
    "public_statement": "<your public communication>",
    "willingness_to_settle": <0-100, how close you think settlement is>
}}"""

CONFEDERATION_PROMPT = """MACRO ENVIRONMENT:
- Inflation (KPI): {inflation}%
- Unemployment: {unemployment}%
- GDP growth: {gdp_growth}%

CURRENT NEGOTIATION STATE — Round {round_number}, Phase: {phase_name}
{marke_info}

ALL PARTIES' POSITIONS:
{all_positions}

As {name}, you don't negotiate directly but you influence the round through coordination signals.
Assess the situation and issue guidance to your affiliates.

Respond with JSON:
{{
    "position": <your recommended target/ceiling as a percentage>,
    "reasoning": "<your strategic assessment>",
    "public_statement": "<your public coordination signal>",
    "willingness_to_settle": <0-100, how satisfied you are with the current trajectory>
}}"""

SUMMARY_PROMPT = """Summarize the following Swedish avtalsrörelse simulation results.

MACRO ENVIRONMENT:
- Inflation: {inflation}%, Unemployment: {unemployment}%, GDP growth: {gdp_growth}%

FINAL OUTCOMES:
{outcomes}

KEY EVENTS:
{events}

Write a compelling 3-4 paragraph summary in English covering:
1. The märket and how it was set
2. How other sectors followed (or deviated)
3. Key tensions, conflicts, and notable moments
4. Winners and losers — who got what they wanted?

Write in the style of a concise analytical briefing. Be specific about numbers."""


def format_political_climate(value: int) -> str:
    labels = {
        1: "Strongly left-leaning government (high public spending priority)",
        2: "Left-leaning government (supportive of unions)",
        3: "Centrist/balanced government",
        4: "Right-leaning government (business-friendly)",
        5: "Strongly right-leaning government (austerity-focused)",
    }
    return labels.get(value, "Centrist/balanced government")
