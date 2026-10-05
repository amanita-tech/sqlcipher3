"""Сверка собранного колеса sqlcipher3 (копия amanita-tech): внутри то, что заявлено.

Запуск: python amanita/proverit_koleso.py <файл колеса.whl>
Колесо уже должно быть установлено в этот Python. Что сверяется:
- версия SQLCipher в базе (PRAGMA cipher_version) равна метке в имени колеса («+sqlcipher4.19.0»);
- провайдер криптографии — OpenSSL, и его версия равна той, что закреплена в conanfile.py;
- база с ключом на диске не открывается без ключа, а канарейка не видна в файле.
Любое расхождение — код возврата 1: сборка не считается зелёной.
"""

from __future__ import annotations

import re
import sys
import tempfile
from pathlib import Path

import sqlcipher3.dbapi2 as sqlcipher

KOREN = Path(__file__).resolve().parent.parent
KANAREJKA = "Канарейка-проверки-колеса"


def ozhidaemoe(put_kolesa: str) -> tuple[str, str]:
    metka = re.search(r"\+sqlcipher(\d+\.\d+\.\d+)", Path(put_kolesa).name)
    if not metka:
        sys.exit(f"В имени колеса нет метки «+sqlcipherX.Y.Z»: {put_kolesa}")
    openssl = re.search(r"openssl/(\d+\.\d+\.\d+)", (KOREN / "conanfile.py").read_text(encoding="utf-8"))
    if not openssl:
        sys.exit("В conanfile.py не найдена версия openssl")
    return metka[1], openssl[1]


def odno(soedinenie, zapros: str) -> str:
    return str(soedinenie.execute(zapros).fetchone()[0])


def main() -> int:
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    sqlcipher_zhdem, openssl_zhdem = ozhidaemoe(sys.argv[1])
    oshibki: list[str] = []

    with tempfile.TemporaryDirectory() as papka:
        put = Path(papka) / "proverka.db"
        klyuch = "x'" + "ab" * 32 + "'"
        s = sqlcipher.connect(str(put))
        s.execute(f'PRAGMA key = "{klyuch}"')
        versiya = odno(s, "PRAGMA cipher_version")
        provajder = odno(s, "PRAGMA cipher_provider")
        versiya_provajdera = odno(s, "PRAGMA cipher_provider_version")
        print(f"cipher_version = {versiya}")
        print(f"cipher_provider = {provajder}")
        print(f"cipher_provider_version = {versiya_provajdera}")
        print(f"sqlite_version = {sqlcipher.sqlite_version}")

        if versiya.split()[0] != sqlcipher_zhdem:
            oshibki.append(f"SQLCipher в колесе {versiya}, а в метке {sqlcipher_zhdem}")
        if provajder.lower() != "openssl":
            oshibki.append(f"провайдер криптографии {provajder}, ожидался openssl")
        openssl = re.match(r"OpenSSL (\d+\.\d+\.\d+)", versiya_provajdera)
        if not openssl or openssl[1] != openssl_zhdem:
            oshibki.append(f"OpenSSL в колесе «{versiya_provajdera}», в conanfile.py {openssl_zhdem}")

        s.execute("CREATE TABLE t (x TEXT)")
        s.execute("INSERT INTO t VALUES (?)", (KANAREJKA,))
        s.commit()
        s.close()
        bajty = put.read_bytes()
        if bajty.startswith(b"SQLite format 3"):
            oshibki.append("файл базы с ключом начинается с открытого заголовка SQLite")
        if KANAREJKA.encode("utf-8") in bajty:
            oshibki.append("канарейка видна в файле базы с ключом")
        bez_klyucha = sqlcipher.connect(str(put))
        try:
            bez_klyucha.execute("SELECT count(*) FROM sqlite_master").fetchone()
            oshibki.append("база с ключом открылась без ключа")
        except sqlcipher.DatabaseError:
            pass
        finally:
            bez_klyucha.close()

    if oshibki:
        print("СВЕРКА НЕ ПРОШЛА:", *oshibki, sep="\n  - ")
        return 1
    print(f"Сверка прошла: SQLCipher {sqlcipher_zhdem}, OpenSSL {openssl_zhdem}, база с ключом нечитаема без ключа")
    return 0


if __name__ == "__main__":
    sys.exit(main())
