"""Pemeriksaan offline untuk generator identitas Indonesia.

Jalankan: python test_identity.py
Tidak menyentuh jaringan dan tidak mengirim respons ke Google Forms.
"""

import datetime as dt
import re

import id_data as D
from core import FormDetails, SubmissionEngine

QUESTIONS = {
    "name": ("Nama lengkap", "Short Answer"),
    "first": ("Nama depan", "Short Answer"),
    "last": ("Nama belakang", "Short Answer"),
    "nick": ("Nama panggilan", "Short Answer"),
    "mother": ("Nama ibu kandung", "Short Answer"),
    "father": ("Nama ayah", "Short Answer"),
    "email": ("Alamat email aktif", "Short Answer"),
    "phone": ("Nomor HP/WhatsApp", "Short Answer"),
    "phone_intl": ("Nomor telepon format +62", "Short Answer"),
    "addr": ("Alamat lengkap domisili", "Paragraph"),
    "addr_short": ("Alamat", "Short Answer"),
    "city": ("Kota tempat tinggal", "Short Answer"),
    "kab": ("Kabupaten/Kota domisili", "Short Answer"),
    "prov": ("Provinsi", "Short Answer"),
    "kec": ("Kecamatan", "Short Answer"),
    "kel": ("Kelurahan", "Short Answer"),
    "zip": ("Kode pos", "Short Answer"),
    "rt": ("RT", "Short Answer"),
    "rw": ("RW", "Short Answer"),
    "street": ("Nama jalan", "Short Answer"),
    "birth": ("Tanggal lahir", "Short Answer"),
    "age": ("Umur", "Short Answer"),
    "gender": ("Jenis kelamin", "Short Answer"),
    "religion": ("Agama", "Short Answer"),
    "marital": ("Status perkawinan", "Short Answer"),
    "nationality": ("Kewarganegaraan", "Short Answer"),
    "blood": ("Golongan darah", "Short Answer"),
    "weight": ("Berat badan", "Short Answer"),
    "height": ("Tinggi badan", "Short Answer"),
    "income": ("Pendapatan per bulan", "Short Answer"),
    "edu": ("Pendidikan terakhir", "Short Answer"),
    "univ": ("Nama universitas", "Short Answer"),
    "school": ("Nama sekolah", "Short Answer"),
    "major": ("Jurusan", "Short Answer"),
    "ipk": ("IPK", "Short Answer"),
    "semester": ("Semester", "Short Answer"),
    "entry": ("Angkatan", "Short Answer"),
    "graduation": ("Tahun lulus", "Short Answer"),
    "class": ("Kelas", "Short Answer"),
    "job": ("Pekerjaan", "Short Answer"),
    "title": ("Jabatan", "Short Answer"),
    "company": ("Nama perusahaan", "Short Answer"),
    "agency": ("Nama instansi", "Short Answer"),
    "nik": ("NIK", "Short Answer"),
    "npwp": ("NPWP", "Short Answer"),
    "kk": ("Nomor kartu keluarga", "Short Answer"),
    "bpjs": ("Nomor BPJS", "Short Answer"),
    "nisn": ("NISN", "Short Answer"),
    "nim": ("NIM", "Short Answer"),
    "nip": ("NIP", "Short Answer"),
    "rek": ("Nomor rekening", "Short Answer"),
    "ig": ("Instagram", "Short Answer"),
    "web": ("Website", "Short Answer"),
    "user": ("Username", "Short Answer"),
    "event": ("Nama kegiatan", "Short Answer"),
    "count": ("Jumlah anggota keluarga", "Short Answer"),
    "year": ("Tahun berapa", "Short Answer"),
    "date": ("Tanggal pengisian", "Short Answer"),
    "time": ("Jam berapa", "Short Answer"),
    "suggest": ("Saran dan masukan", "Paragraph"),
    "complain": ("Kritik dan keluhan", "Paragraph"),
    "hope": ("Harapan", "Paragraph"),
    "reason": ("Alasan memilih", "Paragraph"),
    "exp": ("Ceritakan pengalaman", "Paragraph"),
    "short": ("Pendapat singkat", "Short Answer"),
    "birth_date_type": ("Tanggal lahir", "Date"),
    "time_type": ("Jam kedatangan", "Time"),
    "mc": ("Pilih satu", "Multiple Choice"),
}


def build_questions():
    out = {}
    for key, (text, qtype) in QUESTIONS.items():
        out[key] = {
            "type": qtype,
            "text": text,
            "options": ["Ya", "Tidak"] if qtype == "Multiple Choice" else [],
            "required": True,
        }
    return out


def run_once():
    details = FormDetails(
        url="offline",
        form_action_url="offline",
        questions=build_questions(),
        hidden_fields={},
    )
    engine = SubmissionEngine(details)
    response, _release = engine.generate_response()
    return response


