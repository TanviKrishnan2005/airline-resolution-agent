from pathlib import Path
import json
import re
from datetime import datetime

from policy_engine import (
    check_cancellation_policy,
    check_delay_policy,
    check_refund_policy,
    check_fare_difference,
    check_loyalty_benefit
)


# =========================================================
# DATA LOADING
# =========================================================

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

with open(
    DATA_DIR / "customers.json",
    "r",
    encoding="utf-8"
) as file:
    CUSTOMERS = json.load(file)

with open(
    DATA_DIR / "bookings.json",
    "r",
    encoding="utf-8"
) as file:
    BOOKINGS = json.load(file)


# =========================================================
# ACTION LOG
# =========================================================

ACTION_LOG = []


# =========================================================
# CUSTOMER LOOKUP
# =========================================================

def find_customer(identifier):
    identifier = identifier.lower().strip()

    for customer in CUSTOMERS:

        if (
            identifier == customer["name"].lower()
            or
            identifier == customer["booking_reference"].lower()
        ):
            return customer

    return None


# =========================================================
# BOOKING LOOKUP
# =========================================================

def get_bookings_for_customer(pnr):

    return [
        booking
        for booking in BOOKINGS
        if booking.get("pnr", "").lower() == pnr.lower()
    ]


def get_primary_booking(pnr):

    bookings = get_bookings_for_customer(pnr)

    # Prefer disrupted booking
    for booking in bookings:

        status = booking.get(
            "status",
            ""
        ).lower()

        if status in [
            "cancelled",
            "delayed"
        ]:
            return booking

    return bookings[0] if bookings else None


# =========================================================
# INTENT DETECTION
# =========================================================

def detect_intents(message):

    text = message.lower().strip()

    intents = []

    # Cancellation
    if any(
        word in text
        for word in [
            "cancel",
            "cancelled",
            "canceled"
        ]
    ):
        intents.append("cancellation")

    # Delay
    if any(
        word in text
        for word in [
            "delay",
            "delayed",
            "late"
        ]
    ):
        intents.append("delay")

    # Refund
    if any(
        word in text
        for word in [
            "refund",
            "money back",
            "cash back"
        ]
    ):
        intents.append("refund")

    # Hotel
    if any(
        word in text
        for word in [
            "hotel",
            "accommodation",
            "stay"
        ]
    ):
        intents.append("hotel")

    # Upgrade
    if any(
        word in text
        for word in [
            "upgrade",
            "business class"
        ]
    ):
        intents.append("upgrade")

    # Rebooking
    if any(
        word in text
        for word in [
            "rebook",
            "rebooking",
            "different flight",
            "another flight",
            "move me"
        ]
    ):
        intents.append("rebooking")

    # Compensation
    if any(
        word in text
        for word in [
            "compensation",
            "compensate"
        ]
    ):
        intents.append("compensation")

    # Legal / formal complaint
    if any(
        word in text
        for word in [
            "complaint",
            "legal",
            "lawyer",
            "lawsuit",
            "court"
        ]
    ):
        intents.append("formal_complaint")

    # Angry / frustrated
    if any(
        word in text
        for word in [
            "furious",
            "angry",
            "unacceptable",
            "frustrated",
            "frustrating",
            "ridiculous"
        ]
    ):
        intents.append("angry_customer")

    return list(dict.fromkeys(intents))


# =========================================================
# FARE DIFFERENCE
# =========================================================

def extract_fare_difference(message):

    patterns = [
        r"₹\s*([\d,]+)",
        r"rs\.?\s*([\d,]+)",
        r"inr\s*([\d,]+)",
        r"fare difference[^0-9]*([\d,]+)"
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            message.lower()
        )

        if match:

            return float(
                match.group(1).replace(
                    ",",
                    ""
                )
            )

    return None


# =========================================================
# ACTION LOGGING
# =========================================================

def log_action(
    customer,
    action,
    status,
    details=None
):

    record = {
        "timestamp": datetime.now().isoformat(
            timespec="seconds"
        ),
        "customer": customer["name"],
        "pnr": customer["booking_reference"],
        "action": action,
        "status": status,
        "details": details
    }

    ACTION_LOG.append(record)

    return record


# =========================================================
# PREVIOUS ACTION CHECK
# =========================================================

def has_previous_action(
    customer,
    action
):

    pnr = customer["booking_reference"]

    for record in ACTION_LOG:

        if (
            record["pnr"] == pnr
            and
            record["action"] == action
            and
            record["status"] in [
                "Initiated",
                "Issued",
                "Arranged",
                "Allowed"
            ]
        ):
            return True

    return False


# =========================================================
# PREVIOUS ACTION
# =========================================================

def get_previous_action(
    customer,
    action
):

    pnr = customer["booking_reference"]

    for record in reversed(ACTION_LOG):

        if (
            record["pnr"] == pnr
            and
            record["action"] == action
            and
            record["status"] in [
                "Initiated",
                "Issued",
                "Arranged",
                "Allowed"
            ]
        ):
            return record

    return None


# =========================================================
# ESCALATION
# =========================================================

