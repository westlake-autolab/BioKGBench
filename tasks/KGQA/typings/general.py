import builtins
from typing import List, Dict, Any, Union, Literal
from pydantic import BaseModel, validator

# 定义类型别名
JSONSerializable = Union[None, bool, int, float, str, List[Any], Dict[str, Any]]
SampleIndex = Union[int, str]

# 生成agent，task的实例
class InstanceFactory(BaseModel):
    module: str
    parameters: Dict[str, Any] = {}

    @validator("parameters", pre = True)
    def _ensure_dict(cls, value):
        if value is None:
            return {}
        else:
            return value
        
    def create(self):
        splits = self.module.split(".")
        if len(splits) == 0:
            raise Exception("Invalid module name: {}".format(self.module))
        if len(splits) == 1:
            g = globals()
            if self.module in g:
                class_type = g[self.module]
            else:
                class_type = getattr(builtins, self.module)
            return class_type(**self.parameters)
        else:
            path = ".".join(self.module.split(".")[:-1])
            mod = __import__(path, fromlist=[self.module.split(".")[-1]])
            class_type = getattr(mod, self.module.split(".")[-1])
            return class_type(**self.parameters)
        

class Assignment(BaseModel):
    agent: str
    task: str


class ChatHistoryItem(BaseModel):
    role: Literal["user", "agent"]
    content: str