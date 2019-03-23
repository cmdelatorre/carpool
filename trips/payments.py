import numpy as np

from collections import defaultdict
from decimal import Decimal
from django.contrib.auth import get_user_model


User = get_user_model()


def create_pay_collect_matrix(queryset):
    """
    Rows have collect info, columns have a payment info.
    Cell in (row i, col j), mtx[i][j] == x  means that "i" collects $x from "j" (So "j" should pay
    $x to "i").

    C_i = The sum of row i, indicates how much "i" should collect.
    P_j = The sum of col j, indicates how much "j" should pay.
    T_i = (C_i - P_i) is the difference, telling if "i" ends up paying (negative result) or collecting
          (positive result).

    """
    N = User.objects.count()
    index = {person.id:i for i, person in enumerate(User.objects.all())}
    details = []

    mtx = np.zeros((N, N), np.float64)  # (rows, cols) of Decimals

    for trip in queryset:
        row = mtx[index[trip.car.owner.id]]  # a single Row
        for passenger in trip.passengers.exclude(id=trip.car.owner.id):
            col = index[passenger.id]
            row[col] += float(trip.price_per_passenger)
            details.append((passenger.get_full_name(), trip.car.owner.get_full_name(), float(trip.price_per_passenger)))
    return mtx - mtx.transpose(), details
