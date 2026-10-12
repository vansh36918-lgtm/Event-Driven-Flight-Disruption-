"""
Global Airline Alliance & Interline Re-Ticketing Matrix Engine.
Handles Star Alliance, SkyTeam, and OneWorld interline baggage agreements,
fare class reciprocal mapping, and IATA Rule 240 involuntary endorsement code generation.
"""
from typing import Dict, List, Optional, Tuple


class AirlineAllianceEngine:
    def __init__(self):
        # Global Alliances
        self.alliances: Dict[str, str] = {
            # OneWorld
            "AA": "ONEWORLD",
            "BA": "ONEWORLD",
            "IB": "ONEWORLD",
            "CX": "ONEWORLD",
            "QF": "ONEWORLD",
            "JL": "ONEWORLD",
            "AY": "ONEWORLD",
            "QR": "ONEWORLD",
            # Star Alliance
            "UA": "STAR_ALLIANCE",
            "LH": "STAR_ALLIANCE",
            "AC": "STAR_ALLIANCE",
            "SQ": "STAR_ALLIANCE",
            "NH": "STAR_ALLIANCE",
            "LX": "STAR_ALLIANCE",
            "OS": "STAR_ALLIANCE",
            "TK": "STAR_ALLIANCE",
            # SkyTeam
            "DL": "SKYTEAM",
            "AF": "SKYTEAM",
            "KL": "SKYTEAM",
            "KE": "SKYTEAM",
            "AZ": "SKYTEAM",
            "UX": "SKYTEAM",
            "AM": "SKYTEAM",
            # Non-Alliance / Hybrid Bilateral
            "B6": "HYBRID_PARTNER",
            "AS": "ONEWORLD",
            "WN": "STANDALONE",
        }

        # Bilateral interline e-ticketing agreements outside alliance
        self.bilateral_agreements: List[Tuple[str, str]] = [
            ("B6", "AA"),  # Northeast Alliance legacy interline
            ("B6", "BA"),
            ("B6", "DL"),
            ("AS", "AA"),
            ("AS", "BA"),
        ]

    def get_alliance(self, carrier: str) -> str:
        """Returns the alliance code or STANDALONE for a given carrier."""
        return self.alliances.get(carrier.upper(), "INDEPENDENT")

    def compute_affinity_score(self, original_carrier: str, alternative_carrier: str) -> float:
        """
        Computes routing preference affinity (0.0 to 1.0):
        1.00 - Same operating metal
        0.90 - Same alliance partner (Star Alliance, OneWorld, SkyTeam)
        0.70 - Bilateral interline e-ticketing agreement
        0.35 - Unaffiliated competitor (Rule 240 involuntary ticket endorsement required)
        """
        c1 = original_carrier.upper()
        c2 = alternative_carrier.upper()

        if c1 == c2:
            return 1.00

        alliance1 = self.get_alliance(c1)
        alliance2 = self.get_alliance(c2)

        if alliance1 != "INDEPENDENT" and alliance1 == alliance2:
            return 0.90

        if (c1, c2) in self.bilateral_agreements or (c2, c1) in self.bilateral_agreements:
            return 0.70

        return 0.35

    def check_interline_baggage_through_check(self, carrier1: str, carrier2: str) -> bool:
        """
        Evaluates whether checked luggage can be automatically transferred
        without passenger reclaiming at layover carousel.
        """
        c1 = carrier1.upper()
        c2 = carrier2.upper()

        if c1 == c2:
            return True

        alliance1 = self.get_alliance(c1)
        alliance2 = self.get_alliance(c2)

        # Same alliance or bilateral interline allows through-check
        if alliance1 != "INDEPENDENT" and alliance1 == alliance2:
            return True

        if (c1, c2) in self.bilateral_agreements or (c2, c1) in self.bilateral_agreements:
            return True

        return False

    def generate_rule_240_endorsement(
        self, original_carrier: str, rerouted_carrier: str, pnr_id: str
    ) -> Dict[str, str]:
        """
        Generates official IATA Rule 240 / Rule 80 Involuntary Reroute Endorsement.
        Used on GDS ticket reissue to prevent debit memos between interline accounting departments.
        """
        c1 = original_carrier.upper()
        c2 = rerouted_carrier.upper()
        alliance1 = self.get_alliance(c1)
        alliance2 = self.get_alliance(c2)

        if c1 == c2:
            endorsement_text = f"INVOL REROUTE / {c1} OPS IRROPS / NON-ENDO / FREE EXCHANGE"
            protocol = "SAME_METAL_PROTECTION"
        elif alliance1 != "INDEPENDENT" and alliance1 == alliance2:
            endorsement_text = f"INVOL REROUTE / {alliance1} RECIPROCAL AGREEMENT / IATA RES 766 / {pnr_id}"
            protocol = f"ALLIANCE_{alliance1}_PROTECTION"
        elif (c1, c2) in self.bilateral_agreements or (c2, c1) in self.bilateral_agreements:
            endorsement_text = f"INVOL REROUTE / BILATERAL MITA AGREEMENT / TKT EXCHANGE / {pnr_id}"
            protocol = "BILATERAL_MITA_PROTECTION"
        else:
            endorsement_text = f"INVOL REROUTE / IATA RULE 240 INVOL ENDO / CARRIER SETTLEMENT VIA ICH / {pnr_id}"
            protocol = "RULE_240_INVOLUNTARY"

        return {
            "endorsement_string": endorsement_text,
            "protocol": protocol,
            "interline_clearing_house": "IATA_ICH_SETTLEMENT_GENEVA",
            "baggage_through_check": "APPROVED" if self.check_interline_baggage_through_check(c1, c2) else "MANUAL_RECLAIM_REQUIRED",
        }


# Singleton instance
alliance_engine = AirlineAllianceEngine()
