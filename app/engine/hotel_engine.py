"""
CRS & Sabre Electronic Hotel & Meal Voucher Engine (IATA & EU261 Article 9 / US DOT).
Automates emergency lodging, ground shuttle dispatch, and per-diem meal stipends
for stranded passengers facing overnight delays or extended tarmac/hub disruptions.
"""
from datetime import datetime, timedelta
import random
from typing import Dict, List, Optional, Any
from pydantic import BaseModel


class HotelProperty(BaseModel):
    hotel_id: str
    name: str
    hub: str
    address: str
    phone: str
    shuttle_info: str
    direct_bill_code: str
    room_rate_usd: float
    available_rooms: int


class HotelVoucher(BaseModel):
    voucher_id: str
    pnr_id: str
    passenger_name: str
    disrupted_flight: str
    reaccommodated_flight: Optional[str]
    hub: str
    hotel_name: str
    hotel_address: str
    hotel_phone: str
    shuttle_instructions: str
    room_tier: str  # "STANDARD_KING", "DELUXE_QUEEN", "EXECUTIVE_SUITE"
    meal_stipend_usd: float
    check_in_date: str
    check_out_date: str
    corporate_direct_bill: str
    status: str  # "ISSUED", "REDEEMED", "EXPIRED"
    issued_at: str
    qr_payload: str


