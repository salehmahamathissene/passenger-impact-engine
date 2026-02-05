from pie.domain.models import DisruptionEvent, DisruptionType, EligibilityContext, Passenger, Segment
from pie.domain.regulations.eu261 import EU261Config, assess_eu261


def base_cfg() -> EU261Config:
    return EU261Config(
        meal_cost=15,
        hotel_cost_per_night=90,
        ground_transport_cost=25,
        refund_rate=0.15,
        rebooking_cost_mean=120,
        rebooking_cost_std=45,
    )


def test_not_applicable_zero_cash():
    p = Passenger(id="P00001", segment=Segment.LEISURE, fare_paid=200, refundable=False)
    ctx = EligibilityContext(carrier_is_eu=False, dep_in_eu=False, arr_in_eu=True, distance_km=1000)
    ev = DisruptionEvent(dtype=DisruptionType.CANCEL, delay_minutes=0)
    out = assess_eu261(p, ctx, ev, base_cfg(), sampled_rebooking_cost_eur=100)
    assert out.cash_comp_eur == 0.0
    assert out.total_cost_eur == 0.0
    assert out.note is not None


def test_delay_threshold_short_band():
    p = Passenger(id="P00002", segment=Segment.LEISURE, fare_paid=100, refundable=False)
    ctx = EligibilityContext(carrier_is_eu=True, dep_in_eu=True, arr_in_eu=True, distance_km=1200)
    cfg = base_cfg()

    ev_low = DisruptionEvent(dtype=DisruptionType.DELAY, delay_minutes=119)
    out_low = assess_eu261(p, ctx, ev_low, cfg, sampled_rebooking_cost_eur=0)
    assert out_low.cash_comp_eur == 0.0

    ev_hi = DisruptionEvent(dtype=DisruptionType.DELAY, delay_minutes=120)
    out_hi = assess_eu261(p, ctx, ev_hi, cfg, sampled_rebooking_cost_eur=0)
    assert out_hi.cash_comp_eur == 250.0


def test_cancel_compensation_medium_band():
    p = Passenger(id="P00003", segment=Segment.BUSINESS, fare_paid=800, refundable=True)
    ctx = EligibilityContext(carrier_is_eu=True, dep_in_eu=True, arr_in_eu=True, distance_km=2000)
    ev = DisruptionEvent(dtype=DisruptionType.CANCEL, delay_minutes=0)
    out = assess_eu261(p, ctx, ev, base_cfg(), sampled_rebooking_cost_eur=50)
    assert out.cash_comp_eur == 400.0
    assert out.total_cost_eur > 0
