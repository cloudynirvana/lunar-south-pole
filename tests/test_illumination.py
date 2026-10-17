"""Checks on the geometry. These run without the 115 MB elevation map."""
import numpy as np
import pytest

import illumination as il
import lola


def test_flat_ground_has_a_horizon_just_below_level():
    """On a flat plain the only thing hiding the Sun is the Moon curving away."""
    hor = il.horizon(np.zeros((40, 40), np.float32), res=1000.0, n_azimuth=4, max_km=10)
    middle = hor[:, 10:30, 10:30]
    assert (middle <= 0).all()  # never above level
    assert middle.min() > np.radians(-0.2)  # but only just below it


def test_a_wall_blocks_the_sky_in_its_own_direction_only():
    h = np.zeros((60, 60), np.float32)
    h[:20] = 2000.0  # a 2 km wall across the top of the map, i.e. to the north
    hor = il.horizon(h, res=500.0, n_azimuth=4, max_km=8)
    north, south = hor[0, 30, 30], hor[2, 30, 30]
    assert north > np.radians(10)
    assert south < 0


def test_the_sun_stays_within_its_declination_range():
    elev, az = il.sun_track(step_hours=6)
    assert np.abs(np.degrees(elev)).max() == pytest.approx(il.SOLAR_INCLINATION, abs=0.01)
    assert az.min() >= 0 and az.max() < 2 * np.pi


def test_the_sun_goes_round_the_sky_once_a_month():
    _, az = il.sun_track(days=il.SYNODIC_DAY * 3.5, step_hours=1)
    assert (np.diff(az) < 0).sum() == 3  # three wraps past 360 degrees in three months


def test_a_pixel_away_from_the_pole_sees_the_sun_higher_on_one_side():
    """100 km from the pole the ground tilts by 3.3 degrees, so the Sun rides higher."""
    lat, lon = np.array([-86.7]), np.array([0.0])  # 100 km down the zero meridian
    facing = il.local_offset(lat, lon, azimuth=0.0)
    away = il.local_offset(lat, lon, azimuth=np.pi)
    assert np.degrees(facing)[0] == pytest.approx(3.3, abs=0.1)
    assert np.degrees(away)[0] == pytest.approx(-3.3, abs=0.1)


def test_a_deep_pit_is_permanently_shadowed_and_the_rim_is_not():
    h = np.zeros((80, 80), np.float32)
    h[35:45, 35:45] = -3000.0  # a 5 km wide, 3 km deep hole
    hor = il.horizon(h, res=500.0, n_azimuth=24, max_km=10)
    lat, lon = lola.grid(80, 500.0)
    lit = il.lit_fraction(hor, lat, lon, step_hours=12)
    assert lit[40, 40] == 0.0  # the floor never sees the Sun
    assert lit[20, 40] > 0.3  # the flat ground outside still does


def test_longitude_runs_east_and_zero_points_up_the_map():
    lat, lon = lola.grid(201, 1000.0)
    assert lat[100, 100] == pytest.approx(-90)
    assert lat[0, 100] == pytest.approx(-90 + np.degrees(100_000 / lola.R_MOON), abs=0.05)
    assert lon[0, 100] == pytest.approx(0)  # straight up is the prime meridian
    assert lon[100, 200] == pytest.approx(90)  # to the right is 90 east
