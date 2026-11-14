"""Dataset identitas Indonesia untuk pengisian form acak.

Nama disusun dari pool nama depan dan marga, lalu dibangkitkan sekali
secara deterministik menjadi 2000 nama unik (1000 laki-laki, 1000 perempuan).
"""

import random

# ---------------------------------------------------------------------------
# Nama
# ---------------------------------------------------------------------------

MALE_FIRST = [
    "Adi", "Agus", "Ahmad", "Aji", "Aldi", "Alfian", "Alif", "Andi", "Angga",
    "Anwar", "Ardan", "Arif", "Aris", "Arman", "Arya", "Asep", "Azis", "Bagas",
    "Bagus", "Bahar", "Bambang", "Baskara", "Bayu", "Beni", "Bima", "Budi",
    "Cahyo", "Cakra", "Candra", "Daffa", "Danu", "Darma", "Dedi", "Deni",
    "Dimas", "Doni", "Dwi", "Dzikri", "Eko", "Erwin", "Fahmi", "Fajar",
    "Farel", "Farhan", "Fauzan", "Fauzi", "Febri", "Feri", "Fikri", "Firman",
    "Gading", "Galang", "Galih", "Gibran", "Gilang", "Gunawan", "Habib", "Hadi",
    "Hafiz", "Hamdan", "Hanif", "Haris", "Harun", "Hendra", "Heri", "Herman",
    "Hilmi", "Ikhsan", "Ilham", "Iman", "Imam", "Indra", "Iqbal", "Irfan",
    "Iskandar", "Iwan", "Jabbar", "Joko", "Junaidi", "Kamal", "Kamil", "Kurnia",
    "Lukman", "Luthfi", "Lutfi", "Mahdi", "Malik", "Maman", "Mansur",
    "Mardianto", "Marwan", "Maulana", "Miftah", "Miko", "Muhammad", "Mursyid",
    "Nabil", "Nanda", "Naufal", "Nizar", "Nugroho", "Nur", "Okta", "Panca",
    "Pandu", "Panji", "Pradipta", "Prasetyo", "Putra", "Qori", "Rafi", "Rafif",
    "Ragil", "Rahmat", "Raihan", "Raka", "Ramadhan", "Rangga", "Reza", "Rian",
    "Ridho", "Rizal", "Rizki", "Rizky", "Rudi", "Sabar", "Sahrul", "Samsul",
    "Sandi", "Sapto", "Satria", "Slamet", "Sofyan", "Surya", "Syafiq",
    "Syahrul", "Taufik", "Tedi", "Teguh", "Tio", "Toha", "Tri", "Umar",
    "Vino", "Wafi", "Wahyu", "Wawan", "Wira", "Yandi", "Yanto", "Yoga",
    "Yosef", "Yudha", "Yudi", "Yusuf", "Zainal", "Zaki", "Zulfikar",
]

FEMALE_FIRST = [
    "Adelia", "Afifah", "Aisyah", "Alia", "Alya", "Amalia", "Amelia", "Angel",
    "Ani", "Anindya", "Anisa", "Annisa", "Arini", "Aulia", "Ayu", "Aziza",
    "Azka", "Bela", "Bella", "Bintang", "Bunga", "Cahaya", "Cahya", "Cantika",
    "Chika", "Citra", "Dara", "Dela", "Dewi", "Dian", "Dina", "Dinda", "Dita",
    "Dwi", "Eka", "Elsa", "Elvira", "Endang", "Erika", "Fadia", "Fani", "Fara",
    "Farah", "Fatimah", "Feby", "Fina", "Fitri", "Galuh", "Gita", "Gracia",
    "Hana", "Hanum", "Hasna", "Hesti", "Hilda", "Icha", "Ika", "Imelda",
    "Indah", "Indri", "Ines", "Intan", "Irma", "Jihan", "Juwita", "Karina",
    "Kartika", "Kasih", "Keisha", "Kirana", "Laila", "Laras", "Lestari",
    "Lia", "Lina", "Lintang", "Lisa", "Lita", "Lulu", "Maharani", "Maida",
    "Mala", "Marsha", "Mawar", "Maya", "Mega", "Melati", "Mila", "Milna",
    "Mira", "Mutiara", "Nabila", "Nada", "Nadia", "Nafisa", "Nanda", "Natalia",
    "Naura", "Nia", "Nila", "Ninda", "Ningsih", "Nisa", "Novi", "Novita",
    "Nur", "Nuri", "Nurul", "Oki", "Oktavia", "Olivia", "Permata", "Pratiwi",
    "Puspa", "Putri", "Qonita", "Rachma", "Rahma", "Rani", "Rania", "Rara",
    "Ratna", "Rina", "Rini", "Ririn", "Riska", "Rita", "Rizka", "Rosa",
    "Rosita", "Sabrina", "Salma", "Salsa", "Salsabila", "Sari", "Sekar",
    "Sella", "Shafira", "Shinta", "Sinta", "Siti", "Sonia", "Sri", "Suci",
    "Sulastri", "Susi", "Tania", "Tari", "Tasya", "Tessa", "Tiara", "Tika",
    "Tri", "Ulfa", "Vania", "Vanya", "Vina", "Vivi", "Wanda", "Wati", "Widya",
    "Wulan", "Yani", "Yessi", "Yolanda", "Yulia", "Yumna", "Yuni", "Zahra",
    "Zaskia", "Zubaidah", "Zulaika",
]

