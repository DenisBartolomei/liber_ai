"""
Script per testare la connessione al database Supabase
Esegui: python test_db_connection.py
"""
import os
import sys
from pathlib import Path

# Aggiungi il path backend per gli import
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

from dotenv import load_dotenv

print("=" * 60)
print("TEST CONNESSIONE DATABASE SUPABASE")
print("=" * 60)

# Carica .env
env_file = backend_path / '.env'
if env_file.exists():
    load_dotenv(dotenv_path=env_file)
    print(f"✅ File .env trovato: {env_file}")
else:
    print(f"❌ File .env NON trovato in: {env_file}")
    print("   Cercando in altre posizioni...")
    load_dotenv()  # Prova a caricare dal percorso corrente

# Verifica DATABASE_URL
DATABASE_URL = os.getenv('DATABASE_URL', '')
print(f"\n📋 DATABASE_URL presente: {bool(DATABASE_URL)}")

if not DATABASE_URL:
    print("\n❌ ERRORE: DATABASE_URL non trovata!")
    print("\nVerifica che nel file .env ci sia:")
    print("DATABASE_URL=postgresql://postgres:[PASSWORD]@[HOST]:5432/postgres")
    sys.exit(1)

# Mostra DATABASE_URL (nascondendo la password per sicurezza)
if '@' in DATABASE_URL:
    try:
        # Nascondi password
        parts = DATABASE_URL.split('@')
        auth_part = parts[0]
        if ':' in auth_part:
            user_pass = auth_part.split('://')
            if len(user_pass) > 1:
                user = user_pass[1].split(':')[0]
                protocol = user_pass[0]
                db_url_safe = f"{protocol}://{user}:***@{parts[1]}"
                print(f"🔗 DATABASE_URL (password nascosta): {db_url_safe}")
    except:
        print(f"🔗 DATABASE_URL trovata (formato: {DATABASE_URL[:50]}...)")

# Converti postgres:// in postgresql:// se necessario
if DATABASE_URL.startswith('postgres://'):
    DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)
    print("⚠️  Convertito postgres:// in postgresql://")

print("\n" + "=" * 60)
print("TEST 1: Connessione diretta con psycopg2")
print("=" * 60)

try:
    import psycopg2
    from psycopg2 import sql
    print("✅ psycopg2 importato correttamente")
except ImportError as e:
    print(f"❌ ERRORE: psycopg2 non installato: {e}")
    print("   Installa con: pip install psycopg2-binary")
    sys.exit(1)

try:
    print("\n🔄 Tentativo di connessione...")
    conn = psycopg2.connect(DATABASE_URL, connect_timeout=10)
    print("✅ Connessione riuscita!")
    
    # Test query semplice
    cur = conn.cursor()
    cur.execute("SELECT version();")
    version = cur.fetchone()
    print(f"✅ Query test riuscita")
    print(f"   PostgreSQL: {version[0].split(',')[0]}")
    
    # Verifica tabelle
    print("\n" + "-" * 60)
    print("TEST 2: Verifica tabelle")
    print("-" * 60)
    
    cur.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
        ORDER BY table_name;
    """)
    tables = cur.fetchall()
    table_names = [t[0] for t in tables]
    
    print(f"\n📊 Tabelle trovate: {len(table_names)}")
    
    expected_tables = [
        'venues', 'users', 'products', 'sessions', 
        'messages', 'menu_items', 'wine_proposals'
    ]
    
    print("\n📋 Tabelle attese vs trovate:")
    for table in expected_tables:
        exists = table in table_names
        status = "✅" if exists else "❌"
        print(f"   {status} {table}")
    
    if table_names:
        print(f"\n📋 Tutte le tabelle nel database:")
        for table in table_names:
            print(f"   - {table}")
    else:
        print("\n⚠️  Nessuna tabella trovata! Hai eseguito lo schema.sql?")
    
    # Verifica utente demo
    print("\n" + "-" * 60)
    print("TEST 3: Verifica dati demo")
    print("-" * 60)
    
    if 'users' in table_names:
        cur.execute("SELECT COUNT(*) FROM users;")
        user_count = cur.fetchone()[0]
        print(f"📊 Utenti nel database: {user_count}")
        
        cur.execute("SELECT email, is_active, is_verified FROM users LIMIT 5;")
        users = cur.fetchall()
        if users:
            print("\n👤 Primi utenti:")
            for email, is_active, is_verified in users:
                status = "✅" if is_active else "❌"
                verified = "✓" if is_verified else "✗"
                print(f"   {status} {email} (active: {is_active}, verified: {is_verified})")
        
        # Verifica demo user
        cur.execute("SELECT email, password_hash FROM users WHERE email = 'demo@liber.ai';")
        demo_user = cur.fetchone()
        if demo_user:
            print(f"\n✅ Utente demo trovato: {demo_user[0]}")
            print(f"   Hash password presente: {bool(demo_user[1])}")
            print(f"   Lunghezza hash: {len(demo_user[1]) if demo_user[1] else 0} caratteri")
        else:
            print("\n⚠️  Utente demo@liber.ai NON trovato")
    else:
        print("❌ Tabella 'users' non esiste")
    
    if 'venues' in table_names:
        cur.execute("SELECT COUNT(*) FROM venues;")
        venue_count = cur.fetchone()[0]
        print(f"\n📊 Venues nel database: {venue_count}")
    
    if 'products' in table_names:
        cur.execute("SELECT COUNT(*) FROM products;")
        product_count = cur.fetchone()[0]
        print(f"📊 Products nel database: {product_count}")
    
    cur.close()
    conn.close()
    print("\n✅ Connessione chiusa correttamente")
    
except psycopg2.OperationalError as e:
    print(f"\n❌ ERRORE OPERATIVO: {e}")
    print("\nPossibili cause:")
    print("  - DATABASE_URL non corretta")
    print("  - Password errata")
    print("  - Host non raggiungibile")
    print("  - Firewall o rete blocca la connessione")
    sys.exit(1)
    
except psycopg2.InterfaceError as e:
    print(f"\n❌ ERRORE INTERFACCIA: {e}")
    print("\nPossibili cause:")
    print("  - Formato DATABASE_URL non valido")
    print("  - Driver psycopg2 non installato correttamente")
    sys.exit(1)
    
except Exception as e:
    print(f"\n❌ ERRORE GENERICO: {type(e).__name__}: {e}")
    import traceback
    print("\nTraceback completo:")
    traceback.print_exc()
    sys.exit(1)

# Test con SQLAlchemy
print("\n" + "=" * 60)
print("TEST 4: Connessione con SQLAlchemy")
print("=" * 60)

try:
    from app import create_app, db
    
    app = create_app()
    with app.app_context():
        # Prova connessione
        db.session.execute(db.text("SELECT 1"))
        print("✅ SQLAlchemy: connessione riuscita")
        
        # Prova query su tabella users
        if 'users' in table_names:
            from app.models import User
            user_count = User.query.count()
            print(f"✅ SQLAlchemy: query User.query.count() = {user_count}")
            
            demo_user = User.query.filter_by(email='demo@liber.ai').first()
            if demo_user:
                print(f"✅ SQLAlchemy: utente demo trovato (ID: {demo_user.id})")
            else:
                print("⚠️  SQLAlchemy: utente demo non trovato")
        
except Exception as e:
    print(f"❌ ERRORE SQLAlchemy: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 60)
print("✅ TUTTI I TEST COMPLETATI!")
print("=" * 60)
print("\nSe tutti i test sono passati, il database è configurato correttamente.")
print("Se ci sono errori, controlla il messaggio sopra per capire cosa correggere.")

