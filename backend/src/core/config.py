    # Copyright 2025 Obscura
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from pydantic import BaseModel
import yaml
from pathlib import Path

class Settings(BaseModel):
    policy_mode: str = "strict"
    risk_threshold: int = 60
    max_image_mp: int = 12
    timeouts_ms: dict = {}
    conf_thresholds: dict = {}
    weights: dict = {}

def _load_yaml() -> dict:
    path = Path(__file__).parents[2] / "config" / "default.yaml"
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)

settings = Settings(**_load_yaml())
