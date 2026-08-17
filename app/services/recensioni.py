from models.recensioni import Review
from extensions import db
from models.recensioni import Employee
from sqlalchemy.orm import joinedload
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select

class ReviewService:
    @staticmethod
    def get_all_employees() -> list:
        return db.session.query(Employee).all()

    @staticmethod
    def get_employee(employee_id: int) -> Employee | None:
        return db.session.get(Employee, employee_id)

    @staticmethod
    def does_review_exist(email: str) -> bool:
        return db.session.query(Review).filter_by(customer_email=email, hidden=False).first() is not None

    @staticmethod
    def create(customer_name: str, customer_email: str, language: str, sender_id: int) -> Review:
        try:
            review = Review(
                customer_name=customer_name,
                customer_email=customer_email,
                language=language,
                sender_id=sender_id
            )
            db.session.add(review)
            db.session.commit()
            return review
        except IntegrityError as e:
            db.session.rollback()
            raise ValueError("Errore di integrità: dipendente inesistente o vincolo violato") from e

    @staticmethod
    def get_reviews(hidden: bool | None = None) -> list[Review]:
        stmt = (
            select(Review)
            .options(joinedload(Review.sender))
            .order_by(Review.creation_date.desc())
        )

        if hidden is not None:
            stmt = stmt.where(Review.hidden == hidden)

        return db.session.scalars(stmt).all()

    @staticmethod
    def hide(review_id: int) -> bool:
        review = db.session.get(Review, review_id)
        
        if not review:
            return False

        if not review.hidden:
            review.hidden = True
            db.session.commit()
            
        return True