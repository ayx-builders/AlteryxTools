import sys
import os
from abc import abstractmethod, ABCMeta
from typing import Dict, List
import typing

sys.path.append(os.path.dirname(os.path.realpath(__file__)))

import AlteryxPythonSDK as Sdk
import xml.etree.ElementTree as Et

class Hello:
    def __init__(self, n_tool_id: int, alteryx_engine: object, output_anchor_mgr: object):
        self.toolId: int = n_tool_id
        self.engine: Sdk.AlteryxEngine = alteryx_engine
        self.outputs: Dict[str, Sdk.OutputAnchor] = {}

        manager: Sdk.OutputAnchorManager = output_anchor_mgr
        for conn in self.ListOutputConnections():
            self.outputs[conn] = manager.get_output_anchor(conn)

    def pi_add_outgoing_connection(self, str_name: str) -> bool:
        return True

    def pi_close(self, b_has_errors: bool):
        for output in self.outputs.values():
            output.assert_close()

    def display_error_msg(self, msg_string: str):
        self.alteryx_engine.output_message(self.n_tool_id, Sdk.EngineMessageType.error, msg_string)

    @abstractmethod
    def ListOutputConnections(self) -> List[str]:
        pass


class World(Hello):
    def ListOutputConnections(self):
        return [
            "Output",
            "Reviews"
        ]
