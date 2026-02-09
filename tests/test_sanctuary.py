import pytest
from engine.sanctuary import SanctuaryEngine, SanctuaryZone


def test_sanctuary_zone_contains():
    zone = SanctuaryZone(100, 100, 200, 200)
    assert zone.contains(150, 150)
    assert zone.contains(100, 100)
    assert zone.contains(300, 300)
    assert not zone.contains(50, 50)
    assert not zone.contains(350, 350)


def test_sanctuary_engine_disabled():
    engine = SanctuaryEngine()
    engine.add_zone(100, 100, 200, 200, "test")
    # Should return zero force when disabled
    fx, fy = engine.compute_repulsion(150, 150)
    assert fx == 0.0
    assert fy == 0.0


def test_sanctuary_engine_repulsion_inside():
    engine = SanctuaryEngine()
    engine.enabled = True
    engine.add_zone(100, 100, 200, 200, "test")
    # Fish inside zone should get strong repulsion
    fx, fy = engine.compute_repulsion(200, 200)
    assert abs(fx) > 0 or abs(fy) > 0


def test_sanctuary_engine_repulsion_margin():
    engine = SanctuaryEngine()
    engine.enabled = True
    engine.repulsion_margin = 50
    engine.add_zone(100, 100, 200, 200, "test")
    # Fish in margin zone should get some repulsion
    fx, fy = engine.compute_repulsion(70, 200)
    assert abs(fx) > 0 or abs(fy) > 0


def test_sanctuary_engine_no_repulsion_outside():
    engine = SanctuaryEngine()
    engine.enabled = True
    engine.repulsion_margin = 50
    engine.add_zone(100, 100, 200, 200, "test")
    # Fish far outside should get no repulsion
    fx, fy = engine.compute_repulsion(500, 500)
    assert fx == 0.0
    assert fy == 0.0


def test_sanctuary_toggle():
    engine = SanctuaryEngine()
    assert not engine.enabled
    result = engine.toggle()
    assert result is True
    assert engine.enabled
    result = engine.toggle()
    assert result is False
    assert not engine.enabled


def test_sanctuary_zone_serialization():
    zone = SanctuaryZone(10, 20, 300, 400, "my zone")
    d = zone.to_dict()
    restored = SanctuaryZone.from_dict(d)
    assert restored.x == 10
    assert restored.y == 20
    assert restored.w == 300
    assert restored.h == 400
    assert restored.label == "my zone"


def test_sanctuary_clear_zones():
    engine = SanctuaryEngine()
    engine.add_zone(0, 0, 100, 100)
    engine.add_zone(200, 200, 100, 100)
    assert len(engine.zones) == 2
    engine.clear_zones()
    assert len(engine.zones) == 0
