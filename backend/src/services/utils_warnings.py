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

WARNING_MAP = {
    "email": "Potential email address detected – may expose private contact",
    "phone": "Potential phone number detected – may expose private contact",
    "national_id": "Potential national ID number detected – sensitive identifier",
    "address_text": "Potential address detected – may reveal location",
    "face": "Face detected – may reveal identity",
    "license_plate": "License plate detected – may expose vehicle information",
    "document_id": "Document ID detected – may contain sensitive credentials",
    "address_sign": "Address sign detected – may reveal home or workplace",
    "credit_card": "Credit card number detected – financial risk",
}

def warning_for_kind(kind: str):
    return WARNING_MAP.get(kind)