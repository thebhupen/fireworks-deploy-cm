"""SehatCare: doctor consultations, lab tests and medical records, modelled on Practo / Apollo.

Schema: app_schemas.md section 6. Report and prescription files live in the
Files app; records here point to them by path.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from are.simulation.tool_utils import OperationType, app_tool, env_tool
from are.simulation.types import EventType, event_registered
from are.simulation.utils import type_check

from .common import (
    Address,
    BharatApp,
    dump_records,
    load_records,
    matches,
    parse_date,
    to_dict,
)

FASTING_WINDOW = ("06:00", "10:00")
FULL_REFUND_HOURS = 2
MAX_FREE_RESCHEDULES = 1
CONSULT_MODES = ("in_clinic", "video")
LAB_MODES = ("home_collection", "lab_visit")
RECORD_KINDS = ("lab_report", "prescription", "consult_note")


@dataclass
class Provider:
    provider_id: str
    name: str
    area: str
    type: str
    address: str
    home_collection: bool = False


@dataclass
class Doctor:
    doctor_id: str
    name: str
    speciality: str
    qualifications: str
    experience_years: int
    provider_id: str
    languages: list[str]
    consult_fee: int
    modes: list[str]


@dataclass
class LabTest:
    test_id: str
    name: str
    provider_id: str
    price: int
    fasting_required: bool
    sample_type: str
    report_hours: int
    includes: list[str] = field(default_factory=list)
    description: str = ""


@dataclass
class Slot:
    slot_id: str
    owner_id: str
    date: str
    start_time: str
    end_time: str
    mode: str
    available: bool = True


@dataclass
class Patient:
    patient_id: str
    name: str
    age: int
    gender: str
    relation: str


@dataclass
class Appointment:
    appointment_id: str
    kind: str
    patient_id: str
    slot_id: str
    mode: str
    amount: int
    txn_id: str
    booked_at: str
    status: str = "booked"
    doctor_id: str | None = None
    test_ids: list[str] = field(default_factory=list)
    address_id: str | None = None
    reschedule_count: int = 0
    refunded_amount: int = 0


@dataclass
class MedicalRecord:
    record_id: str
    patient_id: str
    kind: str
    date: str
    summary: str
    appointment_id: str | None = None
    file_path: str | None = None
    results: list[dict[str, Any]] = field(default_factory=list)


class SehatCareApp(BharatApp):
    """
    SehatCare books doctor consultations (in clinic or by video) and lab tests (home sample collection or lab
    visit) for the user's family, and keeps their medical records and lab results.

    Notes:
        - Book for a patient from list_patients; slots come from get_available_slots.
        - All tests in one lab booking must be from the same lab, and the slot must belong to that lab.
        - If any test needs fasting, the slot must start between 06:00 and 10:00.
        - Home collection needs a lab that offers it, a home_collection slot and a saved address_id;
          a lab_visit slot takes no address.
        - Cancelling 2 hours or more before the slot refunds in full; later cancellations get no refund.
        - Each appointment can be rescheduled once for free; after that, cancel and book again.
        - Lab results in medical records carry a flag (normal, low, high) against the reference range.
        - Dates use YYYY-MM-DD, times are local (IST) HH:MM. Amounts are whole rupees.
    """

    def __init__(self, name: str | None = "SehatCare") -> None:
        super().__init__(name)
        self.providers: dict[str, Provider] = {}
        self.doctors: dict[str, Doctor] = {}
        self.lab_tests: dict[str, LabTest] = {}
        self.slots: dict[str, Slot] = {}
        self.patients: dict[str, Patient] = {}
        self.addresses: dict[str, Address] = {}
        self.appointments: dict[str, Appointment] = {}
        self.medical_records: dict[str, MedicalRecord] = {}

    # State -----------------------------------------------------------------
    def get_state(self) -> dict[str, Any]:
        return {
            **self.base_state(),
            "providers": dump_records(self.providers),
            "doctors": dump_records(self.doctors),
            "lab_tests": dump_records(self.lab_tests),
            "slots": dump_records(self.slots),
            "patients": dump_records(self.patients),
            "addresses": dump_records(self.addresses),
            "appointments": dump_records(self.appointments),
            "medical_records": dump_records(self.medical_records),
        }

    def load_state(self, state_dict: dict[str, Any]) -> None:
        self.load_base_state(state_dict)
        self.providers = load_records(Provider, state_dict.get("providers", {}))
        self.doctors = load_records(Doctor, state_dict.get("doctors", {}))
        self.lab_tests = load_records(LabTest, state_dict.get("lab_tests", {}))
        self.slots = load_records(Slot, state_dict.get("slots", {}))
        self.patients = load_records(Patient, state_dict.get("patients", {}))
        self.addresses = load_records(Address, state_dict.get("addresses", {}))
        self.appointments = load_records(Appointment, state_dict.get("appointments", {}))
        self.medical_records = load_records(MedicalRecord, state_dict.get("medical_records", {}))

    # Helpers -----------------------------------------------------------------
    @staticmethod
    def _get(records: dict[str, Any], key: str, label: str) -> Any:
        if key not in records:
            raise ValueError(f"{label} {key} does not exist")
        return records[key]

    @staticmethod
    def _slot_start(slot: Slot) -> datetime:
        day = parse_date(slot.date)
        hours, minutes = (int(part) for part in slot.start_time.split(":"))
        return datetime(day.year, day.month, day.day, hours, minutes, tzinfo=timezone.utc)

    def _open_slot(self, slot_id: str) -> Slot:
        slot = self._get(self.slots, slot_id, "Slot")
        if not slot.available:
            raise ValueError(f"Slot {slot_id} is already taken")
        if self._slot_start(slot) <= self.now():
            raise ValueError(f"Slot {slot_id} is in the past")
        return slot

    def _expanded_tests(self, test_ids: list[str]) -> list[LabTest]:
        tests = [self._get(self.lab_tests, test_id, "Lab test") for test_id in test_ids]
        included = [self._get(self.lab_tests, inner, "Lab test") for test in tests for inner in test.includes]
        return tests + included

    @staticmethod
    def _check_fasting(tests: list[LabTest], slot: Slot) -> None:
        if any(test.fasting_required for test in tests) and not (
            FASTING_WINDOW[0] <= slot.start_time < FASTING_WINDOW[1]
        ):
            raise ValueError(
                f"These tests need fasting; choose a slot starting between {FASTING_WINDOW[0]} and {FASTING_WINDOW[1]}"
            )

    def _appointment(self, appointment_id: str) -> Appointment:
        return self._get(self.appointments, appointment_id, "Appointment")

    def _active(self, appointment_id: str) -> Appointment:
        appointment = self._appointment(appointment_id)
        if appointment.status != "booked":
            raise ValueError(f"Appointment {appointment_id} is {appointment.status}")
        return appointment

    def _book(self, **fields: Any) -> Appointment:
        appointment_id = self.next_id("SC-APT")
        txn_id = self.charge(
            fields["amount"], fields.pop("payment"), "health", appointment_id, merchant=fields.pop("merchant")
        )
        appointment = Appointment(appointment_id=appointment_id, txn_id=txn_id, booked_at=self.now_str(), **fields)
        self.slots[appointment.slot_id].available = False
        self.appointments[appointment_id] = appointment
        return appointment

    # Read tools --------------------------------------------------------------
    @type_check
    @app_tool()
    @event_registered(operation_type=OperationType.READ)
    def search_doctors(
        self,
        speciality: str | None = None,
        query: str | None = None,
        area: str | None = None,
        mode: str | None = None,
        language: str | None = None,
    ) -> list[dict[str, Any]]:
        """
        Search doctors.
        :param speciality: e.g. "General Physician", "Paediatrician", "Endocrinologist"
        :param query: text matched against the doctor's name and clinic name
        :param area: locality of the clinic, e.g. "HSR Layout"
        :param mode: "in_clinic" or "video"
        :param language: a language the doctor speaks, e.g. "Assamese"
        :returns: doctors with fee, clinic and consultation modes
        """
        found = []
        for doctor in self.doctors.values():
            provider = self.providers.get(doctor.provider_id)
            if speciality and not matches(speciality, doctor.speciality):
                continue
            if not matches(query, doctor.name, provider.name if provider else ""):
                continue
            if area and not (provider and matches(area, provider.area)):
                continue
            if mode and mode not in doctor.modes:
                continue
            if language and not any(matches(language, spoken) for spoken in doctor.languages):
                continue
            found.append(
                {
                    **to_dict(doctor),
                    "clinic": provider.name if provider else None,
                    "area": provider.area if provider else None,
                }
            )
        return sorted(found, key=lambda d: d["doctor_id"])

    @type_check
    @app_tool()
    @event_registered(operation_type=OperationType.READ)
    def get_doctor(self, doctor_id: str) -> dict[str, Any]:
        """
        Get a doctor's profile and clinic.
        :param doctor_id: the doctor ID
        :returns: the doctor with clinic details
        """
        doctor = self._get(self.doctors, doctor_id, "Doctor")
        return {
            **to_dict(doctor),
            "clinic": to_dict(self.providers[doctor.provider_id]) if doctor.provider_id in self.providers else None,
        }

    @type_check
    @app_tool()
    @event_registered(operation_type=OperationType.READ)
    def search_lab_tests(self, query: str, home_collection_only: bool = False) -> list[dict[str, Any]]:
        """
        Search lab tests and health packages.
        :param query: test name or keyword, e.g. "HbA1c", "vitamin", "full body"
        :param home_collection_only: only tests from labs that collect samples at home
        :returns: tests with lab, price, fasting need and report time
        """
        found = []
        for test in self.lab_tests.values():
            lab = self.providers.get(test.provider_id)
            if not matches(query, test.name, test.description):
                continue
            if home_collection_only and not (lab and lab.home_collection):
                continue
            found.append(
                {
                    **to_dict(test),
                    "lab": lab.name if lab else None,
                    "home_collection": bool(lab and lab.home_collection),
                }
            )
        return sorted(found, key=lambda t: (t["price"], t["test_id"]))

    @type_check
    @app_tool()
    @event_registered(operation_type=OperationType.READ)
    def get_lab_test(self, test_id: str) -> dict[str, Any]:
        """
        Get one lab test or package, including the tests a package contains.
        :param test_id: the test ID
        :returns: the test
        """
        test = self._get(self.lab_tests, test_id, "Lab test")
        return {
            **to_dict(test),
            "included_tests": [to_dict(self.lab_tests[t]) for t in test.includes if t in self.lab_tests],
        }

    @type_check
    @app_tool()
    @event_registered(operation_type=OperationType.READ)
    def get_available_slots(self, owner_id: str, date: str, mode: str | None = None) -> list[dict[str, Any]]:
        """
        List free slots of a doctor or lab on one date.
        :param owner_id: a doctor_id or a lab's provider_id
        :param date: format YYYY-MM-DD
        :param mode: "in_clinic", "video", "home_collection" or "lab_visit"
        :returns: free future slots sorted by start time
        """
        parse_date(date)
        free = [
            slot
            for slot in self.slots.values()
            if slot.owner_id == owner_id
            and slot.date == date
            and slot.available
            and (mode is None or slot.mode == mode)
            and self._slot_start(slot) > self.now()
        ]
        return [to_dict(slot) for slot in sorted(free, key=lambda s: (s.start_time, s.slot_id))]

    @app_tool()
    @event_registered(operation_type=OperationType.READ)
    def list_patients(self) -> list[dict[str, Any]]:
        """
        List family members saved as patients.
        :returns: patients with name, age, gender and relation
        """
        return [to_dict(patient) for patient in self.patients.values()]

    @type_check
    @app_tool()
    @event_registered(operation_type=OperationType.READ)
    def list_appointments(self, status: str | None = None, patient_id: str | None = None) -> list[dict[str, Any]]:
        """
        List appointments, latest slot first.
        :param status: "booked", "completed" or "cancelled"
        :param patient_id: only this patient's appointments
        :returns: appointments with their slot date and time
        """
        selected = [
            a
            for a in self.appointments.values()
            if (status is None or a.status == status) and (patient_id is None or a.patient_id == patient_id)
        ]
        selected.sort(key=lambda a: self._slot_start(self.slots[a.slot_id]), reverse=True)
        return [{**to_dict(a), "slot": to_dict(self.slots[a.slot_id])} for a in selected]

    @type_check
    @app_tool()
    @event_registered(operation_type=OperationType.READ)
    def get_appointment(self, appointment_id: str) -> dict[str, Any]:
        """
        Get one appointment with its slot.
        :param appointment_id: the appointment ID
        :returns: the appointment
        """
        appointment = self._appointment(appointment_id)
        return {**to_dict(appointment), "slot": to_dict(self.slots[appointment.slot_id])}

    @type_check
    @app_tool()
    @event_registered(operation_type=OperationType.READ)
    def list_medical_records(self, patient_id: str | None = None, kind: str | None = None) -> list[dict[str, Any]]:
        """
        List medical records, newest first.
        :param patient_id: only this patient's records
        :param kind: "lab_report", "prescription" or "consult_note"
        :returns: record summaries (use get_medical_record for test values)
        """
        selected = [
            r
            for r in self.medical_records.values()
            if (patient_id is None or r.patient_id == patient_id) and (kind is None or r.kind == kind)
        ]
        selected.sort(key=lambda r: (r.date, r.record_id), reverse=True)
        return [{key: value for key, value in to_dict(r).items() if key != "results"} for r in selected]

    @type_check
    @app_tool()
    @event_registered(operation_type=OperationType.READ)
    def get_medical_record(self, record_id: str) -> dict[str, Any]:
        """
        Get a medical record including every lab result with value, unit, reference range and flag.
        :param record_id: the record ID
        :returns: the record
        """
        return to_dict(self._get(self.medical_records, record_id, "Medical record"))

    @app_tool()
    @event_registered(operation_type=OperationType.READ)
    def list_addresses(self) -> list[dict[str, Any]]:
        """
        List saved addresses for home sample collection.
        :returns: addresses
        """
        return [to_dict(address) for address in self.addresses.values()]

    # Write tools -----------------------------------------------------------------
    @type_check
    @app_tool()
    @event_registered(operation_type=OperationType.WRITE)
    def book_consultation(self, doctor_id: str, slot_id: str, patient_id: str, payment: str) -> dict[str, Any]:
        """
        Book a doctor consultation and pay the consultation fee through PaySetu.
        :param doctor_id: the doctor ID
        :param slot_id: a free slot of this doctor (its mode decides in-clinic or video)
        :param patient_id: the patient ID
        :param payment: PaySetu source_id to pay with
        :returns: the new appointment
        """
        doctor = self._get(self.doctors, doctor_id, "Doctor")
        self._get(self.patients, patient_id, "Patient")
        slot = self._open_slot(slot_id)
        if slot.owner_id != doctor_id:
            raise ValueError(f"Slot {slot_id} does not belong to {doctor.name}")
        if slot.mode not in doctor.modes:
            raise ValueError(f"{doctor.name} does not offer {slot.mode} consultations")
        clinic = self.providers.get(doctor.provider_id)
        appointment = self._book(
            kind="consultation",
            patient_id=patient_id,
            slot_id=slot_id,
            mode=slot.mode,
            amount=doctor.consult_fee,
            doctor_id=doctor_id,
            payment=payment,
            merchant=clinic.name if clinic else doctor.name,
        )
        return {**to_dict(appointment), "slot": to_dict(slot)}

    @type_check
    @app_tool()
    @event_registered(operation_type=OperationType.WRITE)
    def book_lab_test(
        self,
        test_ids: list[str],
        slot_id: str,
        patient_id: str,
        payment: str,
        address_id: str | None = None,
    ) -> dict[str, Any]:
        """
        Book lab tests from one lab and pay through PaySetu.
        :param test_ids: IDs of tests or packages, all from the same lab
        :param slot_id: a free slot of that lab; a home_collection slot needs address_id, a lab_visit slot takes none
        :param patient_id: the patient ID
        :param payment: PaySetu source_id to pay with
        :param address_id: saved address for home sample collection
        :returns: the new appointment
        """
        if not test_ids or len(set(test_ids)) != len(test_ids):
            raise ValueError("List each test once, and at least one test")
        self._get(self.patients, patient_id, "Patient")
        tests = [self._get(self.lab_tests, test_id, "Lab test") for test_id in test_ids]
        labs = {test.provider_id for test in tests}
        if len(labs) != 1:
            raise ValueError("All tests in one booking must be from the same lab")
        lab = self._get(self.providers, labs.pop(), "Lab")
        slot = self._open_slot(slot_id)
        if slot.owner_id != lab.provider_id or slot.mode not in LAB_MODES:
            raise ValueError(f"Slot {slot_id} is not a sample-collection slot of {lab.name}")
        self._check_fasting(self._expanded_tests(test_ids), slot)
        if slot.mode == "home_collection":
            if not lab.home_collection:
                raise ValueError(f"{lab.name} does not collect samples at home")
            if address_id is None:
                raise ValueError("Home collection needs an address_id")
            self.address(self.addresses, address_id)
        elif address_id is not None:
            raise ValueError("A lab_visit slot does not take an address_id")
        appointment = self._book(
            kind="lab_test",
            patient_id=patient_id,
            slot_id=slot_id,
            mode=slot.mode,
            amount=sum(test.price for test in tests),
            test_ids=list(test_ids),
            address_id=address_id,
            payment=payment,
            merchant=lab.name,
        )
        return {**to_dict(appointment), "slot": to_dict(slot)}

    @type_check
    @app_tool()
    @event_registered(operation_type=OperationType.WRITE)
    def reschedule_appointment(self, appointment_id: str, new_slot_id: str) -> dict[str, Any]:
        """
        Move an appointment to another free slot of the same doctor or lab, with the same mode.
        Allowed once per appointment.
        :param appointment_id: the appointment ID
        :param new_slot_id: the new slot ID
        :returns: the updated appointment
        """
        appointment = self._active(appointment_id)
        if appointment.reschedule_count >= MAX_FREE_RESCHEDULES:
            raise ValueError("This appointment was already rescheduled once; cancel it and book again")
        old = self.slots[appointment.slot_id]
        new = self._open_slot(new_slot_id)
        if new.owner_id != old.owner_id or new.mode != old.mode:
            raise ValueError("The new slot must be with the same doctor or lab and have the same mode")
        if appointment.kind == "lab_test":
            self._check_fasting(self._expanded_tests(appointment.test_ids), new)
        old.available, new.available = True, False
        appointment.slot_id = new_slot_id
        appointment.reschedule_count += 1
        return {**to_dict(appointment), "slot": to_dict(new)}

    @type_check
    @app_tool()
    @event_registered(operation_type=OperationType.WRITE)
    def cancel_appointment(self, appointment_id: str) -> dict[str, Any]:
        """
        Cancel an appointment. Full refund if 2 hours or more before the slot, otherwise no refund.
        :param appointment_id: the appointment ID
        :returns: the refund amount and the updated appointment
        """
        appointment = self._active(appointment_id)
        slot = self.slots[appointment.slot_id]
        hours = self.hours_until(self._slot_start(slot))
        if hours <= 0:
            raise ValueError("The appointment time has passed")
        refund = appointment.amount if hours >= FULL_REFUND_HOURS else 0
        if refund:
            self.refund(appointment.txn_id, refund)
            appointment.refunded_amount = refund
        appointment.status = "cancelled"
        slot.available = True
        return {"refund": refund, "appointment": to_dict(appointment)}

    @type_check
    @app_tool()
    @event_registered(operation_type=OperationType.WRITE)
    def add_patient(self, name: str, age: int, gender: str, relation: str) -> str:
        """
        Save a family member as a patient.
        :param name: full name
        :param age: age in years
        :param gender: Male, Female or Other
        :param relation: relation to the user, e.g. self, spouse, daughter, mother_in_law
        :returns: the patient ID
        """
        patient = Patient(self.next_id("SC-PAT", 3), name, age, gender, relation)
        self.patients[patient.patient_id] = patient
        return patient.patient_id

    # Environment events -------------------------------------------------------
    @type_check
    @env_tool()
    @event_registered(operation_type=OperationType.WRITE, event_type=EventType.ENV)
    def complete_appointment(self, appointment_id: str) -> None:
        """
        Mark an appointment as completed.
        :param appointment_id: the appointment ID
        """
        self._active(appointment_id).status = "completed"

    @type_check
    @env_tool()
    @event_registered(operation_type=OperationType.WRITE, event_type=EventType.ENV)
    def publish_report(
        self,
        appointment_id: str,
        kind: str,
        summary: str,
        results: list[dict[str, Any]] | None = None,
        file_path: str | None = None,
    ) -> str:
        """
        Publish a lab report, prescription or consultation note for an appointment.
        :param appointment_id: the appointment ID
        :param kind: "lab_report", "prescription" or "consult_note"
        :param summary: one-line summary
        :param results: lab results, each with test, value, unit, reference_range and flag
        :param file_path: path of the document in the Files app
        :returns: the record ID
        """
        if kind not in RECORD_KINDS:
            raise ValueError(f"kind must be one of {', '.join(RECORD_KINDS)}")
        appointment = self._appointment(appointment_id)
        record = MedicalRecord(
            record_id=self.next_id("SC-REC"),
            patient_id=appointment.patient_id,
            kind=kind,
            date=self.today().isoformat(),
            summary=summary,
            appointment_id=appointment_id,
            file_path=file_path,
            results=list(results or []),
        )
        self.medical_records[record.record_id] = record
        return record.record_id

    @type_check
    @env_tool()
    @event_registered(operation_type=OperationType.WRITE, event_type=EventType.ENV)
    def cancel_by_provider(self, appointment_id: str) -> int:
        """
        The doctor or lab cancels an appointment; the full amount is refunded.
        :param appointment_id: the appointment ID
        :returns: the refunded amount
        """
        appointment = self._active(appointment_id)
        self.refund(appointment.txn_id, appointment.amount)
        appointment.refunded_amount = appointment.amount
        appointment.status = "cancelled"
        self.slots[appointment.slot_id].available = True
        return appointment.amount

    @type_check
    @env_tool()
    @event_registered(operation_type=OperationType.WRITE, event_type=EventType.ENV)
    def update_slot_availability(self, slot_id: str, available: bool) -> None:
        """
        Open or close a slot.
        :param slot_id: the slot ID
        :param available: whether it can be booked
        """
        self._get(self.slots, slot_id, "Slot").available = available
