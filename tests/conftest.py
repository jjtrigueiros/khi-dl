import pytest
from aioresponses import aioresponses
from yarl import URL
from khi_dl.main import KhiTrack


sample_track_page_html = """
<html>
<body>
    <div id="audio" src="http://example.com/audio.mp3"></div>
</body>
</html>
"""


sample_album_page_html = """
<html>
<body>
    <h2>Sample Album</h2>
    <table id="songlist">
        <tr>
            <th>CD</th>
            <th>#</th>
            <th>Song Name</th>
        </tr>
        <tr>
            <td>1.</td>
            <td>2</td>
            <td><a href="/track1">Track 1</a></td>
        </tr>
        <tr>
            <td>3</td>
            <td>4.</td>
            <td><a href="/track2">Track 2</a></td>
        </tr>
        <tr id="songlist_footer">
	        <th></th>
	        <th></th>
	    	<th></th>
        </tr>
    </table>
</body>
</html>
"""


@pytest.fixture
def khi_track():
    return KhiTrack(
        khi_page=URL("http://example.com/track1"), name="Track 1", number=1, disc=1
    )


@pytest.fixture
def mock_khinsider():
    with aioresponses() as m:
        m.get("http://example.com/album1", body=sample_album_page_html)
        m.get("http://example.com/track1", body=sample_track_page_html)
        m.get("http://example.com/audio.mp3", body=b"1234567890")
        yield m
