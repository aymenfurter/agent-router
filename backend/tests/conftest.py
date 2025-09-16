import sys
import types
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _ensure_module(name: str) -> types.ModuleType:
    if name in sys.modules:
        return sys.modules[name]
    module = types.ModuleType(name)
    sys.modules[name] = module
    return module


def _ensure_azure_stubs():
    _ensure_module("azure")
    _ensure_module("azure.ai")
    _ensure_module("azure.ai.projects")

    models_module = _ensure_module("azure.ai.agents.models")
    identity_module = _ensure_module("azure.identity")

    class _BaseTool:
        def __init__(self, **kwargs):
            self.kwargs = kwargs
            self.definitions = [SimpleNamespace(**kwargs)]
            self.resources = {"values": kwargs}

    class _FileSearchTool(_BaseTool):
        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            self.resources = {"vector_store_ids": kwargs.get("vector_store_ids", [])}

    stubs = {
        "ConnectedAgentTool": _BaseTool,
        "FunctionTool": _BaseTool,
        "FabricTool": _BaseTool,
        "BingGroundingTool": _BaseTool,
        "FileSearchTool": _FileSearchTool,
        "FilePurpose": SimpleNamespace(AGENTS="agents"),
    }

    for name, value in stubs.items():
        if not hasattr(models_module, name):
            setattr(models_module, name, value)

    class _DefaultAzureCredential:
        def __call__(self, *args, **kwargs):
            return self

        def get_token(self, *_, **__):
            return SimpleNamespace(token="token")

    class _AzureCliCredential(_DefaultAzureCredential):
        pass

    if not hasattr(identity_module, "DefaultAzureCredential"):
        identity_module.DefaultAzureCredential = _DefaultAzureCredential
    if not hasattr(identity_module, "AzureCliCredential"):
        identity_module.AzureCliCredential = _AzureCliCredential

    projects_module = sys.modules.setdefault("azure.ai.projects", types.ModuleType("azure.ai.projects"))
    if not hasattr(projects_module, "AIProjectClient"):
        class _AIProjectClient:
            def __init__(self, *args, **kwargs):
                pass
        projects_module.AIProjectClient = _AIProjectClient


_ensure_azure_stubs()
