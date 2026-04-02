from __future__ import annotations


class ModuleRunner:
    """大模块执行桥接样板。

    pytest 后续不直接处理底层动作细节，而是把完整用例中的 module_chain
    交给这个桥接层，再由桥接层调用真正的大模块实现。
    """

    def __init__(self, registry: dict):
        self.registry = registry

    def run_chain(self, actions, element_store, module_chain: list[dict]) -> list[dict]:
        results = []
        for entry in module_chain:
            module = self.registry[entry["module"]]
            elements = element_store.load(entry["module"])
            results.append(module.execute(actions, elements, entry["params"]))
        return results
