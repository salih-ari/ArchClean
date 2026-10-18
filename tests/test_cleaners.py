import os
import tempfile
from archclean.cleaner.cache import UserCacheCleaner
from archclean.cleaner.base import CleanItem


def test_user_cache_scan_and_clean():
    d = tempfile.mkdtemp()
    os.makedirs(os.path.join(d, "foo"))
    with open(os.path.join(d, "foo", "a.txt"), "w") as f:
        f.write("x" * 100)
    with open(os.path.join(d, "bar"), "w") as f:
        f.write("y" * 50)

    c = UserCacheCleaner(cache_dir=d)
    items = c.scan()
    assert len(items) == 2
    for it in items:
        it.selected = True
    res = c.clean(items)
    assert res.removed_count == 2
    assert res.freed_bytes == 150
    assert os.listdir(d) == []
    import shutil
    shutil.rmtree(d)
