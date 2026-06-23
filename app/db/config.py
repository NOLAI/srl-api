from tortoise.contrib.fastapi import register_tortoise
from fastapi import FastAPI
import os

FLORA_ANNOTATION_DATABASE_URI: str = "mysql://{}:{}@{}:{}/{}".format(
    os.getenv('DB_FLORA_ANNOTATION_USER'),
    os.getenv('DB_FLORA_ANNOTATION_PASSWORD'),
    os.getenv('DB_FLORA_ANNOTATION_HOST'),
    os.getenv('DB_FLORA_ANNOTATION_PORT'),
    os.getenv('DB_FLORA_ANNOTATION'),
)

MOODLE_DATABASE_URI: str = "mysql://{}:{}@{}:{}/{}".format(
    os.getenv('DB_MOODLE_USER'),
    os.getenv('DB_MOODLE_PASSWORD'),
    os.getenv('DB_MOODLE_HOST'),
    os.getenv('DB_MOODLE_PORT'),
    os.getenv('DB_MOODLE'),
)

TORTOISE_ORM = {
    "connections": {"flora_annotation": FLORA_ANNOTATION_DATABASE_URI, "moodle": MOODLE_DATABASE_URI},
    "apps": {
        "flora": {
            "models": [
                'app.db.flora_models'
            ],
            "default_connection": "flora_annotation",
        },
        "moodle": {
            "models": [
                'app.db.moodle_models'
            ],
            "default_connection": "moodle",
        },
    },
}
def register_db(app: FastAPI) -> None:
    register_tortoise(
        app,
        config=TORTOISE_ORM,
        generate_schemas=False,
        add_exception_handlers=True,
    )
