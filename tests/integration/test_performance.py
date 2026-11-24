"""TC-NFR-01: catalogue search on 1,000 titles and 3,000 copies, 95th percentile <= 1 s (NFR-01)."""
import random
import time

from library.services.catalogue import is_valid_isbn


def isbn_for(n: int) -> str:
    body = f"978{n:09d}"
    check = (10 - sum(int(d) * (3 if i % 2 else 1) for i, d in enumerate(body)) % 10) % 10
    return body + str(check)


def test_TC_NFR_01_search_performance(svc):
    con = svc.db.connection()
    words = ["river", "night", "garden", "stone", "winter", "empire", "letters", "shadow", "ocean", "silver"]
    titles = [(isbn_for(n), f"{words[n % 10].title()} {words[(n // 10) % 10]} {n}", f"Author {n % 97}", 2000)
              for n in range(1000)]
    assert all(is_valid_isbn(t[0]) for t in titles[:5])
    with svc.db.transaction():
        con.executemany("INSERT INTO title (isbn, title, author, pub_year) VALUES (?, ?, ?, ?)", titles)
        con.executemany("INSERT INTO copy (title_id, code, status) VALUES (?, ?, 'available')",
                        [(t, f"C-{t}-{k}") for t in range(1, 1001) for k in range(3)])

    rnd = random.Random(42)
    timings = []
    for _ in range(100):
        text = rnd.choice(words + ["author 5", "978000000", ""])
        start = time.perf_counter()
        svc.catalogue.search(text)
        timings.append(time.perf_counter() - start)
    p95 = sorted(timings)[94]
    print(f"\nNFR-01 search p95 = {p95 * 1000:.1f} ms")
    assert p95 <= 1.0
