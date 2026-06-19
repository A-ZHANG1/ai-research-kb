import pathlib
import sys
import tempfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "src"))

from memory import Memory  # noqa: E402


def test_dedup_persistence_and_search():
    tmp = tempfile.mkdtemp()
    db = pathlib.Path(tmp) / "test.db"

    mem = Memory(db)
    # unseen at start
    assert not mem.is_seen("http://a.com/1")

    mem.add_article("http://a.com/1", source="A", title="Agent memory deep dive",
                    content="hello world. about agents. foo bar.",
                    summary="s1")
    assert mem.is_seen("http://a.com/1")

    # dedup: inserting same URL again must not duplicate
    mem.add_article("http://a.com/1", source="A", title="dup")
    assert mem.stats()["total_articles"] == 1

    # search the corpus
    assert len(mem.search("agent")) == 1
    assert len(mem.search("nonexistent-term")) == 0

    mem.log_run(1)
    assert mem.stats()["total_runs"] == 1
    mem.close()

    # persistence: reopen the same DB file -> memory survives
    mem2 = Memory(db)
    assert mem2.is_seen("http://a.com/1")
    assert mem2.stats()["total_articles"] == 1
    mem2.close()

    print("test_dedup_persistence_and_search PASSED")


if __name__ == "__main__":
    test_dedup_persistence_and_search()