SURNAMES = [
    "Abbas", "Alatas", "Alhabsyi", "Arief", "Assagaf", "Attamimi", "Bahri",
    "Cahyadi", "Chaniago", "Daulay", "Dharma", "Effendi", "Fadillah",
    "Fauzi", "Firmansyah", "Ginting", "Gunadi", "Gunawan", "Hakim", "Hamid",
    "Harahap", "Hartono", "Hasibuan", "Hermawan", "Hidayat", "Hutapea",
    "Idris", "Indrawan", "Irawan", "Iskandar", "Jaya", "Juanda", "Karim",
    "Kartawijaya", "Koto", "Kurniawan", "Kusnadi", "Kusuma", "Lasut",
    "Latumahina", "Lesmana", "Lubis", "Lumenta", "Lumingkewas", "Lubna",
    "Manurung", "Maulana", "Mulyadi", "Munandar", "Nasution", "Natawidjaja",
    "Nelwan", "Nugroho", "Nurjaman", "Oetomo", "Oktavian", "Palar",
    "Panjaitan", "Pattiasina", "Pattinama", "Pelupessy", "Permana", "Piliang",
    "Pratama", "Prawira", "Pulungan", "Purba", "Purnama", "Qomar", "Rachman",
    "Rahim", "Ramadhan", "Rambe", "Rehatta", "Roring", "Rumambi", "Runtu",
    "Rusdianto", "Salim", "Sani", "Santoso", "Saputra", "Setiawan", "Shihab",
    "Siahaya", "Sihombing", "Sikumbang", "Simanjuntak", "Sinaga", "Siregar",
    "Sitompul", "Sitorus", "Soplanit", "Soputan", "Suherman", "Suryanto",
    "Susanto", "Sutanto", "Sutedjo", "Sumendap", "Tanjung", "Tarigan",
    "Thahir", "Thamrin", "Tirtosudiro", "Tjahjadi", "Tuhumury", "Tumbel",
    "Umami", "Utama", "Waita", "Wantania", "Warouw", "Waskita", "Wenas",
    "Wibisono", "Wibowo", "Wijaya", "Wongsonegoro", "Wowor", "Yudhistira",
    "Yulianto", "Yusuf", "Zainuddin", "Zulkarnain",
]

# 2000 nama unik, dibangkitkan deterministik dari pool di atas.
def _build_name_pool(seed: int = 20261112) -> list:
    rng = random.Random(seed)
    pool = []
    seen = set()
    for gender, firsts in (("Laki-laki", MALE_FIRST), ("Perempuan", FEMALE_FIRST)):
        combos = [(first, last) for first in firsts for last in SURNAMES]
        rng.shuffle(combos)
        added = 0
        for first, last in combos:
            name = f"{first} {last}"
            if name in seen:
                continue
            seen.add(name)
            pool.append((name, gender))
            added += 1
            if added == 1000:
                break
    return pool


NAME_POOL = _build_name_pool()

# ---------------------------------------------------------------------------
# Wilayah
# ---------------------------------------------------------------------------

