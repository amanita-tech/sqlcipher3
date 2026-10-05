# Копия sqlcipher3 для личного ассистента (amanita-tech)

Копия [coleifer/sqlcipher3](https://github.com/coleifer/sqlcipher3) с ядром **SQLCipher 4.19.0**
(SQLite 3.53.4) и **OpenSSL 3.6.5**, собранная в одно колесо — **Windows AMD64, Python 3.14**.
Нужна личному ассистенту (репозиторий `amanita-tech/lichnyy-assistent`, ADR-2, раздел 8):
готовые колёса автора отстают от SQLCipher на семь выпусков. Исходник и сценарий сборки — автора;
здесь только то, что перечислено ниже.

## Чем копия отличается от исходной

| Файл | Что изменено |
|---|---|
| `vendor/sqlite3.c`, `vendor/sqlite3.h` | пересобраны из тега `v4.19.0` репозитория `sqlcipher/sqlcipher` сценарием автора `vendor/update` (запуск — `.github/workflows/obnovit-sqlcipher.yaml`) |
| `setup.py`, `pyproject.toml` | к версии добавлена метка ядра: `0.6.3+sqlcipher4.19.0` |
| `conanfile.py` | `openssl/3.6.5` вместо `3.6.0` |
| `.github/workflows/wheels.yaml` | только Windows AMD64 cp314; вместо публикации в PyPI — сверка колеса и релиз копии |
| `.github/workflows/obnovit-sqlcipher.yaml` | новый: поднятие версии SQLCipher |
| `.github/workflows/sledit-za-vypuskami.yaml` | новый: слежение за выпусками SQLCipher и OpenSSL |
| `amanita/proverit_koleso.py` | новый: сверка готового колеса |
| `SBORKA-AMANITA.md` | этот файл |

Код расширения (`src/`, `sqlcipher3/`, `tests/`) не менялся.

## Как собирается колесо

Сборка идёт по **тегу** вида `<версия обвязки>-sqlcipher<версия ядра>`, например
`0.6.3-sqlcipher4.19.0`. Сценарий `wheels.yaml` (cibuildwheel) делает три шага:

1. **wheels** — собирает колесо `cp314-win_amd64`; OpenSSL приходит из Conan Center и собирается
   из исходников под MSVC статически (внутри колеса, отдельных DLL нет); тесты автора
   (`python tests/`) гоняются на готовом колесе;
2. **proverka** — ставит колесо в чистый Python 3.14 и запускает `amanita/proverit_koleso.py`:
   `PRAGMA cipher_version` равен метке в имени колеса, провайдер — `openssl`, его версия равна
   закреплённой в `conanfile.py`, файл базы с ключом нечитаем без ключа;
3. **vypusk** (только по тегу) — считает `SHA256SUMS`, выпускает подтверждение происхождения
   (attestation) и создаёт релиз с колесом.

Без тега сборку можно запустить вручную (Actions → Build wheels → Run workflow): колесо останется
артефактом запуска, релиз не создаётся.

## Где взять колесо и как сверить

Адрес вида
`https://github.com/amanita-tech/sqlcipher3/releases/download/<тег>/sqlcipher3-<версия>-cp314-cp314-win_amd64.whl`.
Сверка:

- сумма из `SHA256SUMS` релиза совпадает с `Get-FileHash -Algorithm SHA256 <колесо>`;
- происхождение: `gh attestation verify <колесо> --repo amanita-tech/sqlcipher3`;
- главное доверие — сумма, закреплённая в репозитории ассистента (`zavisimosti.txt`): pip сверяет
  её сам при установке.

## Поднять версию SQLCipher

Поводом служит задача `Вышла новая версия SQLCipher: X.Y.Z`, которую открывает слежение
(см. ниже). Дальше:

1. **Пересобрать исходник.** Actions → «Обновить SQLCipher» → Run workflow → `X.Y.Z`. Сценарий
   клонирует `sqlcipher/sqlcipher` тег `vX.Y.Z`, запускает `vendor/update`, сверяет, что в
   `vendor/sqlite3.c` действительно `CIPHER_VERSION_NUMBER X.Y.Z`, переписывает метку версии
   в `setup.py` и `pyproject.toml` и кладёт всё в ветку `sqlcipher-X.Y.Z`. Порядок — не
   менять: сценарий ничего не пишет в master сам.
2. **Просмотреть.** Сравнить ветку с master: правятся только `vendor/` и две строки версии.
   Прочитать `CHANGELOG.md` SQLCipher за пропущенные выпуски: нет ли изменений формата базы,
   значений по умолчанию, переименованных PRAGMA.
3. **Влить в master** (`git merge --ff-only origin/sqlcipher-X.Y.Z`).
4. **Поставить тег** `<версия обвязки>-sqlcipherX.Y.Z` и отправить его:
   `git tag 0.6.3-sqlcipherX.Y.Z && git push origin 0.6.3-sqlcipherX.Y.Z`. Сборка запустится сама
   (около 15 минут: OpenSSL собирается из исходников). Красная сборка — релиза нет, тег можно
   удалить и поставить после правки.
5. **Закрепить в ассистенте.** В релизе взять адрес колеса и сумму из `SHA256SUMS`; в репозитории
   ассистента поправить строку `sqlcipher3 @ …#sha256=…` в `zavisimosti.txt` и `pyproject.toml`,
   ожидаемую версию в `tests/test_sqlcipher_koleso.py`; поставить колесо, прогнать весь pytest и
   `docs/adr/0002-proby/proba_sqlcipher.py`; записать итог в ADR-2.
6. Закрыть задачу из слежения ссылкой на тег.

Если вышел новый **мажорный** выпуск SQLCipher (первая цифра), формат базы мог измениться:
сначала проба открытия копии данных, потом всё остальное.

## Поднять версию OpenSSL

Поводом служит задача `Вышел новый OpenSSL: X.Y.Z` (открывается, только когда пакет уже есть в
Conan Center). Сборка берёт OpenSSL из Conan Center, поэтому:

1. В `conanfile.py` заменить `openssl/A.B.C` на `openssl/X.Y.Z` (ветка — только 3.6, пока решением
   не сменена; смена ветки — решение оператора, его фиксирует ADR-2).
2. Влить в master, поставить тег вида `0.6.3-sqlcipher4.19.0-opensslX.Y.Z`. Имя колеса не
   изменится (метка несёт только версию ядра) — отличают его тег в адресе и сумма.
3. Дальше — как с пятого шага выше; ожидаемую версию OpenSSL поправить в тесте ассистента.

**Сроки жизни ветки** (страница политики выпусков OpenSSL, openssl.org/policies/releasestrat.html,
на 05.10.2026): 3.6 поддерживается до 2026-11-01, 4.0 — до 2027-05-14, 3.5 (долгая поддержка) — до
2030-04-08. Ветку 3.6 выбрало решение оператора; до её конца ветку надо сменить его решением.

## Слежение за выпусками

`.github/workflows/sledit-za-vypuskami.yaml` — раз в сутки (05:17 UTC) и по кнопке:

- версия SQLCipher «у копии» берётся из самого `vendor/sqlite3.c`, OpenSSL — из `conanfile.py`;
- последний выпуск SQLCipher — наибольший тег `vX.Y.Z` без `beta`/`rc`; OpenSSL — наибольший
  `openssl-3.6.N`;
- вышло новое — открывается задача с меткой `sqlcipher-vypusk` и порядком действий; по одной
  версии — одна задача, повторно не открывается; про OpenSSL — только когда пакет есть в Conan
  Center;
- **пробный запуск:** Actions → «Следить за выпусками» → Run workflow, в поле «известная версия
  SQLCipher» ввести старую (например `4.18.0`) — слежение сделает вид, что у копии она старая, и
  откроет задачу; пробную задачу закрыть.

**Ограничение GitHub:** расписание в публичном репозитории отключается после 60 дней без изменений
в нём. Слежение каждый запуск повторно включает само себя через API (это сбрасывает счётчик),
но если GitHub всё же отключил расписание — Actions → «Следить за выпусками» → Enable workflow.

## Подтянуть изменения автора

```
git remote add upstream https://github.com/coleifer/sqlcipher3.git   # один раз
git fetch upstream --tags
git merge upstream/master
```

Конфликты возможны только в файлах из таблицы выше (`setup.py`, `pyproject.toml`, `conanfile.py`,
`wheels.yaml`, `vendor/`): при слиянии `vendor/` брать нашу сторону, а потом пересобирать
сценарием «Обновить SQLCipher».
