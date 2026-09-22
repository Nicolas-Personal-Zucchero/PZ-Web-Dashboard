from typing import Optional
from sqlalchemy.exc import IntegrityError
from extensions import db
from models.themes import Theme


class ThemeService:

    @staticmethod
    def get_theme_by_id(theme_id: int) -> Theme | None:
        return db.session.get(Theme, theme_id)

    @staticmethod
    def get_all_themes(include_hidden: bool = False) -> list[Theme]:
        stmt = db.select(Theme)
        if not include_hidden:
            stmt = stmt.where(Theme.hidden == False)
        return list(db.session.execute(stmt).scalars().all())

    @staticmethod
    def create_theme(name: str) -> Optional[Theme]:
        try:
            theme = Theme(name=name)
            db.session.add(theme)
            db.session.commit()
            return theme
        except IntegrityError:
            db.session.rollback()
            return None

    @staticmethod
    def update_theme(
        theme_id: int, name: str | None = None, hidden: bool | None = None
    ) -> bool:
        theme = db.session.get(Theme, theme_id)
        if not theme:
            return False

        if name is not None:
            theme.name = name
        if hidden is not None:
            theme.hidden = hidden

        try:
            db.session.commit()
            return True
        except IntegrityError:
            db.session.rollback()
            return False

    @staticmethod
    def delete_theme(theme_id: int) -> bool:
        theme = db.session.get(Theme, theme_id)
        if not theme:
            return False

        try:
            db.session.delete(theme)
            db.session.commit()
            return True
        except IntegrityError:
            db.session.rollback()
            return False
