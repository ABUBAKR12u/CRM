from app.scheme.base import Schema


class StatsResponse(Schema):
    users: int
    team_tasks: int
    pending: int
    late: int
    my_tasks: int
    done_week: int
