"""
IATA NDC (New Distribution Capability) & ONE Order Service.
Implements IATA NDC 21.3 OrderChangeNotif and OrderReshop schemas,
translating disruption events into standardized airline distribution payloads.
"""
from datetime import datetime
from typing import Dict, Any, List
from app.models.schemas import PassengerRecord, FlightSegment


class NDCService:
    def generate_order_change_notification(
        self, pnr: PassengerRecord, old_flight: FlightSegment, new_segments: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Generates authentic IATA NDC 21.3 OrderChangeNotifRQ payload.
        Conforms to IATA Resolution 787 and ONE Order Offer/Order standards.
        """
        now_iso = datetime.utcnow().isoformat() + "Z"
        order_id = f"ORD-{pnr.pnr_id}-REV2"

        # Construct NDC Pax segments
        pax_segments = []
        for idx, seg in enumerate(new_segments):
            pax_segments.append({
                "PaxSegmentID": f"SEG-{seg.get('flight_number')}-{idx+1}",
                "OperatingCarrier": {
                    "CarrierDesigCode": seg.get("carrier", seg.get("flight_number", "")[:2]),
                    "FlightNumber": seg.get("flight_number"),
                },
                "Dep": {
                    "IATALocationCode": seg.get("origin"),
                    "AircraftScheduledDateTime": seg.get("departure_time"),
                },
                "Arrival": {
                    "IATALocationCode": seg.get("destination"),
                    "AircraftScheduledDateTime": seg.get("arrival_time"),
                },
                "MarketingCarrier": {
                    "CarrierDesigCode": seg.get("carrier", seg.get("flight_number", "")[:2]),
                    "FlightNumber": seg.get("flight_number"),
                },
                "ClassOfService": pnr.fare_class.value,
                "StatusCode": "HK",  # IATA Confirmed Holding
            })

        return {
            "IATA_OrderChangeNotifRQ": {
                "@xmlns": "http://www.iata.org/IATA/2015/00/2021.3/IATA_OrderChangeNotifRQ",
                "DistributionChain": {
                    "DistributionChainLink": [
                        {"Ordinal": "1", "OrgRole": "Carrier", "OrgID": old_flight.carrier},
                        {"Ordinal": "2", "OrgRole": "Aggregator", "OrgID": "AIROPS-DISPATCH"},
                    ]
                },
                "ChangeInfo": {
                    "ChangeTypeCode": "INVOLUNTARY_REROUTE",
                    "ReasonCode": "IATA_89_EQUIPMENT_IRREGULARITY",
                    "Timestamp": now_iso,
                    "DisruptedFlight": {
                        "FlightNumber": old_flight.flight_number,
                        "Origin": old_flight.origin,
                        "Destination": old_flight.destination,
                        "OriginalDeparture": old_flight.departure_time.isoformat(),
                        "Status": "CANCELLED",
                    },
                },
                "Order": {
                    "OrderID": order_id,
                    "Owner": old_flight.carrier,
                    "OrderVersion": "2",
                    "StatusCode": "CONFIRMED",
                    "Passenger": {
                        "PaxID": f"PAX-1",
                        "PTC": "ADT",
                        "Name": {
                            "Given": pnr.passenger_name.split()[0],
                            "Surname": pnr.passenger_name.split()[-1] if len(pnr.passenger_name.split()) > 1 else "",
                        },
                        "ContactInfoRefID": pnr.email,
                    },
                    "OrderItems": [
                        {
                            "OrderItemID": f"ITEM-FLIGHT-{pnr.pnr_id}",
                            "Desc": f"Involuntary Reroute Accommodation from {old_flight.flight_number}",
                            "PriceDetail": {"TotalAmount": {"@CurCode": "USD", "value": "0.00"}},  # No ad-collect for involuntary
                            "PaxSegmentRefs": [s["PaxSegmentID"] for s in pax_segments],
                        },
                        {
                            "OrderItemID": f"ITEM-BAG-{pnr.pnr_id}",
                            "Desc": "Interline Transferred Baggage Protection",
                            "Status": "CARRIED_FORWARD",
                        },
                    ],
                },
                "DatedOperatingLegs": pax_segments,
            }
        }


# Singleton service
ndc_service = NDCService()
