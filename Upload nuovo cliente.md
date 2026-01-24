4. Utilizzo
Migration: eseguire add_must_change_password.sql sul DB (Supabase).
Onboarding clienti:
copiare example.yaml in clients/nuovo-cliente.yaml;
compilare venue, users (con password iniziale), menu_items, products;
dalla cartella backend:
python -m scripts.onboard_client scripts/clients/nuovo-cliente.yaml
opzionale: --dry-run, --no-sync.
Comunicare al cliente: login URL, email, password iniziale (quella in config / stampata dallo script). Al primo accesso il cliente viene portato su “Cambia password”, deve impostare una nuova password e solo dopo può usare dashboard/onboarding.

Regola:

- per tipo di cucina usiamo:
    Italiana / Mediterranea

    Pizza

    Europea / Occidentale (es. francese, tedesca, iberica, contemporanea “non italiana”)

    Asiatica (cinese, giapponese, thai, coreana, vietnamita, sushi, ramen…)

    Mediorientale / Africana / Indiana (kebab, marocchina, libanese, etiope, indiana…)

    Americana / Latinoamericana (burger, tex-mex, messicana, brasiliana, peruviana…)

    Street food / Fast casual (panini, poke, piadine, tavola calda, takeaway generico)

    Bar / Caffetteria / Dolci (aperitivi, colazioni, pasticceria, gelateria)

- Per target audience:

    Famiglie

    Coppie (date / serata tranquilla)

    Gruppi / Comitive (cene tra amici, feste, tavolate)

    Business / Pranzo di lavoro

    Giovani / Social (locale “di tendenza”, informale, movida)

    Turisti

    Takeaway / Veloci (pranzo rapido, delivery, “mordi e fuggi”)

    Gourmet / Esperienza (food lovers, ricercato, fine dining)


- per category (menu):

    antipasto

    primo

    secondo

    dolce

    piatto unico

Una volta caricato ricordarsi che dobbiamo

- Cercare immagini delle etichette dei vini, caricarle in storage--> "wine-labels"--> prendere ciascun url del vino e incollarlo nella riga del vino stesso