# (kota, provinsi, kode NIK 4 digit, kode pos)
CITIES = [
    ("Banda Aceh", "Aceh", "1171", "23111"),
    ("Lhokseumawe", "Aceh", "1174", "24351"),
    ("Medan", "Sumatera Utara", "1275", "20111"),
    ("Binjai", "Sumatera Utara", "1276", "20711"),
    ("Pematangsiantar", "Sumatera Utara", "1272", "21111"),
    ("Padang", "Sumatera Barat", "1371", "25111"),
    ("Bukittinggi", "Sumatera Barat", "1375", "26111"),
    ("Pekanbaru", "Riau", "1471", "28111"),
    ("Dumai", "Riau", "1472", "28811"),
    ("Jambi", "Jambi", "1571", "36111"),
    ("Palembang", "Sumatera Selatan", "1671", "30111"),
    ("Lubuklinggau", "Sumatera Selatan", "1673", "31611"),
    ("Bengkulu", "Bengkulu", "1771", "38111"),
    ("Bandar Lampung", "Lampung", "1871", "35111"),
    ("Metro", "Lampung", "1872", "34111"),
    ("Pangkalpinang", "Kepulauan Bangka Belitung", "1971", "33111"),
    ("Batam", "Kepulauan Riau", "2171", "29411"),
    ("Tanjungpinang", "Kepulauan Riau", "2172", "29111"),
    ("Jakarta Pusat", "DKI Jakarta", "3171", "10110"),
    ("Jakarta Selatan", "DKI Jakarta", "3174", "12110"),
    ("Jakarta Barat", "DKI Jakarta", "3173", "11110"),
    ("Jakarta Timur", "DKI Jakarta", "3175", "13110"),
    ("Jakarta Utara", "DKI Jakarta", "3172", "14110"),
    ("Bogor", "Jawa Barat", "3271", "16111"),
    ("Depok", "Jawa Barat", "3276", "16411"),
    ("Bekasi", "Jawa Barat", "3275", "17111"),
    ("Bandung", "Jawa Barat", "3273", "40111"),
    ("Cimahi", "Jawa Barat", "3277", "40511"),
    ("Sukabumi", "Jawa Barat", "3272", "43111"),
    ("Tasikmalaya", "Jawa Barat", "3278", "46111"),
    ("Cirebon", "Jawa Barat", "3274", "45111"),
    ("Semarang", "Jawa Tengah", "3374", "50111"),
    ("Surakarta", "Jawa Tengah", "3372", "57111"),
    ("Magelang", "Jawa Tengah", "3371", "56111"),
    ("Salatiga", "Jawa Tengah", "3373", "50711"),
    ("Pekalongan", "Jawa Tengah", "3375", "51111"),
    ("Tegal", "Jawa Tengah", "3376", "52111"),
    ("Yogyakarta", "DI Yogyakarta", "3471", "55111"),
    ("Sleman", "DI Yogyakarta", "3404", "55511"),
    ("Bantul", "DI Yogyakarta", "3402", "55711"),
    ("Surabaya", "Jawa Timur", "3578", "60111"),
    ("Malang", "Jawa Timur", "3573", "65111"),
    ("Kediri", "Jawa Timur", "3571", "64111"),
    ("Madiun", "Jawa Timur", "3577", "63111"),
    ("Mojokerto", "Jawa Timur", "3576", "61311"),
    ("Pasuruan", "Jawa Timur", "3575", "67111"),
    ("Probolinggo", "Jawa Timur", "3574", "67211"),
    ("Banyuwangi", "Jawa Timur", "3510", "68411"),
    ("Jember", "Jawa Timur", "3509", "68111"),
    ("Serang", "Banten", "3673", "42111"),
    ("Tangerang", "Banten", "3671", "15111"),
    ("Tangerang Selatan", "Banten", "3674", "15411"),
    ("Cilegon", "Banten", "3672", "42411"),
    ("Denpasar", "Bali", "5171", "80111"),
    ("Singaraja", "Bali", "5108", "81111"),
    ("Mataram", "Nusa Tenggara Barat", "5271", "83111"),
    ("Bima", "Nusa Tenggara Barat", "5272", "84111"),
    ("Kupang", "Nusa Tenggara Timur", "5371", "85111"),
    ("Maumere", "Nusa Tenggara Timur", "5306", "86111"),
    ("Pontianak", "Kalimantan Barat", "6171", "78111"),
    ("Singkawang", "Kalimantan Barat", "6172", "79111"),
    ("Palangka Raya", "Kalimantan Tengah", "6271", "73111"),
    ("Banjarmasin", "Kalimantan Selatan", "6371", "70111"),
    ("Banjarbaru", "Kalimantan Selatan", "6372", "70711"),
    ("Samarinda", "Kalimantan Timur", "6471", "75111"),
    ("Balikpapan", "Kalimantan Timur", "6474", "76111"),
    ("Bontang", "Kalimantan Timur", "6473", "75311"),
    ("Tarakan", "Kalimantan Utara", "6571", "77111"),
    ("Manado", "Sulawesi Utara", "7171", "95111"),
    ("Bitung", "Sulawesi Utara", "7172", "95511"),
    ("Palu", "Sulawesi Tengah", "7271", "94111"),
    ("Makassar", "Sulawesi Selatan", "7371", "90111"),
    ("Parepare", "Sulawesi Selatan", "7372", "91111"),
    ("Palopo", "Sulawesi Selatan", "7373", "91911"),
    ("Kendari", "Sulawesi Tenggara", "7471", "93111"),
    ("Baubau", "Sulawesi Tenggara", "7472", "93711"),
    ("Gorontalo", "Gorontalo", "7571", "96111"),
    ("Mamuju", "Sulawesi Barat", "7671", "91511"),
    ("Ambon", "Maluku", "8171", "97111"),
    ("Tual", "Maluku", "8172", "97611"),
    ("Ternate", "Maluku Utara", "8271", "97711"),
    ("Tidore Kepulauan", "Maluku Utara", "8272", "97811"),
    ("Jayapura", "Papua", "9171", "99111"),
    ("Manokwari", "Papua Barat", "9202", "98311"),
    ("Sorong", "Papua Barat", "9271", "98411"),
    ("Timika", "Papua", "9404", "99910"),
    ("Merauke", "Papua", "9403", "99611"),
]