def add_escalation(
    customer,
    reason,
    actions
):

    # Avoid duplicate escalation records

    for record in ACTION_LOG:

        if (
            record["pnr"]
            == customer["booking_reference"]
            and
            record["action"]
            == "escalation"
            and
            record["details"]
            == reason
        ):
            return False

    actions.append(
        log_action(
            customer,
            "escalation",
            "Escalated to human agent",
            reason
        )
    )

    return True


# =========================================================
# MAIN AGENT
# =========================================================

def process_message(
    message,
    customer_identifier
):

    # -----------------------------------------------------
    # CUSTOMER
    # -----------------------------------------------------

    customer = find_customer(
        customer_identifier
    )

    if not customer:

        return {
            "success": False,
            "response": (
                "I couldn't identify a customer from "
                "the information provided."
            ),
            "actions": [],
            "escalated": False
        }


    # -----------------------------------------------------
    # BOOKING
    # -----------------------------------------------------

    pnr = customer[
        "booking_reference"
    ]

    booking = get_primary_booking(
        pnr
    )

    if not booking:

        return {
            "success": False,
            "response": (
                "I couldn't find a booking associated "
                "with this customer."
            ),
            "actions": [],
            "escalated": False
        }


    # -----------------------------------------------------
    # BASIC VARIABLES
    # -----------------------------------------------------

    status = booking.get(
        "status",
        ""
    ).lower()

    intents = detect_intents(
        message
    )

    fare_difference = extract_fare_difference(
        message
    )

    actions = []

    response_parts = []

    escalation_reasons = []


    # =====================================================
    # GENERAL GREETING / NO INTENT
    # =====================================================

    if not intents and fare_difference is None:

        if status == "cancelled":

            response_parts.append(
                f"Hi {customer['name']}, I can help with "
                f"your cancelled flight "
                f"{booking.get('flight')} from "
                f"{booking.get('route')}. "
                f"Would you prefer a free rebooking on the "
                f"next available flight within 24 hours, "
                f"or a full refund to your original payment method?"
            )

        elif status == "delayed":

            response_parts.append(
                f"Hi {customer['name']}, I can help with "
                f"your delayed flight "
                f"{booking.get('flight')} from "
                f"{booking.get('route')}. "
                f"What would you like help with regarding "
                f"the delay?"
            )

        else:

            response_parts.append(
                f"Hi {customer['name']}, how can I help "
                f"with your booking today?"
            )


    # =====================================================
    # FORMAL COMPLAINT / LEGAL
    # =====================================================

    if "formal_complaint" in intents:

        reason = (
            "Customer mentioned legal action "
            "or a formal complaint."
        )

        escalation_reasons.append(
            reason
        )

        response_parts.append(
            "Because you mentioned legal action or a "
            "formal complaint, this must be handled "
            "by a human specialist."
        )


    # =====================================================
    # CANCELLED FLIGHT
    # =====================================================

    cancellation_intent = any(
        intent in intents
        for intent in [
            "cancellation",
            "refund",
            "rebooking",
            "upgrade"
        ]
    )

    if (
        status == "cancelled"
        and
        cancellation_intent
    ):

        cancellation = check_cancellation_policy(
            booking
        )

        response_parts.append(
            f"I can confirm that flight "
            f"{booking.get('flight')} from "
            f"{booking.get('route')} was cancelled "
            f"due to "
            f"{booking.get('reason', 'operational reasons').lower()}."
        )


        # -------------------------------------------------
        # REFUND
        # -------------------------------------------------

        if "refund" in intents:

            refund = check_refund_policy(
                booking
            )

            if refund.get("eligible"):

                previous_refund = get_previous_action(
                    customer,
                    "refund_request"
                )

                if previous_refund:

                    response_parts.append(
                        "A full refund has already been "
                        "initiated to your original payment "
                        "method. It is processed within "
                        "7 business days."
                    )

                else:

                    actions.append(
                        log_action(
                            customer,
                            "refund_request",
                            "Initiated",
                            "Full refund to original payment method"
                        )
                    )

                    response_parts.append(
                        "I have initiated a full refund to "
                        "your original payment method. "
                        "Refunds are processed within "
                        "7 business days."
                    )


        # -------------------------------------------------
        # REBOOKING
        # -------------------------------------------------

        if "rebooking" in intents:

            if has_previous_action(
                customer,
                "rebooking"
            ):

                response_parts.append(
                    "Your rebooking request has already "
                    "been recorded."
                )

            else:

                actions.append(
                    log_action(
                        customer,
                        "rebooking",
                        "Allowed",
                        "Next available flight within 24 hours"
                    )
                )

                response_parts.append(
                    "I can rebook you on the next available "
                    "flight within 24 hours at no charge."
                )


    # =====================================================
    # DELAYED FLIGHT
    # =====================================================

    delay_intent = any(
        intent in intents
        for intent in [
            "delay",
            "hotel",
            "compensation"
        ]
    )

    if (
        status == "delayed"
        and
        delay_intent
    ):

        delay_hours = booking.get(
            "delay_hours"
        )

        delay_policy = check_delay_policy(
            delay_hours
        )

        response_parts.append(
            f"Your flight is delayed by "
            f"{delay_hours} hours, with a new departure "
            f"time of "
            f"{booking.get('new_departure')}."
        )


        # -------------------------------------------------
        # MEAL VOUCHER
        # -------------------------------------------------

        if delay_policy.get(
            "meal_voucher"
        ):

            if not has_previous_action(
                customer,
                "meal_voucher"
            ):

                actions.append(
                    log_action(
                        customer,
                        "meal_voucher",
                        "Issued",
                        "Issued according to delay compensation policy"
                    )
                )


        # -------------------------------------------------
        # LOUNGE ACCESS
        # -------------------------------------------------

        if delay_policy.get(
            "lounge_access"
        ):

            if not has_previous_action(
                customer,
                "lounge_access"
            ):

                actions.append(
                    log_action(
                        customer,
                        "lounge_access",
                        "Issued",
                        "Issued according to delay compensation policy"
                    )
                )


        # -------------------------------------------------
        # HOTEL
        # -------------------------------------------------

        if "hotel" in intents:

            if delay_policy.get(
                "hotel"
            ):

                previous_hotel = get_previous_action(
                    customer,
                    "hotel_accommodation"
                )

                if previous_hotel:

                    response_parts.append(
                        "Hotel accommodation covering "
                        "the delayed hours has already "
                        "been arranged."
                    )

                else:

                    actions.append(
                        log_action(
                            customer,
                            "hotel_accommodation",
                            "Arranged",
                            delay_policy.get(
                                "hotel_scope"
                            )
                        )
                    )

                    response_parts.append(
                        "Your delay qualifies for hotel "
                        "accommodation covering the "
                        "delayed hours only, not a full "
                        "night's stay."
                    )

            else:

                response_parts.append(
                    "Hotel accommodation does not apply "
                    "under the supplied policy for this "
                    "delay duration."
                )


        # -------------------------------------------------
        # POLICY BENEFITS
        # -------------------------------------------------

        if delay_policy.get(
            "meal_voucher"
        ):

            response_parts.append(
                "Your delay qualifies for a meal voucher."
            )

        if delay_policy.get(
            "lounge_access"
        ):

            response_parts.append(
                "It also qualifies for lounge access."
            )


    # =====================================================
    # BUSINESS CLASS UPGRADE
    # =====================================================

    if "upgrade" in intents:

        reason = (
            "Requested free business-class upgrade is "
            "not included in the supplied service policy."
        )

        escalation_reasons.append(
            reason
        )

        response_parts.append(
            "The requested free business-class upgrade "
            "is not covered by the supplied service policy, "
            "so I cannot approve it directly."
        )


    # =====================================================
    # FARE DIFFERENCE
    # =====================================================

    if fare_difference is not None:

        fare_policy = check_fare_difference(
            fare_difference
        )

        if fare_policy.get(
            "supervisor_required"
        ):

            reason = (
                f"Fare difference of "
                f"₹{fare_difference:,.0f} exceeds "
                f"the agent's ₹1,500 authority."
            )

            escalation_reasons.append(
                reason
            )

            response_parts.append(
                f"The requested flight has a fare "
                f"difference of ₹{fare_difference:,.0f}. "
                f"I cannot waive a fare difference above "
                f"₹1,500, so this request requires "
                f"supervisor approval."
            )


    # =====================================================
    # LOYALTY BENEFIT
    # =====================================================

    loyalty = check_loyalty_benefit(
        customer.get(
            "loyalty_tier",
            ""
        )
    )

    if loyalty.get(
        "priority_rebooking"
    ):

        # Only mention priority rebooking when relevant
        if (
            "rebooking" in intents
            or
            status == "cancelled"
            and
            not intents
        ):

            response_parts.append(
                f"As a {customer.get('loyalty_tier')} "
                f"customer, you receive priority access "
                f"to next-available rebooking. This does "
                f"not provide additional compensation "
                f"beyond the standard policy."
            )


    # =====================================================
    # ESCALATIONS
    # =====================================================

    escalated = False

    for reason in escalation_reasons:

        created = add_escalation(
            customer,
            reason,
            actions
        )

        escalated = True

    if escalation_reasons:

        response_parts.append(
            "I have escalated the applicable parts of "
            "your request to a human specialist because "
            "they are outside my authority."
        )


    # =====================================================
    # ANGRY CUSTOMER EMPATHY
    # =====================================================

    if (
        "angry_customer" in intents
        and
        response_parts
    ):

        response = (
            "I understand you're frustrated, and I'm "
            "sorry for the disruption. "
            +
            " ".join(response_parts)
        )

    else:

        response = " ".join(
            response_parts
        )


    # =====================================================
    # FALLBACK
    # =====================================================

    if not response:

        response = (
            f"I can help with your booking "
            f"{customer['booking_reference']}. "
            f"Please tell me what you need help with."
        )


    # =====================================================
    # RESULT
    # =====================================================

    return {
        "success": True,
        "customer": customer,
        "booking": booking,
        "intents": intents,
        "response": response,
        "actions": actions,
        "escalated": escalated
    }


# =========================================================
# ACTION LOG API
# =========================================================

def get_action_log():

    return ACTION_LOG