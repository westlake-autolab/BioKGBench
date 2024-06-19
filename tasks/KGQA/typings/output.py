from pydantic import BaseModel, root_validator
from typing import Optional, List
from .general import SampleIndex, JSONSerializable, ChatHistoryItem
from .status import SampleStatus, AgentOutputStatus

class TaskOutput(BaseModel):
    index: Optional[SampleIndex] = None
    status: SampleStatus = SampleStatus.RUNNING
    result: JSONSerializable = None
    history: Optional[List[ChatHistoryItem]] = None

class TaskClientOutput(BaseModel):
    info: Optional[str] = None
    error: Optional[str] = None
    output: Optional[TaskOutput] = None

class AgentOutput(BaseModel):
    status: AgentOutputStatus = AgentOutputStatus.NORMAL
    content: Optional[str] = None

    # at least one of them should be not None
    @root_validator(pre=False, skip_on_failure=True)
    def post_vadidation(cls, instance: dict):
        assert(
            instance.get("status") is not AgentOutputStatus.NORMAL
            or instance.get("content") is not None
        ), "If status is NORMAL, content should not be None"
        return instance
    
class TaskSampleExecutionResult(BaseModel):
    status: SampleStatus = SampleStatus.COMPLETED
    result: JSONSerializable = None


