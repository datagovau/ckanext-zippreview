import ckanext.zippreview.utils as utils


def test_can_view_invalid():
    res_data = {
        'url': 'https://test.com/123/sdsd/cr_86362_3.jpeg',
        'format': ''
    }
    assert not utils.is_resource_supported(res_data)


def test_can_view_valid():
    res_data = {
        'url': 'https://test.com/123/sdsd/cr_86362_3.zip',
        'format': 'zip'
    }
    assert utils.is_resource_supported(res_data)


def test_can_view_parse_from_url():
    res_data = {
        'url': 'https://test.com/123/sdsd/cr_86362_3.zip',
        'format': ''
    }
    assert utils.is_resource_supported(res_data)


def test_can_view_no_format():
    res_data = {
        'url': 'https://test.com/123/sdsd/cr_86362_3',
        'format': ''
    }
    assert not utils.is_resource_supported(res_data)

