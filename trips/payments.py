import numpy as np
import logging
from collections import defaultdict, namedtuple
from decimal import Decimal
from django.contrib.auth import get_user_model


logger = logging.getLogger(__name__)
User = get_user_model()


def analyze_trips(queryset):
    """
    Rows have collect info, columns have a payment info.
    Cell in (row i, col j), mtx[i][j] == x  means that "i" collects $x from "j" (So "j" should pay
    $x to "i").

    C_i = The sum of row i, indicates how much "i" should collect.
    P_j = The sum of col j, indicates how much "j" should pay.
    T_i = (C_i - P_i) is the difference, telling if "i" ends up paying (negative result) or collecting
          (positive result).

    Returns a dict with:
        "index": dict matching matrix row-indices with User IDs
        "balance": collect (rows) and pay (columns) matrix
        "details": List with tuples (u,c,p) user u, travelling with car owner c, pays p
    """
    N = User.objects.count()
    index = {person.id: i for i, person in enumerate(User.objects.all())}
    details = []

    mtx = np.zeros((N, N), np.float64)  # (rows, cols) of Decimals

    for trip in queryset:
        row = mtx[index[trip.car.owner.id]]  # a single Row
        for passenger in trip.passengers.exclude(id=trip.car.owner.id):
            col = index[passenger.id]
            row[col] += float(trip.price_per_passenger)
            details.append(
                (passenger.get_full_name(),
                 trip.car.owner.get_full_name(),
                 trip.date,
                 float(trip.price_per_passenger))
            )
    return {
        "index": {i: u for u, i in index.items()},  # Reverse the current index
        "reverse_index": index,
        "balance": mtx - mtx.transpose(),
        "details": details
    }


# Relates User IDs with an ammount
Transaction = namedtuple("Transaction", ("id", "ammount"))


def resolve_collectors_and_payers(balance, index):
    """From the trips balance, determine who ends up paying, who collecting and who's even.

    Returns 3 lists of Transactions:
      - Users who must collect (and how much each)
      - Users who must pay (and how much each)
      - Users who are even (ammount is 0 for all of them)
    """

    N = balance.shape[0]
    collectors, payers, even = [], [], []
    for idx, ammount in enumerate(balance.sum(axis=1)):
        if ammount > 0:
            target_list = collectors
        elif ammount < 0:
            target_list = payers
        else:
            target_list = even
        target_list.append(Transaction(index[idx], round(abs(ammount), 2)))
    assert all(t.ammount == 0 for t in even)
    return collectors, payers, even


def assing_payments(collectors, payers):
    """Assing payments to collectors.

    Return a dict, where keys are """

    payments_to_collectors = {}
    for c, ammount_to_collect in collectors:
        payments = []  # Los que le pagan a c
        accum = 0  # voy sumando lo que le pagan a c
        while accum < ammount_to_collect:
            debt = payers.pop(0)  # saco un deudor
            accum += debt.ammount
            if accum <= ammount_to_collect:
                # El deudor d le paga toda su deuda a c. c sigue cobrando
                payments.append(debt)
            else: # este deudor cubre lo que le falta a c, con excedente
                excess = accum - ammount_to_collect
                to_pay = debt.ammount - excess  # Cubre lo que falta para terminar la deuda
                payments.append(
                    Transaction(debt.id, round(to_pay, 2))
                )
                new_debt = Transaction(debt.id, round(excess, 2))
                payers.append(new_debt)  # El resto de lo que debe pagar d se vuelve a meter al pozo
                accum = ammount_to_collect  # Salda la deuda
        payments_to_collectors[c] = payments
        logger.info(payments_to_collectors[c])
    logger.info(payers)
    assert len(payers) == 0

    return payments_to_collectors


def aux(p):
    f = lambda t: "{} pays {}".format(User.objects.get(pk=t.id).get_full_name(), t.ammount)
    for u, payments in p.items():
        print("{} collects: {}".format(User.objects.get(pk=u).get_full_name(), ", ".join(map(f, payments))))
