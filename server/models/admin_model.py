from typing import Dict

import fire_watch
from fire_watch.errorfactory import InvalidCredentialsError
from fire_watch.log.log_configs import get_logger
from fire_watch.utils import pagination_utils

from .base_model import BaseModel


class AdminModel(BaseModel):
    logger = get_logger(__name__, filename="./alerts.log")

    def log_user_request(self, doc: Dict[str, str]):
        existing_user = self.db.Admin.find_one({"email": doc["email"]})
        #! Change to sns or ses
        if existing_user:
            self.logger.warning(f"User Update Request!")
        else:
            self.logger.warning(f"User insertion!")
        # Maintain a record of all units with users!
        self.db.Admin.insert_one(doc)

    def get_unit_details(self, page: int):
        project_pipeline = {
            "$project": {
                "_id": 0,
            }
        }
        skip, limit = pagination_utils(
            page=page,
            page_limit=fire_watch.conf.pagination_limit,
        )
        data = self.db.Admin.aggregate(
            pipeline=[
                {"$limit": limit},
                {"$skip": skip},
                project_pipeline,
            ]
        )
        return list(data)

    def login(self, password, email):
        admin = self.db.Admin.find_one({"email": email, "password": password})
        if admin:
            return admin
        raise InvalidCredentialsError({"error": "Invalid credentials!"})