STREETS = [
    "Merdeka", "Sudirman", "Diponegoro", "Gatot Subroto", "Ahmad Yani",
    "Pemuda", "Pahlawan", "Veteran", "Kartini", "Cut Nyak Dien",
    "Imam Bonjol", "Pattimura", "Teuku Umar", "Sisingamangaraja",
    "Pangeran Antasari", "Hasanuddin", "Gajah Mada", "Majapahit",
    "Hayam Wuruk", "Malioboro", "Asia Afrika", "Brahmana", "Cihampelas",
    "Dago", "Riau", "Soekarno Hatta", "Pasteur", "Cendrawasih", "Kenanga",
    "Melati", "Mawar", "Anggrek", "Flamboyan", "Kamboja", "Cempaka",
    "Aster", "Dahlia", "Tulip", "Sakura", "Teratai", "Seruni",
    "Wijaya Kusuma", "Kebon Jeruk", "Kemanggisan", "Menteng", "Kuningan",
    "Senayan", "Thamrin", "HR Rasuna Said", "Wahid Hasyim", "Sabang",
    "Bendungan Hilir", "Cikini", "Salemba", "Kramat", "Senen",
    "Jatinegara", "Matraman", "Pramuka", "Sutomo", "Kalimalang",
    "Raya Bogor", "Raya Jakarta", "Raya Serpong", "Gading Serpong",
    "BSD", "Pahlawan Seribu", "Ciledug Raya", "Fatmawati", "Antasari",
    "Ciputat Raya", "Otto Iskandardinata", "Ronggowarsito", "Pasar Baru",
    "Gardujati", "Pasirkoja", "Buah Batu", "Kiaracondong", "Moch Toha",
    "Kopo", "Soreang", "Setiabudi", "Ciumbuleuit", "Surya Sumantri",
    "Djunjunan", "Pajajaran", "Puncak", "Raya Cibubur", "Raya Narogong",
    "Kalibaru", "Tipar", "Cakung", "Pulo Gebang", "Raya Bekasi",
    "Raya Hankam", "Jatiwaringin", "Jati Makmur", "Tebet Raya",
    "Kapten Tendean", "Wolter Monginsidi", "Panglima Polim", "Radio Dalam",
    "Cipete Raya", "Lebak Bulus", "Tanjung Barat", "Margonda", "Juanda",
    "Siliwangi", "Gunung Sahari", "Bangka", "Blimbing", "Kayu Manis",
    "Prambanan", "Kaliurang", "Magelang", "Solo", "Wonorejo", "Kertajaya",
    "Dharmahusada", "Manyar", "Kenjeran", "Simpang Dukuh", "Bung Tomo",
]

KELURAHAN = [
    "Sukamaju", "Sukamulya", "Sukajadi", "Sukasari", "Cibaduyut", "Cibuntu",
    "Cigondewah", "Cihaurgeulis", "Cikutra", "Cipaganti", "Cipedes",
    "Ciseureuh", "Ciumbuleuit", "Dago", "Gegerkalong", "Isola", "Lebakgede",
    "Pasteur", "Sarijadi", "Setiabudi", "Sukarasa", "Sukawarna", "Babakan",
    "Braga", "Kebon Jeruk", "Karet", "Kuningan Barat", "Menteng",
    "Pegangsaan", "Cikini", "Gondangdia", "Kebon Sirih", "Senen", "Kwitang",
    "Kramat", "Kenari", "Paseban", "Jati", "Rawamangun", "Jatinegara",
    "Cipinang", "Penggilingan", "Duren Sawit", "Pondok Kelapa", "Cakung",
    "Kalibaru", "Pulogadung", "Kayu Putih", "Tebet Barat", "Tebet Timur",
    "Bukit Duri", "Manggarai", "Pasar Minggu", "Pejaten", "Cilandak",
    "Lebak Bulus", "Pondok Pinang", "Bintaro", "Pesanggrahan", "Ulujami",
    "Petukangan", "Grogol", "Jelambar", "Tanjung Duren", "Duri Kepa",
    "Kembangan", "Meruya", "Srengseng", "Cengkareng", "Kapuk", "Kalideres",
    "Penjaringan", "Pluit", "Ancol", "Sunter", "Kelapa Gading", "Cilincing",
    "Marunda", "Tanjung Priok", "Koja", "Semper", "Rawa Badak",
]

KECAMATAN = [
    "Coblong", "Sukajadi", "Cicendo", "Andir", "Astanaanyar", "Bandung Wetan",
    "Lengkong", "Sumur Bandung", "Cibeunying", "Cidadap", "Sukasari",
    "Antapani", "Arcamanik", "Buahbatu", "Kiaracondong", "Ujungberung",
    "Cibiru", "Gedebage", "Rancasari", "Regol", "Batununggal", "Cinambo",
    "Mandalajati", "Gambir", "Menteng", "Tanah Abang", "Setiabudi", "Tebet",
    "Pancoran", "Mampang Prapatan", "Kebayoran Baru", "Kebayoran Lama",
    "Cilandak", "Jagakarsa", "Pasar Minggu", "Pesanggrahan", "Kembangan",
    "Kebon Jeruk", "Grogol Petamburan", "Palmerah", "Cengkareng",
    "Kalideres", "Penjaringan", "Pademangan", "Tanjung Priok", "Koja",
    "Kelapa Gading", "Cilincing", "Matraman", "Jatinegara", "Duren Sawit",
    "Cakung", "Pulogadung", "Kramat Jati", "Makasar", "Ciracas",
    "Pasar Rebo", "Cipayung", "Gubeng", "Tegalsari", "Genteng",
    "Tambaksari", "Sukolilo", "Rungkut", "Wonokromo", "Wiyung",
    "Karang Pilang", "Sawahan", "Bubutan", "Simokerto", "Semampir",
    "Pabean Cantian", "Kenjeran", "Bulak", "Mulyorejo",
]

