import asyncio
import logging
from typing import Dict, Any, List

from stac_manager.config import WorkflowDefinition
from stac_manager.context import WorkflowContext
from stac_manager.failures import FailureCollector
from stac_manager.registry import get_module_class
from stac_manager.graph import build_execution_levels
from stac_manager.exceptions import ModuleException

class StacManager:
    def __init__(self, config: WorkflowDefinition):
        self.config = config
        self.context = WorkflowContext(
            workflow_id=config.name,
            config=config,
            logger=logging.getLogger("stac_manager"),
            failure_collector=FailureCollector(),
            checkpoints=None,
            data={}
        )
        self.instances = {}
        
    def _instantiate_modules(self):
        for step in self.config.steps:
            cls = get_module_class(step.module)
            self.instances[step.id] = cls(step.config)
            
    async def _execute_step(self, step_id: str):
        instance = self.instances[step_id]
        
        # Determine Input
        step_def = next(s for s in self.config.steps if s.id == step_id)
        input_data = None
        if step_def.depends_on:
            # Assumption: Single linear dependency for stream, or merged? 
            # Spec says "stream_tee" for branching, but here let's assume simple linear for now.
            parent_id = step_def.depends_on[0]
            input_data = self.context.data.get(parent_id)
        
        # Execute based on role
        if hasattr(instance, 'fetch'):
            # Fetchers typically start the stream or take context input
            result = instance.fetch(self.context)
        elif hasattr(instance, 'modify'):
            # Manual pipe since modifiers are sync
            # Assumes input_data is an AsyncIterator or iterable
            async def pipe(source):
                if not source:
                    return # Or empty stream
                async for item in source:
                    res = instance.modify(item, self.context)
                    if res:
                        yield res
            result = pipe(input_data)
        elif hasattr(instance, 'bundle'):
            # Bundlers consume the stream
            if input_data:
                async for item in input_data:
                    instance.bundle(item, self.context)
            result = instance.finalize(self.context)
        else:
            raise ModuleException(f"Module {step_id} has no valid role method (fetch, modify, bundle)")
            
        self.context.data[step_id] = result

    async def execute(self):
        self._instantiate_modules()
        levels = build_execution_levels(self.config.steps)
        
        for level in levels:
            self.context.logger.info(f"Executing Level: {level}")
            tasks = [self._execute_step(step_id) for step_id in level]
            await asyncio.gather(*tasks)
            
        return {
            "success": True,
            "failure_count": self.context.failure_collector.count()
        }
