"""
B2C System Prompt for Restaurant Customers
Two-phase system:
- Phase 1 (Gathering): Collect wine preferences from customer
- Phase 2 (Recommending): Make wine recommendations based on gathered info
"""
from typing import Optional, Dict, List
import math


def calculate_bottles_needed(guest_count: int, courses_per_person: float = 2.0) -> int:
    """
    Calculate number of wine bottles needed for a table.
    
    Formula:
    - 1 bottle = 6 glasses
    - 1 person per course = 1 glasses
    - Average courses per person for wine journey = 2.0
    
    Rounding rule: if decimal > 0.5 → round up, else round down
    
    Args:
        guest_count: Number of people at the table
        courses_per_person: Average number of courses per person (default 2.0)
        
    Returns:
        Number of bottles needed (rounded)
    """
    glasses_per_person_per_course = 1
    glasses_per_bottle = 6.0
    
    # Total glasses needed
    total_glasses = guest_count * courses_per_person * glasses_per_person_per_course
    
    # Bottles needed (with decimal)
    bottles_decimal = total_glasses / glasses_per_bottle
    
    # Rounding: if decimal part > 0.5, round up, else round down
    decimal_part = bottles_decimal - math.floor(bottles_decimal)
    
    if decimal_part > 0.5:
        return math.ceil(bottles_decimal)
    else:
        return math.floor(bottles_decimal)


def get_b2c_opening_prompt(
    venue_name: str,
    sommelier_style: str = 'professional',
    context: Optional[Dict] = None,
    gathered_info: Optional[Dict] = None
) -> str:
    """
    Generate opening prompt for the FIRST message only.
    Welcomes customer, recaps choices, asks for special requirements.
    NO wine suggestions or recommendations.
    """
    
    # Style variations
    style_intros = {
        'professional': f"Sei il sommelier di {venue_name}. Sei elegante, competente e accogliente.",
        'friendly': f"Sei il sommelier di {venue_name}. Sei caloroso e informale, fai sentire i clienti come amici.",
        'expert': f"Sei il sommelier di {venue_name}. Sei un esperto accessibile che ama condividere la sua passione.",
        'playful': f"Sei il sommelier di {venue_name}. Sei creativo e ami rendere la scelta del vino un momento piacevole."
    }
    
    intro = style_intros.get(sommelier_style, style_intros['professional'])
    
    # Build context
    dishes = context.get('dishes', []) if context else []
    guest_count = context.get('guest_count', 2) if context else 2
    
    # Build dish list and characteristics
    dish_list = []
    dish_characteristics = []
    
    for dish in dishes:
        dish_name = dish.get('name', 'Piatto')
        main_ingredient = dish.get('main_ingredient', '').lower() if dish.get('main_ingredient') else ''
        dish_list.append(dish_name)
        
        # Analyze dish for characteristics using main_ingredient if available, otherwise dish name
        search_text = main_ingredient if main_ingredient else dish_name.lower()
        
        if any(word in search_text for word in ['carne', 'manzo', 'vitello', 'agnello', 'tagliata', 'bistecca', 'maiale', 'pollo']):
            dish_characteristics.append('carni')
        elif any(word in search_text for word in ['pesce', 'branzino', 'orata', 'tonno', 'salmone', 'vongole', 'cozze', 'gamberi', 'gamberetti']):
            dish_characteristics.append('pesce')
        elif any(word in search_text for word in ['pasta', 'risotto', 'tagliatelle', 'tortelli']):
            dish_characteristics.append('primi')
        elif any(word in search_text for word in ['formaggio', 'burrata', 'mozzarella', 'parmigiano']):
            dish_characteristics.append('formaggi')
        elif any(word in search_text for word in ['funghi', 'porcini', 'tartufo']):
            dish_characteristics.append('sapori terrosi')
    
    unique_chars = list(set(dish_characteristics))
    characteristics_desc = ", ".join(unique_chars) if unique_chars else "piatti vari"
    
    # Build preferences summary
    info = gathered_info or {}
    journey_pref = info.get('journey_preference', 'single')
    wine_type = info.get('wine_type', 'any')
    budget = info.get('budget')
    
    journey_text = "un percorso di vini diversi" if journey_pref == 'journey' else "una singola etichetta"
    wine_type_text = "si affida alla tua esperienza" if wine_type == 'any' else wine_type
    
    if budget is None or budget == 'nolimit':
        budget_text = 'senza limiti di budget'
    elif isinstance(budget, (int, float)):
        budget_text = f'massimo €{budget:.2f} per bottiglia'
    else:
        budget_labels = {
            'base': 'base (fino a €20)', 'spinto': 'spinto (€20-40)',
            'low': 'base (fino a €20)', 'medium': 'spinto (€20-40)',
            'high': 'senza limiti', 'any': 'senza limiti'
        }
        budget_text = budget_labels.get(budget, str(budget))
    
    prompt = f"""{intro}

## IL TUO OBIETTIVO

Dare il benvenuto, fare un breve recap delle scelte del cliente, e chiedere se hanno esigenze particolari.

**STRUTTURA:**

1. Benvenuto caloroso (una riga)

2. Recap:
   - Piatti: {', '.join(dish_list) if dish_list else 'nessuno'}
   - Commensali: {guest_count}
   - Modalità (journey vuol dire etichette diverse, altrimenti singola etichetta): {journey_text}
   - Tipo vino: {wine_type_text}
   - Budget: {budget_text}

3. Caratteristiche piatti (due righe): {characteristics_desc}

4. Chiedi esigenze particolari (allergie, gusti da evitare, occasioni speciali)

**REGOLE:**
- NON proporre vini o raccomandazioni
- NON menzionare "proposta" o "raccomandazione"
- Sii BREVE: massimo 80 parole
- NO ragionamenti, solo benvenuto e recap
- Aspetta la risposta del cliente

Rispondi sempre in italiano."""

    return prompt


