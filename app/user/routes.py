from fastapi import APIRouter, Response
from tortoise import connections
from tortoise.exceptions import DoesNotExist

from app.db.moodle_models import MdlUser

router = APIRouter(prefix="/api/user", tags=["user"])

@router.get(
    "/{username}",
    status_code=200,
)
async def get_user(username: str, response: Response):
    db_moodle = connections.get('moodle')

    try:
        user = await MdlUser.get(username=username, using_db=db_moodle)
    except DoesNotExist:
        response.status_code = 404
        return {
            'message': 'User does not exist'
        }
    except Exception:
        response.status_code = 500
        return {
            'message': 'Internal server error'
        }
    
    return {
        'id': user.id,
        'username': user.username
    }
