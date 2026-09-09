from extensions import db
from models.employees import Employee

class EmployeeService:
    @staticmethod
    def get_employees(departments: list[str] = []) -> list:
        query = db.session.query(Employee)
        if departments:
            query = query.filter(Employee.department.in_(departments))
        return query.all()

    @staticmethod
    def get_employee(employee_id: int) -> Employee | None:
        return db.session.get(Employee, employee_id)