def get_b2c_system_prompt(
    venue_name: str,
    cuisine_type: Optional[str] = None,
    sommelier_style: str = 'professional',
    context: Optional[Dict] = None,
    gathered_info: Optional[Dict] = None,
    is_first_message: bool = False
) -> str:
    """
    Generate prompt for wine recommendations.
    Used AFTER opening prompt, when customer has confirmed.
    """
    
    style_intros = {
        'professional': f"Sei il sommelier di {venue_name}. Sei elegante e competente, sai raccontare il vino con passione.",
        'friendly': f"Sei il sommelier di {venue_name}. Sei caloroso, informale e ami condividere la tua passione per il vino.",
        'expert': f"Sei il sommelier di {venue_name}. Sei un esperto che sa rendere accessibile anche il vino più complesso.",
        'playful': f"Sei il sommelier di {venue_name}. Sei creativo e ami sorprendere, rendendo ogni scelta un piccolo racconto."
    }
    
    intro = style_intros.get(sommelier_style, style_intros['professional'])
    
    # Build context
    meal_context = ""
    guest_count = 2
    
    if context:
        dishes = context.get('dishes', [])
        guest_count = context.get('guest_count', 2)
        
        if dishes:
            meal_context = "\n## Piatti Ordinati\n"
            for dish in dishes:
                dish_line = f"- {dish.get('name', 'Piatto')}"
                if dish.get('category'):
                    dish_line += f" ({dish['category']})"
                meal_context += dish_line + "\n"
        
        meal_context += f"\nCommensali: {guest_count}\n"
    
    # Build preferences
    preferences_context = "\n## Preferenze Cliente (già raccolte - NON chiedere di nuovo)\n"
    info = gathered_info or {}
    
    wine_type = info.get('wine_type', 'any')
    preferences_context += f"- Tipo vino: {wine_type if wine_type != 'any' else 'Si affida al sommelier'}\n"
    
    journey_pref = info.get('journey_preference', 'single')
    bottles_count = info.get('bottles_count')
    
    if journey_pref == 'journey':
        if bottles_count:
            preferences_context += f"- Modalità: PERCORSO di {bottles_count} {('bottiglia' if bottles_count == 1 else 'bottiglie')} (già confermato)\n"
        else:
            preferences_context += "- Modalità: PERCORSO (numero bottiglie da confermare)\n"
    else:
        preferences_context += "- Modalità: SINGOLA etichetta (con alternative)\n"
    
    budget = info.get('budget')
    if budget is None or budget == 'nolimit':
        preferences_context += "- Budget: Nessuna restrizione\n"
    elif isinstance(budget, (int, float)):
        budget_max = float(budget)
        min_price = budget_max * 0.80  # budget - 20%
        max_price = budget_max * 1.15  # budget + 15%
        preferences_context += f"- Budget: Massimo €{budget:.2f} per bottiglia (la carta è già filtrata per includere vini tra €{min_price:.2f} e €{max_price:.2f})\n"
    
    # Format instructions
    if journey_pref == 'journey':
        if bottles_count:
            format_instructions = f"""
## FORMATO (PERCORSO {bottles_count} BOTTIGLIE)

Proponi almeno 2 percorsi completi. Ogni percorso contiene esattamente {bottles_count} vini.

**Per iniziare** - [Nome Vino ESATTO] - €[Prezzo]
[Descrizione breve e evocativa]
Lo berremo con [piatto specifico]

**Per proseguire** - [Nome Vino ESATTO] - €[Prezzo]
[Come evolve rispetto al primo]
Questo accompagnerà [piatto specifico]

[Aggiungi altri vini se necessario per raggiungere {bottles_count} bottiglie]

**Come si beve questo percorso**: [Spiegazione ordine degustazione]
"""
        else:
            suggested_bottles = calculate_bottles_needed(guest_count)
            format_instructions = f"""
## FORMATO (PERCORSO - CONFERMA BOTTIGLIE PRIMA)

Prima suggerisci {suggested_bottles} bottiglie e chiedi conferma. Solo DOPO la conferma, proponi i vini.

**Per iniziare** - [Nome Vino ESATTO] - €[Prezzo]
[Descrizione]
Lo berremo con [piatto]

**Per proseguire** - [Nome Vino ESATTO] - €[Prezzo]
[Descrizione]
Questo accompagnerà [piatto]
"""
    else:
        format_instructions = """
## FORMATO (SINGOLA ETICHETTA)

Proponi ALMENO 2 alternative (ideale 2-4, ma puoi aggiungere altre se molto affini al profilo richiesto):

**Il mio consiglio** - [Nome Vino ESATTO] - €[Prezzo]
[Descrizione breve e perché è perfetto per i loro piatti]

**Un'alternativa interessante** - [Nome Vino ESATTO] - €[Prezzo]
[Perché potrebbe piacere, differenza rispetto al primo]

[Se ci sono altre alternative molto affini al profilo richiesto, aggiungile con lo stesso formato]
"""
    
    prompt = f"""{intro}

{meal_context}
{preferences_context}

## IL TUO COMPORTAMENTO

{"**Se è la prima risposta**: Dà il benvenuto, fai un breve recap naturale, poi procedi con le raccomandazioni." if is_first_message else "**Se è una risposta successiva**: NON ricominciare con benvenuto/recap. Rispondi direttamente alla richiesta mantenendo il contesto. Continua la conversazione naturalmente."}

## COME PARLI

**EVITA:**
- Frasi tecniche/metadescrittive ("basata esclusivamente sui dati forniti", "rispetta tutti i criteri")
- Riferimenti espliciti a "preferenze raccolte" o "parametri"
- Elenchi meccanici

**USA:**
- Linguaggio naturale e conversazionale
- Racconta il vino, le sue caratteristiche, l'abbinamento con i piatti
- "Guardando i vostri piatti, mi viene in mente...", "C'è un vino che racconta perfettamente questa serata..."

{format_instructions}

## REGOLE CRITICHE

1. **SOLO VINI DALLA CARTA**: Mai inventare vini, nomi, cantine, annate. Se non è nella carta, NON ESISTE. Proponi sempre qualcosa dalla carta.

2. **DA 3 A 5 ALTERNATIVE**: Devi proporre DA 3 A 5 vini diversi dalla carta quando possibile. Se la carta ha molti vini affini al profilo richiesto, suggerisci 3-4 alternative per dare più scelta al cliente. Solo se ci sono pochi vini disponibili, puoi proporre 2 vini.

3. **BUDGET E OTTIMIZZAZIONE RICAVO**: 
   - L'obiettivo è OTTIMIZZARE IL RICAVO proponendo vini quanto più vicini al budget indicato
   - Proponi sempre vini che si avvicinano al budget (non troppo al di sotto, idealmente vicino al limite)
   - Mantieni SEMPRE l'affinità con le richieste del cliente (piatti, preferenze, tipo vino)
   - Se il budget è €30, preferisci vini tra €25-30 piuttosto che €15-20, mantenendo comunque l'aderenza ai piatti
   - **Bilanciamento**: Massimizza il valore proponendo vini di qualità che si avvicinano al limite superiore del budget, sempre mantenendo la pertinenza con le preferenze

4. **NOMI ESATTI DEI VINI - CRITICO**: 
   ⚠️ Quando proponi un vino, DEVI SEMPRE menzionare il NOME ESATTO così come appare nella "Carta dei Vini Disponibili".
   - Se nella carta c'è "Focara Pinot Noir D.O.C. 2014", DEVI dire esattamente "Focara Pinot Noir D.O.C. 2014"
   - NON dire "un Pinot Noir" o "Focara" o "un vino della cantina Focara"
   - Usa sempre il nome completo con annata, denominazione, etc.
   - Questo è ESSENZIALE: senza il nome esatto, il sistema non può mostrare le card corrette

5. **MAI DESSERT WINE CON PIATTI SALATI**: Non proporre mai vini passiti, dolci, dessert wine con antipasti/primi/secondi.

6. **FLUSSO NATURALE**: Analizza la conversazione fatta fino a ora e mantieni il flusso naturale. Non ripetere informazioni già date.

7. **PREZZI**: Sempre indicare il prezzo per ogni vino proposto.

Rispondi sempre in italiano."""

    return prompt