class HotelEngine:
    """
    Simulates airline automated hotel inventory integration
    (comparable to Sabre Travelliance / API Global Automated IRROPS lodging).
    """

    def __init__(self):
        self.hotels: Dict[str, List[HotelProperty]] = {}
        self.issued_vouchers: Dict[str, HotelVoucher] = {}  # voucher_id -> voucher
        self.pnr_to_voucher: Dict[str, str] = {}  # pnr_id -> voucher_id
        self._initialize_contracted_hotels()

    def _initialize_contracted_hotels(self):
        contracted = [
            HotelProperty(
                hotel_id="HTL-ORD-01",
                name="Hilton Chicago O'Hare Airport",
                hub="ORD",
                address="10000 W O'Hare Ave, Chicago, IL 60666",
                phone="+1 (773) 686-8000",
                shuttle_info="Direct underground concourse walkway from Terminals 1, 2 & 3",
                direct_bill_code="SABRE-DIRBILL-ORD-991",
                room_rate_usd=195.0,
                available_rooms=85,
            ),
            HotelProperty(
                hotel_id="HTL-ORD-02",
                name="Hyatt Regency O'Hare",
                hub="ORD",
                address="9300 Bryn Mawr Ave, Rosemont, IL 60018",
                phone="+1 (847) 696-1234",
                shuttle_info="Complimentary 24/7 shuttle every 15 min at Bus/Shuttle Center Door 1",
                direct_bill_code="SABRE-DIRBILL-ORD-992",
                room_rate_usd=165.0,
                available_rooms=120,
            ),
            HotelProperty(
                hotel_id="HTL-JFK-01",
                name="TWA Hotel at JFK Airport",
                hub="JFK",
                address="One Idlewild Drive, Terminal 5, JFK Airport, NY 11430",
                phone="+1 (212) 806-9000",
                shuttle_info="Direct AirTrain connection to Terminal 5 Station",
                direct_bill_code="SABRE-DIRBILL-JFK-810",
                room_rate_usd=230.0,
                available_rooms=60,
            ),
            HotelProperty(
                hotel_id="HTL-ATL-01",
                name="Atlanta Airport Marriott Gateway",
                hub="ATL",
                address="2020 Convention Center Concourse, Atlanta, GA 30337",
                phone="+1 (404) 763-1544",
                shuttle_info="ATL SkyTrain direct connection (2 min ride from Main Terminal)",
                direct_bill_code="SABRE-DIRBILL-ATL-401",
                room_rate_usd=175.0,
                available_rooms=95,
            ),
            HotelProperty(
                hotel_id="HTL-DFW-01",
                name="Grand Hyatt DFW Airport",
                hub="DFW",
                address="2337 S International Pkwy, Terminal D, DFW Airport, TX 75261",
                phone="+1 (972) 973-1234",
                shuttle_info="Located inside International Terminal D before pre-security",
                direct_bill_code="SABRE-DIRBILL-DFW-705",
                room_rate_usd=210.0,
                available_rooms=70,
            ),
            HotelProperty(
                hotel_id="HTL-LAX-01",
                name="Hyatt Regency Los Angeles International Airport",
                hub="LAX",
                address="6225 W Century Blvd, Los Angeles, CA 90045",
                phone="+1 (424) 702-1234",
                shuttle_info="Complimentary continuous airport shuttle from Upper/Departures level",
                direct_bill_code="SABRE-DIRBILL-LAX-330",
                room_rate_usd=185.0,
                available_rooms=110,
            ),
            # Indian Airport Hotel Network (DGCA Mandated Overnight Accommodations)
            HotelProperty(
                hotel_id="HTL-DEL-01",
                name="Radisson Blu Plaza Delhi Airport (Aerocity)",
                hub="DEL",
                address="National Highway 8, Mahipalpur, Aerocity, New Delhi, 110037",
                phone="+91 11 2677 9199",
                shuttle_info="Complimentary 24/7 Aerocity Shuttle Bus from Terminal 3 Pillar 10",
                direct_bill_code="SABRE-DIRBILL-DEL-601",
                room_rate_usd=140.0,
                available_rooms=90,
            ),
            HotelProperty(
                hotel_id="HTL-BOM-01",
                name="Taj Santacruz Mumbai Airport",
                hub="BOM",
                address="Chhatrapati Shivaji Maharaj Airport, Western Express Hwy, Mumbai, 400099",
                phone="+91 22 6211 5211",
                shuttle_info="Direct indoor pedestrian concourse link to Terminal 1 Domestic / T2 Shuttle",
                direct_bill_code="SABRE-DIRBILL-BOM-702",
                room_rate_usd=165.0,
                available_rooms=75,
            ),
            HotelProperty(
                hotel_id="HTL-BLR-01",
                name="Taj Bangalore (Kempegowda Airport Concourse)",
                hub="BLR",
                address="Opposite Kempegowda International Airport, Devanahalli, Bengaluru, 560300",
                phone="+91 80 6600 3300",
                shuttle_info="Walking distance direct concourse link from Terminal 1 & 2 arrival hall",
                direct_bill_code="SABRE-DIRBILL-BLR-803",
                room_rate_usd=150.0,
                available_rooms=80,
            ),
            HotelProperty(
                hotel_id="HTL-HYD-01",
                name="Novotel Hyderabad Airport",
                hub="HYD",
                address="Rajiv Gandhi Intl Airport, Shamshabad, Hyderabad, 500108",
                phone="+91 40 6625 5555",
                shuttle_info="Dedicated 24/7 Airport Shuttle every 10 min from Arrivals Gate E",
                direct_bill_code="SABRE-DIRBILL-HYD-904",
                room_rate_usd=130.0,
                available_rooms=65,
            ),
        ]
        for h in contracted:
            if h.hub not in self.hotels:
                self.hotels[h.hub] = []
            self.hotels[h.hub].append(h)

    def is_overnight_delay(
        self,
        scheduled_departure_iso: str,
        reaccommodated_departure_iso: Optional[str] = None,
        delay_minutes: int = 0,
    ) -> bool:
        """
        Determines whether the delay legally mandates overnight lodging
        under EU261 Article 9 / US DOT 14 CFR 259:
        - Re-accommodated departure is on the next calendar day, or
        - Total delay exceeds 360 minutes (6 hours), or
        - Departure/arrival straddles the nocturnal window (22:00 to 06:00 local).
        """
        try:
            sched_dt = datetime.fromisoformat(scheduled_departure_iso.replace("Z", "+00:00"))
        except Exception:
            sched_dt = datetime.utcnow()

        if reaccommodated_departure_iso:
            try:
                new_dt = datetime.fromisoformat(reaccommodated_departure_iso.replace("Z", "+00:00"))
                # Next day departure
                if new_dt.date() > sched_dt.date():
                    return True
                # Large gap
                if (new_dt - sched_dt).total_seconds() >= 21600:  # 6 hours
                    return True
            except Exception:
                pass

        if delay_minutes >= 360:
            return True

        # Nocturnal departure window (22:00 to 06:00) with delay >= 120m
        if (sched_dt.hour >= 22 or sched_dt.hour <= 6) and delay_minutes >= 120:
            return True

        return False

    def issue_hotel_voucher(
        self,
        pnr_id: str,
        passenger_name: str,
        disrupted_flight_num: str,
        hub_airport: str,
        cabin_class: str = "ECONOMY",
        pvs_score: int = 500,
        reaccommodated_flight_num: Optional[str] = None,
        force: bool = False,
    ) -> Optional[HotelVoucher]:
        """
        Issues an automated CRS hotel and meal voucher linked to the passenger PNR.
        VIP / Business Class passengers receive Executive Suites and elevated meal per-diems.
        """
        # Return existing voucher if already issued
        if pnr_id in self.pnr_to_voucher:
            return self.issued_vouchers[self.pnr_to_voucher[pnr_id]]

        # Fallback to ORD if hub has no contracted properties
        properties = self.hotels.get(hub_airport, self.hotels.get("ORD", []))
        if not properties:
            return None

        hotel = properties[0]
        if hotel.available_rooms > 0:
            hotel.available_rooms -= 1

        voucher_num = f"VCH-HTL-{hub_airport}-{random.randint(10000, 99999)}"

        # Room Tier selection based on cabin class and PVS score
        c_upper = str(cabin_class).upper()
        if "BUSINESS" in c_upper or "FIRST" in c_upper or pvs_score >= 650:
            room_tier = "EXECUTIVE_SUITE"
            meal_stipend = 95.00  # Elevated meal allowance for premium travelers
        else:
            room_tier = "STANDARD_KING"
            meal_stipend = 65.00

        today_dt = datetime.utcnow()
        check_in = today_dt.strftime("%Y-%m-%d")
        check_out = (today_dt + timedelta(days=1)).strftime("%Y-%m-%d")

        qr_data = (
            f"VOUCHER:{voucher_num}|PNR:{pnr_id}|HTL:{hotel.hotel_id}|"
            f"EXP:{check_out}|STIPEND:${meal_stipend:.2f}|BILL:{hotel.direct_bill_code}"
        )

        voucher = HotelVoucher(
            voucher_id=voucher_num,
            pnr_id=pnr_id,
            passenger_name=passenger_name,
            disrupted_flight=disrupted_flight_num,
            reaccommodated_flight=reaccommodated_flight_num,
            hub=hub_airport,
            hotel_name=hotel.name,
            hotel_address=hotel.address,
            hotel_phone=hotel.phone,
            shuttle_instructions=hotel.shuttle_info,
            room_tier=room_tier,
            meal_stipend_usd=meal_stipend,
            check_in_date=check_in,
            check_out_date=check_out,
            corporate_direct_bill=hotel.direct_bill_code,
            status="ISSUED",
            issued_at=datetime.utcnow().isoformat() + "Z",
            qr_payload=qr_data,
        )

        self.issued_vouchers[voucher_num] = voucher
        self.pnr_to_voucher[pnr_id] = voucher_num
        return voucher

    def get_voucher_by_pnr(self, pnr_id: str) -> Optional[HotelVoucher]:
        vid = self.pnr_to_voucher.get(pnr_id)
        if vid and vid in self.issued_vouchers:
            return self.issued_vouchers[vid]
        return None

    def get_all_vouchers(self) -> List[HotelVoucher]:
        return list(self.issued_vouchers.values())

    def get_hotel_properties(self, hub: Optional[str] = None) -> List[HotelProperty]:
        if hub:
            return self.hotels.get(hub, [])
        all_props = []
        for prop_list in self.hotels.values():
            all_props.extend(prop_list)
        return all_props


# Singleton instance
hotel_engine = HotelEngine()
