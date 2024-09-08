# Copyright Lightning AI. Licensed under the Apache License 2.0, see LICENSE file.

import logging
import re
from mini_omni.litgpt.model import GPT  # needs to be imported before config
from mini_omni.litgpt.config import Config
from mini_omni.litgpt.tokenizer import Tokenizer

# Suppress excessive warnings, see https://github.com/pytorch/pytorch/issues/111632
pattern = re.compile(".*Profiler function .* will be ignored")
logging.getLogger("torch._dynamo.variables.torch").addFilter(
    lambda record: not pattern.search(record.getMessage())
)

# Avoid printing state-dict profiling output at the WARNING level when saving a checkpoint
logging.getLogger("torch.distributed.fsdp._optim_utils").disabled = True
logging.getLogger("torch.distributed.fsdp._debug_utils").disabled = True

__all__ = ["GPT", "Config", "Tokenizer"]
