import pytest
from utils.social_media_handler import SocialMediaHandler


def test_txt_to_json(db, client):
    txt = 'a=b&c=xxx-sdf_a1&k=123'
    res = SocialMediaHandler().txt_to_json(txt)
    assert res == {
        'a': 'b',
        'c': 'xxx-sdf_a1',
        'k': '123'
    }

    txt = 'a'
    with pytest.raises(ValueError):
        SocialMediaHandler().txt_to_json(txt)