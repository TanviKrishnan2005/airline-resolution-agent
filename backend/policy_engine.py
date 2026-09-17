from pathlib import Path
import json


# ---------------------------------------------------------
# Load policy data
# ---------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent
POLICY_FILE = BASE_DIR / "data" / "policies.json"

with open(POLICY_FILE, "r", encoding="utf-8") as file:
    POLICIES = json.load(file)


# ---------------------------------------------------------
# Cancellation
# ---------------------------------------------------------

def check_cancellation_policy(booking):
    """
    Determine what the customer is entitled to when
    an airline-caused cancellation occurs.
    """

    if booking.get("status", "").lower() != "cancelled":
        return {
            "eligible": False,
            "reason": "The flight is not marked as cancelled."
        }

    return {
        "eligible": True,
        "options": [
            "free_rebooking_within_24_hours",
            "full_refund"
        ],
        "customer_choice": True
    }


# ---------------------------------------------------------
# Delay compensation
# ---------------------------------------------------------

def check_delay_policy(delay_hours):
    """
    Determine compensation based on the supplied delay rules.
    """

    if delay_hours is None:
        return {
            "eligible": False,
            "reason": "Delay duration is unavailable."
        }

    delay_hours = float(delay_hours)

    if delay_hours < 3:
        return {
            "eligible": True,
            "meal_voucher": True,
            "meal_voucher_amount": 500,
            "lounge_access": False,
            "hotel": False
        }

    if delay_hours > 5:
        return {
            "eligible": True,
            "meal_voucher": True,
            "meal_voucher_amount": None,
            "lounge_access": True,
            "hotel": True,
            "hotel_scope": "Delayed hours only, not a full night's stay"
        }

    # 3 hours through 5 hours
    return {
        "eligible": True,
        "meal_voucher": True,
        "meal_voucher_amount": None,
        "lounge_access": True,
        "hotel": False
    }


# ---------------------------------------------------------
# Refund
# ---------------------------------------------------------

def check_refund_policy(booking):
    """
    Determine whether a full refund can be initiated.
    """

    if (
        booking.get("status", "").lower() == "cancelled"
        and booking.get("reason", "").lower() == "operational reasons"
    ):
        return {
            "eligible": True,
            "refund_type": "Full refund",
            "processing_time": "Within 7 business days",
            "payment_method": "Original payment method only"
        }

    return {
        "eligible": False,
        "reason": "The supplied data does not establish eligibility for an airline-caused cancellation refund."
    }


# ---------------------------------------------------------
# Fare difference
# ---------------------------------------------------------

def check_fare_difference(fare_difference):
    """
    Determine whether the agent can handle a higher-fare
    rebooking request.
    """

    if fare_difference is None:
        return {
            "eligible": False,
            "reason": "Fare difference is unavailable."
        }

    fare_difference = float(fare_difference)

    if fare_difference <= 1500:
        return {
            "eligible": True,
            "fare_difference": fare_difference,
            "supervisor_required": False
        }

    return {
        "eligible": False,
        "fare_difference": fare_difference,
        "supervisor_required": True,
        "reason": "Fare difference exceeds the agent's ₹1,500 waiver authority."
    }


# ---------------------------------------------------------
# Loyalty
# ---------------------------------------------------------

def check_loyalty_benefit(loyalty_tier):
    """
    Gold and Platinum customers receive priority rebooking.
    Loyalty tier does not provide additional compensation.
    """

    tier = loyalty_tier.lower()

    if tier in ["gold", "platinum"]:
        return {
            "priority_rebooking": True,
            "additional_compensation": False
        }

    return {
        "priority_rebooking": False,
        "additional_compensation": False
    }


# ---------------------------------------------------------
# Full policy evaluation
# ---------------------------------------------------------

def evaluate_booking(booking, customer):
    """
    Evaluate the applicable policies for a customer's booking.
    """

    result = {
        "pnr": booking.get("pnr"),
        "customer": customer.get("name"),
        "loyalty_tier": customer.get("loyalty_tier"),
        "flight": booking.get("flight"),
        "status": booking.get("status"),
        "policies": {}
    }

    # Cancellation
    if booking.get("status", "").lower() == "cancelled":
        result["policies"]["cancellation"] = check_cancellation_policy(
            booking
        )

        result["policies"]["refund"] = check_refund_policy(
            booking
        )

    # Delay
    if booking.get("status", "").lower() == "delayed":
        result["policies"]["delay"] = check_delay_policy(
            booking.get("delay_hours")
        )

    # Loyalty
    result["policies"]["loyalty"] = check_loyalty_benefit(
        customer.get("loyalty_tier", "")
    )

    return result