# ---------------------------------------------------------------------------
# Pekerjaan dan organisasi
# ---------------------------------------------------------------------------

JOBS = [
    "Karyawan swasta", "Guru", "Dosen", "Mahasiswa", "Pelajar", "Wirausaha",
    "Pegawai negeri sipil", "Karyawan BUMN", "Freelancer",
    "Ibu rumah tangga", "Dokter", "Perawat", "Bidan", "Apoteker", "Petani",
    "Nelayan", "Pedagang", "Buruh", "Sopir", "Montir", "Barista", "Chef",
    "Desainer grafis", "Programmer", "Data analyst", "Digital marketer",
    "Akuntan", "Konsultan", "Notaris", "Pengacara", "Polisi", "Tentara",
    "Pemadam kebakaran", "Pramugari", "Pilot", "Arsitek", "Insinyur sipil",
    "Teknisi", "Tukang kayu", "Tukang listrik", "Penjahit", "Fotografer",
    "Videografer", "Penulis", "Editor", "Jurnalis", "Content creator",
    "Social media specialist", "HRD", "Admin", "Customer service", "Sales",
    "Marketing", "Staff produksi", "Quality control", "Staff logistik",
    "Kurir", "Security", "Cleaning service", "Resepsionis", "Sekretaris",
    "Bendahara", "Kasir", "Teller", "Analis kredit", "Auditor", "Konsultan pajak",
    "Aktuaris", "Statistikawan", "Peneliti", "Laboran", "Pustakawan",
    "Guru les", "Tutor", "Terapis", "Psikolog", "Fisioterapis", "Ahli gizi",
    "Radiografer", "Analis laboratorium", "Dokter gigi", "Dokter hewan",
    "Pengusaha", "Investor", "Surveyor", "Estimator", "Drafter",
    "Operator mesin", "Welder", "Operator forklift", "Ojek online",
    "Pengemudi", "Agen properti", "Agen asuransi", "Pialang",
    "Event organizer", "Wedding organizer", "Tour guide", "Penerjemah",
    "Interpreter", "Guru musik", "Pelatih", "Atlet", "Seniman", "Musisi",
    "Penyanyi", "Aktor", "Model", "Perancang busana", "Fotografer produk",
    "Konsultan SDM", "Analis sistem", "Network engineer", "DevOps engineer",
    "QA engineer", "Product manager", "Project manager", "Business analyst",
]

TITLES = [
    "Staff", "Senior Staff", "Supervisor", "Assistant Manager", "Manager",
    "Senior Manager", "General Manager", "Direktur", "Komisaris",
    "Kepala Divisi", "Kepala Bagian", "Kepala Seksi", "Kepala Unit",
    "Koordinator", "Leader", "Team Lead", "Analyst", "Specialist",
    "Konsultan", "Advisor", "Sekretaris", "Bendahara", "Ketua",
    "Wakil Ketua", "Anggota", "Operator", "Teknisi", "Admin", "Magang",
    "Freelancer",
]

COMPANIES = [
    "PT Sinar Nusantara", "PT Bumi Sejahtera", "PT Karya Mandiri",
    "PT Cahaya Abadi", "PT Mitra Bersama", "PT Sentosa Jaya",
    "PT Prima Kencana", "PT Tunas Harapan", "PT Global Sentosa",
    "PT Digital Nusantara", "PT Teknologi Cerdas", "PT Data Prima",
    "PT Solusi Mandiri", "PT Reka Cipta", "PT Inovasi Bersama",
    "PT Kreatif Media", "PT Media Cipta", "PT Visi Global",
    "PT Energi Baru", "PT Sumber Makmur", "PT Pangan Sejahtera",
    "PT Agro Lestari", "PT Bahari Jaya", "PT Logistik Nusantara",
    "PT Trans Cepat", "PT Properti Indah", "PT Griya Asri",
    "PT Konstruksi Utama", "PT Bangun Persada", "PT Teknik Sejahtera",
    "CV Karya Mandiri", "CV Sinar Jaya", "CV Berkah Abadi",
    "CV Mulia Sentosa", "CV Tunas Muda", "CV Cipta Karya",
    "CV Reka Media", "CV Digital Kreatif", "CV Solusi Tepat",
    "CV Mitra Usaha", "UD Sumber Rejeki", "UD Makmur Jaya",
    "UD Berkah Lancar", "UD Sari Alam", "UD Tani Makmur",
    "UD Niaga Sentosa", "UD Bumi Asri", "UD Karya Bakti",
    "PT Andalan Prima", "PT Cipta Solusi", "PT Nusa Teknologi",
    "PT Integra Data", "PT Mega Sarana", "PT Anugerah Abadi",
    "PT Wirausaha Muda", "PT Karya Utama", "PT Sejahtera Bersama",
    "PT Mandiri Perkasa", "PT Satu Visi", "PT Langkah Maju",
    "PT Cakrawala Nusantara", "PT Samudra Biru", "PT Rimba Lestari",
    "PT Cahaya Timur", "PT Bintang Utara", "PT Graha Sentral",
    "PT Prima Medika", "PT Sehat Bersama", "PT Edukasi Cerdas",
    "PT Kreasi Digital", "PT Media Inovasi", "PT Jasa Utama",
]

