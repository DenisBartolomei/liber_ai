#!/usr/bin/env python3
"""
LIBER onboarding script: create venue, users, menu_items, products from YAML/JSON config.
Run from backend/: python -m scripts.onboard_client <config-path> [--no-sync] [--dry-run]
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

# Add backend root to path so we can import app
_backend_root = Path(__file__).resolve().parent.parent
if str(_backend_root) not in sys.path:
    sys.path.insert(0, str(_backend_root))

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)

PRODUCT_TYPES = ("red", "white", "rose", "sparkling", "dessert", "fortified")


def load_config(path: Path) -> dict:
    """Load YAML or JSON config."""
    text = path.read_text(encoding="utf-8")
    suf = path.suffix.lower()
    if suf in (".yaml", ".yml"):
        try:
            import yaml
        except ImportError:
            logger.error("PyYAML not installed. pip install PyYAML")
            sys.exit(1)
        return yaml.safe_load(text) or {}
    if suf == ".json":
        return json.loads(text)
    logger.error("Config must be .yaml, .yml, or .json")
    sys.exit(1)


def validate_config(data: dict) -> list[str]:
    """Validate config. Return list of error messages."""
    errs = []
    if not data:
        return ["Config is empty"]
    v = data.get("venue")
    if not v or not isinstance(v, dict):
        errs.append("venue (object) is required")
    else:
        if not (v.get("name") or "").strip():
            errs.append("venue.name is required")
    users = data.get("users")
    if not users or not isinstance(users, list):
        errs.append("users (non-empty list) is required")
    else:
        for i, u in enumerate(users):
            if not isinstance(u, dict):
                errs.append(f"users[{i}] must be an object")
                continue
            if not (u.get("email") or "").strip():
                errs.append(f"users[{i}].email is required")
            if not (u.get("password") or "").strip():
                errs.append(f"users[{i}].password is required")
    menu_items = data.get("menu_items")
    if menu_items is not None and not isinstance(menu_items, list):
        errs.append("menu_items must be a list")
    else:
        for i, m in enumerate(menu_items or []):
            if not isinstance(m, dict):
                errs.append(f"menu_items[{i}] must be an object")
                continue
            if not (m.get("name") or "").strip():
                errs.append(f"menu_items[{i}].name is required")
    products = data.get("products")
    if products is not None and not isinstance(products, list):
        errs.append("products must be a list")
    else:
        for i, p in enumerate(products or []):
            if not isinstance(p, dict):
                errs.append(f"products[{i}] must be an object")
                continue
            if not (p.get("name") or "").strip():
                errs.append(f"products[{i}].name is required")
            if not (p.get("type") or "").strip():
                errs.append(f"products[{i}].type is required")
            elif (p.get("type") or "").strip().lower() not in PRODUCT_TYPES:
                errs.append(
                    f"products[{i}].type must be one of: {', '.join(PRODUCT_TYPES)}"
                )
            if "price" not in p or p.get("price") is None:
                errs.append(f"products[{i}].price is required")
    return errs


def run(config_path: Path, dry_run: bool, no_sync: bool) -> None:
    """Load config, validate, optionally insert and sync."""
    if not config_path.is_file():
        logger.error("Config file not found: %s", config_path)
        sys.exit(1)
    data = load_config(config_path)
    errs = validate_config(data)
    if errs:
        for e in errs:
            logger.error("Validation: %s", e)
        sys.exit(1)

    from app import create_app, db
    from app.models import Venue, User, MenuItem, Product

    app = create_app()
    venue_data = data["venue"]
    users_data = data["users"]
    menu_items_data = data.get("menu_items") or []
    products_data = data.get("products") or []

    with app.app_context():
        slug = (venue_data.get("slug") or "").strip()
        if not slug:
            slug = Venue.generate_slug(venue_data["name"])
        else:
            slug = slug.lower().strip()
            import re
            slug = re.sub(r"[^\w\s-]", "", slug)
            slug = re.sub(r"[-\s]+", "-", slug)

        existing_venue = Venue.query.filter_by(slug=slug).first()
        if existing_venue:
            logger.error("Slug already exists: %s", slug)
            sys.exit(1)
        for u in users_data:
            existing = User.query.filter_by(email=(u.get("email") or "").strip()).first()
            if existing:
                logger.error("Email already exists: %s", u.get("email"))
                sys.exit(1)

        if dry_run:
            logger.info("Dry run: validation OK, slug=%s, users=%d, menu_items=%d, products=%d",
                        slug, len(users_data), len(menu_items_data), len(products_data))
            return

        # Create venue
        venue = Venue(
            name=venue_data["name"].strip(),
            slug=slug,
            description=(venue_data.get("description") or "").strip() or None,
            cuisine_type=(venue_data.get("cuisine_type") or "").strip() or None,
            welcome_message=(venue_data.get("welcome_message") or "").strip() or None,
            sommelier_style=(venue_data.get("sommelier_style") or "professional").strip(),
            plan=(venue_data.get("plan") or "trial").strip(),
            is_onboarded=bool(venue_data.get("is_onboarded", True)),
            is_active=bool(venue_data.get("is_active", True)),
            menu_style=venue_data.get("menu_style"),
            preferences=venue_data.get("preferences"),
            target_audience=venue_data.get("target_audience"),
            logo_url=(venue_data.get("logo_url") or "").strip() or None,
            menu_link_enabled=bool(venue_data.get("menu_link_enabled", False)),
            menu_link=(venue_data.get("menu_link") or "").strip() or None,
            wine_list_link_enabled=bool(venue_data.get("wine_list_link_enabled", False)),
            wine_list_link=(venue_data.get("wine_list_link") or "").strip() or None,
        )
        db.session.add(venue)
        db.session.flush()

        for u in users_data:
            user = User(
                venue_id=venue.id,
                email=(u["email"] or "").strip(),
                first_name=(u.get("first_name") or "").strip() or None,
                last_name=(u.get("last_name") or "").strip() or None,
                role=(u.get("role") or "owner").strip(),
                is_active=True,
                must_change_password=True,
            )
            user.set_password((u["password"] or "").strip())
            db.session.add(user)

        for i, m in enumerate(menu_items_data):
            mi = MenuItem(
                venue_id=venue.id,
                name=(m["name"] or "").strip(),
                description=(m.get("description") or "").strip() or None,
                category=(m.get("category") or "").strip() or None,
                main_ingredient=(m.get("main_ingredient") or "").strip() or None,
                cooking_method=(m.get("cooking_method") or "").strip() or None,
                flavor_profile=m.get("flavor_profile") if isinstance(m.get("flavor_profile"), list) else None,
                price=float(m["price"]) if m.get("price") is not None else None,
                is_available=bool(m.get("is_available", True)),
                display_order=int(m["display_order"]) if m.get("display_order") is not None else i,
            )
            db.session.add(mi)

        for p in products_data:
            pr = Product(
                venue_id=venue.id,
                name=(p["name"] or "").strip(),
                type=(p["type"] or "").strip().lower(),
                price=float(p["price"]),
                region=(p.get("region") or "").strip() or None,
                country=(p.get("country") or "Italia").strip() or None,
                grape_variety=(p.get("grape_variety") or "").strip() or None,
                vintage=int(p["vintage"]) if p.get("vintage") is not None else None,
                alcohol_content=float(p["alcohol_content"]) if p.get("alcohol_content") is not None else None,
                price_glass=float(p["price_glass"]) if p.get("price_glass") is not None else None,
                cost_price=float(p["cost_price"]) if p.get("cost_price") is not None else None,
                description=(p.get("description") or "").strip() or None,
                is_available=bool(p.get("is_available", True)),
                stock_quantity=int(p["stock_quantity"]) if p.get("stock_quantity") is not None else None,
                image_url=(p.get("image_url") or "").strip() or None,
                external_id=(p.get("external_id") or "").strip() or None,
            )
            db.session.add(pr)

        db.session.commit()
        logger.info("Venue created: id=%s slug=%s name=%s", venue.id, venue.slug, venue.name)

        # Reload products for sync (they have ids now)
        products = Product.query.filter_by(venue_id=venue.id).all()
        if not no_sync and products:
            try:
                from app.services.vector_search import VectorSearchService
                svc = VectorSearchService()
                n = svc.bulk_index(products)
                db.session.commit()
                logger.info("Vector sync: %d products indexed", n)
            except Exception as e:
                logger.warning("Vector sync skipped or failed: %s", e)

        # Output
        base = app.config.get("FRONTEND_URL", "http://localhost:5173").rstrip("/")
        login_url = f"{base}/login"
        print("\n--- Onboarding completo ---")
        print(f"Venue: id={venue.id} slug={venue.slug} name={venue.name}")
        for u in users_data:
            email = (u.get("email") or "").strip()
            pw = (u.get("password") or "").strip()
            print(f"  User: {email} ({u.get('first_name') or ''} {u.get('last_name') or ''})")
            print(f"  Password iniziale per {email}: {pw}")
            print("  → Comunicala al cliente; dovrà cambiarla al primo accesso.")
        print(f"\nLogin URL: {login_url}\n")


def main() -> None:
    ap = argparse.ArgumentParser(description="LIBER onboarding: create venue, users, menu_items, products")
    ap.add_argument("config", type=Path, help="Path to YAML or JSON config")
    ap.add_argument("--no-sync", action="store_true", help="Skip Qdrant vector sync")
    ap.add_argument("--dry-run", action="store_true", help="Validate only, no INSERT")
    args = ap.parse_args()
    run(args.config, dry_run=args.dry_run, no_sync=args.no_sync)


if __name__ == "__main__":
    main()
