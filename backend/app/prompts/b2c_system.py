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
        dish_list.append(dish_name)
        
        # Analyze dish for characteristics
        dish_lower = dish_name.lower()
        if any(word in dish_lower for word in ['carne', 'manzo', 'vitello', 'agnello', 'tagliata', 'bistecca']):
            dish_characteristics.append('carni')
        elif any(word in dish_lower for word in ['pesce', 'branzino', 'orata', 'tonno', 'salmone', 'vongole', 'cozze']):
            dish_characteristics.append('pesce')
        elif any(word in dish_lower for word in ['pasta', 'risotto', 'tagliatelle', 'tortelli']):
            dish_characteristics.append('primi')
        elif any(word in dish_lower for word in ['formaggio', 'burrata', 'mozzarella', 'parmigiano']):
            dish_characteristics.append('formaggi')
        elif any(word in dish_lower for word in ['funghi', 'porcini', 'tartufo']):
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
   - Modalità: {journey_text}
   - Tipo vino: {wine_type_text}
   - Budget: {budget_text}

3. Caratteristiche piatti (UNA RIGA): {characteristics_desc}

4. Chiedi esigenze particolari (allergie, gusti da evitare, occasioni speciali)

**REGOLE:**
- NON proporre vini o raccomandazioni
- NON menzionare "proposta" o "raccomandazione"
- Sii breve e naturale
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
        preferences_context += f"- Budget: Massimo €{budget:.2f} per bottiglia (puoi superarlo di un massimo del 10%)\n"
    
    pairing_hints = _generate_pairing_hints(context.get('dishes', []) if context else [])
    
    # Format instructions
    if journey_pref == 'journey':
        if bottles_count:
            format_instructions = f"""
## FORMATO (PERCORSO {bottles_count} BOTTIGLIE)

Proponi 1-2 percorsi completi. Ogni percorso contiene esattamente {bottles_count} vini.

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

Proponi 3 vini come racconto:

**Il mio consiglio** - [Nome Vino ESATTO] - €[Prezzo]
[Descrizione breve e perché è perfetto per i loro piatti]

**Un'alternativa interessante** - [Nome Vino ESATTO] - €[Prezzo]
[Perché potrebbe piacere, differenza rispetto al primo]

**Per chi ama osare** - [Nome Vino ESATTO] - €[Prezzo]
[Perché è una scelta coraggiosa ma vincente]
"""
    
    prompt = f"""{intro}

{meal_context}
{preferences_context}
{pairing_hints}

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

2. **NOMI ESATTI DEI VINI - CRITICO**: 
   ⚠️ Quando proponi un vino, DEVI SEMPRE menzionare il NOME ESATTO così come appare nella "Carta dei Vini Disponibili".
   - Se nella carta c'è "Focara Pinot Noir D.O.C. 2014", DEVI dire esattamente "Focara Pinot Noir D.O.C. 2014"
   - NON dire "un Pinot Noir" o "Focara" o "un vino della cantina Focara"
   - Usa sempre il nome completo con annata, denominazione, etc.
   - Questo è ESSENZIALE: senza il nome esatto, il sistema non può mostrare le card corrette

3. **MAI DESSERT WINE CON PIATTI SALATI**: Non proporre mai vini passiti, dolci, dessert wine con antipasti/primi/secondi.

4. **FLUSSO NATURALE**: Analizza la conversazione fatta fino a ora e mantieni il flusso naturale. Non ripetere informazioni già date.

5. **PREZZI E BUDGET**: Sempre indicare il prezzo. Rispetta il budget indicato.

Rispondi sempre in italiano."""

    return prompt


def _generate_pairing_hints(dishes: List[Dict]) -> str:
    """Generate internal hints for the AI about dish pairings."""
    if not dishes:
        return ""
    
    hints = "\n## Note Interne Abbinamento (non mostrare al cliente)\n"
    
    # Analyze dish names for common ingredients
    dish_names = [d.get('name', '').lower() for d in dishes]
    dish_categories = [d.get('category', '').lower() for d in dishes]
    all_text = ' '.join(dish_names)
    
    has_fish = any(word in all_text for word in ['pesce', 'branzino', 'orata', 'tonno', 'salmone', 'vongole', 'cozze', 'gamberi', 'scampi', 'mare', 'frutti'])
    has_red_meat = any(word in all_text for word in ['manzo', 'vitello', 'agnello', 'tagliata', 'bistecca', 'filetto', 'brasato', 'cinghiale'])
    has_pork = any(word in all_text for word in ['maiale', 'porchetta', 'salsiccia'])
    has_pasta = any(word in all_text for word in ['spaghetti', 'penne', 'rigatoni', 'tagliatelle', 'pappardelle', 'risotto', 'gnocchi', 'tortelli'])
    has_cheese = any(word in all_text for word in ['formaggio', 'burrata', 'mozzarella', 'parmigiano', 'pecorino', 'gorgonzola'])
    has_raw = any(word in all_text for word in ['carpaccio', 'tartare', 'crudo', 'sashimi'])
    has_mushrooms = any(word in all_text for word in ['funghi', 'porcini', 'tartufo'])
    has_dessert = any(cat in ['dolce', 'dessert'] for cat in dish_categories) or any(word in all_text for word in ['dolce', 'dessert', 'torta', 'tiramisu', 'gelato', 'crema'])
    has_savory = any(cat in ['antipasto', 'primo', 'secondo', 'contorno'] for cat in dish_categories) or (has_pasta or has_red_meat or has_fish or has_pork)
    
    # CRITICAL: Never suggest dessert wines with savory dishes
    if has_savory and not has_dessert:
        hints += "⚠️ CRITICO: I piatti sono SALATI (antipasti, primi, secondi). NON proporre MAI vini passiti, dolci, dessert wine, liquorosi. Solo vini da pasto (rossi, bianchi, rosati, bollicine secco).\n"
    
    if has_fish and has_red_meat:
        hints += "- Mix pesce/carne: OTTIMA OCCASIONE per proporre un percorso di 2 vini!\n"
    elif has_fish:
        hints += "- Pesce: bianchi freschi, bollicine, o rosati leggeri\n"
    elif has_red_meat:
        hints += "- Carne rossa: rossi strutturati con tannino\n"
    
    if has_raw:
        hints += "- Piatti crudi: vini delicati, bollicine, bianchi minerali\n"
    
    if has_mushrooms:
        hints += "- Funghi/tartufo: rossi morbidi (Pinot Nero, Nebbiolo)\n"
    
    if has_pasta and not has_fish and not has_red_meat:
        hints += "- Primi: vini versatili, bianchi strutturati o rossi leggeri\n"
    
    return hints


