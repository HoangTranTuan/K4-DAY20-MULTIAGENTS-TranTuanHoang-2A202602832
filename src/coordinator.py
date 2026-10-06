"""Coordinator Agent for Multi-Agent Architecture.

Responsibilities:
1. Receive request from user
2. Analyze task (task_type, parameters, priority)
3. Route to worker agents
4. Wait for results with timeout
5. Aggregate and verify results from multiple workers
6. Return response to user
"""

import asyncio
from datetime import datetime
import json
import re
from typing import Any, Dict, List, Optional

try:
    from base_agent import BaseAgent, MessageQueue, CoordinatorException, WorkerError, get_logger
except ImportError:
    from src.base_agent import BaseAgent, MessageQueue, CoordinatorException, WorkerError, get_logger


class Coordinator:
    """Coordinator agent managing worker dispatch, lifecycle, and aggregation."""

    def __init__(
        self,
        model: Any = None,
        worker_agents: Optional[List[BaseAgent]] = None,
        message_queue: Optional[MessageQueue] = None,
        workers: Optional[List[BaseAgent]] = None,
    ) -> None:
        self.model = model
        all_workers = workers if workers is not None else (worker_agents or [])
        self.workers = {agent.name: agent for agent in all_workers}
        self.task_queue = message_queue if message_queue is not None else MessageQueue()
        self.active_tasks: Dict[str, Any] = {}  # Track ongoing tasks
        self.logger = get_logger("coordinator")

    def parse_request(self, user_input: str) -> Dict[str, Any]:
        """Extract task type and parameters from user input."""
        if not user_input or not isinstance(user_input, str):
            raise ValueError("Invalid user input")

        extracted_type = "data_analysis"
        extracted_params: Dict[str, Any] = {"query": user_input}
        extracted_priority = "medium"

        lower_input = user_input.lower()
        if "and" in lower_input and any(k in lower_input for k in ["report", "code", "chart", "biểu đồ", "plot"]):
            extracted_type = "complex"
            extracted_priority = "high"
        elif any(k in lower_input for k in ["analyze", "phân tích", "doanh thu", "sales", "data", "tổng"]):
            extracted_type = "data_analysis"
        elif any(k in lower_input for k in ["code", "script", "generate", "tạo biểu đồ", "lập trình"]):
            extracted_type = "code_generation"
        elif any(k in lower_input for k in ["eval", "đánh giá", "test", "verify"]):
            extracted_type = "evaluation"

        if self.model is not None:
            prompt = f"""Analyze this user request and determine:
1. Task type (data_analysis, code_generation, evaluation, complex)
2. Required parameters (in JSON format)
3. Priority (low, medium, high)

User request: {user_input}

Respond with valid JSON:
{{
  "task_type": "...",
  "parameters": {{...}},
  "priority": "..."
}}"""
            try:
                response = self.model.invoke(prompt)
                content = getattr(response, "content", response)
                if isinstance(content, str):
                    # extract json if embedded in markdown
                    json_match = re.search(r"\{.*\}", content, re.DOTALL)
                    if json_match:
                        parsed = json.loads(json_match.group(0))
                        extracted_type = parsed.get("task_type", extracted_type)
                        extracted_params = parsed.get("parameters", extracted_params)
                        extracted_priority = parsed.get("priority", extracted_priority)
            except Exception as e:
                self.logger.warning(f"Failed to parse with model, using heuristics: {e}")

        return {
            "task_type": extracted_type,
            "parameters": extracted_params,
            "priority": extracted_priority,
        }

    def route_task(self, task_type: str, content: Any = None) -> List[str]:
        """Route task to appropriate worker(s)."""
        routing_map: Dict[str, List[str]] = {
            "data_analysis": ["data_agent"],
            "code_generation": ["code_agent"],
            "evaluation": ["evaluator_agent"],
            "complex": ["data_agent", "code_agent"],  # Multiple workers
        }
        return routing_map.get(task_type, ["data_agent"])

    def execute_tasks(self, tasks: List[Dict[str, Any]], timeout: Any = 60.0, message_queue: Optional[Any] = None) -> Any:
        """Execute tasks on worker agents, wait for results (direct execution or via message queue)."""
        actual_mq = message_queue
        actual_timeout = timeout if isinstance(timeout, (int, float)) else 60.0
        if not isinstance(timeout, (int, float)) and timeout is not None:
            actual_mq = timeout

        if actual_mq is not None:
            async def _execute_via_mq():
                futures = []
                for task in tasks:
                    worker_name = task.get("worker")
                    await actual_mq.send_message(
                        from_agent="coordinator",
                        to_agent=worker_name,
                        message={
                            "type": "task",
                            "task_id": task.get("id"),
                            "content": task.get("content"),
                            "parameters": task.get("parameters", {}),
                        },
                    )

                    async def listen_for_result(w_name):
                        try:
                            result = await actual_mq.receive_message("coordinator", timeout=actual_timeout)
                            return result
                        except TimeoutError:
                            return {"status": "timeout", "worker": w_name}

                    futures.append(listen_for_result(worker_name))
                return await asyncio.gather(*futures)

            return _execute_via_mq()

        results: List[Any] = []
        futures: Dict[str, Any] = {}

        for idx, task in enumerate(tasks):
            worker_name = task.get("worker")
            task_id = str(task.get("id", idx))
            if worker_name not in self.workers:
                raise WorkerError(f"Worker '{worker_name}' not registered in coordinator")
            worker = self.workers[worker_name]
            future = worker.process_async(task.get("content"))
            futures[task_id] = future
            self.active_tasks[task_id] = task

        if not futures:
            return results

        async def _run_all():
            tasks_to_gather = [asyncio.ensure_future(f) for f in futures.values()]
            try:
                return await asyncio.wait_for(asyncio.gather(*tasks_to_gather), timeout=actual_timeout)
            except (asyncio.TimeoutError, TimeoutError):
                for t in tasks_to_gather:
                    if not t.done():
                        t.cancel()
                raise

        try:
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = None

            if loop and loop.is_running():
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                    results = executor.submit(asyncio.run, _run_all()).result()
            else:
                results = asyncio.run(_run_all())
        except (asyncio.TimeoutError, TimeoutError):
            self.logger.error("Task timeout")
            raise TimeoutError("Task timeout")
        except WorkerError:
            raise
        except Exception as e:
            self.logger.error(f"Error during execution: {e}")
            raise WorkerError(str(e))
        finally:
            self.active_tasks.clear()

        return results

    def aggregate_results(self, results: List[Any]) -> Dict[str, Any]:
        """Combine results from multiple workers."""
        aggregated: Dict[str, Any] = {
            "status": "success",
            "data": {},
            "code": None,
            "evaluation": None,
            "timestamp": datetime.now().isoformat(),
        }

        for result in results:
            if isinstance(result, dict):
                res_type = result.get("type")
                content = result.get("content", result)
                if res_type == "data":
                    aggregated["data"] = content
                elif res_type == "code":
                    aggregated["code"] = content
                elif res_type == "evaluation":
                    aggregated["evaluation"] = content
                else:
                    if "data" in result:
                        aggregated["data"] = result["data"]
                    elif "code" in result:
                        aggregated["code"] = result["code"]
                    elif "evaluation" in result:
                        aggregated["evaluation"] = result["evaluation"]
                    else:
                        aggregated[str(res_type or "output")] = content
            elif isinstance(result, str):
                aggregated["data"] = result

        return aggregated

    def execute_tasks_with_retry(self, tasks: List[Dict[str, Any]], max_retries: int = 2, timeout: float = 60.0) -> List[Any]:
        """Execute tasks with retry handling on timeout and worker failures."""
        for attempt in range(max_retries):
            try:
                return self.execute_tasks(tasks, timeout=timeout)
            except (TimeoutError, asyncio.TimeoutError):
                self.logger.warning(f"Retry {attempt + 1}/{max_retries}")
                if attempt == max_retries - 1:
                    raise CoordinatorException("All retries exhausted")
            except WorkerError as e:
                self.logger.error(f"Worker error: {e}")
                if attempt == max_retries - 1:
                    raise CoordinatorException(f"Worker error: {e}")
        return []

    async def handle_request(self, user_input: str, timeout: float = 60.0) -> Dict[str, Any]:
        """Handle request asynchronously from user: parse -> route -> execute -> aggregate."""
        parsed = self.parse_request(user_input)
        task_type = parsed["task_type"]
        routed_workers = self.route_task(task_type, user_input)

        tasks = []
        for idx, worker_name in enumerate(routed_workers):
            tasks.append({
                "id": str(idx),
                "worker": worker_name,
                "content": user_input,
                "parameters": parsed.get("parameters", {}),
            })

        results = self.execute_tasks(tasks, timeout=timeout)
        aggregated = self.aggregate_results(results)
        return aggregated


class CoordinatorPool:
    """Pool of coordinators with round-robin load balancing (Bonus 6a)."""

    def __init__(
        self,
        num_coordinators: int = 3,
        model: Any = None,
        workers: Optional[List[BaseAgent]] = None,
    ) -> None:
        self.coordinators = [
            Coordinator(model=model, workers=workers)
            for _ in range(num_coordinators)
        ]
        self.current_index = 0

    async def handle_request(self, request: str) -> Dict[str, Any]:
        """Round-robin distribute requests across coordinator instances."""
        coordinator = self.coordinators[self.current_index]
        self.current_index = (self.current_index + 1) % len(self.coordinators)
        return await coordinator.handle_request(request)