def get_finetuned_selection_prompt(
    venue_name: str,
    context: Dict,
    gathered_info: Dict,
    all_wines: List[Dict],
    featured_wines: List[int] = None
) -> str:
    """
    Generate prompt for fine-tuned model to select wines and return structured JSON.
    
    Args:
        venue_name: Name of the venue
        context: Context with dishes, guest_count
        gathered_info: Preferences (wine_type, journey_preference, budget)
        all_wines: Complete list of wines from DB
        featured_wines: Optional list of product IDs to prioritize (max 2)
        
    Returns:
        System prompt for fine-tuned model
    """
    # Build context
    dishes = context.get('dishes', []) if context else []
    guest_count = context.get('guest_count', 2) if context else 2
    
    # Build preferences
    wine_type = gathered_info.get('wine_type', 'any')
    journey_pref = gathered_info.get('journey_preference', 'single')
    budget = gathered_info.get('budget')
    bottles_count = gathered_info.get('bottles_count')
    
    # Handle featured_wines parameter (ensure it's a list)
    if featured_wines is None:
        featured_wines = []
    if not isinstance(featured_wines, list):
        featured_wines = []
    
    # Build wine list context
    wines_context = _build_wines_list_for_finetuned(all_wines)
    
    # Build featured wines context for prompt
    featured_wines_context = ""
    if featured_wines:
        featured_wines_list = []
        for wine_id in featured_wines:
            wine = next((w for w in all_wines if w.get('id') == wine_id), None)
            if wine:
                featured_wines_list.append(f"ID: {wine_id} | {wine.get('name', 'N/D')} | Tipo: {wine.get('type', 'N/D')} | Prezzo: €{wine.get('price', 'N/D')}")
        
        if featured_wines_list:
            featured_wines_context = f"""
## VINI IN EVIDENZA (PRIORITÀ)

I seguenti vini devono avere PRIORITÀ quando rientrano nei parametri del cliente:

{chr(10).join(featured_wines_list)}

IMPORTANTE: Questi vini devono essere proposti con best=true quando appropriati, ma SOLO se rientrano nei parametri (budget, tipo vino, abbinamenti).
"""
    
    # Build featured wines priority rules text
    featured_wines_priority_text = ""
    if featured_wines:
        featured_ids_str = ', '.join(map(str, featured_wines))
        featured_wines_priority_text = f"""⚠️ IMPORTANTE: Ci sono vini in evidenza che devono avere PRIORITÀ quando appropriati:

   - Vini in evidenza (ID: {featured_ids_str}): Questi vini devono essere PROPOSTI quando rientrano nei parametri del cliente (budget, tipo vino, abbinamenti).
   - Se un vino in evidenza rientra nei parametri, DEVE essere incluso nelle proposte con best=true (consiglio principale).
   - Se ci sono 2 vini in evidenza e entrambi rientrano nei parametri, includere entrambi (uno con best=true, l'altro con best=false).
   - La proposta deve essere NATURALE e TRASPARENTE - non menzionare che è una scelta del ristorante.
   - I vini in evidenza hanno PRIORITÀ rispetto ad altri vini simili quando entrambi rientrano nei parametri.
   - Se un vino in evidenza NON rientra nei parametri (es. budget troppo basso, tipo vino diverso), NON forzarlo - procedi normalmente."""
    else:
        featured_wines_priority_text = "Nessun vino in evidenza configurato."
    
    # Build dish context with main_ingredient and cooking_method
    dish_context_parts = []
    for dish in dishes:
        dish_name = dish.get('name', 'Piatto')
        main_ingredient = dish.get('main_ingredient')
        cooking_method = dish.get('cooking_method')
        
        dish_info = f"- {dish_name}"
        if main_ingredient:
            dish_info += f" (Ingrediente principale: {main_ingredient})"
        if cooking_method:
            dish_info += f" (Cottura: {cooking_method})"
        
        dish_context_parts.append(dish_info)
    
    dish_context = "\n".join(dish_context_parts) if dish_context_parts else "Nessun piatto specificato"
    
    # Budget constraints
    budget_text = ""
    budget_max = None
    if budget is None or budget == 'nolimit':
        budget_text = "Nessuna restrizione di budget. Ottimizza il ricavo proponendo vini di qualità."
    elif isinstance(budget, (int, float)):
        budget_max = float(budget)
        min_price = budget_max * 0.80  # budget - 20%
        max_price = budget_max * 1.15  # budget + 15%
        budget_text = f"Budget massimo: €{budget:.2f} per bottiglia (la carta è già filtrata per includere vini tra €{min_price:.2f} e €{max_price:.2f})."
    else:
        budget_labels = {
            'base': 'Budget base: fino a €20 per bottiglia',
            'spinto': 'Budget spinto: €20-40 per bottiglia',
            'low': 'Budget base: fino a €20 per bottiglia',
            'medium': 'Budget spinto: €20-40 per bottiglia',
            'high': 'Nessuna restrizione di budget'
        }
        budget_text = budget_labels.get(budget, 'Nessuna restrizione di budget')
        # Extract numeric budget for single label mode
        if journey_pref == 'single':
            if budget == 'base' or budget == 'low':
                budget_max = 20.0
                min_price = budget_max * 0.80  # 16.0
                max_price = budget_max * 1.15  # 23.0
                budget_text += f" La carta è già filtrata per includere vini tra €{min_price:.2f} e €{max_price:.2f}."
            elif budget == 'spinto' or budget == 'medium':
                budget_max = 40.0
                min_price = budget_max * 0.80  # 32.0
                max_price = budget_max * 1.15  # 46.0
                budget_text += f" La carta è già filtrata per includere vini tra €{min_price:.2f} e €{max_price:.2f}."
    
    # Determine output format
    if journey_pref == 'journey':
        if bottles_count:
            format_spec = f"""
## FORMATO OUTPUT JSON (PERCORSO {bottles_count} BOTTIGLIE)

Devi restituire un JSON con questa struttura:

{{
  "journeys": [
    {{
      "id": 1,
      "name": "Nome del percorso (es. 'Dal Mare alla Terra')",
      "reason": "Spiegazione breve del perché questo percorso è perfetto per i loro piatti",
      "wines": [
        {{"id": <id_vino>, "name": "<nome_esatto_dalla_carta>", "price": <prezzo>}},
        {{"id": <id_vino>, "name": "<nome_esatto_dalla_carta>", "price": <prezzo>}}
        // Esattamente {bottles_count} vini per percorso
      ]
    }}
    // ESATTAMENTE 2-3 percorsi totali
  ]
}}

IMPORTANTE: 
- ESATTAMENTE 2-3 percorsi devono essere generati
- Ogni percorso deve contenere esattamente {bottles_count} vini
- NON generare più di 3 percorsi, NON generare meno di 2 percorsi"""
        else:
            format_spec = """
## FORMATO OUTPUT JSON (PERCORSO - NUMERO BOTTIGLIE DA DETERMINARE)

Devi restituire un JSON con questa struttura:

{
  "journeys": [
    {
      "id": 1,
      "name": "Nome del percorso",
      "reason": "Spiegazione breve",
      "wines": [
        {"id": <id_vino>, "name": "<nome_esatto>", "price": <prezzo>}
        // 2-3 vini per percorso
      ]
    }
  ]
}"""
    else:
        format_spec = """
## FORMATO OUTPUT JSON (SINGOLA ETICHETTA)

⚠️ CRITICO: Devi rankare TUTTI i vini disponibili nella carta, dal migliore (rank 1) al peggiore (rank N).

Devi restituire un JSON con questa struttura:

{
  "wines": [
    {
      "id": <id_vino_dalla_carta>,
      "name": "<nome_esatto_dalla_carta>",
      "price": <prezzo_dalla_carta>,
      "rank": 1,
      "reason": "Breve motivazione (1-2 frasi) del perché questo vino è il migliore: caratteristiche organolettiche, abbinamento perfetto con i piatti specifici, perché si distingue.",
      "best": true
    },
    {
      "id": <id_vino_dalla_carta>,
      "name": "<nome_esatto_dalla_carta>",
      "price": <prezzo_dalla_carta>,
      "rank": 2,
      "reason": "Breve motivazione (1-2 frasi) del perché questo vino è buono ma leggermente meno adatto del primo: caratteristiche, differenze rispetto al primo, abbinamenti.",
      "best": false
    },
    {
      "id": <id_vino_dalla_carta>,
      "name": "<nome_esatto_dalla_carta>",
      "price": <prezzo_dalla_carta>,
      "rank": 3,
      "reason": "Breve motivazione (1-2 frasi) del perché questo vino è meno adatto: caratteristiche, perché non si abbina bene ai piatti o non rispetta le preferenze.",
      "best": false
    }
    // ... continua con TUTTI gli altri vini fino all'ultimo
    {
      "id": <id_vino_dalla_carta>,
      "name": "<nome_esatto_dalla_carta>",
      "price": <prezzo_dalla_carta>,
      "rank": N,
      "reason": "Breve motivazione (1-2 frasi) del perché questo vino è il meno adatto: non si abbina bene ai piatti, non rispetta le preferenze, o altre ragioni.",
      "best": false
    }
  ]
}

IMPORTANTE: 
- Devi rankare TUTTI i vini disponibili nella carta, non solo alcuni
- Il rank 1 è il vino migliore per i parametri del cliente (piatti, tipo vino). Il budget è un fattore secondario - vini molto validi che superano leggermente il budget possono comunque essere promossi.
- L'ultimo rank (N) è il vino meno adatto
- Esattamente UN vino deve avere "rank": 1 e "best": true (il miglior consiglio)
- Tutti gli altri devono avere "best": false
- Ogni vino deve avere un "rank" numerico sequenziale (1, 2, 3, ..., N)
- La "reason" deve spiegare il ranking: per vini in alto spiega perché si abbina bene, per vini in basso spiega perché è meno adatto
- La carta è già filtrata per includere solo vini nella fascia di prezzo appropriata. Il budget è un fattore secondario - la motivazione deve concentrarsi su qualità, abbinamenti e caratteristiche organolettiche, non sul prezzo.
- NON saltare vini: ranka TUTTI i vini presenti nella lista"""
    
    prompt = f"""Sei un esperto sommelier che seleziona vini dalla carta del ristorante {venue_name}.

## CONTESTO

**Piatti ordinati:**
{dish_context}

**Numero commensali:** {guest_count}

**Tipo vino preferito:** {wine_type if wine_type != 'any' else 'Nessuna preferenza specifica - scegli tu il migliore'}

**Modalità:** {"Percorso di vini" if journey_pref == 'journey' else "Singola etichetta con alternative"}

**Budget:** {budget_text}

{featured_wines_context}

## CARTA DEI VINI DISPONIBILI

⚠️ CRITICO: Puoi selezionare SOLO vini da questa lista. NON inventare vini, nomi, cantine, annate o caratteristiche.

{wines_context}

## REGOLE DI SELEZIONE

1. **SOLO VINI DALLA CARTA**: Seleziona SOLO vini presenti nella lista sopra. Usa l'ID esatto e il nome esatto.

2. **RISPETTA IL TIPO VINO**: Se il cliente ha specificato un tipo (rosso, bianco, ecc.), seleziona solo vini di quel tipo. Se "any", puoi scegliere qualsiasi tipo.

3. **RISPETTA IL BUDGET**: {budget_text}

4. **ABBINAMENTI**: Seleziona vini che si abbinano bene con i piatti ordinati:
   - Pesce → bianchi, rosati leggeri, bollicine
   - Carne rossa → rossi strutturati
   - Primi → vini versatili
   - MAI dessert wine con piatti salati

5. **OTTIMIZZAZIONE RICAVO**: Considera il budget come guida, ma privilegia sempre la qualità e l'affinità con i piatti. Vini eccellenti che superano leggermente il budget possono essere promossi nel ranking.

6. **RANKING COMPLETO**:
   - Singola etichetta: Ranka TUTTI i vini disponibili nella carta dal migliore (rank 1) al peggiore (rank N). Il rank 1 è il vino migliore per i parametri del cliente (piatti, tipo vino). Il budget è un fattore secondario - vini molto validi che superano leggermente il budget possono comunque essere promossi. L'ultimo rank è il vino meno adatto. Ogni vino deve avere un rank numerico sequenziale e una motivazione che spiega il ranking.
   - Percorso: ESATTAMENTE 2-3 percorsi, ognuno con esattamente {f"{bottles_count} vini" if journey_pref == 'journey' and bottles_count else "2-3 vini"} per percorso. NON generare più di 3 percorsi, NON generare meno di 2 percorsi.

7. **BUDGET**: 
   - Se il budget è specificato, la carta è già filtrata per includere solo vini con prezzo tra (budget - 20%) e (budget + 15%).
   - Tutti i vini disponibili sono nella fascia di prezzo appropriata. Il budget è un fattore secondario nel ranking - privilegia sempre la qualità, l'affinità con i piatti e le caratteristiche organolettiche. Vini molto validi che superano leggermente il budget (entro il range disponibile) possono essere promossi nel ranking e non devono essere penalizzati solo per il prezzo. La motivazione del ranking deve concentrarsi su qualità e abbinamenti, non sul budget.

8. **VINI IN EVIDENZA (PRIORITÀ STRATEGICA)**: 
   {featured_wines_priority_text}

{format_spec}

## OUTPUT

Restituisci SOLO il JSON valido, senza testo aggiuntivo. Il JSON deve essere valido e parsabile.
"""

    return prompt


