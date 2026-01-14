import json

import pytest
from sqlmodel import Session, select

from db.db_client import DBClient
from db.model import Case
from shared.dto import CaseQueryResponseDTO, CaseResponseDTO, Meta


@pytest.fixture
def db_client(get_config):
    get_config.db_name = ":memory:"
    return DBClient(get_config)


def make_case(id: int, ts: int):
    return CaseResponseDTO(
        id=id,
        logical_timestamp=ts,
    )


def make_page(cases, offset=0, total=None):
    return CaseQueryResponseDTO(
        meta=Meta(
            limit=len(cases),
            offset=offset,
            next=None,
            previous=None,
            total_count=total or len(cases),
        ),
        objects=cases,
    )


def test_insert_case_persists_case(get_config):
    db_client = DBClient(get_config)

    case = Case(
        id=123,
        logical_timestamp=42,
        blob=json.dumps({"id": 123, "name": "Test Case"}),
    )

    db_client.insert_case(case)

    with Session(db_client._engine) as session:
        stmt = select(Case).where(Case.id == 123)
        persisted_case = session.exec(stmt).one_or_none()

        assert persisted_case is not None
        assert persisted_case.id == 123
        assert persisted_case.logical_timestamp == 42
        assert json.loads(persisted_case.blob)["name"] == "Test Case"


def test_insert_case_commit_failure(monkeypatch, get_config):
    db_client = DBClient(get_config)

    def fail_commit(self):
        raise RuntimeError("Simulated DB commit failure")

    monkeypatch.setattr(Session, "commit", fail_commit)

    case = Case(
        id=1,
        logical_timestamp=1,
        blob="{}",
    )

    with pytest.raises(RuntimeError, match="Simulated DB commit failure"):
        db_client.insert_case(case)


def test_sync_inserts_missing_case(db_client):
    remote_pages = iter([make_page([make_case(1, 10)])])

    db_client.synchronize_with_intempus(remote_pages)

    with Session(db_client._engine) as session:
        case = session.exec(select(Case)).one()
        assert case.id == 1
        assert case.logical_timestamp == 10


def test_sync_updates_case_when_remote_newer(db_client):
    db_client.insert_case(Case(id=1, logical_timestamp=5, blob='{"old": true}'))

    remote_pages = iter([make_page([make_case(1, 10)])])

    db_client.synchronize_with_intempus(remote_pages)

    with Session(db_client._engine) as session:
        case = session.get(Case, 1)
        assert case.logical_timestamp == 10  # ty:ignore[possibly-missing-attribute]


def test_sync_noop_when_timestamps_equal(db_client):
    db_client.insert_case(Case(id=1, logical_timestamp=10, blob='{"same": true}'))

    remote_pages = iter([make_page([make_case(1, 10)])])

    db_client.synchronize_with_intempus(remote_pages)

    with Session(db_client._engine) as session:
        case = session.get(Case, 1)
        assert case.blob == '{"same": true}'  # ty:ignore[possibly-missing-attribute]


def test_sync_deletes_local_when_missing_remotely(db_client):
    db_client.insert_case(Case(id=1, logical_timestamp=10, blob="{}"))

    remote_pages = iter([make_page([])])

    db_client.synchronize_with_intempus(remote_pages)

    with Session(db_client._engine) as session:
        assert session.get(Case, 1) is None


def test_sync_mixed_operations(db_client):
    db_client.insert_case(Case(id=1, logical_timestamp=5, blob="{}"))
    db_client.insert_case(Case(id=2, logical_timestamp=10, blob="{}"))

    remote_pages = iter(
        [
            make_page(
                [
                    make_case(1, 20),
                    make_case(3, 1),
                ]
            )
        ]
    )

    db_client.synchronize_with_intempus(remote_pages)

    with Session(db_client._engine) as session:
        ids = {c.id for c in session.exec(select(Case))}
        assert ids == {1, 3}

        case1 = session.get(Case, 1)
        assert case1.logical_timestamp == 20  # ty:ignore[possibly-missing-attribute]


def test_sync_multiple_pages(db_client):
    remote_pages = iter(
        [
            make_page([make_case(1, 1)], offset=0),
            make_page([make_case(2, 1)], offset=1),
        ]
    )

    db_client.synchronize_with_intempus(remote_pages)

    with Session(db_client._engine) as session:
        ids = sorted(c.id for c in session.exec(select(Case)))  # ty:ignore[invalid-argument-type]
        assert ids == [1, 2]


def huge_remote_generator(n):
    for i in range(1, n + 1):
        yield make_page([make_case(i, i)])

@pytest.mark.slow
def test_sync_million_pages_behavior(db_client):
    N = 1_000_000

    remote_pages = huge_remote_generator(N)

    # Preload a small local dataset to force merge logic
    db_client.insert_case(Case(id=500_000, logical_timestamp=1, blob="{}"))

    db_client.synchronize_with_intempus(remote_pages)

    # Verify only final DB state sanity, not full count
    with Session(db_client._engine) as session:
        # Spot-check boundaries
        assert session.get(Case, 1) is not None
        assert session.get(Case, 500_000).logical_timestamp == 500_000  # ty:ignore[possibly-missing-attribute]
        assert session.get(Case, N) is not None
