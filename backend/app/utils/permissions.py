from sqlalchemy import Select, false, or_, select

from app.model.tasks import Task, TaskStatus
from app.model.users import Role, User

EMPLOYEE_MOVES = {
    TaskStatus.TODO: [TaskStatus.IN_PROGRESS],
    TaskStatus.IN_PROGRESS: [TaskStatus.TODO, TaskStatus.REVIEW],
}
REVIEWER_MOVES = {
    TaskStatus.REVIEW: [TaskStatus.DONE, TaskStatus.IN_PROGRESS],
}


def visible_tasks(user: User) -> Select[tuple[Task]]:
    query = select(Task)
    if user.role is Role.ADMIN:
        return query
    if user.role is Role.MANAGER:
        team = select(User.id).where(User.manager_id == user.id)
        return query.where(or_(Task.assignee_id == user.id, Task.creator_id == user.id, Task.assignee_id.in_(team)))
    return query.where(Task.assignee_id == user.id)


def assignable_users(user: User) -> Select[tuple[User]]:
    query = select(User).where(User.active)
    if user.role is Role.ADMIN:
        return query.where(User.role != Role.ADMIN)
    if user.role is Role.MANAGER:
        return query.where(User.manager_id == user.id)
    return query.where(false())


def can_manage(user: User, task: Task) -> bool:
    return task.assignee_id != user.id and user.role in (Role.ADMIN, Role.MANAGER)


def allowed_moves(user: User, task: Task) -> list[TaskStatus]:
    if task.assignee_id == user.id:
        return EMPLOYEE_MOVES.get(task.status, [])
    if can_manage(user, task):
        return REVIEWER_MOVES.get(task.status, [])
    return []
