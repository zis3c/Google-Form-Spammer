"""Pembuat identitas dan jawaban teks berbahasa Indonesia.

Satu profil dibuat per respons supaya jawaban saling konsisten:
nama, email, tanggal lahir, usia, NIK, telepon, dan alamat berasal dari
orang yang sama. Jawaban pilihan ganda tetap memakai opsi asli form.
"""

import datetime as _dt
import random
import re
from dataclasses import dataclass

import id_data as D


def _norm(text: str) -> str:
    text = (text or "").lower()
    text = re.sub(r"[^a-z0-9+@./ -]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _has(q: str, *needles: str) -> bool:
    return any(n in q for n in needles)


def _has_word(q: str, *words: str) -> bool:
    return any(re.search(rf"\b{re.escape(w)}\b", q) for w in words)


@dataclass
class Profile:
    gender: str
    first: str
    last: str
    full_name: str
    birthdate: _dt.date
    age: int
    city: str
    regency: str
    province: str
    postal: str
    nik: str
    npwp: str
    kk: str
    bpjs: str
    nisn: str
    nim: str
    nip: str
    phone_local: str
    phone_intl: str
    email: str
    street: str
    kelurahan: str
    kecamatan: str
    rt: str
    rw: str
    address_short: str
    address_full: str
    job: str
    title: str
    company: str
    agency: str
    school: str
    university: str
    major: str
    education: str
    ipk: str
    semester: str
    entry_year: str
    graduation_year: str
    school_class: str
    religion: str
    blood: str
    marital: str
    weight: str
    height: str
    income: str
    website: str
    instagram: str
    username: str
    account_number: str
    mother_name: str
    father_name: str
    guardian_name: str


def _digits(rng: random.Random, n: int, first: str = "") -> str:
    first = first[:1]
    rest = "".join(str(rng.randint(0, 9)) for _ in range(n - len(first)))
    return (first + rest) if first else rest


_MALE_NAMES = [name for name, g in D.NAME_POOL if g == "Laki-laki"]
_FEMALE_NAMES = [name for name, g in D.NAME_POOL if g == "Perempuan"]
_MALE_JOBS = [job for job in D.JOBS if job not in D.FEMALE_ONLY_JOBS]


def _pick_name(rng: random.Random, gender: str) -> str:
    return rng.choice(_MALE_NAMES if gender == "Laki-laki" else _FEMALE_NAMES)


def build_profile(rng: random.Random = None) -> Profile:
    rng = rng or random

    gender = rng.choice(["Laki-laki", "Perempuan"])
    full_name = _pick_name(rng, gender)
    first, last = full_name.split(" ", 1)

    today = _dt.date.today()
    age = rng.randint(18, 60)
    birth_year = today.year - age
    birthdate = _dt.date(birth_year, rng.randint(1, 12), rng.randint(1, 28))
    real_age = today.year - birthdate.year - (
        (today.month, today.day) < (birthdate.month, birthdate.day)
    )

    city, province, nik4, postal = rng.choice(D.CITIES)
    regency = f"Kota {city}" if rng.random() < 0.6 else f"Kabupaten {city}"
    kecamatan = rng.choice(D.KECAMATAN)
    kelurahan = rng.choice(D.KELURAHAN)
    street = f"Jl. {rng.choice(D.STREETS)} No. {rng.randint(1, 250)}"
    rt = f"{rng.randint(1, 15):03d}"
    rw = f"{rng.randint(1, 12):03d}"

    day = birthdate.day + (40 if gender == "Perempuan" else 0)
    nik = (
        f"{nik4}{rng.randint(10, 99):02d}{day:02d}"
        f"{birthdate.month:02d}{str(birthdate.year)[-2:]}{rng.randint(1000, 9999)}"
    )
    kk = (
        f"{nik4}{rng.randint(10, 99):02d}{rng.randint(10, 99):02d}"
        f"{rng.randint(10, 99):02d}{rng.randint(100000, 999999)}"
    )
    npwp = nik
    bpjs = _digits(rng, 13, "1")
    nisn = _digits(rng, 10, str(rng.randint(1, 9)))
    entry_year = today.year - rng.randint(1, 5)
    nim = f"{entry_year}{rng.randint(100000, 999999)}"
    nip = (
        f"{birthdate.year}{birthdate.month:02d}{birthdate.day:02d}"
        f"{entry_year}{rng.randint(1, 12):02d}"
        f"{'2' if gender == 'Perempuan' else '1'}{rng.randint(100, 999)}"
    )

    phone_local = rng.choice(D.PHONE_PREFIXES) + _digits(rng, 8)
    phone_intl = "+62" + phone_local[1:]
    local = re.sub(r"[^a-z0-9.]", "", f"{first}.{last}".lower())
    email = f"{local}{rng.randint(1, 99)}@{rng.choice(D.EMAIL_DOMAINS)}"

    address_short = f"{street}, {city}"
    address_full = (
        f"{street}, RT {rt}/RW {rw}, Kel. {kelurahan}, "
        f"Kec. {kecamatan}, {city}, {province} {postal}"
    )

    agency_name = rng.choice(D.AGENCIES)
    if agency_name.startswith(("Dinas", "Kantor")):
        agency_name = f"{agency_name} {city}"

    income = rng.choice([
        "Rp 3.000.000", "Rp 3.500.000", "Rp 4.000.000", "Rp 4.500.000",
        "Rp 5.000.000", "Rp 6.000.000", "Rp 7.500.000", "Rp 10.000.000",
        "Rp 12.000.000", "Rp 15.000.000", "Rp 20.000.000",
    ])

    slug = re.sub(r"[^a-z0-9]", "", f"{first}{last}".lower())

    return Profile(
        gender=gender,
        first=first,
        last=last,
        full_name=full_name,
        birthdate=birthdate,
        age=real_age,
        city=city,
        regency=regency,
        province=province,
        postal=postal,
        nik=nik,
        npwp=npwp,
        kk=kk,
        bpjs=bpjs,
        nisn=nisn,
        nim=nim,
        nip=nip,
        phone_local=phone_local,
        phone_intl=phone_intl,
        email=email,
        street=street,
        kelurahan=kelurahan,
        kecamatan=kecamatan,
        rt=rt,
        rw=rw,
        address_short=address_short,
        address_full=address_full,
        job=rng.choice(_MALE_JOBS if gender == "Laki-laki" else D.JOBS),
        title=rng.choice(D.TITLES),
        company=rng.choice(D.COMPANIES),
        agency=agency_name,
        school=f"{rng.choice(D.SCHOOL_PREFIXES)} {city}",
        university=rng.choice(D.UNIVERSITIES),
        major=rng.choice(D.MAJORS),
        education=rng.choice(D.EDUCATION_LEVELS),
        ipk=f"{rng.uniform(2.75, 4.0):.2f}",
        semester=str(rng.randint(2, 8)),
        entry_year=str(entry_year),
        graduation_year=str(today.year - rng.randint(0, 8)),
        school_class=rng.choice(D.SCHOOL_CLASSES),
        religion=rng.choice(D.RELIGIONS),
        blood=rng.choice(D.BLOOD_TYPES),
        marital=rng.choice(D.MARITAL_STATUSES),
        weight=str(rng.randint(55, 95) if gender == "Laki-laki" else rng.randint(42, 80)),
        height=str(rng.randint(160, 185) if gender == "Laki-laki" else rng.randint(148, 172)),
        income=income,
        website=f"https://www.{slug}{rng.randint(1, 99)}.com",
        instagram=f"@{slug}{rng.randint(1, 99)}",
        username=f"{slug}{rng.randint(1, 999)}",
        account_number=_digits(rng, rng.randint(10, 14), "1"),
        mother_name=_pick_name(rng, "Perempuan"),
        father_name=_pick_name(rng, "Laki-laki"),
        guardian_name=_pick_name(rng, rng.choice(["Laki-laki", "Perempuan"])),
    )


def _intent_bank(q: str) -> list:
    if _has(q, "saran", "masukan", "rekomendasi", "suggest"):
        return D.SUGGESTION_SENTENCES
    if _has(q, "kritik", "keluhan", "kekurangan", "masalah", "complain"):
        return D.COMPLAINT_SENTENCES
    if _has(q, "harapan", "ekspektasi", "hope"):
        return D.HOPE_SENTENCES
    if _has(q, "alasan", "mengapa", "kenapa", "reason"):
        return D.REASON_SENTENCES
    if _has(q, "pengalaman", "ceritakan", "cerita", "experience"):
        return D.EXPERIENCE_SENTENCES
    return D.GENERAL_SENTENCES


def _paragraph(bank: list, rng: random.Random) -> str:
    if bank is D.GENERAL_SENTENCES:
        count = rng.randint(2, 3)
        return " ".join(rng.sample(bank, count))
    parts = [rng.choice(bank)]
    parts.extend(rng.sample(D.GENERAL_SENTENCES, rng.randint(1, 2)))
    return " ".join(parts)


def text_answer(question: str, q_type: str, p: Profile, rng: random.Random = None) -> str:
    """Jawaban teks Indonesia untuk satu pertanyaan, konsisten dengan profil."""
    rng = rng or random
    q = _norm(question)

    # --- Identitas digital -------------------------------------------------
    if _has(q, "email", "e-mail", "surel"):
        return p.email
    if _has(q, "instagram") or _has_word(q, "ig"):
        return p.instagram
    if _has(q, "website", "situs", "url", "tautan", "link", "web"):
        return p.website
    if _has(q, "username", "nama pengguna", "user name") or _has_word(q, "akun"):
        return p.username
    if _has(q, "tiktok", "twitter", "facebook", "linkedin"):
        return p.username

    # --- Nomor dokumen -----------------------------------------------------
    if _has(q, "rekening", "norek", "no rek"):
        return p.account_number
    if _has(q, "kartu keluarga") or _has(q, "nomor kk") or _has_word(q, "kk"):
        return p.kk
    if _has(q, "kartu tanda penduduk") or _has_word(q, "nik", "ktp"):
        return p.nik
    if _has(q, "npwp"):
        return p.npwp
    if _has(q, "bpjs"):
        return p.bpjs
    if _has(q, "nisn"):
        return p.nisn
    if _has_word(q, "nim"):
        return p.nim
    if _has_word(q, "nip"):
        return p.nip
    if _has(q, "nomor induk"):
        return p.nim

    # --- Alamat ------------------------------------------------------------
    if _has(q, "kode pos", "kodepos", "postal"):
        return p.postal
    if _has(q, "kelurahan", "desa"):
        return p.kelurahan
    if _has(q, "kecamatan", "kec."):
        return p.kecamatan
    if _has(q, "provinsi", "propinsi"):
        return p.province
    if _has(q, "tempat lahir", "kota lahir", "kota kelahiran"):
        return p.city
    if _has(q, "kabupaten"):
        return p.regency
    if _has(q, "kota"):
        return p.city
    if _has_word(q, "rt"):
        return p.rt
    if _has_word(q, "rw"):
        return p.rw
    if _has(q, "jalan", "jl.", "jl ", "street"):
        return p.street
    if _has(q, "alamat", "domisili", "tempat tinggal", "address"):
        return p.address_full if _has(q, "lengkap") else p.address_short

    # --- Tanggal lahir dan usia -------------------------------------------
    if _has(q, "tanggal lahir", "tgl lahir", "tgl. lahir", "birthdate",
            "birth date"):
        return p.birthdate.strftime("%d/%m/%Y")
    if _has(q, "tahun lahir"):
        return str(p.birthdate.year)
    if _has(q, "umur", "usia") or _has_word(q, "age"):
        return str(p.age)

    # --- Telepon -----------------------------------------------------------
    if _has(q, "telepon", "telp", "ponsel", "handphone", "whatsapp",
            "phone", "mobile", "kontak", "hubungi") or _has_word(q, "hp", "wa"):
        return p.phone_intl if _has(q, "+62", "internasional") else p.phone_local
    if _has(q, "nomor urut", "no urut", "nomor absen", "no absen"):
        return str(rng.randint(1, 40))
    if _has(q, "nomor") or _has_word(q, "no"):
        return p.phone_local

    # --- Demografi ---------------------------------------------------------
    if _has(q, "jenis kelamin", "gender", "kelamin"):
        return p.gender
    if _has(q, "agama", "religion"):
        return p.religion
    if _has(q, "status perkawinan", "status pernikahan", "marital"):
        return p.marital
    if _has(q, "kewarganegaraan", "warganegara", "nationality"):
        return "WNI"
    if _has(q, "golongan darah", "blood"):
        return p.blood
    if _has(q, "berat badan"):
        return p.weight
    if _has(q, "tinggi badan"):
        return p.height
    if _has(q, "pendapatan", "penghasilan", "gaji", "income", "upah"):
        return p.income

    # --- Pendidikan --------------------------------------------------------
    if _has(q, "pendidikan terakhir", "jenjang pendidikan"):
        return p.education
    if _has(q, "universitas", "kampus", "perguruan tinggi", "almamater",
            "alumni"):
        return p.university
    if _has(q, "sekolah", "sma", "smk", "asal sekolah"):
        return p.school
    if _has(q, "jurusan", "prodi", "program studi"):
        return p.major
    if _has(q, "ipk", "gpa", "indeks prestasi"):
        return p.ipk
    if _has(q, "semester"):
        return p.semester
    if _has(q, "angkatan"):
        return p.entry_year
    if _has(q, "tahun lulus", "tahun kelulusan", "lulus tahun"):
        return p.graduation_year
    if _has(q, "kelas"):
        return p.school_class

    # --- Pekerjaan ---------------------------------------------------------
    if _has(q, "jabatan", "posisi", "position", "title"):
        return p.title
    if _has(q, "pekerjaan", "profesi", "occupation"):
        return p.job
    if _has(q, "perusahaan", "company", "tempat kerja", "organisasi",
            "employer"):
        return p.company
    if _has(q, "instansi", "kantor", "dinas", "kementerian", "lembaga"):
        return p.agency

    # --- Kegiatan ----------------------------------------------------------
    if _has(q, "acara", "kegiatan", "event"):
        return rng.choice(D.EVENTS)

    # --- Nama orang --------------------------------------------------------
    if _has(q, "nama ibu", "nama mama", "ibu kandung"):
        return p.mother_name
    if _has(q, "nama ayah", "nama bapak", "ayah kandung"):
        return p.father_name
    if _has(q, "nama wali") or _has_word(q, "wali"):
        return p.guardian_name
    if _has(q, "nama depan", "first name"):
        return p.first
    if _has(q, "nama belakang", "nama akhir", "last name", "surname"):
        return p.last
    if _has(q, "nama panggilan", "nickname", "panggilan"):
        return p.first
    if _has(q, "nama lengkap", "full name") or _has_word(q, "nama", "name"):
        return p.full_name

    # --- Angka dan waktu ---------------------------------------------------
    if _has(q, "jumlah", "banyak", "total", "berapa orang"):
        return str(rng.randint(1, 10))
    if _has(q, "tahun"):
        return str(rng.randint(1985, 2005))
    if _has(q, "tanggal", "tgl") or _has_word(q, "date"):
        return (today_date() - _dt.timedelta(days=rng.randint(0, 365))).strftime("%d/%m/%Y")
    if _has(q, "jam", "pukul", "waktu") or _has_word(q, "time"):
        return f"{rng.randint(0, 23):02d}:{rng.randint(0, 59):02d}"

    # --- Kalimat bebas -----------------------------------------------------
    bank = _intent_bank(q)
    if q_type in ("Short Answer", "Open Ended") or _has(q, "singkat"):
        return rng.choice(bank)
    return _paragraph(bank, rng)


def today_date() -> _dt.date:
    return _dt.date.today()