AGENCIES = [
    "Dinas Pendidikan", "Dinas Kesehatan", "Dinas Pekerjaan Umum",
    "Dinas Sosial", "Dinas Perhubungan", "Dinas Lingkungan Hidup",
    "Dinas Kependudukan dan Pencatatan Sipil", "Dinas Tenaga Kerja",
    "Kementerian Keuangan", "Kementerian Pendidikan",
    "Kementerian Kesehatan", "Kementerian Dalam Negeri",
    "Badan Pusat Statistik", "Badan Perencanaan Pembangunan Daerah",
    "Kantor Kecamatan", "Kantor Kelurahan", "Pemerintah Kota",
    "Pemerintah Kabupaten", "Sekretariat Daerah", "Inspektorat Daerah",
]

UNIVERSITIES = [
    "Universitas Indonesia", "Institut Teknologi Bandung",
    "Universitas Gadjah Mada", "Institut Teknologi Sepuluh Nopember",
    "Universitas Airlangga", "Universitas Brawijaya",
    "Universitas Diponegoro", "Universitas Padjadjaran",
    "Universitas Hasanuddin", "Universitas Andalas",
    "Universitas Syiah Kuala", "Universitas Sumatera Utara",
    "Universitas Riau", "Universitas Sriwijaya", "Universitas Lampung",
    "Universitas Jambi", "Universitas Bengkulu", "Universitas Tanjungpura",
    "Universitas Palangka Raya", "Universitas Lambung Mangkurat",
    "Universitas Mulawarman", "Universitas Sam Ratulangi",
    "Universitas Tadulako", "Universitas Halu Oleo",
    "Universitas Negeri Gorontalo", "Universitas Udayana",
    "Universitas Mataram", "Universitas Nusa Cendana",
    "Universitas Pattimura", "Universitas Cenderawasih",
    "Universitas Negeri Yogyakarta", "Universitas Sebelas Maret",
    "Universitas Negeri Semarang", "Universitas Negeri Surabaya",
    "Universitas Negeri Malang", "Universitas Pendidikan Indonesia",
    "Universitas Islam Negeri Sunan Kalijaga",
    "Universitas Islam Indonesia", "Universitas Muhammadiyah Yogyakarta",
    "Universitas Bina Nusantara", "Universitas Telkom",
    "Universitas Multimedia Nusantara", "Universitas Prasetiya Mulya",
    "Universitas Pelita Harapan", "Universitas Tarumanagara",
    "Universitas Katolik Parahyangan", "Universitas Atma Jaya",
    "Universitas Sanata Dharma", "Universitas Kristen Satya Wacana",
    "Universitas Ahmad Dahlan", "Universitas Islam Negeri Jakarta",
    "Universitas Negeri Jakarta", "Universitas Trisakti",
    "Universitas Mercu Buana", "Universitas Gunadarma",
    "Universitas Bakrie", "Universitas Pertamina",
    "Institut Pertanian Bogor", "Institut Teknologi Del",
    "Politeknik Negeri Jakarta", "Politeknik Negeri Bandung",
    "Politeknik Elektronika Negeri Surabaya", "Universitas Terbuka",
]

MAJORS = [
    "Teknik Informatika", "Sistem Informasi", "Ilmu Komputer",
    "Teknik Elektro", "Teknik Mesin", "Teknik Sipil", "Teknik Industri",
    "Arsitektur", "Desain Komunikasi Visual", "Manajemen", "Akuntansi",
    "Ilmu Ekonomi", "Ekonomi Pembangunan", "Bisnis Digital",
    "Administrasi Bisnis", "Ilmu Komunikasi", "Jurnalistik",
    "Hubungan Internasional", "Ilmu Hukum", "Psikologi", "Sosiologi",
    "Antropologi", "Ilmu Politik", "Administrasi Publik",
    "Pendidikan Guru Sekolah Dasar", "Pendidikan Bahasa Indonesia",
    "Pendidikan Bahasa Inggris", "Sastra Indonesia", "Sastra Inggris",
    "Sejarah", "Filsafat", "Matematika", "Statistika", "Fisika", "Kimia",
    "Biologi", "Kedokteran", "Kedokteran Gigi", "Keperawatan", "Kebidanan",
    "Farmasi", "Kesehatan Masyarakat", "Gizi", "Teknologi Pangan",
    "Agroteknologi", "Peternakan", "Kehutanan", "Perikanan", "Kelautan",
    "Geografi", "Geologi", "Meteorologi", "Astronomi", "Teknik Kimia",
    "Teknik Fisika", "Teknik Lingkungan", "Teknik Pertambangan",
    "Teknik Perminyakan", "Teknik Geodesi",
    "Perencanaan Wilayah dan Kota", "Pariwisata", "Tata Boga",
    "Seni Musik", "Seni Rupa", "Desain Produk",
]

SCHOOL_PREFIXES = [
    "SMA Negeri 1", "SMA Negeri 2", "SMA Negeri 3", "SMA Swasta",
    "SMK Negeri 1", "SMK Negeri 2", "MA Negeri 1",
]

