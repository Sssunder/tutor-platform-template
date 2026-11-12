# Changelog — tutor-platform-template

## 2026-11-12 — Fix invisible sticky-bar toggle text in light themes (pushed)
- Same scoped `#teacherStickyBar #toggleViewBtn` override as maria-math so the dark admin bar's toggle stays translucent-white + white text in every theme (universal `[class*="bg-white"]` binding no longer makes it white-on-white).
- `python verify.py` → **PASS**. Pushed to origin/master. `dist/index.html` not regenerated.

## 2026-11-12 — Obvious «Пройти обучение заново» button + post-skip hint baked into template.html
- Faint «Экскурсия» pill → prominent white «Пройти обучение заново» in cabinet tab bar; on skip (Пропустить/Esc) a ~6s bottom toast + button pulse point back to it (toast `pointer-events:none`), so an accidental skip is recoverable.
- `python verify.py` → **PASS**. `dist/index.html` not regenerated.

## 2026-11-12 — Plain-language connect guide + VPN links baked into template.html
- Telegram card self-explains for owners «с компьютером на вы»: persistent «Как подключить (2 минуты)» list (VPN → «Подключить уведомления» → «Запустить» /start → «Я подписался — обновить статус») + Pavel's VPN referral links (`quattro.app/register?ref=HEmqibBsi5vz1Qz2` / `QuattroVPN_BOT?start=r_HEmqibBsi5vz1Qz2`); slim VPN line when connected. Tour Telegram section now 3 steps.
- `python verify.py` → **PASS** (node --check, forbidden strings, Playwright 1440/360 0 errors 0 overflow). `dist/index.html` not regenerated.

## 2026-11-12 — Universal Telegram booking-notification platform baked into template.html
- Every generated site now ships the shared-bot notification platform: `TG_NOTIFY_URL`, `DEFAULT_SITE_CONFIG.telegram` (bot_username `GojoNotifyBot`), deep-merge in `mergeSiteConfig`, `notifyNewBooking()` after booking success, Telegram connect-card in cabinet Texts tab, `saveTelegramBotUsername`/`setTelegramEnabled`/`refreshTelegramStatus`/`persistTelegramConfig` (inline `admin_save_config` with `activeTeacherPin`). One shared bot → one-click connect for any niche.
- Tour Telegram step switches to the card's tab before spotlighting.
- `python verify.py` → **PASS** (node --check, forbidden strings, Playwright 1440/360 0 errors 0 overflow). `dist/index.html` not regenerated.

## 2026-11-12 — Cabinet mini-tour baked into template.html (onboarding «Экскурсия»)
- Self-contained onboarding tour appended before `</body>` in `template.html`, so every generated tutor site gets it: first cabinet login → spotlight + white card walks the tabs step-by-step in plain language; «Экскурсия» pill in tab bar replays; shown once via `localStorage cabinetTourDone:<path>`. Auto-detects `teacherView`/`masterView` + `data-*-tab` buttons + panel ids; theme-safe, mobile-clamped, Esc/Пропустить/Назад/Дальше.
- Verified on the 3 live sites via `maria-loop/verify_tour.py` (mocked RPC, zero DB writes): 0 overflow 1440/360, 0 console errors, correct step sequence per site. `dist/index.html` not regenerated (build artifact).

