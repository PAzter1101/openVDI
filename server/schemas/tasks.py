from pydantic import BaseModel
from schemas._enums import TaskTypeEnum
   

class WorkerTask(BaseModel):
    type: TaskTypeEnum
    data: dict
