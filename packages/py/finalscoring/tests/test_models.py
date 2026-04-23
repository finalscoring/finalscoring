from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from finalscoring.db.base import Base
from finalscoring.db.models import GameModel, PublicationModel, ReviewModel


def test_models():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    game = GameModel(name="Test Game", slug="test-game", year_published=2024)
    session.add(game)
    session.commit()

    publication = PublicationModel(name="Test Publication", slug="test-publication")
    session.add(publication)
    session.commit()

    review = ReviewModel(
        game_id=game.id,
        publication_id=publication.id,
        title="Test Review",
        url="https://example.com/test-review",
        original_score="8/10",
        normalised_score=0.8,
    )
    session.add(review)
    session.commit()

    assert game.id is not None
    assert publication.id is not None
    assert review.id is not None
    assert session.query(GameModel).count() == 1
    assert session.query(PublicationModel).count() == 1
    assert session.query(ReviewModel).count() == 1
    session.close()
