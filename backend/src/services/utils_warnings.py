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

WARNING_MAP: dict[str, str] = {
    # biometric / ID
    "face": "Face detected – may reveal identity",
    "license_plate": "License plate detected – may expose vehicle information",
    "document_id": "Document ID detected – may contain sensitive credentials",
    "address_sign": "Address sign detected – may reveal home or workplace",

    # PII via OCR
    "email": "Potential email address detected – may expose private contact",
    "phone": "Potential phone number detected – may expose private contact",
    "credit_card": "Credit card number detected – financial risk",
    "address_text": "Potential address detected – may reveal location",
    "dob": "Date of birth detected – may expose age or identity",
    "national_id": "Potential national ID number detected – sensitive identifier",
    "passport": "Passport number detected – sensitive identity/travel document",
    "iban": "IBAN (bank account) detected – financial identifier",
    "bic": "BIC/SWIFT code detected – financial identifier",

    # scene / object categories
    "person": "Person detected – may reveal presence or activities",
    "rider": "Rider detected – may reveal transport or travel context",
    "car": "Car detected – may reveal vehicle presence",
    "truck": "Truck detected – may reveal vehicle presence",
    "bus": "Bus detected – may reveal vehicle presence",
    "train": "Train detected – may reveal transport usage",
    "motorcycle": "Motorcycle detected – may reveal vehicle presence",
    "bicycle": "Bicycle detected – may reveal vehicle presence",
    "traffic light": "Traffic light detected – contextual scene element",
    "traffic sign": "Traffic sign detected – may reveal location context",
    "building": "Building detected – may reveal workplace or residence",
}

def warning_for_kind(kind: str):
    return WARNING_MAP.get(kind)