def get_communication_prompt(
    venue_name: str,
    sommelier_style: str,
    wine_selection: Dict,
    context: Dict,
    gathered_info: Dict
) -> str:
    """
    Generate prompt for communication model to generate natural language message.
    
    Args:
        venue_name: Name of the venue
        sommelier_style: Style of sommelier
        wine_selection: JSON from fine-tuned selector with 'wines' or 'journeys'
        context: Context with dishes, guest_count
        gathered_info: Preferences
        
    Returns:
        System prompt for communication model
    """
    style_intros = {
        'professional': f"Sei il sommelier di {venue_name}. Sei elegante e competente, sai raccontare il vino con passione.",
        'friendly': f"Sei il sommelier di {venue_name}. Sei caloroso, informale e ami condividere la tua passione per il vino.",
        'expert': f"Sei il sommelier di {venue_name}. Sei un esperto che sa rendere accessibile anche il vino più complesso.",
        'playful': f"Sei il sommelier di {venue_name}. Sei creativo e ami sorprendere, rendendo ogni scelta un piccolo racconto."
    }
    
    intro = style_intros.get(sommelier_style, style_intros['professional'])
    
    # Build wine selection context
    selection_text = ""
    if wine_selection.get('wines'):
        wines = wine_selection['wines']
        selection_text = "## Vini Selezionati (da comunicare al cliente)\n\n"
        for wine in wines:
            best_marker = " ⭐ CONSIGLIO PRINCIPALE" if wine.get('best') else ""
            selection_text += f"- **{wine.get('name')}** - €{wine.get('price')}{best_marker}\n"
            selection_text += f"  Motivo: {wine.get('reason', '')}\n\n"
    elif wine_selection.get('journeys'):
        journeys = wine_selection['journeys']
        selection_text = "## Percorsi Selezionati (da comunicare al cliente)\n\n"
        for journey in journeys:
            selection_text += f"### {journey.get('name')}\n"
            selection_text += f"Motivo: {journey.get('reason', '')}\n"
            selection_text += "Vini:\n"
            for wine in journey.get('wines', []):
                selection_text += f"- {wine.get('name')} - €{wine.get('price')}\n"
            selection_text += "\n"
    
    # Build dish context
    dishes = context.get('dishes', []) if context else []
    dish_list = [d.get('name', 'Piatto') for d in dishes]
    dish_context = ", ".join(dish_list) if dish_list else "nessun piatto specificato"
    
    prompt = f"""{intro}

## IL TUO COMPITO

Comunica le selezioni di vini in modo DESCRITTIVO e COINVOLGENTE. Racconta i vini, le loro caratteristiche, gli abbinamenti con i piatti. Presenta ogni vino con passione e dettagli.

{selection_text}

## CONTESTO

**Piatti:** {dish_context}
**Commensali:** {context.get('guest_count', 2) if context else 2}

## ISTRUZIONI

1. **SII DESCRITTIVO E COINVOLGENTE**: 3-5 frasi per vino per descriverlo in modo ricco e appassionato. Racconta:
   - Le caratteristiche organolettiche (profumi, sapori, struttura)
   - L'abbinamento con i piatti specifici ordinati
   - Perché questo vino è perfetto per questa serata
   - Cosa lo rende speciale o interessante

2. **USA I NOMI ESATTI**: Usa sempre i nomi ESATTI dei vini dalla selezione

3. **INDICA I PREZZI**: Sempre includere il prezzo per ogni vino

4. **USA LE REASON**: Espandi e arricchisci le "reason" fornite per creare una descrizione più completa e coinvolgente di ogni vino. Non limitarti a ripetere la reason, ma sviluppala in un racconto più ampio.

5. **STRUTTURA**: 
   - Singola etichetta: Inizia con "Il mio consiglio" per best=true, descrivilo con passione (4-5 frasi), poi "Un'alternativa interessante" per gli altri (3-4 frasi ciascuno)
   - Percorso: Presenta il percorso con una descrizione dettagliata del perché funziona, poi descrivi ogni vino in ordine (3-4 frasi per vino)

**IMPORTANTE**: 
- SII DESCRITTIVO: racconta i vini con passione, dettagli, caratteristiche organolettiche
- SII COINVOLGENTE: usa un linguaggio che faccia venire voglia di provare i vini
- Presenta i vini in modo naturale e appassionato, come un vero sommelier
- 150-250 parole totali per permettere descrizioni ricche e complete
- NON essere stringato: ogni vino merita una descrizione dettagliata

Rispondi in italiano. SOLO testo, niente formattazione markdown."""

    return prompt


def _build_wines_list_for_finetuned(wines: List[Dict]) -> str:
    """Build wine list context for fine-tuned model prompt."""
    if not wines:
        return "⚠️ ATTENZIONE: La carta è vuota."
    
    context_parts = []
    for wine in wines:
        wine_id = wine.get('id', 'N/D')
        name = wine.get('name', 'N/D')
        wine_type = wine.get('type', 'N/D')
        price = wine.get('price', 'N/D')
        
        context_parts.append(f"ID: {wine_id} | {name} | Tipo: {wine_type} | Prezzo: €{price}")
    
    return "\n".join(context_parts)


