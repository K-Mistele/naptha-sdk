from naptha_sdk.client.node import Node
from naptha_sdk.schemas import AgentRunInput
from naptha_sdk.utils import get_logger, node_to_url

logger = get_logger(__name__)

class Agent:
    def __init__(self, 
        module_run, 
        agent_index,
        *args,
        **kwargs
    ):
        self.module_run = module_run
        self.agent_index = agent_index
        self.worker_node = Node(self.module_run.deployment.agent_deployments[self.agent_index].node)

    async def call_agent_func(self, *args, **kwargs):
        logger.info(f"Running agent on worker node {self.worker_node.node_url}")

        agent_run_input = AgentRunInput(
            consumer_id=self.module_run.consumer_id,
            inputs=kwargs,
            deployment=self.module_run.deployment.agent_deployments[self.agent_index].model_dump(),
        )
        
        agent_run = await self.worker_node.run_agent_in_node(agent_run_input)
        return agent_run