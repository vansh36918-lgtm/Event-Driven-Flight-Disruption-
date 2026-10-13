"""
Framer-Style Headless CMS Engine.
Provides schema-driven CMS collections (Destinations, Aircraft Fleet, Disruption Regulations, Airline Partners)
with dynamic REST APIs and in-memory persistence mirroring Framer's CMS engine.
"""
from typing import Dict, List, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field


class CMSFieldSchema(BaseModel):
    name: str
    field_type: str  # text, formatted_text, image_url, number, boolean, select
    label: str
    required: bool = False
    options: Optional[List[str]] = None


class CMSCollectionSchema(BaseModel):
    slug: str
    name: str
    description: str
    icon: str
    fields: List[CMSFieldSchema]


class CMSItem(BaseModel):
    item_id: str
    collection_slug: str
    title: str
    slug: str
    fields: Dict[str, Any]
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    updated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")


class FramerCMSEngine:
    def __init__(self):
        self.schemas: Dict[str, CMSCollectionSchema] = {}
        self.items: Dict[str, Dict[str, CMSItem]] = {}
        self._init_default_collections()

    def _init_default_collections(self):
        # 1. Destinations Collection
        self.register_collection(
            CMSCollectionSchema(
                slug="destinations",
                name="Airport Destinations",
                description="Hub airports, runway configurations, CAT-III ILS capabilities, and ground alternates.",
                icon="fa-solid fa-plane-arrival",
                fields=[
                    CMSFieldSchema(name="airport_code", field_type="text", label="IATA Airport Code", required=True),
                    CMSFieldSchema(name="city_name", field_type="text", label="City Name", required=True),
                    CMSFieldSchema(name="country", field_type="text", label="Country", required=True),
                    CMSFieldSchema(name="ils_category", field_type="select", label="ILS Category", options=["CAT I", "CAT II", "CAT IIIa", "CAT IIIb"]),
                    CMSFieldSchema(name="primary_alternate", field_type="text", label="Primary Fuel Alternate"),
                    CMSFieldSchema(name="coach_transfer_available", field_type="boolean", label="Luxury Coach Transfer Available"),
                    CMSFieldSchema(name="latitude", field_type="number", label="Latitude"),
                    CMSFieldSchema(name="longitude", field_type="number", label="Longitude"),
                ]
            )
        )

        # 2. Fleet Collection
        self.register_collection(
            CMSCollectionSchema(
                slug="fleet",
                name="Aircraft Fleet",
                description="Commercial fleet specifications, registration tails, seat maps, and range.",
                icon="fa-solid fa-jet-fighter",
                fields=[
                    CMSFieldSchema(name="tail_number", field_type="text", label="Registration Tail (VT- / N-)", required=True),
                    CMSFieldSchema(name="aircraft_model", field_type="text", label="Aircraft Model", required=True),
                    CMSFieldSchema(name="carrier_code", field_type="text", label="Operating Carrier (6E, AI, QP, UK)", required=True),
                    CMSFieldSchema(name="total_seats", field_type="number", label="Passenger Capacity"),
                    CMSFieldSchema(name="business_seats", field_type="number", label="Business Class Capacity"),
                    CMSFieldSchema(name="wifi_equipped", field_type="boolean", label="High-Speed Satellite Wi-Fi"),
                    CMSFieldSchema(name="status", field_type="select", label="Fleet Status", options=["ACTIVE", "MAINTENANCE", "RESERVE", "DIVERTED"]),
                ]
            )
        )

        # 3. Disruption Regulations Collection
        self.register_collection(
            CMSCollectionSchema(
                slug="regulations",
                name="Aviation Regulations",
                description="Statutory passenger rights, mandatory compensations, and tarmac delay penalties.",
                icon="fa-solid fa-scale-balanced",
                fields=[
                    CMSFieldSchema(name="regulatory_code", field_type="text", label="Regulation Code (DGCA, DOT, EU261)", required=True),
                    CMSFieldSchema(name="jurisdiction", field_type="text", label="Jurisdiction (India, USA, European Union)", required=True),
                    CMSFieldSchema(name="short_haul_compensation", field_type="text", label="Short-Haul Statutory Entitlement"),
                    CMSFieldSchema(name="long_haul_compensation", field_type="text", label="Long-Haul Statutory Entitlement"),
                    CMSFieldSchema(name="tarmac_limit_minutes", field_type="number", label="Maximum Tarmac Taxi Limit (Mins)"),
                    CMSFieldSchema(name="welfare_mandate", field_type="text", label="Care & Welfare Mandate"),
                ]
            )
        )

        # 4. Airline Partners Collection
        self.register_collection(
            CMSCollectionSchema(
                slug="partners",
                name="Airline Interline Partners",
                description="Global alliances, IATA Rule 240 involuntary endorsement agreements, and baggage interlining.",
                icon="fa-solid fa-handshake",
                fields=[
                    CMSFieldSchema(name="carrier_code", field_type="text", label="IATA Carrier Code", required=True),
                    CMSFieldSchema(name="airline_name", field_type="text", label="Airline Full Name", required=True),
                    CMSFieldSchema(name="alliance", field_type="select", label="Global Alliance", options=["Star Alliance", "SkyTeam", "OneWorld", "Independent"]),
                    CMSFieldSchema(name="rule_240_accepted", field_type="boolean", label="Accepts IATA Rule 240 Involuntary Endorsements"),
                    CMSFieldSchema(name="baggage_through_check", field_type="boolean", label="Through-Check Luggage Supported"),
                ]
            )
        )

        # Seed pre-populated CMS items
        self._seed_default_items()

    def register_collection(self, schema: CMSCollectionSchema):
        self.schemas[schema.slug] = schema
        if schema.slug not in self.items:
            self.items[schema.slug] = {}

    def _seed_default_items(self):
        # Seed Destinations
        destinations_data = [
            {
                "id": "DEST-DEL", "title": "Indira Gandhi International (DEL)", "slug": "new-delhi-del",
                "fields": {"airport_code": "DEL", "city_name": "New Delhi", "country": "India", "ils_category": "CAT IIIb", "primary_alternate": "JAI", "coach_transfer_available": True, "latitude": 28.5562, "longitude": 77.1000}
            },
            {
                "id": "DEST-BOM", "title": "Chhatrapati Shivaji Maharaj (BOM)", "slug": "mumbai-bom",
                "fields": {"airport_code": "BOM", "city_name": "Mumbai", "country": "India", "ils_category": "CAT II", "primary_alternate": "PNQ", "coach_transfer_available": True, "latitude": 19.0896, "longitude": 72.8656}
            },
            {
                "id": "DEST-BLR", "title": "Kempegowda International (BLR)", "slug": "bengaluru-blr",
                "fields": {"airport_code": "BLR", "city_name": "Bengaluru", "country": "India", "ils_category": "CAT IIIb", "primary_alternate": "MAA", "coach_transfer_available": False, "latitude": 13.1986, "longitude": 77.7066}
            },
            {
                "id": "DEST-CCU", "title": "Netaji Subhash Chandra Bose (CCU)", "slug": "kolkata-ccu",
                "fields": {"airport_code": "CCU", "city_name": "Kolkata", "country": "India", "ils_category": "CAT II", "primary_alternate": "BBI", "coach_transfer_available": False, "latitude": 22.6547, "longitude": 88.4467}
            },
            {
                "id": "DEST-GOI", "title": "Dabolim / Manohar MOPA (GOI)", "slug": "goa-goi",
                "fields": {"airport_code": "GOI", "city_name": "Goa", "country": "India", "ils_category": "CAT I", "primary_alternate": "BOM", "coach_transfer_available": False, "latitude": 15.3808, "longitude": 73.8314}
            },
            {
                "id": "DEST-JFK", "title": "John F. Kennedy International (JFK)", "slug": "new-york-jfk",
                "fields": {"airport_code": "JFK", "city_name": "New York", "country": "United States", "ils_category": "CAT IIIb", "primary_alternate": "PHL", "coach_transfer_available": True, "latitude": 40.6413, "longitude": -73.7781}
            },
        ]
        for d in destinations_data:
            self.create_item("destinations", d["id"], d["title"], d["slug"], d["fields"])

        # Seed Fleet
        fleet_data = [
            {"id": "FLT-VT-ING", "title": "IndiGo Airbus A321neo (VT-ING)", "slug": "vt-ing-a321neo", "fields": {"tail_number": "VT-ING", "aircraft_model": "Airbus A321neo", "carrier_code": "6E", "total_seats": 222, "business_seats": 0, "wifi_equipped": False, "status": "ACTIVE"}},
            {"id": "FLT-VT-NAA", "title": "Air India Boeing 787-9 Dreamliner (VT-NAA)", "slug": "vt-naa-b789", "fields": {"tail_number": "VT-NAA", "aircraft_model": "Boeing 787-9 Dreamliner", "carrier_code": "AI", "total_seats": 296, "business_seats": 30, "wifi_equipped": True, "status": "ACTIVE"}},
            {"id": "FLT-VT-IRA", "title": "Air India Airbus A350-900 (VT-IRA)", "slug": "vt-ira-a359", "fields": {"tail_number": "VT-IRA", "aircraft_model": "Airbus A350-900", "carrier_code": "AI", "total_seats": 316, "business_seats": 28, "wifi_equipped": True, "status": "ACTIVE"}},
            {"id": "FLT-VT-YAA", "title": "Akasa Air Boeing 737 MAX 8 (VT-YAA)", "slug": "vt-yaa-b38m", "fields": {"tail_number": "VT-YAA", "aircraft_model": "Boeing 737 MAX 8", "carrier_code": "QP", "total_seats": 189, "business_seats": 0, "wifi_equipped": False, "status": "ACTIVE"}},
            {"id": "FLT-N100AA", "title": "American Airlines Boeing 737-800 (N100AA)", "slug": "n100aa-b738", "fields": {"tail_number": "N100AA", "aircraft_model": "Boeing 737-800", "carrier_code": "AA", "total_seats": 172, "business_seats": 16, "wifi_equipped": True, "status": "ACTIVE"}},
        ]
        for f in fleet_data:
            self.create_item("fleet", f["id"], f["title"], f["slug"], f["fields"])

        # Seed Regulations
        reg_data = [
            {
                "id": "REG-DGCA-CAR3", "title": "DGCA CAR Section 3, Series M, Part IV", "slug": "dgca-car-3",
                "fields": {
                    "regulatory_code": "DGCA CAR Section 3", "jurisdiction": "India",
                    "short_haul_compensation": "₹5,000 (Block time ≤ 1h)",
                    "long_haul_compensation": "₹10,000 (Block time > 2h)",
                    "tarmac_limit_minutes": 180,
                    "welfare_mandate": "Free snacks, meals (₹450 voucher), drinking water, and immediate gate deplaning."
                }
            },
            {
                "id": "REG-DOT-14CFR", "title": "US DOT 14 CFR Part 259.4", "slug": "dot-14-cfr-259",
                "fields": {
                    "regulatory_code": "14 CFR § 259.4", "jurisdiction": "United States",
                    "short_haul_compensation": "400% One-way fare (up to $1,550)",
                    "long_haul_compensation": "400% One-way fare (up to $1,550)",
                    "tarmac_limit_minutes": 180,
                    "welfare_mandate": "Mandatory potable water and snacks after 2 hours. Mandatory gate return before 3 hours ($27,500/pax fine)."
                }
            },
            {
                "id": "REG-EU261", "title": "European Union Regulation (EC) 261/2004", "slug": "eu-reg-261-2004",
                "fields": {
                    "regulatory_code": "EU261/2004", "jurisdiction": "European Union",
                    "short_haul_compensation": "€250 (≤1,500 km)",
                    "long_haul_compensation": "€600 (>3,500 km)",
                    "tarmac_limit_minutes": 180,
                    "welfare_mandate": "Right to care: complimentary meals, 2 free telephone calls, and complimentary hotel accommodation."
                }
            },
        ]
        for r in reg_data:
            self.create_item("regulations", r["id"], r["title"], r["slug"], r["fields"])

        # Seed Partners
        partners_data = [
            {"id": "PTR-6E", "title": "IndiGo (6E)", "slug": "indigo-6e", "fields": {"carrier_code": "6E", "airline_name": "InterGlobe Aviation Limited (IndiGo)", "alliance": "Independent", "rule_240_accepted": True, "baggage_through_check": True}},
            {"id": "PTR-AI", "title": "Air India (AI)", "slug": "air-india-ai", "fields": {"carrier_code": "AI", "airline_name": "Air India Limited", "alliance": "Star Alliance", "rule_240_accepted": True, "baggage_through_check": True}},
            {"id": "PTR-UK", "title": "Vistara (UK)", "slug": "vistara-uk", "fields": {"carrier_code": "UK", "airline_name": "Tata SIA Airlines (Vistara)", "alliance": "Star Alliance", "rule_240_accepted": True, "baggage_through_check": True}},
            {"id": "PTR-QP", "title": "Akasa Air (QP)", "slug": "akasa-air-qp", "fields": {"carrier_code": "QP", "airline_name": "SNV Aviation (Akasa Air)", "alliance": "Independent", "rule_240_accepted": True, "baggage_through_check": True}},
            {"id": "PTR-UA", "title": "United Airlines (UA)", "slug": "united-airlines-ua", "fields": {"carrier_code": "UA", "airline_name": "United Airlines, Inc.", "alliance": "Star Alliance", "rule_240_accepted": True, "baggage_through_check": True}},
            {"id": "PTR-DL", "title": "Delta Air Lines (DL)", "slug": "delta-air-lines-dl", "fields": {"carrier_code": "DL", "airline_name": "Delta Air Lines, Inc.", "alliance": "SkyTeam", "rule_240_accepted": True, "baggage_through_check": True}},
        ]
        for p in partners_data:
            self.create_item("partners", p["id"], p["title"], p["slug"], p["fields"])

    def list_collections(self) -> List[CMSCollectionSchema]:
        return list(self.schemas.values())

    def get_collection(self, slug: str) -> Optional[CMSCollectionSchema]:
        return self.schemas.get(slug)

    def get_items(self, collection_slug: str) -> List[CMSItem]:
        if collection_slug not in self.items:
            return []
        return list(self.items[collection_slug].values())

    def get_item(self, collection_slug: str, item_id_or_slug: str) -> Optional[CMSItem]:
        col = self.items.get(collection_slug, {})
        # Check by item_id
        if item_id_or_slug in col:
            return col[item_id_or_slug]
        # Check by slug
        for item in col.values():
            if item.slug == item_id_or_slug:
                return item
        return None

    def create_item(self, collection_slug: str, item_id: str, title: str, slug: str, fields: Dict[str, Any]) -> CMSItem:
        if collection_slug not in self.items:
            self.items[collection_slug] = {}
        item = CMSItem(
            item_id=item_id,
            collection_slug=collection_slug,
            title=title,
            slug=slug,
            fields=fields
        )
        self.items[collection_slug][item_id] = item
        return item

    def update_item(self, collection_slug: str, item_id: str, fields: Dict[str, Any], title: Optional[str] = None) -> Optional[CMSItem]:
        item = self.get_item(collection_slug, item_id)
        if not item:
            return None
        if title:
            item.title = title
        item.fields.update(fields)
        item.updated_at = datetime.utcnow().isoformat() + "Z"
        return item

    def delete_item(self, collection_slug: str, item_id: str) -> bool:
        if collection_slug in self.items and item_id in self.items[collection_slug]:
            del self.items[collection_slug][item_id]
            return True
        return False


# Global singleton instance
cms_engine = FramerCMSEngine()
