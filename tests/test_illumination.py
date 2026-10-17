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


def test_a_window_gives_the_same_horizon_as_tracing_the_whole_map():
    """The window only restricts which pixels we answer for, not what blocks them."""
    rng = np.random.default_rng(3)
    h = rng.normal(0, 400, (90, 90)).astype(np.float32)
    full = il.horizon(h, res=400.0, n_azimuth=8, max_km=12)
    win = (slice(30, 50), slice(60, 75))
    assert np.array_equal(il.horizon(h, res=400.0, n_azimuth=8, max_km=12, window=win),
                          full[(slice(None), *win)])


def test_the_disc_slices_split_the_sun_into_equal_areas():
    """Each slice height is the midpoint of an equal-probability band of the disc."""
    v = il.disc_levels(9)
    assert len(v) == 9
    assert np.allclose(v, -v[::-1])  # symmetric about the centre
    assert v[4] == pytest.approx(0.0)
    assert np.abs(v).max() < 1.0  # inside the disc, not on its edge
    # A chord at height v cuts off a known fraction of the disc; the slice
    # heights should sit at 1/18, 3/18, ... of the way through it.
    above = (np.arccos(v) - v * np.sqrt(1 - v * v)) / np.pi
    assert np.allclose(above, 1 - (np.arange(9) + 0.5) / 9, atol=1e-4)


def test_one_slice_is_exactly_the_point_sun():
    """disc=1 must reproduce the older definition, counted here by hand."""
    h = np.zeros((40, 40), np.float32)
    h[:12] = 1500.0
    hor = il.horizon(h, res=600.0, n_azimuth=12, max_km=10)
    lat, lon = lola.grid(40, 600.0)
    elev, az = il.sun_track(step_hours=6)
    bins = np.round(az / (2 * np.pi) * 12).astype(int) % 12
    by_hand = np.zeros(h.shape)
    for i in range(12):
        need = hor[i] - il.local_offset(lat, lon, 2 * np.pi * i / 12)
        by_hand += (elev[bins == i][:, None, None] > need).sum(0)
    assert np.allclose(il.lit_fraction(hor, lat, lon, step_hours=6, disc=1),
                       by_hand / len(elev), atol=1e-6)


def test_a_disc_of_a_sun_finds_light_a_point_misses_entirely():
    """The case that matters here: a horizon just above where the Sun ever gets.

    The Sun's centre never clears it, so the point model calls the place dark
    for the whole year. But the top of the disc does clear it, so a panel there
    would see a sliver of Sun. That sliver is what the first pass threw away.
    """
    lat, lon = np.array([[-90.0]]), np.array([[0.0]])
    peak = np.radians(il.SOLAR_INCLINATION)
    hor = np.full((12, 1, 1), peak + 0.2 * np.radians(il.SOLAR_RADIUS_DEG), np.float32)
    assert il.lit_fraction(hor, lat, lon, disc=1)[0, 0] == 0.0
    assert il.lit_fraction(hor, lat, lon, disc=7)[0, 0] > 0.01

    # And a horizon a full solar diameter above that is dark under either model.
    hor[:] = peak + 2 * np.radians(il.SOLAR_RADIUS_DEG)
    assert il.lit_fraction(hor, lat, lon, disc=15)[0, 0] == 0.0


def test_the_disc_only_matters_at_the_edge_of_being_lit():
    """On terrain rough enough to scatter the horizons, it is a wash either way.

    Worth pinning down, because it says the disc correction is not a free
    brightening of the whole map: it moves ground that was marginal, which near
    the pole is almost all of the ground that matters, and nothing else.
    """
    rng = np.random.default_rng(11)
    h = rng.normal(0, 600, (70, 70)).astype(np.float32)
    hor = il.horizon(h, res=500.0, n_azimuth=24, max_km=15)
    lat, lon = lola.grid(70, 500.0)
    point = il.lit_fraction(hor, lat, lon, step_hours=4, disc=1)
    disc = il.lit_fraction(hor, lat, lon, step_hours=4, disc=7)
    assert abs(disc.mean() - point.mean()) < 0.001
    assert np.abs(disc - point).max() < 0.02
    assert disc.max() <= 1.0


def test_a_pit_deep_enough_stays_dark_even_with_a_disc_of_a_sun():
    """Permanent shadow has to survive the softer definition, or the ice claim goes."""
    h = np.zeros((80, 80), np.float32)
    h[35:45, 35:45] = -3000.0
    hor = il.horizon(h, res=500.0, n_azimuth=24, max_km=10)
    lat, lon = lola.grid(80, 500.0)
    assert il.lit_fraction(hor, lat, lon, step_hours=12, disc=15)[40, 40] == 0.0
