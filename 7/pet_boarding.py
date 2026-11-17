
import math


def parse_booking(text):
    if not isinstance(text, str):
        return "", 0.0

    parts = text.split(':')

    if len(parts) != 2:
        return "", 0.0

    pet, days = parts
    pet = pet.strip()

    if not pet:
        return "", 0.0

    try:
        days = float(days)
        if not math.isfinite(days) or days < 0:
            return "", 0.0
    except (ValueError, TypeError):
        return "", 0.0

    return pet.title(), days


def stay_average(days_csv):
    if not isinstance(days_csv, str) or not days_csv.strip():
        return 0

    try:
        parts = days_csv.split(',')
        values = [int(r.strip()) for r in parts]

        if not values or any(v < 0 for v in values):
            return 0

        return sum(values) // len(values)

    except (ValueError, TypeError):
        return 0


def payable_fee(text):
    if not isinstance(text, str):
        return 0.0

    parts = text.split('|')

    if len(parts) != 2:
        return 0.0

    try:
        fee = float(parts[0].strip())
        discount = float(parts[1].strip())

        if not math.isfinite(fee) or not math.isfinite(discount):
            return 0.0

        if fee < 0 or discount < 0:
            return 0.0

        total = fee * 1.18 - discount

        return max(total, 0.0)

    except (ValueError, TypeError):
        return 0.0


def main():
    print("==== Running parse_booking ====")
    user_input = input("Enter pet:days (e.g. dog:5): ")
    result = parse_booking(user_input)
    print("Pet and Days:", result)

    print("\n==== Running stay_average ====")
    user_input = input("Enter stay lengths in days as CSV (e.g. 2,5,7): ")
    result = stay_average(user_input)
    print("Average Stay:", result)

    print("\n==== Running payable_fee ====")
    user_input = input("Enter fee|discount (e.g. 1500|100): ")
    result = payable_fee(user_input)
    print("Payable Fee:", result)


if __name__ == "__main__":
    main()