## 2026-11-12 — Автопроверки verify.py + check_live_sites.py, заготовка clients/new-client.example.json
- **`verify.py`** (новый): генерация `config.example.json` во временный dist-тест; 0 плейсхолдеров `{{...}}` (сгенерированный файл и `dist/index.html`); `node --check` на 2 inline `<script>` (exit 0); нет `"1234"`/`"service_role"` в `template.html` и `dist/index.html`; Playwright с замоканными RPC Supabase (БД не затрагивается) и раздачей `/assets/*` из `../maria-math/assets` через временный локальный сервер (структура `dist` не меняется): 0 pageerror, 0px overflow, 0 битых картинок на `1440x900` и `360x800`. Запуск `python verify.py` → **PASS, exit 0**.
- **`check_live_sites.py`** (новый): одним запуском 3 живых URL из HANDOFF (`natalia-math`, `maria-math`, `elen-beauty`): HTTP 200, маркеры Constructor v3 (`#cfgDefaultTheme`, `#cfgReviewsChannelUrl`, `#admReviewLivePreview`), 0 ошибок консоли/сети, 0px overflow на `1440x900` и `360x800`. Запуск → **все 3 сайта PASS, exit 0**.
- **`clients/new-client.example.json`** (новый): заготовка конфига нового клиента по `config.schema.json` (тема `theme.default`, контакты вкл. `reviewsChannelUrl`/`avitoUrl`, 3 формата). Проверено: required-поля схемы PASS, `generate.py` с ним → 0 плейсхолдеров.
- Статусы в `natalia-math/CHANGELOG.md` (`a0d0ad0`) и `elena-beauty/CHANGELOG.md` (`76dd4d9`) обновлены: коммиты запушены, живые сайты проверены. Не запушено в git.
- **Инфраструктура агентов:** общий склад скиллов `~/.agents/skills` (junctions для 8 приложений), скиллы `user-voice-anticipation` + `dev-passenger-pair`, субагенты Claude Code `passenger`/`developer`. Демо-захват пассажира: `ux-capture-demo/` (maria-math live: 0 ошибок, 0px overflow, 154 интерактивных элемента, скриншоты desktop/mobile).
- **Loop Engineering:** скилл `loop-engineering` (runner самопроверяющегося цикла: контракт LOOP.json → maker `claude -p` → валидаторы → checker → стоп-условия; пример контракта использует `verify.py` этого репо). Протестирован: зелёный контракт exit 0. OmniRoute 3.8.53 установлен; лаунчер `claude-omniroute.cmd` ждёт ключ из дашборда. Не запушено в git.

## 2026-11-12 — Constructor v3 (Темы, Контакты, Форматы, Отзывы + Live Preview)
- **Tab 2 (`#teacherTabTexts`, Конструктор сайта)**:
  - Селектор темы по умолчанию (`siteConfig.default_theme`: `cozy-cat`, `sakura`, `artek`, `cyber`): применяется на публичном сайте при отсутствии ручного выбора (`maria_theme_manual`) и сразу при сохранении.
  - Автосинхронизация телефона (`+7/8/9...` → `+7XXXXXXXXXX`) и Telegram (`@user` / `user` / `+7...` / `https://t.me/...`), кнопка «Обновить МАКС и ТГ из номера», единый `resolveSiteContacts()` для шапки, hero, квиза/записи (`#tgDirectBtn`/`#maxDirectBtn`), отзывов и подвала; сохранение `?text=` на открытых handoff-кнопках.
  - Поле `#cfgReviewsChannelUrl` (`contacts.reviews_channel_url`) для кнопок `#reviewsChannelLink` (рядом с Авито) и `#footerReviewsChannelLink`.
  - Конструктор форматов: переключение видимости `hidden` (с защитой `>= 1` активного тарифа), «+ Добавить формат» и удаление кастомных форматов.
- **Tab 3 (`#teacherTabReviews`, Отзывы и PIN)**:
  - Компактная 3-шаговая инструкция (канал отзывов в ТГ/МАКС, Авито, первые 2–3 отзыва).
  - Форма «Добавить отзыв» (`author`, `role`, `rating`, дата `DD.MM.YYYY`, `text`, чекбокс публикации) + Live Preview (`#admReviewLivePreview`) через общий `buildPublicReviewCardHtml(r)` и RPC `admin_add_review`.
  - Список отзывов в кабинете показывает опубликованные («На сайте») и скрытые («Скрыт»), поддерживает «Скрыть»/«Показать» (`admin_set_review_visibility`) и архивирование «Удалить» (`admin_delete_review`).
- **Генератор и конфиги**: добавлены опциональные `contacts.reviewsChannelUrl`, `theme.default`, `programs[].hidden` в `generate.py`, `config.example.json`, `config.schema.json`, `README.md`; пересобран `dist/index.html`.
- **Проверки**: `generate.py` (0 оставшихся `{{...}}` токенов), `node --check` на 2 inline `<script>` блоках (exit 0), Playwright с замоканными RPC Supabase across `1440x900`, `393x852`, `360x800` × 4 темы (48 layout-проверок, `0px` horizontal overflow, `0` console/page errors). Не запушено в git.
