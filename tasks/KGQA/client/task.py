from enum import Enum
import requests
from typing import List
from ..typings import *
from ..utils import ColorMessage
from .agent import AgentClient


class TaskError(Enum):
    START_FAILED = "start failed"
    INTERACT_FAILED = "interact failed"
    AGENT_FAILED = "agent failed"
    NETWORK_FAILED = "network failed"
    NOT_AVAILABLE = "not available"


class TaskClient:
    def __init__(
        self, name: str, controller_address: str = "http://172.16.55.90:7623/api", *args, **kwargs
    ) -> None:
        self.name = name
        self.controller_address = controller_address
        print("TaskClient created: {} ({})".format(name, controller_address))

    def get_indices(self) -> List[SampleIndex]:
        response = requests.get(
            url=self.controller_address + "/get_indices", params={"name": self.name}
        )
        if response.status_code != 200:
            raise ControllerException(response.text, response.status_code, self.name)
        return response.json()
    
    def get_concurrency(self) -> int:
        try:
            response = requests.get(
                self.controller_address + "/list_workers"
            )
        except Exception as e:
            print(ColorMessage.yellow(f"Warning task {self.name} cannot connect to controller {e}"))
            return 0
        if response.status_code != 200:
            raise ControllerException(response.text, response.status_code, self.name)
        response = response.json()
        if self.name not in response:
            print(ColorMessage.yellow(f"task {self.name} not found in the worker_list."))
            return 0
        concurrency = 0
        for worker in response[self.name]["workers"].values():
            if worker["status"] == WorkerStatus.ALIVE:
                concurrency += worker["capacity"] - worker["current"]
        return concurrency
    
    def run_sample(self, index: SampleIndex, agent: AgentClient) -> TaskClientOutput:
        try:
            response = requests.post(
                self.controller_address + "/start_sample",
                json = StartSampleRequest(name = self.name, index = index).dict(),
            )
            # print("TRYING START SAMPLE...")
        except Exception as e:
            print("TaskError.NETWORK_FAILED...")
            return TaskClientOutput(error=TaskError.NETWORK_FAILED.value, info=str(e))
        if response.status_code == 406:
            print("TaskError.NOT_AVAILABLE...")
            return TaskClientOutput(error=TaskError.NOT_AVAILABLE.value, info=response.text)
        if response.status_code != 200:
            print(response.status_code)
            print("TaskError.START_FAILED...")
            return TaskClientOutput(error=TaskError.START_FAILED.value, info=response.text)
        
        response = response.json()
        sid = response["session_id"]
        latest_response = response
        while SampleStatus(response["output"]["status"]) == SampleStatus.RUNNING:
            try:
                content = agent.inference(response["output"]["history"])
                agent_response = AgentOutput(content=content)
                
            except AgentContextLimitException:
                agent_response = AgentOutput(status=AgentOutputStatus.AGENT_CONTEXT_LIMIT)
            except Exception as e:
                if hasattr(agent, "model_name"):
                    model_name = agent.model_name
                elif hasattr(agent, "name"):
                    model_name = agent.model_name
                else:
                    model_name = agent.__class__.__name__
                print(f"ERROR: {model_name}/{self.name} agent error", e)
                requests.post(
                    self.controller_address + "/cancel",
                    json=CancelRequest(session_id=sid).dict()
                )
                return TaskClientOutput(
                    error = TaskError.AGENT_FAILED.value,
                    info = str(e),
                    output = latest_response,
                )
            try:
                response = requests.post(
                    self.controller_address + "/interact",
                    json=InteractRequest(
                        session_id = sid,
                        agent_response = agent_response,
                    ).dict()
                )
            except Exception as e:
                return TaskClientOutput(
                    error=TaskError.NETWORK_FAILED.value, 
                    info=str(e), 
                    output=latest_response,
                )
            if response.status_code != 200:
                requests.post(
                    self.controller_address + "/cancel",
                    json=CancelRequest(session_id=sid).dict()
                )
                return TaskClientOutput(
                    error=TaskError.INTERACT_FAILED.value,
                    info=response.text,
                    output=latest_response,
                )
            response = response.json()
            latest_response = response
        
        return TaskClientOutput(output=response["output"])

    def calculate_overall(self, results: List[TaskOutput]) -> JSONSerializable:
        statistics = {s: 0 for s in SampleStatus}
        for result in results:
            statistics[SampleStatus(result.status)] += 1
        for s in SampleStatus:
            statistics[s] /= len(results)
        statistics["average_history_length"] = sum(
            [len(result.history) for result in results]
        ) / len(results)
        statistics["max_history_length"] = max(
            [len(result.history) for result in results]
        )
        statistics["min_history_length"] = min(
            [len(result.history) for result in results]
        )
        ret = {
            "total": len(results),
            "validation": statistics,
        }
        res = requests.post(
            self.controller_address + "/calculate_overall",
            json=CalculateOverallRequest(name=self.name, results=results).dict(),
        )
        if res.status_code != 200:
            raise TaskNetworkException(res.text)
        ret["custom"] = res.json()
        return ret
    

    