def main():
    assert len(D.NAME_POOL) == 2000, len(D.NAME_POOL)
    assert len({name for name, _ in D.NAME_POOL}) == 2000
    assert {g for _, g in D.NAME_POOL} == {"Laki-laki", "Perempuan"}

    gender_of = dict(D.NAME_POOL)
    city_of = {c: (p, n, z) for c, p, n, z in D.CITIES}
    female_names = {n for n, g in D.NAME_POOL if g == "Perempuan"}
    male_names = {n for n, g in D.NAME_POOL if g == "Laki-laki"}

    r = run_once()

    for key, value in r.items():
        assert str(value).strip(), f"{key} kosong"

    full = r["name"]
    first, last = full.split(" ", 1)
    assert r["first"] == first
    assert r["last"] == last
    assert r["nick"] == first
    assert r["gender"] == gender_of[full]
    assert r["mother"] in female_names
    assert r["father"] in male_names

    email = r["email"]
    assert re.fullmatch(r"[a-z0-9.]+[0-9]{1,2}@[a-z0-9.-]+", email), email
    assert email.split("@")[0].startswith(f"{first}.{last}".lower())

    phone = r["phone"]
    assert re.fullmatch(r"08[0-9]{8,11}", phone), phone
    assert r["phone_intl"] == "+62" + phone[1:]

    birth = dt.datetime.strptime(r["birth"], "%d/%m/%Y").date()
    age = int(r["age"])
    today = dt.date.today()
    real_age = today.year - birth.year - (
        (today.month, today.day) < (birth.month, birth.day)
    )
    assert age == real_age

    province, nik4, postal = city_of[r["city"]]
    assert r["prov"] == province
    assert r["zip"] == postal
    assert r["kab"].endswith(r["city"])
    assert r["kel"] in D.KELURAHAN
    assert r["kec"] in D.KECAMATAN
    assert re.fullmatch(r"\d{3}", r["rt"])
    assert re.fullmatch(r"\d{3}", r["rw"])
    assert r["street"].startswith("Jl. ")
    assert r["city"] in r["addr"] and postal in r["addr"]
    assert r["city"] in r["addr_short"]

    nik = r["nik"]
    assert re.fullmatch(r"\d{16}", nik)
    assert nik.startswith(nik4)
    day = int(nik[6:8])
    if r["gender"] == "Perempuan":
        day -= 40
    assert day == birth.day
    assert int(nik[8:10]) == birth.month
    assert int(nik[10:12]) == birth.year % 100
    assert r["npwp"] == nik
    assert re.fullmatch(r"\d{16}", r["kk"])
    assert re.fullmatch(r"\d{13}", r["bpjs"])
    assert re.fullmatch(r"\d{10}", r["nisn"])
    assert r["nim"].startswith(r["entry"])
    assert re.fullmatch(r"\d{18}", r["nip"])
    assert r["nip"].startswith(birth.strftime("%Y%m%d"))
    assert re.fullmatch(r"\d{10,14}", r["rek"])

    assert r["religion"] in set(D.RELIGIONS)
    assert r["blood"] in {"A", "B", "AB", "O"}
    assert r["marital"] in set(D.MARITAL_STATUSES)
    assert r["nationality"] == "WNI"
    if r["gender"] == "Laki-laki":
        assert 55 <= int(r["weight"]) <= 95
        assert 160 <= int(r["height"]) <= 185
        assert r["job"] not in D.FEMALE_ONLY_JOBS
    else:
        assert 42 <= int(r["weight"]) <= 80
        assert 148 <= int(r["height"]) <= 172
    assert r["income"].startswith("Rp ")

    assert r["edu"] in set(D.EDUCATION_LEVELS)
    assert r["univ"] in D.UNIVERSITIES
    assert r["school"].startswith(tuple(D.SCHOOL_PREFIXES))
    assert r["school"].endswith(r["city"])
    assert r["major"] in D.MAJORS
    assert 2.75 <= float(r["ipk"]) <= 4.0
    assert 2 <= int(r["semester"]) <= 8
    assert r["class"] in D.SCHOOL_CLASSES
    assert r["entry"].isdigit() and r["graduation"].isdigit()

    assert r["job"] in D.JOBS
    assert r["title"] in D.TITLES
    assert r["company"] in D.COMPANIES
    assert r["company"] != full
    assert r["agency"] in D.AGENCIES or any(
        r["agency"].startswith(p) for p in ("Dinas", "Kantor")
    )

    assert r["ig"].startswith("@")
    assert r["web"].startswith("https://")
    assert re.fullmatch(r"[a-z0-9]+", r["user"])

    assert r["event"] in D.EVENTS
    assert 1 <= int(r["count"]) <= 10
    assert 1985 <= int(r["year"]) <= 2005
    assert re.fullmatch(r"\d{2}/\d{2}/\d{4}", r["date"])
    assert re.fullmatch(r"\d{2}:\d{2}", r["time"])

    assert any(s in r["suggest"] for s in D.SUGGESTION_SENTENCES)
    assert any(s in r["complain"] for s in D.COMPLAINT_SENTENCES)
    assert any(s in r["hope"] for s in D.HOPE_SENTENCES)
    assert any(s in r["reason"] for s in D.REASON_SENTENCES)
    assert any(s in r["exp"] for s in D.EXPERIENCE_SENTENCES)
    assert r["short"] in D.GENERAL_SENTENCES
    for key in ("suggest", "complain", "hope", "reason", "exp"):
        assert r[key].count(".") >= 2, key

    assert r["mc"] in ("Ya", "Tidak")
    assert r["birth_date_type_year"] == str(birth.year)
    assert r["birth_date_type_month"] == f"{birth.month:02d}"
    assert r["birth_date_type_day"] == f"{birth.day:02d}"
    assert re.fullmatch(r"\d{2}", r["time_type_hour"])
    assert re.fullmatch(r"\d{2}", r["time_type_minute"])

    print("OK: 2000 nama unik, profil konsisten, seluruh field tervalidasi")


if __name__ == "__main__":
    main()
