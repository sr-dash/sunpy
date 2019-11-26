import pytest

import astropy.units as u
from astropy.coordinates import BaseCoordinateFrame, SkyCoord, frame_transform_graph
from astropy.tests.helper import assert_quantity_allclose

import sunpy.coordinates.frames as f
from sunpy.coordinates.metaframes import RotatedSunFrame, _rotatedsun_cache


# NorthOffsetFrame is tested in test_offset_frame.py


@pytest.fixture
def rot_frames():
    return {'hgs': RotatedSunFrame(lon=1*u.deg, lat=2*u.deg, radius=3*u.AU,
                   base=f.HeliographicStonyhurst(obstime='2001-01-01'),
                   duration=4*u.day),
            'hgc': RotatedSunFrame(lon=1*u.deg, lat=2*u.deg, radius=3*u.AU,
                   base=f.HeliographicCarrington(obstime='2001-01-01'),
                   duration=4*u.day),
            'hci': RotatedSunFrame(lon=1*u.deg, lat=2*u.deg, distance=3*u.AU,
                   base=f.HeliocentricInertial(obstime='2001-01-01'),
                   duration=4*u.day),
            'hcc': RotatedSunFrame(x=1*u.AU, y=2*u.AU, z=3*u.AU,
                   base=f.Heliocentric(observer='earth', obstime='2001-01-01'),
                   duration=4*u.day),
            'hpc': RotatedSunFrame(Tx=1*u.deg, Ty=2*u.deg, distance=3*u.AU,
                   base=f.Helioprojective(observer='earth', obstime='2001-01-01'),
                   duration=4*u.day),
           }


@pytest.fixture
def base_classes():
    return {'hgs': f.HeliographicStonyhurst,
            'hgc': f.HeliographicCarrington,
            'hci': f.HeliocentricInertial,
            'hcc': f.Heliocentric,
            'hpc': f.Helioprojective,
            }


def test_class_creation(rot_frames, base_classes):
    for rot_frame, base_class in [(rot_frames[key], base_classes[key]) for key in rot_frames.keys()]:
        rot_class = type(rot_frame)

        # Check that that the RotatedSunFrame metaclass is derived from the frame's metaclass
        assert issubclass(type(rot_class), type(base_class))

        # Check that the RotatedSunFrame class name has both 'RotatedSun' and the name of the base
        assert 'RotatedSun' in rot_class.__name__
        assert base_class.__name__ in rot_class.__name__

        # Check that the base class is in fact the spcified class
        assert type(rot_frame.base) == base_class

        # Check that one-leg transformations have been created
        assert len(frame_transform_graph.get_transform(rot_class, rot_class).transforms) == 1
        assert len(frame_transform_graph.get_transform(base_class, rot_class).transforms) == 1
        assert len(frame_transform_graph.get_transform(rot_class, base_class).transforms) == 1

        # Check that the base frame is in the cache
        assert base_class in _rotatedsun_cache

        # Check that the component data has been migrated
        assert rot_frame.has_data
        assert not rot_frame.base.has_data


def test_as_base(rot_frames):
    # Check the as_base() method
    rot_hgs = rot_frames['hgs']
    a = rot_hgs.as_base()

    assert type(a) == type(rot_hgs.base)

    assert_quantity_allclose(a.lon, rot_hgs.lon)
    assert_quantity_allclose(a.lat, rot_hgs.lat)
    assert_quantity_allclose(a.radius, rot_hgs.radius)


def test_no_base():
    with pytest.raises(TypeError):
        RotatedSunFrame()


def test_no_sunpy_frame():
    with pytest.raises(TypeError):
        RotatedSunFrame(base=BaseCoordinateFrame)


def test_no_obstime():
    with pytest.raises(ValueError):
        RotatedSunFrame(base=f.HeliographicStonyhurst(obstime=None))


def test_default_duration():
    r = RotatedSunFrame(base=f.HeliographicStonyhurst(obstime='2001-01-01'))
    assert_quantity_allclose(r.duration, 0*u.day)


def test_rotated_time_to_duration():
    r1 = RotatedSunFrame(base=f.HeliographicStonyhurst(obstime='2001-01-02'),
                         rotated_time='2001-01-03')
    assert_quantity_allclose(r1.duration, 1*u.day)

    r2 = RotatedSunFrame(base=f.HeliographicStonyhurst(obstime='2001-01-02'),
                         rotated_time='2001-01-01')
    assert_quantity_allclose(r2.duration, -1*u.day)


def test_base_skycoord(rot_frames):
    # Check that RotatedSunFrame can be instantiated from a SkyCoord
    s = SkyCoord(1*u.deg, 2*u.deg, 3*u.AU, frame=f.HeliographicStonyhurst, obstime='2001-01-01')
    r = RotatedSunFrame(base=s)

    assert type(r) == type(rot_frames['hgs'])
    assert r.has_data
    assert not r.base.has_data

    assert_quantity_allclose(r.lon, s.lon)
    assert_quantity_allclose(r.lat, s.lat)
    assert_quantity_allclose(r.radius, s.radius)


def test_default_rotation_model():
    r = RotatedSunFrame(base=f.HeliographicStonyhurst(obstime='2001-01-01'))
    assert r.rotation_model == "howard"


def test_alternate_rotation_model():
    r = RotatedSunFrame(base=f.HeliographicStonyhurst(obstime='2001-01-01'),
                        rotation_model="allen")
    assert r.rotation_model == "allen"