EVENTS = [
    "Seminar Nasional", "Workshop UI/UX", "Pelatihan Kepemimpinan",
    "Lomba Karya Tulis", "Festival Budaya", "Webinar Teknologi",
    "Kelas Online", "Bootcamp Data", "Hackathon", "Konferensi Tahunan",
    "Pelatihan Publik Speaking", "Seminar Karier", "Pameran Produk",
    "Bazar UMKM", "Kegiatan Sosial", "Bakti Desa", "Studi Banding",
    "Pelatihan Kewirausahaan", "Lomba Desain", "Kompetisi Bisnis",
]

BANKS = [
    "BCA", "BRI", "BNI", "Mandiri", "BSI", "CIMB Niaga", "Permata",
    "Danamon", "BTN", "OCBC", "Panin", "Mega", "Bukopin", "Jago",
    "SeaBank", "Blu", "Jenius", "Allo", "Neo", "Sinarmas",
]

EMAIL_DOMAINS = [
    "gmail.com", "yahoo.com", "outlook.com", "hotmail.com", "icloud.com",
    "proton.me", "mail.com",
]

PHONE_PREFIXES = [
    "0811", "0812", "0813", "0821", "0822", "0823", "0851", "0852",
    "0853", "0855", "0856", "0857", "0858", "0814", "0815", "0816",
    "0817", "0818", "0819", "0895", "0896", "0897", "0898", "0899",
]

RELIGIONS = (
    ["Islam"] * 7
    + ["Kristen"] * 2
    + ["Katolik"]
    + ["Hindu", "Buddha", "Konghucu"]
)

BLOOD_TYPES = ["A", "B", "AB", "O", "O", "A"]
FEMALE_ONLY_JOBS = {"Ibu rumah tangga", "Bidan", "Pramugari"}
MARITAL_STATUSES = ["Belum menikah", "Belum menikah", "Menikah", "Cerai"]
EDUCATION_LEVELS = ["SMA/SMK", "D3", "S1", "S1", "S1", "S2"]
SCHOOL_CLASSES = [
    "X IPA 1", "X IPA 2", "X IPS 1", "XI IPA 1", "XI IPA 2", "XI IPS 1",
    "XII IPA 1", "XII IPA 2", "XII IPS 1", "XII Bahasa 1",
]

# ---------------------------------------------------------------------------
# Bank kalimat
# ---------------------------------------------------------------------------

GENERAL_SENTENCES = [
    "Pelayanannya sudah cukup baik dan mudah digunakan.",
    "Saya merasa informasi yang diberikan jelas dan membantu.",
    "Secara keseluruhan pengalaman saya menyenangkan.",
    "Prosesnya cepat dan tidak membingungkan.",
    "Saya akan merekomendasikan ini kepada teman dan keluarga.",
    "Kualitas yang diberikan sudah sesuai dengan harapan saya.",
    "Masih ada beberapa hal yang bisa ditingkatkan ke depannya.",
    "Saya puas dengan kemudahan akses dan tampilan yang ada.",
    "Informasi yang disampaikan mudah dipahami oleh pengguna baru.",
    "Semoga layanan ini terus ditingkatkan kualitasnya.",
    "Saya menggunakan layanan ini hampir setiap hari.",
    "Tidak ada kendala berarti selama saya menggunakannya.",
    "Saya menilai layanan ini sudah memenuhi kebutuhan saya.",
    "Pengalaman saya sejauh ini positif dan menyenangkan.",
    "Beberapa fitur sangat membantu pekerjaan saya.",
    "Saya berharap kualitasnya tetap terjaga.",
    "Pelayanan yang diberikan ramah dan responsif.",
    "Prosesnya sederhana dan tidak memakan waktu lama.",
    "Saya merasa nyaman menggunakan layanan ini.",
    "Secara pribadi, saya cukup terbantu dengan layanan ini.",
]

SUGGESTION_SENTENCES = [
    "Sebaiknya tampilan dibuat lebih sederhana agar mudah dipahami.",
    "Saya menyarankan agar informasi penting ditampilkan lebih jelas.",
    "Akan lebih baik jika prosesnya bisa dilakukan dalam satu halaman.",
    "Sebaiknya ditambahkan panduan singkat untuk pengguna baru.",
    "Saya menyarankan adanya fitur pencarian agar lebih cepat.",
    "Akan lebih membantu jika tersedia notifikasi untuk setiap perubahan.",
    "Sebaiknya akses melalui ponsel lebih dioptimalkan lagi.",
    "Saya menyarankan agar istilah teknis diganti dengan bahasa yang lebih mudah.",
    "Akan lebih baik jika tersedia opsi untuk menyimpan data sementara.",
    "Sebaiknya waktu proses dipersingkat lagi.",
    "Saya menyarankan penambahan fitur riwayat aktivitas.",
    "Akan lebih nyaman jika warna dan tata letak dibuat lebih konsisten.",
    "Sebaiknya disediakan kanal bantuan yang mudah dihubungi.",
    "Saya menyarankan evaluasi berkala terhadap kualitas layanan.",
    "Akan lebih baik jika ada penjelasan di setiap langkah pengisian.",
    "Sebaiknya ukuran teks dan tombol diperbesar agar mudah dibaca.",
    "Saya menyarankan agar data pengguna dijaga dengan lebih baik.",
    "Akan lebih efisien jika pengisian bisa disimpan otomatis.",
    "Sebaiknya ditambahkan contoh pengisian pada setiap bagian.",
    "Saya menyarankan agar proses verifikasi dibuat lebih cepat.",
]

