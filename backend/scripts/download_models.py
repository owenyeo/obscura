    #!/usr/bin/env python3
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

from pathlib import Path

def main():
    models = Path(__file__).parents[1] / "models"
    models.mkdir(parents=True, exist_ok=True)
    print(f"Models dir prepared at {models.resolve()}")

if __name__ == "__main__":
    main()
