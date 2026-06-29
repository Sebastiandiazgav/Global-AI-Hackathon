"""
MyAgent - Reference Data Provider
Provides business catalogs and reference datasets.
In-memory with expanded product catalog for the hackathon.
PostgreSQL persistence will be added in the next phase.
"""

from __future__ import annotations

from typing import Any, Dict


def _build_datasets() -> Dict[str, Any]:
    """Build the complete reference data catalog with expanded products."""
    return {
        # ============================================
        # ENERGY VERTICAL
        # ============================================
        "energia_tarifas_mercado": {
            "EnergíaVerde Hogar": {"precio_kwh": 0.12, "fijo_mensual": 3.50, "tipo": "plana", "origen": "100% renovable"},
            "LuzDirecta Plus": {"precio_kwh": 0.135, "fijo_mensual": 2.80, "tipo": "plana", "origen": "mix"},
            "TarifaNocturna Pro": {"precio_kwh_punta": 0.18, "precio_kwh_valle": 0.08, "fijo_mensual": 3.20, "tipo": "discriminacion_horaria"},
            "SolarMax": {"precio_kwh": 0.11, "fijo_mensual": 4.00, "tipo": "plana", "origen": "solar"},
            "FlexiLuz": {"precio_kwh": 0.14, "fijo_mensual": 2.50, "tipo": "indexada", "origen": "mix"},
            "EcoHogar 360": {"precio_kwh": 0.125, "fijo_mensual": 3.00, "tipo": "plana", "origen": "eólica + solar"},
            "IndustrialPower": {"precio_kwh_punta": 0.16, "precio_kwh_valle": 0.07, "fijo_mensual": 5.00, "tipo": "discriminacion_horaria"},
            "BasicLight": {"precio_kwh": 0.155, "fijo_mensual": 1.90, "tipo": "plana", "origen": "mix"},
        },
        "energia_precios_actuales": {
            "plana": 0.19,
            "indexada": 0.17,
            "discriminacion_horaria": 0.21,
        },
        "energia_tarifas_catalogo": {
            "tarifas": [
                {"nombre": "EnergíaVerde Hogar", "precio_kwh": "0.12€", "fijo": "3.50€/mes", "tipo": "Flat rate", "origen": "100% Renewable", "comision_vendedor": "25€"},
                {"nombre": "LuzDirecta Plus", "precio_kwh": "0.135€", "fijo": "2.80€/mes", "tipo": "Flat rate", "origen": "Mix", "comision_vendedor": "20€"},
                {"nombre": "TarifaNocturna Pro", "precio_kwh": "0.18/0.08€", "fijo": "3.20€/mes", "tipo": "Time-of-use", "origen": "Mix", "comision_vendedor": "22€"},
                {"nombre": "SolarMax", "precio_kwh": "0.11€", "fijo": "4.00€/mes", "tipo": "Flat rate", "origen": "Solar", "comision_vendedor": "28€"},
                {"nombre": "FlexiLuz", "precio_kwh": "0.14€", "fijo": "2.50€/mes", "tipo": "Indexed", "origen": "Mix", "comision_vendedor": "18€"},
                {"nombre": "EcoHogar 360", "precio_kwh": "0.125€", "fijo": "3.00€/mes", "tipo": "Flat rate", "origen": "Wind + Solar", "comision_vendedor": "26€"},
                {"nombre": "IndustrialPower", "precio_kwh": "0.16/0.07€", "fijo": "5.00€/mes", "tipo": "Time-of-use", "origen": "Mix", "comision_vendedor": "35€"},
                {"nombre": "BasicLight", "precio_kwh": "0.155€", "fijo": "1.90€/mes", "tipo": "Flat rate", "origen": "Mix", "comision_vendedor": "15€"},
            ]
        },

        # ============================================
        # LOGISTICS VERTICAL
        # ============================================
        "logistica_comision_por_transportista": {
            "amazon": 0.30,
            "gls": 0.25,
            "seur": 0.28,
            "correos": 0.20,
            "mrw": 0.22,
            "dhl": 0.35,
            "ups": 0.32,
            "fedex": 0.33,
            "nacex": 0.24,
            "ctt": 0.21,
            "default": 0.25,
        },
        "logistica_paquetes_pendientes": {
            "total_pendientes": 12,
            "paquetes": [
                {"tracking": "AMZ-20260609-0001", "transportista": "Amazon", "dias": 1, "destinatario": "Client ***4521"},
                {"tracking": "AMZ-20260609-0002", "transportista": "Amazon", "dias": 1, "destinatario": "Client ***8832"},
                {"tracking": "GLS-20260608-0001", "transportista": "GLS", "dias": 2, "destinatario": "Client ***1245"},
                {"tracking": "SEUR-20260607-0001", "transportista": "SEUR", "dias": 3, "destinatario": "Client ***9903"},
                {"tracking": "DHL-20260609-0001", "transportista": "DHL", "dias": 1, "destinatario": "Client ***6677"},
                {"tracking": "MRW-20260606-0001", "transportista": "MRW", "dias": 4, "destinatario": "Client ***3344"},
                {"tracking": "AMZ-20260605-0003", "transportista": "Amazon", "dias": 5, "destinatario": "Client ***7788"},
                {"tracking": "UPS-20260609-0001", "transportista": "UPS", "dias": 1, "destinatario": "Client ***2211"},
                {"tracking": "FEDEX-20260608-0001", "transportista": "FedEx", "dias": 2, "destinatario": "Client ***5566"},
                {"tracking": "GLS-20260607-0002", "transportista": "GLS", "dias": 3, "destinatario": "Client ***4455"},
                {"tracking": "NACEX-20260609-0001", "transportista": "Nacex", "dias": 1, "destinatario": "Client ***8899"},
                {"tracking": "CTT-20260608-0001", "transportista": "CTT", "dias": 2, "destinatario": "Client ***1122"},
            ],
            "alerta": "2 packages close to 7-day return deadline",
        },

        # ============================================
        # SUPPORT & CATALOG VERTICAL (EXPANDED)
        # ============================================
        "soporte_operadores_por_pais": {
            "españa": ["Movistar", "Vodafone", "Orange", "MásMóvil", "Yoigo", "Simyo", "Pepephone", "Lowi"],
            "colombia": ["Claro", "Movistar", "Tigo", "WOM", "Virgin Mobile"],
            "ecuador": ["Claro", "Movistar", "CNT", "Tuenti"],
            "peru": ["Claro", "Movistar", "Entel", "Bitel"],
            "rep_dominicana": ["Claro", "Altice", "Viva"],
            "usa": ["T-Mobile", "AT&T", "Verizon", "Mint Mobile"],
            "uk": ["EE", "Three", "O2", "Vodafone UK"],
            "france": ["Orange FR", "SFR", "Bouygues", "Free Mobile"],
            "germany": ["Telekom", "Vodafone DE", "O2 DE"],
            "italy": ["TIM", "Vodafone IT", "WindTre", "Iliad"],
            "portugal": ["MEO", "NOS", "Vodafone PT"],
            "brazil": ["Claro BR", "Vivo", "TIM BR", "Oi"],
            "mexico": ["Telcel", "AT&T MX", "Movistar MX"],
        },
        "soporte_catalogo_pines": {
            "netflix": {"productos": ["Standard Monthly", "Premium Monthly", "Gift Card 25€", "Gift Card 50€"], "comision": 2.50},
            "spotify": {"productos": ["Premium Individual", "Premium Duo", "Premium Family", "Gift Card 10€", "Gift Card 30€"], "comision": 1.50},
            "playstation": {"productos": ["PS Plus Essential 1 Month", "PS Plus Extra 3 Months", "PS Store 20€", "PS Store 50€", "PS Plus Premium"], "comision": 2.00},
            "xbox": {"productos": ["Game Pass Core", "Game Pass Ultimate", "Xbox Gift Card 15€", "Xbox Gift Card 25€", "Xbox Gift Card 50€"], "comision": 2.00},
            "steam": {"productos": ["Steam Wallet 10€", "Steam Wallet 20€", "Steam Wallet 50€", "Steam Wallet 100€"], "comision": 1.80},
            "nintendo": {"productos": ["Nintendo Online Individual", "Nintendo Online Family", "eShop 15€", "eShop 25€", "eShop 50€"], "comision": 1.80},
            "disney": {"productos": ["Disney+ Monthly", "Disney+ Annual", "Gift Card 25€", "Gift Card 50€"], "comision": 2.00},
            "hbo": {"productos": ["Max Monthly", "Max Annual", "Gift Card 15€"], "comision": 1.80},
            "apple": {"productos": ["App Store 15€", "App Store 25€", "App Store 50€", "Apple Music Individual", "Apple TV+ Monthly", "iCloud 50GB"], "comision": 2.20},
            "google": {"productos": ["Google Play 15€", "Google Play 25€", "Google Play 50€", "YouTube Premium"], "comision": 2.00},
            "amazon_prime": {"productos": ["Prime Monthly", "Prime Annual", "Prime Video Gift"], "comision": 1.50},
            "crunchyroll": {"productos": ["Fan Monthly", "Mega Fan Monthly", "Gift Card 15€"], "comision": 1.20},
            "twitch": {"productos": ["Turbo Monthly", "Gift Sub Tier 1", "Bits 500", "Bits 1500"], "comision": 1.50},
            "roblox": {"productos": ["Robux 400", "Robux 800", "Robux 2000", "Premium Monthly"], "comision": 1.80},
            "fortnite": {"productos": ["V-Bucks 1000", "V-Bucks 2800", "V-Bucks 5000", "Crew Monthly"], "comision": 2.00},
            "minecraft": {"productos": ["Java Edition", "Bedrock Edition", "Minecoins 320", "Minecoins 1020"], "comision": 1.60},
            "ea_play": {"productos": ["EA Play Monthly", "EA Play Pro Monthly", "FIFA Points 1050", "FIFA Points 2200"], "comision": 2.00},
            "vpn": {"productos": ["NordVPN 1 Month", "NordVPN 1 Year", "ExpressVPN 1 Month", "Surfshark 1 Month"], "comision": 3.00},
            "antivirus": {"productos": ["Norton 360 Standard", "McAfee Total Protection", "Kaspersky Standard"], "comision": 3.50},
            "office": {"productos": ["Microsoft 365 Personal", "Microsoft 365 Family", "Office Home 2024"], "comision": 4.00},
        },
        "soporte_catalogo_productos": {
            "recargas": {
                "productos": [
                    {"nombre": "National Recharge 5-50€", "rango": "5€ - 50€", "comision": "5%"},
                    {"nombre": "International Recharge 10-100€", "rango": "10€ - 100€", "comision": "8%"},
                    {"nombre": "Data Bundle Spain", "rango": "5€ - 30€", "comision": "6%"},
                    {"nombre": "Prepaid SIM Activation", "precio": "10€", "comision": "3€"},
                ]
            },
            "streaming": {
                "productos": [
                    {"nombre": "Netflix Standard", "precio": "12.99€/mes", "comision": "2.50€"},
                    {"nombre": "Netflix Premium", "precio": "17.99€/mes", "comision": "2.50€"},
                    {"nombre": "Disney+ Monthly", "precio": "8.99€/mes", "comision": "2.00€"},
                    {"nombre": "HBO Max Monthly", "precio": "9.99€/mes", "comision": "1.80€"},
                    {"nombre": "Spotify Premium", "precio": "10.99€/mes", "comision": "1.50€"},
                    {"nombre": "Apple TV+ Monthly", "precio": "9.99€/mes", "comision": "2.20€"},
                    {"nombre": "Amazon Prime Video", "precio": "4.99€/mes", "comision": "1.50€"},
                    {"nombre": "Crunchyroll Mega Fan", "precio": "6.99€/mes", "comision": "1.20€"},
                    {"nombre": "YouTube Premium", "precio": "11.99€/mes", "comision": "2.00€"},
                ]
            },
            "gaming": {
                "productos": [
                    {"nombre": "PlayStation PS Plus Essential", "precio": "8.99€/mes", "comision": "2.00€"},
                    {"nombre": "PlayStation PS Plus Extra", "precio": "13.99€/mes", "comision": "2.00€"},
                    {"nombre": "Xbox Game Pass Ultimate", "precio": "14.99€/mes", "comision": "2.00€"},
                    {"nombre": "Nintendo Online Individual", "precio": "3.99€/mes", "comision": "1.80€"},
                    {"nombre": "EA Play", "precio": "4.99€/mes", "comision": "2.00€"},
                    {"nombre": "Steam Wallet 20€", "precio": "20€", "comision": "1.80€"},
                    {"nombre": "Roblox Premium", "precio": "4.99€/mes", "comision": "1.80€"},
                    {"nombre": "Fortnite Crew", "precio": "11.99€/mes", "comision": "2.00€"},
                    {"nombre": "V-Bucks 2800", "precio": "19.99€", "comision": "2.00€"},
                    {"nombre": "Minecraft Java+Bedrock", "precio": "23.95€", "comision": "1.60€"},
                ]
            },
            "gift_cards": {
                "productos": [
                    {"nombre": "Amazon Gift Card", "rango": "10€ - 200€", "comision": "2%"},
                    {"nombre": "Apple Gift Card", "rango": "15€ - 100€", "comision": "3%"},
                    {"nombre": "Google Play Gift Card", "rango": "15€ - 100€", "comision": "3%"},
                    {"nombre": "Zalando Gift Card", "rango": "25€ - 100€", "comision": "2.5%"},
                    {"nombre": "IKEA Gift Card", "rango": "25€ - 150€", "comision": "2%"},
                    {"nombre": "El Corte Inglés Gift Card", "rango": "20€ - 200€", "comision": "2%"},
                    {"nombre": "Primark Gift Card", "rango": "10€ - 50€", "comision": "2%"},
                    {"nombre": "Decathlon Gift Card", "rango": "20€ - 100€", "comision": "2.5%"},
                ]
            },
            "servicios": {
                "productos": [
                    {"nombre": "NordVPN 1 Year", "precio": "59.88€", "comision": "3.00€"},
                    {"nombre": "Microsoft 365 Personal", "precio": "69.99€/año", "comision": "4.00€"},
                    {"nombre": "Norton 360 Standard", "precio": "29.99€/año", "comision": "3.50€"},
                    {"nombre": "Canva Pro Monthly", "precio": "12.99€/mes", "comision": "2.00€"},
                    {"nombre": "Duolingo Plus", "precio": "7.99€/mes", "comision": "1.50€"},
                    {"nombre": "Calm Premium", "precio": "14.99€/mes", "comision": "2.00€"},
                    {"nombre": "Adobe Creative Cloud", "precio": "59.99€/mes", "comision": "5.00€"},
                ]
            },
            "transporte": {
                "productos": [
                    {"nombre": "Uber Gift Card", "rango": "15€ - 50€", "comision": "2%"},
                    {"nombre": "Cabify Credit", "rango": "10€ - 50€", "comision": "2%"},
                    {"nombre": "BlaBlaCar Gift Card", "rango": "20€ - 50€", "comision": "2%"},
                    {"nombre": "Public Transport Card Top-up", "rango": "10€ - 50€", "comision": "1%"},
                    {"nombre": "Bolt Gift Card", "rango": "10€ - 30€", "comision": "2%"},
                    {"nombre": "Lime Scooter Credit", "rango": "5€ - 20€", "comision": "2%"},
                ]
            },
            "food_delivery": {
                "productos": [
                    {"nombre": "Glovo Gift Card", "rango": "10€ - 50€", "comision": "2.5%"},
                    {"nombre": "Just Eat Gift Card", "rango": "15€ - 50€", "comision": "2%"},
                    {"nombre": "Uber Eats Gift Card", "rango": "15€ - 50€", "comision": "2%"},
                    {"nombre": "Deliveroo Credit", "rango": "10€ - 40€", "comision": "2%"},
                ]
            },
            "education": {
                "productos": [
                    {"nombre": "Duolingo Plus 1 Year", "precio": "83.99€", "comision": "4.00€"},
                    {"nombre": "Coursera Plus Monthly", "precio": "49.00€/mes", "comision": "3.50€"},
                    {"nombre": "Udemy Gift Card", "rango": "20€ - 100€", "comision": "3%"},
                    {"nombre": "Skillshare Premium", "precio": "13.99€/mes", "comision": "2.00€"},
                    {"nombre": "MasterClass Annual", "precio": "10.00€/mes", "comision": "3.00€"},
                    {"nombre": "Babbel 12 Months", "precio": "6.99€/mes", "comision": "2.50€"},
                ]
            },
            "fitness_wellness": {
                "productos": [
                    {"nombre": "Calm Premium Annual", "precio": "49.99€/año", "comision": "3.00€"},
                    {"nombre": "Headspace Plus", "precio": "12.99€/mes", "comision": "2.00€"},
                    {"nombre": "Strava Premium", "precio": "7.99€/mes", "comision": "1.50€"},
                    {"nombre": "Nike Training Club Premium", "precio": "14.99€/mes", "comision": "2.00€"},
                    {"nombre": "Freeletics Coach", "precio": "11.99€/mes", "comision": "2.00€"},
                ]
            },
            "cloud_storage": {
                "productos": [
                    {"nombre": "iCloud+ 50GB", "precio": "0.99€/mes", "comision": "0.50€"},
                    {"nombre": "iCloud+ 200GB", "precio": "2.99€/mes", "comision": "1.00€"},
                    {"nombre": "Google One 100GB", "precio": "1.99€/mes", "comision": "0.80€"},
                    {"nombre": "Google One 2TB", "precio": "9.99€/mes", "comision": "2.00€"},
                    {"nombre": "Dropbox Plus", "precio": "11.99€/mes", "comision": "2.50€"},
                    {"nombre": "OneDrive 1TB", "precio": "7.00€/mes", "comision": "1.50€"},
                ]
            },
            "crypto_fintech": {
                "productos": [
                    {"nombre": "Bitsa Prepaid Card Top-up", "rango": "10€ - 200€", "comision": "2%"},
                    {"nombre": "Paysafecard 25€", "precio": "25€", "comision": "1.50€"},
                    {"nombre": "Paysafecard 50€", "precio": "50€", "comision": "2.50€"},
                    {"nombre": "Neosurf 15€", "precio": "15€", "comision": "1.00€"},
                    {"nombre": "Neosurf 50€", "precio": "50€", "comision": "2.50€"},
                ]
            },
        },
    }


_DATASETS = _build_datasets()


def get_reference_dataset(dataset_name: str) -> Any:
    """Return a reference dataset by name."""
    if dataset_name not in _DATASETS:
        raise KeyError(f"Reference dataset '{dataset_name}' not found. Available: {list(_DATASETS.keys())}")
    return _DATASETS[dataset_name]


def validate_required_reference_data() -> None:
    """Validate that all required reference datasets are available."""
    required = [
        "energia_tarifas_mercado",
        "energia_precios_actuales",
        "energia_tarifas_catalogo",
        "logistica_comision_por_transportista",
        "logistica_paquetes_pendientes",
        "soporte_operadores_por_pais",
        "soporte_catalogo_pines",
        "soporte_catalogo_productos",
    ]
    missing = [name for name in required if name not in _DATASETS]
    if missing:
        raise RuntimeError(f"Missing reference datasets: {missing}")
