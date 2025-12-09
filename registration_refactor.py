# registration_refactor.py
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List


# ------------------------------
# Bagian A: Kode Bermasalah (Before)
# ------------------------------
@dataclass
class StudentRegistration:
    student_id: str
    name: str
    current_sks: int          # SKS yang sudah diambil saat ini
    requested_sks: int        # SKS yang ingin didaftar (jumlah)
    completed_courses: List[str]  # kode mata kuliah yg sudah lulus
    requested_courses: List[str]  # kode mata kuliah yg ingin diambil
    schedule: List[str]           # simple list of time slots like ["Mon-09", "Tue-11"]


class ValidatorManager:  # God-class: menangani semua validasi dengan if/else
    def validate(self, reg: StudentRegistration):
        print("ValidatorManager: memulai validasi gabungan (Sks & Prasyarat & Jadwal)...")
        # SKS limit check
        if reg.current_sks + reg.requested_sks > 24:
            print("Gagal: Melebihi batas SKS (max 24).")
            return False

        # Prerequisite check (hardcoded)
        for course in reg.requested_courses:
            if course == "CS201" and "CS101" not in reg.completed_courses:
                print("Gagal: Prasyarat CS101 belum terpenuhi untuk CS201.")
                return False

        # Jadwal bentrok (simple) — jika ada duplikat slot di requested vs existing schedule
        for slot in reg.schedule:
            if slot in reg.schedule:  # BUG: contoh logika konyol (selalu True)
                pass

        # Asumsi lulus
        print("Semua pengecekan pada ValidatorManager dilewati.")
        return True


# ------------------------------
# Bagian B: Refactor (After) — Abstraksi + Rules + Coordinator
# ------------------------------

# Abstraksi validasi (IValidationRule) -> DIP / OCP
class IValidationRule(ABC):
    @abstractmethod
    def validate(self, reg: StudentRegistration) -> (bool, str):
        """
        Kembalikan (True, "") jika lulus; jika gagal return (False, "Pesan kesalahan")
        """
        pass


# Rule 1: SksLimitRule
class SksLimitRule(IValidationRule):
    def __init__(self, max_sks: int = 24):
        self.max_sks = max_sks

    def validate(self, reg: StudentRegistration) -> (bool, str):
        if reg.current_sks + reg.requested_sks > self.max_sks:
            return False, f"Gagal: Melebihi batas SKS (max {self.max_sks})."
        return True, ""


# Rule 2: PrerequisiteRule
class PrerequisiteRule(IValidationRule):
    def __init__(self, prereq_map: dict):
        """
        prereq_map: dict, key = course, value = list of prerequisite course codes
        contoh: {"CS201": ["CS101"]}
        """
        self.prereq_map = prereq_map

    def validate(self, reg: StudentRegistration) -> (bool, str):
        for course in reg.requested_courses:
            required = self.prereq_map.get(course, [])
            for req in required:
                if req not in reg.completed_courses:
                    return False, f"Gagal: Prasyarat {req} belum terpenuhi untuk {course}."
        return True, ""


# Rule 3: JadwalBentrokRule (Challenge / Pembuktian OCP)
class JadwalBentrokRule(IValidationRule):
    def __init__(self, existing_schedule: List[str] = None):
        # existing_schedule ini bisa berupa jadwal kuliah mahasiswa yang sudah terdaftar
        self.existing_schedule = existing_schedule or []

    def validate(self, reg: StudentRegistration) -> (bool, str):
        # Kita asumsikan reg.schedule berisi jadwal saat ini,
        # dan reg.requested_courses jadwalnya kita map sederhana via course->slot map
        # Untuk contoh sederhana, kita berikan mapping statis (bisa diganti eksternal)
        course_slot_map = {
            "CS101": "Mon-09",
            "CS102": "Tue-11",
            "CS201": "Mon-09",  # bentrok dengan CS101
            "MA101": "Wed-10",
        }
        # Buat set dari jadwal yang sudah ada (existing + reg.schedule)
        occupied = set(self.existing_schedule + reg.schedule)

        # cek setiap requested course apakah slotnya sudah terpakai
        for course in reg.requested_courses:
            slot = course_slot_map.get(course)
            if slot is None:
                # jika tidak ada mapping, anggap aman
                continue
            if slot in occupied:
                return False, f"Gagal: Jadwal bentrok untuk {course} pada slot {slot}."
            # jika tidak bentrok, tambahkan ke occupied agar mencegah bentrok antar requested courses juga
            occupied.add(slot)

        return True, ""


# Coordinator: RegistrationService (SRP) — menerima list of IValidationRule via DI
class RegistrationService:
    def __init__(self, rules: List[IValidationRule]):
        self.rules = rules

    def register(self, reg: StudentRegistration) -> (bool, str):
        for rule in self.rules:
            ok, msg = rule.validate(reg)
            rule_name = rule.__class__.__name__
            print(f"[{rule_name}] -> {'OK' if ok else 'FAIL'} {(' - ' + msg) if msg else ''}")
            if not ok:
                return False, msg
        return True, "Registrasi berhasil."


# ------------------------------
# Bagian C: Demonstrasi & Pembuktian OCP
# ------------------------------
def demo_before_refactor():
    print("=== Demo BEFORE refactor (ValidatorManager) ===")
    reg = StudentRegistration(
        student_id="S001",
        name="Ani",
        current_sks=20,
        requested_sks=6,
        completed_courses=["CS101"],
        requested_courses=["CS201"],
        schedule=["Tue-11"]
    )
    vm = ValidatorManager()
    ok = vm.validate(reg)
    print("Hasil ValidatorManager:", ok)
    print()


def demo_after_refactor(include_jadwal_rule=False):
    print("=== Demo AFTER refactor (RegistrationService with Rules) ===")
    reg = StudentRegistration(
        student_id="S002",
        name="Budi",
        current_sks=18,
        requested_sks=6,  # total 24 => batas
        completed_courses=["CS101"],
        requested_courses=["CS201", "MA101"],
        schedule=["Wed-10"]  # punya jadwal pada Wed-10
    )

    # rules: SKS limit + Prasyarat
    prereq_map = {"CS201": ["CS101"]}
    rules = [
        SksLimitRule(max_sks=24),
        PrerequisiteRule(prereq_map=prereq_map)
    ]

    # optional: injeksikan JadwalBentrokRule tanpa ubah RegistrationService
    if include_jadwal_rule:
        # Suppose existing schedule contains "Mon-09" so CS201 maps to Mon-09 and will conflict
        jadwal_rule = JadwalBentrokRule(existing_schedule=["Mon-09"])
        rules.append(jadwal_rule)

    service = RegistrationService(rules=rules)

    ok, msg = service.register(reg)
    print("Hasil RegistrationService:", ok, msg)
    print()


if __name__ == "__main__":
    # Demo sebelum refactor (menunjukkan kode problematik)
    demo_before_refactor()

    # Demo setelah refactor tanpa JadwalBentrokRule
    demo_after_refactor(include_jadwal_rule=False)

    # Demo setelah refactor DENGAN JadwalBentrokRule (challenge) -> menunjukkan OCP
    # Kita *menambahkan* rule baru ke list rules, TIDAK mengubah kode RegistrationService
    demo_after_refactor(include_jadwal_rule=True)