COMPLAINT_SENTENCES = [
    "Saya kurang puas karena prosesnya terasa lambat.",
    "Informasi yang diberikan masih belum jelas bagi saya.",
    "Tampilan cukup membingungkan saat pertama kali digunakan.",
    "Saya mengalami kendala saat mengisi beberapa bagian.",
    "Beberapa tombol sulit ditemukan pada layar ponsel.",
    "Proses yang terlalu panjang membuat saya cepat lelah.",
    "Saya berharap kendala teknis seperti ini tidak terulang.",
    "Petunjuk yang ada masih terlalu sedikit.",
    "Saya sempat gagal beberapa kali sebelum berhasil.",
    "Waktu tunggu yang dibutuhkan terasa terlalu lama.",
    "Beberapa istilah sulit dipahami oleh pengguna awam.",
    "Saya menilai masih banyak bagian yang perlu diperbaiki.",
    "Pengalaman saya kali ini belum sesuai harapan.",
    "Saya kesulitan menemukan informasi yang saya butuhkan.",
    "Sebaiknya kualitas layanan lebih diperhatikan lagi.",
]

HOPE_SENTENCES = [
    "Saya berharap layanan ini semakin baik ke depannya.",
    "Semoga kecepatan dan kualitasnya terus ditingkatkan.",
    "Saya berharap fitur-fitur baru tetap mudah digunakan.",
    "Semoga informasi yang disampaikan semakin lengkap.",
    "Saya berharap layanan ini dapat diakses oleh semua kalangan.",
    "Semoga kendala teknis dapat segera diperbaiki.",
    "Saya berharap tampilan tetap sederhana meski fiturnya bertambah.",
    "Semoga pelayanan yang ramah dapat dipertahankan.",
    "Saya berharap ada pembaruan secara berkala.",
    "Semoga prosesnya semakin cepat dan efisien.",
    "Saya berharap kualitas data tetap terjaga.",
    "Semoga semakin banyak pengguna yang merasakan manfaatnya.",
    "Saya berharap bantuan pelanggan merespons lebih cepat.",
    "Semoga kerja sama dan komunikasi tetap berjalan baik.",
    "Saya berharap layanan ini berkelanjutan dalam jangka panjang.",
]

REASON_SENTENCES = [
    "Karena layanan ini mudah digunakan dan tidak membingungkan.",
    "Saya memilih ini karena prosesnya cepat dan praktis.",
    "Alasannya sederhana, yaitu sesuai dengan kebutuhan saya.",
    "Karena informasi yang tersedia cukup jelas dan lengkap.",
    "Saya menggunakan layanan ini karena mudah diakses kapan saja.",
    "Karena tampilannya nyaman dilihat dan tidak melelahkan.",
    "Alasan utamanya adalah kualitas yang sudah terbukti baik.",
    "Karena saya mendapatkan pengalaman positif sebelumnya.",
    "Saya memilih layanan ini karena direkomendasikan oleh teman.",
    "Karena proses pendaftaran yang tidak berbelit-belit.",
    "Alasannya karena layanan ini mendukung pekerjaan sehari-hari.",
    "Karena saya ingin mencoba pengalaman yang lebih efisien.",
    "Saya memilihnya karena sesuai dengan anggaran yang tersedia.",
    "Karena respons petugas cukup cepat saat saya bertanya.",
    "Alasan saya karena fiturnya lengkap dan mudah dipahami.",
]

EXPERIENCE_SENTENCES = [
    "Saya sudah menggunakan layanan ini selama beberapa bulan terakhir.",
    "Awalnya saya ragu, tetapi setelah dicoba hasilnya memuaskan.",
    "Saya pernah mengalami kendala, namun segera terbantu oleh petugas.",
    "Pengalaman pertama saya cukup menyenangkan dan tidak rumit.",
    "Saya menggunakan layanan ini bersama rekan kerja setiap hari.",
    "Selama menggunakan, saya belum menemukan masalah berarti.",
    "Saya pernah mencoba layanan serupa, tetapi ini lebih mudah.",
    "Prosesnya berjalan lancar sejak awal hingga selesai.",
    "Saya terbantu karena informasi yang disediakan lengkap.",
    "Pengalaman saya cukup baik meski ada beberapa kekurangan kecil.",
    "Saya mulai menggunakan layanan ini atas rekomendasi keluarga.",
    "Sejauh ini saya merasa nyaman dengan tampilan dan alurnya.",
    "Saya biasanya mengakses layanan ini melalui ponsel.",
    "Saya sempat membutuhkan bantuan, dan prosesnya cukup cepat.",
    "Kesan pertama saya positif karena pelayanannya ramah.",
]
