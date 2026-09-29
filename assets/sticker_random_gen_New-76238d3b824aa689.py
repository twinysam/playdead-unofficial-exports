from __future__ import annotations

import os
import random
import subprocess
import sys
import threading
from collections import Counter
from pathlib import Path

if sys.version_info < (3, 8) or sys.version_info >= (3, 17):
    sys.exit('Python 3.8 to 3.16 required.')

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    in_venv = (getattr(sys, 'base_prefix', sys.prefix) != sys.prefix)
    cmd = [sys.executable, '-m', 'pip', 'install', '--quiet', 'pillow']
    if not in_venv:
        cmd.append('--user')
    subprocess.check_call(cmd)
    from PIL import Image, ImageDraw, ImageFont

import tkinter as tk
from tkinter import ttk, filedialog, messagebox


KNOWN = {
      2: 'G',   3: 'R',   4: 'R',   5: 'G',   7: 'G',
      9: 'G',  10: 'R',  12: 'R',  13: 'G',  14: 'R',  15: 'G',  17: 'G',
     18: 'R',  19: 'R',  20: 'G',  21: 'R',  23: 'R',  24: 'R',
     26: 'R',  29: 'G',  30: 'G',  31: 'R',  32: 'G',  36: 'G',
     37: 'R',  38: 'G',  39: 'G',  40: 'G',  42: 'G',  43: 'G',
     44: 'R',  46: 'G',  47: 'G',  48: 'G',  51: 'R',  53: 'R',
     56: 'G',  57: 'R',  59: 'G',  60: 'G',  63: 'G',  65: 'G',
     66: 'G',  69: 'G',  70: 'R',  71: 'R',  72: 'R',  74: 'R',
     75: 'R',  76: 'G',  78: 'G',  79: 'G',  80: 'G',  81: 'G',
     85: 'Y',  86: 'G',  89: 'Y',  90: 'Y',  92: 'Y',  95: 'Y',
     96: 'G',  97: 'Y',  98: 'Y', 101: 'G', 108: 'G',
}
CELL_NUMBERS = range(1, 109)
PIECE_LAYOUT = 'by piece'
LAYOUTS = {'9x12': (12, 9), '12x9': (9, 12), '6x18': (18, 6),
           '18x6': (6, 18), '4x27': (27, 4), '27x4': (4, 27),
           PIECE_LAYOUT: (9, 12)}
PIECE_LETTERS = 'ABCDEFGHI'
CMAP = {'G': (160, 160, 160), 'R': (220, 30, 30),
        'Y': (240, 220, 30), 'K': (0, 0, 0)}
CMAP_HEX = {k: '#{:02x}{:02x}{:02x}'.format(*v) for k, v in CMAP.items()}
PERIODS = [54, 36, 27, 18, 12, 9, 6, 4]
MODEL_PERIOD_WEIGHTS = {54: 1.0, 36: 0.7, 27: 0.6, 18: 0.5, 12: 0.4,
                        9: 0.4, 6: 0.3, 4: 0.25, 3: 0.2, 2: 0.15}
MODEL_LINE_WEIGHT = 0.3
BLOCK_LAST = 81
GUESS_CONF = 0.45
STICKERS_LOST = 42
STICKERS_UNKNOWN_OWNER = 35
STICKERS_FOUND_FALLBACK = 82
STICKER_DIR = Path('D:/INSIDE_ARG/ARG/inside-args/images/stickers')
MAGENTA = (200, 60, 200)
ORANGE = (230, 140, 0)
CHECK_RIGHT = (60, 170, 80)
CHECK_WRONG = (210, 50, 50)
DIM_PRED = (70, 80, 90)
DIM_KNOWN = (40, 40, 40)
GLYPHS = {'G': '/', 'R': '—', 'Y': '•', 'K': ''}


BG_BASE = '#0F1115'
BG_PANEL = '#1A1D24'
BG_CARD = '#232730'
BG_HOVER = '#2A2F3A'
BG_INPUT = '#1F232B'
ACCENT = '#4F8FF7'
ACCENT_HOVER = '#6BA3FB'
ACCENT_DIM = '#3A6FC7'
TEXT_PRIMARY = '#E8E8EC'
TEXT_SECONDARY = '#9598A1'
TEXT_DIM = '#6B6E78'
BORDER_SUBTLE = '#2A2F3A'
SUCCESS = '#4AC774'
WARN = '#F5A623'
DANGER = '#E74C3C'

BG_MAIN = BG_BASE
BG_SIDE = BG_PANEL
FG_MAIN = TEXT_PRIMARY
FG_DIM = TEXT_SECONDARY
BORDER_BLUE = ACCENT_DIM
ACCENT_BLUE = ACCENT
SIDE_INACTIVE_BG = BG_PANEL
SIDE_INACTIVE_FG = TEXT_SECONDARY


TAB_KEYS = [
    'known_only',
    'by_piece',
    'pattern_mod54',
    'multi_period',
    'random_sampler',
    'export_bundle',
    'prediction_zoned',
    'prediction_cross',
    'confidence_heatmap',
    'hard_residues',
]

TAB_META = {
    'known_only': {'legend_kind': 'symbol3_plus_unk'},
    'by_piece': {'legend_kind': 'piece'},
    'pattern_mod54': {'legend_kind': 'symbol3'},
    'multi_period': {'legend_kind': 'symbol3_plus_lowagree'},
    'random_sampler': {'legend_kind': 'symbol3'},
    'export_bundle': {'legend_kind': 'symbol3'},
    'prediction_zoned': {'legend_kind': 'symbol3_guess'},
    'prediction_cross': {'legend_kind': 'symbol3_guess'},
    'confidence_heatmap': {'legend_kind': 'model_check'},
    'hard_residues': {'legend_kind': 'wanted'},
}


LANGS = ('en', 'ru', 'de', 'it', 'da')
DEFAULT_LANG = 'en'

_I18N_DATA: dict[str, tuple] = {
    'app_title': ('INSIDE Sticker Studio', 'INSIDE Sticker Studio', 'INSIDE Sticker Studio', 'INSIDE Sticker Studio', 'INSIDE Sticker Studio'),
    'app_subtitle': (
        "INSIDE Collector's Edition · 108-cell sticker puzzle",
        'Коллекционное издание INSIDE · головоломка из 108 клеток',
        "INSIDE Collector's Edition · Sticker-Rätsel mit 108 Zellen",
        'Edizione da collezione INSIDE · puzzle di sticker da 108 celle',
        "INSIDE Collector's Edition · klistermærke-puslespil med 108 felter",
    ),
    'view_modes_header': ('VIEW MODES', 'РЕЖИМЫ', 'ANSICHTEN', 'MODI', 'VISNINGER'),
    'live_preview': ('Live preview', 'Превью', 'Live-Vorschau', 'Anteprima', 'Live preview'),
    'layout_label': ('Layout', 'Сетка', 'Layout', 'Layout', 'Layout'),
    'cell_size_label': ('Cell size (PNG output)', 'Размер клетки (PNG)', 'Zellgröße (PNG)', 'Dimensione cella (PNG)', 'Cellestørrelse (PNG)'),
    'output_label': ('Output', 'Папка', 'Ausgabe', 'Output', 'Output'),
    'browse_button': ('Browse', 'Выбрать', 'Durchsuchen', 'Sfoglia', 'Gennemse'),
    'save_legend_button': ('Save with legend', 'Сохранить с легендой', 'Mit Legende speichern', 'Salva con legenda', 'Gem med forklaring'),
    'open_folder_button': ('Open folder', 'Открыть папку', 'Ordner öffnen', 'Apri cartella', 'Åbn mappe'),
    'show_numbers_checkbox': ('Show numbers (known)', 'Показать номера (известные)', 'Nummern anzeigen (bekannt)', 'Mostra numeri (noti)', 'Vis numre (kendte)'),
    'show_symbols_checkbox': ('Show symbols (/, —, •)', 'Показать символы (/, —, •)', 'Symbole anzeigen (/, —, •)', 'Mostra simboli (/, —, •)', 'Vis symboler (/, —, •)'),
    'piece_fill_checkbox': ('Fill unknown cells with model guesses (pale)', 'Заполнить неизвестные клетки догадками модели (бледно)', 'Unbekannte Zellen mit Modell-Vermutungen füllen (blass)', 'Riempi le celle sconosciute con le ipotesi del modello (pallide)', 'Udfyld ukendte felter med modellens gæt (blegt)'),
    'ready_status': ('Ready.', 'Готово.', 'Bereit.', 'Pronto.', 'Klar.'),
    'pill_stickers_found': ('{n} stickers found', '{n} стикеров найдено', '{n} Sticker gefunden', '{n} sticker trovati', '{n} klistermærker fundet'),
    'pill_lost': ('{n} lost', '{n} утеряно', '{n} verloren', '{n} persi', '{n} tabt'),
    'pill_owner_unknown': ('{n} owners still open', '{n} владельцев ещё не ответили', '{n} Besitzer noch offen', '{n} proprietari ancora aperti', '{n} ejere stadig åbne'),
    'pill_residues_known': ('{n} of 108 cells known', '{n} из 108 клеток известно', '{n} von 108 Zellen bekannt', '{n} di 108 celle note', '{n} af 108 felter kendt'),
    'pill_top_slash': ('1–81: slash {pct}%', '1–81: слеш {pct}%', '1–81: Schrägstrich {pct}%', '1–81: barra {pct}%', '1–81: skråstreg {pct}%'),
    'pill_bottom_slash': ('82–108: slash {pct}%', '82–108: слеш {pct}%', '82–108: Schrägstrich {pct}%', '82–108: barra {pct}%', '82–108: skråstreg {pct}%'),
    'reroll_button': ('Reroll', 'Перебросить', 'Neu würfeln', 'Rilancia', 'Slå om'),
    'export_button': ('Export 8 PNGs', 'Экспорт 8 PNG', 'Export 8 PNGs', 'Esporta 8 PNG', 'Eksporter 8 PNG'),
    'seed_label': ('Seed', 'Seed', 'Seed', 'Seed', 'Seed'),
    'samples_label': ('Samples', 'Образцов', 'Proben', 'Campioni', 'Prøver'),
    'min_agree_label': ('Min periods to agree', 'Минимум согласных периодов', 'Min. übereinstimmende Perioden', 'Periodi minimi concordi', 'Min. enige perioder'),
    'status_saved': ('Saved {filename}', 'Сохранено: {filename}', 'Gespeichert: {filename}', 'Salvato: {filename}', 'Gemt: {filename}'),
    'status_generating': ('Generating...', 'Генерация...', 'Generierung...', 'Generazione...', 'Genererer...'),
    'status_done_count': ('Done. {n} images saved.', 'Готово. Сохранено изображений: {n}.', 'Fertig. {n} Bilder gespeichert.', 'Fatto. {n} immagini salvate.', 'Færdig. {n} billeder gemt.'),
    'status_progress': ('[{done}/{total}] {filename}', '[{done}/{total}] {filename}', '[{done}/{total}] {filename}', '[{done}/{total}] {filename}', '[{done}/{total}] {filename}'),
    'error_bad_input_int': (
        'Cell size must be an integer.',
        'Размер клетки должен быть целым числом.',
        'Zellgröße muss eine Ganzzahl sein.',
        'La dimensione cella deve essere un intero.',
        'Cellestørrelse skal være et heltal.',
    ),
    'error_bad_input_int_title': ('Bad input', 'Неверный ввод', 'Ungültige Eingabe', 'Input non valido', 'Ugyldigt input'),
    'error_bad_layout': ('Pick a valid layout.', 'Выберите корректную сетку.', 'Wählen Sie ein gültiges Layout.', 'Selezionare un layout valido.', 'Vælg et gyldigt layout.'),
    'error_bad_layout_title': ('Bad layout', 'Неверная сетка', 'Ungültiges Layout', 'Layout non valido', 'Ugyldigt layout'),
    'error_folder_missing': ('Folder does not exist yet.', 'Папка ещё не существует.', 'Ordner existiert noch nicht.', 'La cartella non esiste ancora.', 'Mappen findes ikke endnu.'),
    'error_folder_missing_title': ('Not yet', 'Пока нет', 'Noch nicht', 'Non ancora', 'Ikke endnu'),
    'swatch_slash': ('/ slash', '/ слеш', '/ Schrägstrich', '/ barra', '/ skråstreg'),
    'swatch_dash': ('— dash', '— тире', '— Bindestrich', '— trattino', '— bindestreg'),
    'swatch_dot': ('• dot', '• точка', '• Punkt', '• punto', '• prik'),
    'swatch_unknown_black': ('unknown (black)', 'неизвестно (чёрное)', 'unbekannt (schwarz)', 'sconosciuto (nero)', 'ukendt (sort)'),
    'swatch_no_agreement': ('no agreement (black)', 'нет согласия (чёрное)', 'keine Übereinstimmung (schwarz)', 'nessun accordo (nero)', 'ingen enighed (sort)'),
    'swatch_known': ('known', 'известное', 'bekannt', 'noto', 'kendt'),
    'swatch_guess': ('guess (pale)', 'догадка (бледная)', 'Vermutung (blass)', 'ipotesi (pallida)', 'gæt (bleg)'),
    'swatch_model_right': ('model right', 'модель угадала', 'Modell richtig', 'modello giusto', 'model rigtig'),
    'swatch_model_wrong': ('model wrong', 'модель ошиблась', 'Modell falsch', 'modello sbagliato', 'model forkert'),
    'swatch_unknown_dark': ('unknown', 'неизвестно', 'unbekannt', 'sconosciuto', 'ukendt'),
    'swatch_wanted_block': ('unknown in 9×9 block (1–81)', 'неизвестно в блоке 9×9 (1–81)', 'unbekannt im 9×9-Block (1–81)', 'sconosciuto nel blocco 9×9 (1–81)', 'ukendt i 9×9-blokken (1–81)'),
    'swatch_wanted_tail': ('unknown in tail (82–108)', 'неизвестно в хвосте (82–108)', 'unbekannt im Schwanz (82–108)', 'sconosciuto nella coda (82–108)', 'ukendt i halen (82–108)'),
    'legend_note_guess': ('pale cells are guesses, not predictions', 'бледные клетки — догадки, а не предсказания', 'blasse Zellen sind Vermutungen, keine Vorhersagen', 'le celle pallide sono ipotesi, non previsioni', 'blege felter er gæt, ikke forudsigelser'),
    'stats_known': ('known', 'известно', 'bekannt', 'noti', 'kendte'),
    'stats_guessed': ('guessed', 'догадок', 'vermutet', 'ipotesi', 'gættet'),
    'stats_slash': ('slash', 'слеш', 'Schrägstr.', 'barra', 'skråstreg'),
    'stats_dash': ('dash', 'тире', 'Bindestr.', 'trattino', 'bindestreg'),
    'stats_dot': ('dot', 'точка', 'Punkt', 'punto', 'prik'),
    'stats_unknown': ('unknown', 'неизв.', 'unbek.', 'sconosc.', 'ukendt'),
    'stats_right': ('right', 'верно', 'richtig', 'giuste', 'rigtige'),
    'stats_wrong': ('wrong', 'ошибок', 'falsch', 'sbagliate', 'forkerte'),
    'stats_zone_guess': ('zone guess', 'догадка по зоне', 'Zonen-Vermutung', 'ipotesi di zona', 'zone-gæt'),
    'stats_check': ('leave-one-out', 'проверка по одной', 'Leave-one-out', 'leave-one-out', 'leave-one-out'),
    'stats_block': ('unknown in 9×9', 'неизв. в 9×9', 'unbek. im 9×9', 'sconosc. nel 9×9', 'ukendt i 9×9'),
    'stats_tail': ('unknown in tail', 'неизв. в хвосте', 'unbek. im Schwanz', 'sconosc. nella coda', 'ukendt i halen'),
    'stats_stickers': ('sticker numbers', 'номеров стикеров', 'Stickernummern', 'numeri di sticker', 'klistermærkenumre'),
    'tail_prediction_numbers': ('pale cells = guesses', 'бледные = догадки', 'blasse Zellen = Vermutungen', 'celle pallide = ipotesi', 'blege felter = gæt'),
    'tail_heatmap_numbers': ('cell number on every cell', 'номер на каждой клетке', 'Nummer auf jeder Zelle', 'numero su ogni cella', 'nummer på hvert felt'),
    'tail_hard_numbers': ('number on unknown cells', 'номера на неизвестных', 'Nummern auf unbekannten Zellen', 'numeri sulle celle sconosciute', 'numre på ukendte felter'),
    'tail_piece_numbers': ('row = background piece A–I', 'ряд = фоновая картинка A–I', 'Zeile = Hintergrundbild A–I', 'riga = sfondo A–I', 'række = baggrundsbillede A–I'),
    'controls_status_known_only': ('{known} cells known, {unknown} unknown (black)', '{known} клеток известно, {unknown} неизвестно (чёрные)', '{known} Zellen bekannt, {unknown} unbekannt (schwarz)', '{known} celle note, {unknown} sconosciute (nere)', '{known} felter kendt, {unknown} ukendte (sorte)'),
    'controls_facts': (
        'Zero exceptions so far: repeats every 108  ·  1–81 only / or —  ·  82–108 only / or •  ·  background = (n−1) mod 9',
        'Без единого исключения: повтор каждые 108  ·  1–81 только / или —  ·  82–108 только / или •  ·  картинка = (n−1) mod 9',
        'Bisher ohne Ausnahme: Wiederholung alle 108  ·  1–81 nur / oder —  ·  82–108 nur / oder •  ·  Hintergrund = (n−1) mod 9',
        'Finora senza eccezioni: ripetizione ogni 108  ·  1–81 solo / o —  ·  82–108 solo / o •  ·  sfondo = (n−1) mod 9',
        'Indtil nu uden undtagelser: gentages hver 108  ·  1–81 kun / eller —  ·  82–108 kun / eller •  ·  baggrund = (n−1) mod 9',
    ),
    'controls_status_pattern_mod54': ('Leave-one-out check: {acc_mod54}% right   ·   zone guess: {base}%', 'Проверка по одной: {acc_mod54}% верно   ·   догадка по зоне: {base}%', 'Leave-one-out-Prüfung: {acc_mod54}% richtig   ·   Zonen-Vermutung: {base}%', 'Verifica leave-one-out: {acc_mod54}% giuste   ·   ipotesi di zona: {base}%', 'Leave-one-out-tjek: {acc_mod54}% rigtige   ·   zone-gæt: {base}%'),
    'controls_status_multi_live': ('Check at N={n}: fills {cov}% of hidden cells, {acc}% of those right   ·   zone guess: {base}%', 'Проверка при N={n}: заполняет {cov}% спрятанных клеток, из них верно {acc}%   ·   догадка по зоне: {base}%', 'Prüfung bei N={n}: füllt {cov}% der verborgenen Zellen, davon {acc}% richtig   ·   Zonen-Vermutung: {base}%', 'Verifica con N={n}: riempie il {cov}% delle celle nascoste, di cui {acc}% giuste   ·   ipotesi di zona: {base}%', 'Tjek ved N={n}: udfylder {cov}% af skjulte felter, {acc}% af dem rigtige   ·   zone-gæt: {base}%'),
    'controls_status_export_bundle': ('   Saves known + mod 54 + multi (2, 3) + random (1, 2) + by piece (known, guesses).', '   Сохраняет known + mod 54 + multi (2, 3) + random (1, 2) + по картинкам (известные, догадки).', '   Speichert known + mod 54 + multi (2, 3) + random (1, 2) + nach Bild (bekannt, Vermutungen).', '   Salva known + mod 54 + multi (2, 3) + random (1, 2) + per sfondo (note, ipotesi).', '   Gemmer known + mod 54 + multi (2, 3) + random (1, 2) + efter billede (kendte, gæt).'),
    'controls_model_line': ('guessed={guessed}  G={g}  R={r}  Y={y}   ·   leave-one-out {acc}% right, zone guess {base}%', 'догадок={guessed}  G={g}  R={r}  Y={y}   ·   проверка по одной: {acc}% верно, догадка по зоне {base}%', 'vermutet={guessed}  G={g}  R={r}  Y={y}   ·   Leave-one-out {acc}% richtig, Zonen-Vermutung {base}%', 'ipotesi={guessed}  G={g}  R={r}  Y={y}   ·   leave-one-out {acc}% giuste, ipotesi di zona {base}%', 'gættet={guessed}  G={g}  R={r}  Y={y}   ·   leave-one-out {acc}% rigtige, zone-gæt {base}%'),
    'controls_check_line': ('right: {mc_right}   wrong: {mc_wrong}   model: {acc_model_z}%   zone guess: {base}%', 'верно: {mc_right}   ошибок: {mc_wrong}   модель: {acc_model_z}%   догадка по зоне: {base}%', 'richtig: {mc_right}   falsch: {mc_wrong}   Modell: {acc_model_z}%   Zonen-Vermutung: {base}%', 'giuste: {mc_right}   sbagliate: {mc_wrong}   modello: {acc_model_z}%   ipotesi di zona: {base}%', 'rigtige: {mc_right}   forkerte: {mc_wrong}   model: {acc_model_z}%   zone-gæt: {base}%'),
    'controls_wanted_header': ('Sticker numbers to look for (cell: its 6 sticker numbers)', 'Какие номера стикеров искать (клетка: её 6 номеров)', 'Gesuchte Stickernummern (Zelle: ihre 6 Nummern)', 'Numeri di sticker da cercare (cella: i suoi 6 numeri)', 'Klistermærkenumre at lede efter (felt: dets 6 numre)'),
    'wanted_tag_block': ('9×9', '9×9', '9×9', '9×9', '9×9'),
    'wanted_tag_tail': ('tail', 'хвост', 'Schwanz', 'coda', 'hale'),
    'tab_known_only_card_title': ('Known cells', 'Известные клетки', 'Bekannte Zellen', 'Celle note', 'Kendte felter'),
    'tab_known_only_card_subtitle': ('{known} confirmed cells', '{known} подтверждённых клеток', '{known} bestätigte Zellen', '{known} celle confermate', '{known} bekræftede felter'),
    'tab_known_only_big_title': ('Known cells only', 'Только известные клетки', 'Nur bekannte Zellen', 'Solo celle note', 'Kun kendte felter'),
    'tab_known_only_description': (
        'Only what the stickers confirm. {found} stickers have been collected; several land on the same cell (each cell is printed 6 times), so together they fill {known} of 108 cells. The other {unknown} cells stay BLACK. All {repeats} stickers that landed on an already known cell show the same symbol.',
        'Только то, что подтверждают стикеры. Собрано {found} стикеров; некоторые попадают в одну и ту же клетку (каждая клетка напечатана 6 раз), поэтому вместе они заполняют {known} из 108 клеток. Остальные {unknown} клеток остаются ЧЁРНЫМИ. Все {repeats} стикеров, попавших в уже известную клетку, показывают тот же символ.',
        'Nur was die Sticker bestätigen. {found} Sticker wurden gesammelt; mehrere landen auf derselben Zelle (jede Zelle ist 6-mal gedruckt), zusammen füllen sie {known} von 108 Zellen. Die übrigen {unknown} Zellen bleiben SCHWARZ. Alle {repeats} Sticker, die auf einer bereits bekannten Zelle landeten, zeigen dasselbe Symbol.',
        'Solo ciò che gli sticker confermano. Sono stati raccolti {found} sticker; diversi cadono sulla stessa cella (ogni cella è stampata 6 volte), quindi insieme riempiono {known} celle su 108. Le altre {unknown} celle restano NERE. Tutti i {repeats} sticker caduti su una cella già nota mostrano lo stesso simbolo.',
        'Kun det, klistermærkerne bekræfter. {found} klistermærker er indsamlet; flere lander på samme felt (hvert felt er trykt 6 gange), så tilsammen udfylder de {known} af 108 felter. De øvrige {unknown} felter forbliver SORTE. Alle {repeats} klistermærker, der landede på et allerede kendt felt, viser samme symbol.',
    ),
    'tab_known_only_numbers_info': (
        "Numbers: the cell number (1–108) on every known cell when 'Show numbers' is on. Unknown cells stay black.",
        'Номера: номер клетки (1–108) на каждой известной клетке, если включено «Показать номера». Неизвестные остаются чёрными.',
        'Nummern: die Zellnummer (1–108) auf jeder bekannten Zelle, wenn «Nummern anzeigen» aktiv ist. Unbekannte Zellen bleiben schwarz.',
        'Numeri: il numero della cella (1–108) su ogni cella nota quando «Mostra numeri» è attivo. Le celle sconosciute restano nere.',
        'Numre: feltnummeret (1–108) på hvert kendt felt, når «Vis numre» er slået til. Ukendte felter forbliver sorte.',
    ),
    'tab_by_piece_card_title': ('By background piece', 'По фоновым картинкам', 'Nach Hintergrundbild', 'Per sfondo', 'Efter baggrundsbillede'),
    'tab_by_piece_card_subtitle': ('A Fluffy Seal layout, 9 × 12', 'Раскладка A Fluffy Seal, 9 × 12', 'Layout von A Fluffy Seal, 9 × 12', 'Layout di A Fluffy Seal, 9 × 12', 'A Fluffy Seals layout, 9 × 12'),
    'tab_by_piece_big_title': (
        'By background piece · 9 rows of 12 stickers',
        'По фоновым картинкам · 9 рядов по 12 стикеров',
        'Nach Hintergrundbild · 9 Zeilen mit je 12 Stickern',
        'Per sfondo · 9 righe da 12 sticker',
        'Efter baggrundsbillede · 9 rækker med 12 klistermærker',
    ),
    'tab_by_piece_description': (
        "Layout suggested by A Fluffy Seal. Each row is one background picture (A–I) and lists its 12 stickers in order: row A = 1, 10, 19 … 100. The last 3 columns (82–108) are the tail, the only place where dots appear. Tick the box to fill unknown cells with the model's guesses, drawn pale.",
        'Раскладка, предложенная A Fluffy Seal. Каждый ряд — одна фоновая картинка (A–I), в нём по порядку её 12 стикеров: ряд A = 1, 10, 19 … 100. Последние 3 столбца (82–108) — хвост, единственное место, где бывают точки. Галочка заполняет неизвестные клетки догадками модели, бледным цветом.',
        'Layout nach A Fluffy Seal. Jede Zeile ist ein Hintergrundbild (A–I) und zeigt seine 12 Sticker der Reihe nach: Zeile A = 1, 10, 19 … 100. Die letzten 3 Spalten (82–108) sind der Schwanz, der einzige Ort mit Punkten. Mit dem Häkchen werden unbekannte Zellen mit den Vermutungen des Modells blass gefüllt.',
        "Layout proposto da A Fluffy Seal. Ogni riga è uno sfondo (A–I) ed elenca in ordine i suoi 12 sticker: riga A = 1, 10, 19 … 100. Le ultime 3 colonne (82–108) sono la coda, l'unico posto con i punti. La casella riempie le celle sconosciute con le ipotesi del modello, in colore pallido.",
        'Layout foreslået af A Fluffy Seal. Hver række er ét baggrundsbillede (A–I) og viser dets 12 klistermærker i rækkefølge: række A = 1, 10, 19 … 100. De sidste 3 kolonner (82–108) er halen, det eneste sted med prikker. Afkrydsningen udfylder ukendte felter blegt med modellens gæt.',
    ),
    'tab_by_piece_numbers_info': (
        "Numbers: the sticker number is always shown on every cell; symbols follow 'Show symbols'.",
        'Номера: номер стикера всегда показан на каждой клетке; символы — по галочке «Показать символы».',
        'Nummern: die Stickernummer steht immer auf jeder Zelle; Symbole folgen «Symbole anzeigen».',
        'Numeri: il numero dello sticker è sempre su ogni cella; i simboli seguono «Mostra simboli».',
        'Numre: klistermærkenummeret vises altid på hvert felt; symboler følger «Vis symboler».',
    ),
    'tab_pattern_mod54_card_title': ('Experiment · mod 54', 'Эксперимент · mod 54', 'Experiment · mod 54', 'Esperimento · mod 54', 'Eksperiment · mod 54'),
    'tab_pattern_mod54_card_subtitle': ('No better than a guess', 'Не лучше догадки', 'Nicht besser als Raten', "Non meglio di un'ipotesi", 'Ikke bedre end et gæt'),
    'tab_pattern_mod54_big_title': (
        'Experiment · copy from 54 cells away',
        'Эксперимент · копия клетки через 54',
        'Experiment · Kopie aus 54 Zellen Abstand',
        'Esperimento · copia da 54 celle di distanza',
        'Eksperiment · kopi fra 54 felter væk',
    ),
    'tab_pattern_mod54_description': (
        "Fills each unknown cell with the symbol of the cell 54 steps away (zone rule applied; no partner means /). Honest check: hide each known cell in turn and let this rule guess it. It gets {acc_mod54}% right; simply guessing the zone's most common symbol gets {base}%. Filled cells are guesses, not predictions.",
        'Заполняет каждую неизвестную клетку символом клетки через 54 (с правилом зон; нет партнёра — ставится /). Честная проверка: по очереди прячем каждую известную клетку и даём правилу её угадать. Оно угадывает {acc_mod54}%, а простая догадка «самый частый символ зоны» — {base}%. Заполненные клетки — догадки, а не предсказания.',
        'Füllt jede unbekannte Zelle mit dem Symbol der Zelle 54 Schritte entfernt (Zonenregel angewendet; ohne Partner wird / gesetzt). Ehrliche Prüfung: jede bekannte Zelle wird der Reihe nach versteckt und von dieser Regel erraten. Sie liegt zu {acc_mod54}% richtig; einfach das häufigste Symbol der Zone zu raten ergibt {base}%. Gefüllte Zellen sind Vermutungen, keine Vorhersagen.',
        'Riempie ogni cella sconosciuta con il simbolo della cella a 54 passi (regola di zona applicata; senza partner si mette /). Verifica onesta: si nasconde a turno ogni cella nota e la regola la indovina. Indovina il {acc_mod54}%; indovinare semplicemente il simbolo più comune della zona dà il {base}%. Le celle riempite sono ipotesi, non previsioni.',
        'Udfylder hvert ukendt felt med symbolet fra feltet 54 skridt væk (zoneregel anvendt; uden partner sættes /). Ærligt tjek: hvert kendt felt skjules på skift, og reglen gætter det. Den rammer {acc_mod54}%; blot at gætte zonens mest almindelige symbol giver {base}%. Udfyldte felter er gæt, ikke forudsigelser.',
    ),
    'tab_pattern_mod54_numbers_info': (
        "Numbers: 'Show numbers' overlays the cell number on known cells. Filled cells are not labelled.",
        'Номера: «Показать номера» подписывает известные клетки. Заполненные догадками не подписываются.',
        'Nummern: «Nummern anzeigen» beschriftet bekannte Zellen. Gefüllte Zellen werden nicht beschriftet.',
        'Numeri: «Mostra numeri» etichetta le celle note. Le celle riempite non sono etichettate.',
        'Numre: «Vis numre» mærker kendte felter. Udfyldte felter mærkes ikke.',
    ),
    'tab_multi_period_card_title': ('Experiment · multi-period', 'Эксперимент · много периодов', 'Experiment · Mehrperioden', 'Esperimento · multi-periodo', 'Eksperiment · multi-periode'),
    'tab_multi_period_card_subtitle': ('8 periods, threshold', '8 периодов, порог', '8 Perioden, Schwelle', '8 periodi, soglia', '8 perioder, tærskel'),
    'tab_multi_period_big_title': ('Experiment · multi-period agreement vote', 'Эксперимент · согласие нескольких периодов', 'Experiment · Mehrperioden-Konsens', 'Esperimento · consenso multi-periodo', 'Eksperiment · multi-periode enighed'),
    'tab_multi_period_description': (
        'Voting across 8 periods (54, 36, 27, 18, 12, 9, 6, 4). A cell is filled only when at least N periods agree on the same symbol; otherwise it stays BLACK. Next to the control: the honest check for the chosen N (how many hidden known cells it dares to fill, and how many of those it gets right).',
        'Голосование по 8 периодам (54, 36, 27, 18, 12, 9, 6, 4). Клетка заполняется, только если не меньше N периодов сходятся на одном символе; иначе она остаётся ЧЁРНОЙ. Рядом с настройкой — честная проверка для выбранного N: сколько спрятанных известных клеток правило решается заполнить и сколько из них угадывает.',
        'Abstimmung über 8 Perioden (54, 36, 27, 18, 12, 9, 6, 4). Eine Zelle wird nur gefüllt, wenn mindestens N Perioden auf dasselbe Symbol kommen; sonst bleibt sie SCHWARZ. Neben dem Regler: die ehrliche Prüfung für das gewählte N (wie viele versteckte bekannte Zellen gefüllt werden und wie viele davon richtig sind).',
        "Voto su 8 periodi (54, 36, 27, 18, 12, 9, 6, 4). Una cella viene riempita solo se almeno N periodi concordano sullo stesso simbolo; altrimenti resta NERA. Accanto al controllo: la verifica onesta per l'N scelto (quante celle note nascoste osa riempire e quante di queste indovina).",
        'Afstemning over 8 perioder (54, 36, 27, 18, 12, 9, 6, 4). Et felt udfyldes kun, hvis mindst N perioder er enige om samme symbol; ellers forbliver det SORT. Ved siden af kontrollen: det ærlige tjek for det valgte N (hvor mange skjulte kendte felter den tør udfylde, og hvor mange af dem den rammer).',
    ),
    'tab_multi_period_numbers_info': (
        "Numbers: 'Show numbers' overlays the cell number on known cells. Black = no agreement; not labelled.",
        'Номера: «Показать номера» подписывает известные клетки. Чёрные — периоды не сошлись; не подписываются.',
        'Nummern: «Nummern anzeigen» beschriftet bekannte Zellen. Schwarz = keine Einigung; nicht beschriftet.',
        'Numeri: «Mostra numeri» etichetta le celle note. Nero = nessun accordo; non etichettate.',
        'Numre: «Vis numre» mærker kendte felter. Sort = ingen enighed; ikke mærket.',
    ),
    'tab_random_sampler_card_title': ('Random sampler', 'Случайная выборка', 'Zufallsstichprobe', 'Campione casuale', 'Tilfældig prøve'),
    'tab_random_sampler_card_subtitle': ('Seeded, zone odds', 'С seed, шансы зоны', 'Seed, Zonen-Chancen', 'Seed, probabilità di zona', 'Seed, zone-odds'),
    'tab_random_sampler_big_title': ('Random sample with zone odds', 'Случайная выборка с шансами зоны', 'Zufallsstichprobe mit Zonen-Chancen', 'Campione casuale con probabilità di zona', 'Tilfældig prøve med zone-odds'),
    'tab_random_sampler_description': (
        'Fills each unknown cell at random with the zone odds (1–81: / or —, 82–108: / or •). The same seed always gives the same grid; Reroll bumps the seed by one. These are random guesses, not predictions.',
        'Заполняет каждую неизвестную клетку случайно, с шансами своей зоны (1–81: / или —, 82–108: / или •). Один и тот же seed всегда даёт одну сетку; «Перебросить» увеличивает seed на 1. Это случайные догадки, а не предсказания.',
        'Füllt jede unbekannte Zelle zufällig mit den Zonen-Chancen (1–81: / oder —, 82–108: / oder •). Derselbe Seed ergibt immer dasselbe Gitter; «Neu würfeln» erhöht den Seed um 1. Das sind Zufallsvermutungen, keine Vorhersagen.',
        'Riempie ogni cella sconosciuta a caso con le probabilità della zona (1–81: / o —, 82–108: / o •). Lo stesso seed dà sempre la stessa griglia; «Rilancia» aumenta il seed di 1. Sono ipotesi casuali, non previsioni.',
        'Udfylder hvert ukendt felt tilfældigt med zonens odds (1–81: / eller —, 82–108: / eller •). Samme seed giver altid samme gitter; «Slå om» hæver seed med 1. Det er tilfældige gæt, ikke forudsigelser.',
    ),
    'tab_random_sampler_numbers_info': (
        "Numbers: 'Show numbers' overlays the cell number on known cells. Random fills are not labelled.",
        'Номера: «Показать номера» подписывает известные клетки. Случайные заполнения не подписываются.',
        'Nummern: «Nummern anzeigen» beschriftet bekannte Zellen. Zufallsfüllungen werden nicht beschriftet.',
        'Numeri: «Mostra numeri» etichetta le celle note. I riempimenti casuali non sono etichettati.',
        'Numre: «Vis numre» mærker kendte felter. Tilfældige udfyldninger mærkes ikke.',
    ),
    'tab_export_bundle_card_title': ('Export bundle', 'Экспорт набора', 'Export-Paket', 'Bundle di esportazione', 'Eksport-pakke'),
    'tab_export_bundle_card_subtitle': ('All modes, one click', 'Все режимы за раз', 'Alle Modi, ein Klick', 'Tutti i modi, un clic', 'Alle modi, ét klik'),
    'tab_export_bundle_big_title': ('Export bundle · 8 PNGs', 'Экспорт набора · 8 PNG', 'Export-Paket · 8 PNGs', 'Bundle di esportazione · 8 PNG', 'Eksport-pakke · 8 PNG'),
    'tab_export_bundle_description': (
        'One-click export: known cells, the mod 54 and multi-period experiments (N = 2 and 3), two random samples (seeds 1 and 2) and the two by-piece images (known only, with guesses). 8 PNGs saved to the output folder.',
        'Экспорт в один клик: известные клетки, эксперименты mod 54 и много периодов (N = 2 и 3), две случайные выборки (seed 1 и 2) и две картинки по фоновым картинкам (только известные, с догадками). 8 PNG в папку вывода.',
        'Export mit einem Klick: bekannte Zellen, die Experimente mod 54 und Mehrperioden (N = 2 und 3), zwei Zufallsstichproben (Seeds 1 und 2) und die zwei Bilder nach Hintergrundbild (nur bekannt, mit Vermutungen). 8 PNGs im Ausgabeordner.',
        'Esportazione con un clic: celle note, gli esperimenti mod 54 e multi-periodo (N = 2 e 3), due campioni casuali (seed 1 e 2) e le due immagini per sfondo (solo note, con ipotesi). 8 PNG nella cartella di output.',
        'Eksport med ét klik: kendte felter, eksperimenterne mod 54 og multi-periode (N = 2 og 3), to tilfældige prøver (seed 1 og 2) og de to billeder efter baggrund (kun kendte, med gæt). 8 PNG i outputmappen.',
    ),
    'tab_export_bundle_numbers_info': (
        'The first 6 PNGs are plain 108-cell grids; the two by-piece PNGs carry numbers and symbols.',
        'Первые 6 PNG — простые сетки из 108 клеток; две картинки по фоновым картинкам — с номерами и символами.',
        'Die ersten 6 PNGs sind reine 108-Zellen-Gitter; die zwei Bilder nach Hintergrund tragen Nummern und Symbole.',
        'I primi 6 PNG sono griglie semplici da 108 celle; le due immagini per sfondo hanno numeri e simboli.',
        'De første 6 PNG er rene 108-felts gitre; de to billeder efter baggrund har numre og symboler.',
    ),
    'tab_prediction_zoned_card_title': ('Experiment · model (zoned)', 'Эксперимент · модель (зоны)', 'Experiment · Modell (zonal)', 'Esperimento · modello (zonale)', 'Eksperiment · model (zonal)'),
    'tab_prediction_zoned_card_subtitle': ('Old main model', 'Бывшая основная модель', 'Früheres Hauptmodell', 'Ex modello principale', 'Tidligere hovedmodel'),
    'tab_prediction_zoned_big_title': (
        'Experiment · partner-vote model, own zone only',
        'Эксперимент · голосование партнёров, только своя зона',
        'Experiment · Partner-Abstimmung, nur eigene Zone',
        'Esperimento · voto dei partner, solo la propria zona',
        'Eksperiment · partner-afstemning, kun egen zone',
    ),
    'tab_prediction_zoned_description': (
        "The old main model: partner votes over 10 periods plus row and column, using only cells from the same zone. Honest check: {acc_model_z}% right when each known cell is hidden in turn (zone guess: {base}%). Its own confidence turned out upside down (the surer it was, the more often it was wrong), so confidence is no longer shown: every guessed cell is drawn equally pale.",
        'Бывшая основная модель: голоса партнёров по 10 периодам плюс строка и столбец, только клетки из той же зоны. Честная проверка: {acc_model_z}% верно, когда по очереди прячем каждую известную клетку (догадка по зоне: {base}%). Её собственная уверенность оказалась перевёрнутой (чем увереннее, тем чаще ошибка), поэтому уверенность больше не показывается: все клетки-догадки одинаково бледные.',
        'Das frühere Hauptmodell: Partner-Stimmen über 10 Perioden plus Zeile und Spalte, nur aus derselben Zone. Ehrliche Prüfung: {acc_model_z}% richtig, wenn jede bekannte Zelle der Reihe nach versteckt wird (Zonen-Vermutung: {base}%). Seine eigene Konfidenz war verkehrt herum (je sicherer, desto öfter falsch), daher wird sie nicht mehr gezeigt: alle vermuteten Zellen sind gleich blass.',
        'Il vecchio modello principale: voti dei partner su 10 periodi più riga e colonna, solo celle della stessa zona. Verifica onesta: {acc_model_z}% giuste quando ogni cella nota viene nascosta a turno (ipotesi di zona: {base}%). La sua confidenza si è rivelata capovolta (più era sicuro, più spesso sbagliava), quindi non viene più mostrata: tutte le celle ipotizzate sono ugualmente pallide.',
        'Den tidligere hovedmodel: partnerstemmer over 10 perioder plus række og kolonne, kun felter fra samme zone. Ærligt tjek: {acc_model_z}% rigtige, når hvert kendt felt skjules på skift (zone-gæt: {base}%). Dens egen konfidens viste sig at være omvendt (jo mere sikker, jo oftere forkert), så den vises ikke længere: alle gættede felter er lige blege.',
    ),
    'tab_prediction_zoned_numbers_info': (
        "Numbers: 'Show numbers' overlays the cell number on known cells. Pale cells are guesses.",
        'Номера: «Показать номера» подписывает известные клетки. Бледные клетки — догадки.',
        'Nummern: «Nummern anzeigen» beschriftet bekannte Zellen. Blasse Zellen sind Vermutungen.',
        'Numeri: «Mostra numeri» etichetta le celle note. Le celle pallide sono ipotesi.',
        'Numre: «Vis numre» mærker kendte felter. Blege felter er gæt.',
    ),
    'tab_prediction_cross_card_title': ('Experiment · model (cross)', 'Эксперимент · модель (кросс)', 'Experiment · Modell (übergreifend)', 'Esperimento · modello (incrociato)', 'Eksperiment · model (på tværs)'),
    'tab_prediction_cross_card_subtitle': ('Partners from both zones', 'Партнёры из обеих зон', 'Partner aus beiden Zonen', 'Partner da entrambe le zone', 'Partnere fra begge zoner'),
    'tab_prediction_cross_big_title': (
        'Experiment · partner-vote model, both zones',
        'Эксперимент · голосование партнёров, обе зоны',
        'Experiment · Partner-Abstimmung, beide Zonen',
        'Esperimento · voto dei partner, entrambe le zone',
        'Eksperiment · partner-afstemning, begge zoner',
    ),
    'tab_prediction_cross_description': (
        'Same model, but partners come from both zones. Honest check: {acc_model_x}% right when each known cell is hidden in turn (zone guess: {base}%). Every guessed cell is drawn equally pale.',
        'Та же модель, но партнёры берутся из обеих зон. Честная проверка: {acc_model_x}% верно, когда по очереди прячем каждую известную клетку (догадка по зоне: {base}%). Все клетки-догадки одинаково бледные.',
        'Dasselbe Modell, aber Partner aus beiden Zonen. Ehrliche Prüfung: {acc_model_x}% richtig, wenn jede bekannte Zelle der Reihe nach versteckt wird (Zonen-Vermutung: {base}%). Alle vermuteten Zellen sind gleich blass.',
        'Stesso modello, ma i partner vengono da entrambe le zone. Verifica onesta: {acc_model_x}% giuste quando ogni cella nota viene nascosta a turno (ipotesi di zona: {base}%). Tutte le celle ipotizzate sono ugualmente pallide.',
        'Samme model, men partnere fra begge zoner. Ærligt tjek: {acc_model_x}% rigtige, når hvert kendt felt skjules på skift (zone-gæt: {base}%). Alle gættede felter er lige blege.',
    ),
    'tab_prediction_cross_numbers_info': (
        "Numbers: 'Show numbers' overlays the cell number on known cells. Pale cells are guesses.",
        'Номера: «Показать номера» подписывает известные клетки. Бледные клетки — догадки.',
        'Nummern: «Nummern anzeigen» beschriftet bekannte Zellen. Blasse Zellen sind Vermutungen.',
        'Numeri: «Mostra numeri» etichetta le celle note. Le celle pallide sono ipotesi.',
        'Numre: «Vis numre» mærker kendte felter. Blege felter er gæt.',
    ),
    'tab_confidence_heatmap_card_title': ('Model check', 'Проверка модели', 'Modell-Prüfung', 'Verifica del modello', 'Modeltjek'),
    'tab_confidence_heatmap_card_subtitle': ('Where the model fails', 'Где модель ошибается', 'Wo das Modell scheitert', 'Dove il modello sbaglia', 'Hvor modellen fejler'),
    'tab_confidence_heatmap_big_title': (
        'Model check · each known cell hidden in turn',
        'Проверка модели · каждая известная клетка спрятана по очереди',
        'Modell-Prüfung · jede bekannte Zelle der Reihe nach versteckt',
        'Verifica del modello · ogni cella nota nascosta a turno',
        'Modeltjek · hvert kendt felt skjult på skift',
    ),
    'tab_confidence_heatmap_description': (
        "Each known cell is hidden and the zoned model guesses it from the other cells. GREEN = guessed right, RED = guessed wrong, dark = unknown cell. Right {mc_right} of {known} ({acc_model_z}%); guessing the zone's most common symbol gets {base}%.",
        'Каждую известную клетку прячем, и зональная модель угадывает её по остальным. ЗЕЛЁНАЯ — угадала, КРАСНАЯ — ошиблась, тёмная — неизвестная клетка. Верно {mc_right} из {known} ({acc_model_z}%); догадка «самый частый символ зоны» даёт {base}%.',
        'Jede bekannte Zelle wird versteckt und das zonale Modell errät sie aus den anderen. GRÜN = richtig, ROT = falsch, dunkel = unbekannte Zelle. Richtig {mc_right} von {known} ({acc_model_z}%); das häufigste Symbol der Zone zu raten ergibt {base}%.',
        'Ogni cella nota viene nascosta e il modello zonale la indovina dalle altre. VERDE = giusta, ROSSA = sbagliata, scura = cella sconosciuta. Giuste {mc_right} su {known} ({acc_model_z}%); indovinare il simbolo più comune della zona dà il {base}%.',
        'Hvert kendt felt skjules, og den zonale model gætter det ud fra de andre. GRØN = rigtigt, RØD = forkert, mørk = ukendt felt. Rigtige {mc_right} af {known} ({acc_model_z}%); at gætte zonens mest almindelige symbol giver {base}%.',
    ),
    'tab_confidence_heatmap_numbers_info': (
        'Numbers: the cell number is always shown on every cell.',
        'Номера: номер клетки всегда показан на каждой клетке.',
        'Nummern: die Zellnummer steht immer auf jeder Zelle.',
        'Numeri: il numero della cella è sempre mostrato su ogni cella.',
        'Numre: feltnummeret vises altid på hvert felt.',
    ),
    'tab_hard_residues_card_title': ('Wanted stickers', 'Нужные стикеры', 'Gesuchte Sticker', 'Sticker cercati', 'Eftersøgte klistermærker'),
    'tab_hard_residues_card_subtitle': ('{unknown} unknown cells', '{unknown} неизвестных клеток', '{unknown} unbekannte Zellen', '{unknown} celle sconosciute', '{unknown} ukendte felter'),
    'tab_hard_residues_big_title': (
        'Wanted stickers · unknown cells and their sticker numbers',
        'Нужные стикеры · неизвестные клетки и их номера',
        'Gesuchte Sticker · unbekannte Zellen und ihre Nummern',
        'Sticker cercati · celle sconosciute e i loro numeri',
        'Eftersøgte klistermærker · ukendte felter og deres numre',
    ),
    'tab_hard_residues_description': (
        'No rule predicts the unknown cells better than a guess, so each one is equally uncertain. MAGENTA: unknown cells inside the 9×9 block (stickers 1–81), where a picture or letters could show up. ORANGE: unknown cells in the tail (82–108). Every cell is printed 6 times: cell n = stickers n, n+108, n+216, n+324, n+432, n+540.',
        'Ни одно правило не угадывает неизвестные клетки лучше простой догадки, поэтому все они одинаково неизвестны. ПУРПУРНЫЕ: неизвестные клетки в блоке 9×9 (стикеры 1–81), где может проявиться рисунок или буквы. ОРАНЖЕВЫЕ: неизвестные клетки в хвосте (82–108). Каждая клетка напечатана 6 раз: клетка n = стикеры n, n+108, n+216, n+324, n+432, n+540.',
        'Keine Regel sagt die unbekannten Zellen besser voraus als Raten, daher ist jede gleich unsicher. MAGENTA: unbekannte Zellen im 9×9-Block (Sticker 1–81), wo ein Bild oder Buchstaben erscheinen könnten. ORANGE: unbekannte Zellen im Schwanz (82–108). Jede Zelle ist 6-mal gedruckt: Zelle n = Sticker n, n+108, n+216, n+324, n+432, n+540.',
        "Nessuna regola prevede le celle sconosciute meglio di un'ipotesi, quindi ognuna è ugualmente incerta. MAGENTA: celle sconosciute nel blocco 9×9 (sticker 1–81), dove potrebbe apparire un'immagine o delle lettere. ARANCIONE: celle sconosciute nella coda (82–108). Ogni cella è stampata 6 volte: cella n = sticker n, n+108, n+216, n+324, n+432, n+540.",
        'Ingen regel forudsiger de ukendte felter bedre end et gæt, så hvert felt er lige usikkert. MAGENTA: ukendte felter i 9×9-blokken (klistermærker 1–81), hvor et billede eller bogstaver kunne dukke op. ORANGE: ukendte felter i halen (82–108). Hvert felt er trykt 6 gange: felt n = klistermærker n, n+108, n+216, n+324, n+432, n+540.',
    ),
    'tab_hard_residues_numbers_info': (
        "Numbers: the cell number is always shown on unknown cells; 'Show numbers' adds it on known cells.",
        'Номера: номер всегда показан на неизвестных клетках; «Показать номера» добавляет его на известные.',
        'Nummern: die Zellnummer steht immer auf unbekannten Zellen; «Nummern anzeigen» ergänzt sie auf bekannten.',
        'Numeri: il numero è sempre mostrato sulle celle sconosciute; «Mostra numeri» lo aggiunge su quelle note.',
        'Numre: nummeret vises altid på ukendte felter; «Vis numre» tilføjer det på kendte.',
    ),
}

I18N: dict[str, dict[str, str]] = {
    lang: {k: vals[i] for k, vals in _I18N_DATA.items()}
    for i, lang in enumerate(LANGS)
}


def blend_to_white(rgb, conf):
    w = max(0.0, min(1.0, 1.0 - conf))
    r, g, b = rgb
    return (int(r + (255 - r) * w),
            int(g + (255 - g) * w),
            int(b + (255 - b) * w))


def hex_of(rgb):
    return '#{:02x}{:02x}{:02x}'.format(*rgb)


def _contrast_text_color(hex_color):
    if not hex_color or not hex_color.startswith('#') or len(hex_color) < 7:
        return '#222222'
    r = int(hex_color[1:3], 16)
    g = int(hex_color[3:5], 16)
    b = int(hex_color[5:7], 16)
    L = 0.299 * r + 0.587 * g + 0.114 * b
    return '#000000' if L > 140 else '#f0f0f0'


def count_stickers_found():
    try:
        if not STICKER_DIR.exists():
            return STICKERS_FOUND_FALLBACK
        seen = set()
        for f in STICKER_DIR.iterdir():
            if (f.is_file() and f.stem.isdigit()
                    and f.suffix.lower() in ('.jpg', '.jpeg', '.png')):
                seen.add(f.stem)
        for sub in ('slesh', 'dash', 'dot'):
            d = STICKER_DIR / 'resized' / sub
            if not d.exists():
                continue
            for f in d.iterdir():
                if (f.is_file() and f.stem.isdigit()
                        and f.suffix.lower() in ('.jpg', '.jpeg', '.png')):
                    seen.add(f.stem)
        return len(seen) if seen else STICKERS_FOUND_FALLBACK
    except Exception:
        return STICKERS_FOUND_FALLBACK


def chains_for(n):
    return [n + 108 * k for k in range(6)]


def is_top(n):
    return n <= BLOCK_LAST


def pct(x):
    return f'{x * 100:.1f}'


def same_class(a, b, period):
    return (a - b) % period == 0


def zone_weights():
    tg = sum(1 for n, s in KNOWN.items() if is_top(n) and s == 'G')
    tr = sum(1 for n, s in KNOWN.items() if is_top(n) and s == 'R')
    bg = sum(1 for n, s in KNOWN.items() if not is_top(n) and s == 'G')
    by = sum(1 for n, s in KNOWN.items() if not is_top(n) and s == 'Y')
    return tg / (tg + tr), bg / (bg + by)


def grid_known_only():
    return [KNOWN.get(n, 'K') for n in CELL_NUMBERS]


def mod54_guess(known, n):
    bucket = Counter(s for k, s in known.items() if k != n and same_class(k, n, 54))
    if not bucket:
        return 'G'
    top = bucket.most_common(1)[0][0]
    if is_top(n) and top == 'Y':
        others = {s: c for s, c in bucket.items() if s != 'Y'}
        top = max(others, key=others.get) if others else 'G'
    elif (not is_top(n)) and top == 'R':
        others = {s: c for s, c in bucket.items() if s != 'R'}
        top = max(others, key=others.get) if others else 'G'
    return top


def predict_mod54():
    return [KNOWN[n] if n in KNOWN else mod54_guess(KNOWN, n) for n in CELL_NUMBERS]


def multi_guess(known, n, min_agree):
    votes = Counter()
    for period in PERIODS:
        colors = [known[p] for p in CELL_NUMBERS
                  if p != n and p in known and same_class(p, n, period)]
        valid = [c for c in colors
                 if not (is_top(n) and c == 'Y')
                 and not (not is_top(n) and c == 'R')]
        if not valid:
            continue
        ccount = Counter(valid)
        if len(ccount) == 1:
            votes[next(iter(ccount))] += 1
        else:
            votes[ccount.most_common(1)[0][0]] += 0.5
    if votes:
        color, score = votes.most_common(1)[0]
        if score >= min_agree:
            return color
    return None


def predict_multi(min_agree):
    return [KNOWN[n] if n in KNOWN else (multi_guess(KNOWN, n, min_agree) or 'K')
            for n in CELL_NUMBERS]


def sample_random(seed):
    rng = random.Random(seed)
    tg, bg = zone_weights()
    out = []
    for n in CELL_NUMBERS:
        if n in KNOWN:
            out.append(KNOWN[n])
        elif is_top(n):
            out.append('G' if rng.random() < tg else 'R')
        else:
            out.append('G' if rng.random() < bg else 'Y')
    return out


def _model_add(n, known, zoned, members, weight, totals):
    vals = [known[q] for q in members
            if q != n and q in known and (not zoned or is_top(q) == is_top(n))]
    if vals:
        for s in totals:
            totals[s] += vals.count(s) / len(vals) * weight


def model_predict(n, known, zoned):
    totals = {'G': 0.0, 'R': 0.0, 'Y': 0.0}
    for period, weight in MODEL_PERIOD_WEIGHTS.items():
        _model_add(n, known, zoned,
                   [q for q in CELL_NUMBERS if same_class(q, n, period)], weight, totals)
    _model_add(n, known, zoned,
               [q for q in CELL_NUMBERS if same_class(q, n, 9)], MODEL_LINE_WEIGHT, totals)
    _model_add(n, known, zoned,
               [q for q in CELL_NUMBERS if (q - 1) // 9 == (n - 1) // 9],
               MODEL_LINE_WEIGHT, totals)
    allowed = ('G', 'R') if is_top(n) else ('G', 'Y')
    for s in totals:
        if s not in allowed:
            totals[s] = 0.0
    total = sum(totals.values())
    if total <= 0:
        return 'G', 1.0
    best = max(('G', 'R', 'Y'), key=lambda s: totals[s])
    return best, round(totals[best] / total, 3)


def model_table(known, zoned):
    return {n: (known[n], 1.0) if n in known else model_predict(n, known, zoned)
            for n in CELL_NUMBERS}


def zone_guess(known, n):
    c = Counter(s for k, s in known.items() if is_top(k) == is_top(n))
    return c.most_common(1)[0][0] if c else 'G'


def without(n):
    return {k: v for k, v in KNOWN.items() if k != n}


def loo_accuracy(rule):
    return sum(rule(without(n), n) == s for n, s in KNOWN.items()) / len(KNOWN)


def multi_check(min_agree):
    filled = right = 0
    for n, s in KNOWN.items():
        guess = multi_guess(without(n), n, min_agree)
        if guess is not None:
            filled += 1
            right += guess == s
    return filled / len(KNOWN), (right / filled if filled else 0.0)


def model_check():
    return {n: model_predict(n, without(n), True)[0] == s for n, s in KNOWN.items()}


def piece_gap(layout, cell_px):
    return max(4, cell_px // 4) if layout == PIECE_LAYOUT else 0


def cell_rc(p, layout):
    if layout == PIECE_LAYOUT:
        return p % 9, p // 9
    cols = LAYOUTS[layout][1]
    return p // cols, p % cols


def cell_xy(p, layout, cell_px):
    r, c = cell_rc(p, layout)
    return c * cell_px + (piece_gap(layout, cell_px) if c >= 9 else 0), r * cell_px


def _font(size):
    for name in ('arial.ttf', 'Arial.ttf', 'segoeui.ttf', 'DejaVuSans.ttf'):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def _ink(rgb):
    return (0, 0, 0) if 0.299 * rgb[0] + 0.587 * rgb[1] + 0.114 * rgb[2] > 140 else (255, 255, 255)


def _centre(draw, box, text, font, fill, dy=0):
    x, y, size = box
    tb = draw.textbbox((0, 0), text, font=font)
    draw.text((x + (size - (tb[2] - tb[0])) // 2 - tb[0],
               y + (size - (tb[3] - tb[1])) // 2 - tb[1] + dy), text, fill=fill, font=font)


def make_grid_image(colors, layout, cell_px, labels=None, symbols=None):
    rows, cols = LAYOUTS[layout]
    margin = cell_px // 2 + 8 if layout == PIECE_LAYOUT else 0
    img = Image.new('RGB', (margin + cols * cell_px + piece_gap(layout, cell_px),
                            rows * cell_px), (0, 0, 0))
    draw = ImageDraw.Draw(img)
    num_font = _font(max(9, int(round(cell_px * (0.24 if symbols else 0.34)))))
    sym_font = _font(max(10, int(round(cell_px * 0.55))))
    edge = 1 if cell_px >= 24 else 0
    for n in CELL_NUMBERS:
        p = n - 1
        x, y = cell_xy(p, layout, cell_px)
        x += margin
        color = colors[p]
        draw.rectangle([x, y, x + cell_px - 1 - edge, y + cell_px - 1 - edge], fill=color)
        ink = _ink(color)
        text = labels.get(n, '') if labels else ''
        glyph = GLYPHS.get(symbols[p], '') if symbols and cell_px >= 18 else ''
        if glyph:
            _centre(draw, (x, y, cell_px), glyph, sym_font, ink, cell_px // 10 if text else 0)
        if text and cell_px >= 12:
            if glyph:
                tb = draw.textbbox((0, 0), text, font=num_font)
                draw.text((x + 3 - tb[0], y + 2 - tb[1]), text, fill=ink, font=num_font)
            else:
                _centre(draw, (x, y, cell_px), text, num_font, ink)
    if margin:
        row_font = _font(max(10, int(round(cell_px * 0.4))))
        for r in range(9):
            _centre(draw, ((margin - cell_px) // 2, r * cell_px, cell_px),
                    PIECE_LETTERS[r], row_font, (200, 200, 200))
    return img


def cells_rgb(cells):
    return [CMAP[s] for s in cells]


def render(colors, layout, cell_px, path, labels=None, symbols=None):
    make_grid_image(colors, layout, cell_px, labels, symbols).save(path, dpi=(300, 300))


def _load_fonts_sized(title_px, legend_px):
    title_font = legend_font = None
    for name in ('arial.ttf', 'Arial.ttf', 'segoeui.ttf', 'DejaVuSans.ttf'):
        try:
            title_font = ImageFont.truetype(name, title_px)
            legend_font = ImageFont.truetype(name, legend_px)
            break
        except OSError:
            continue
    if title_font is None:
        title_font = ImageFont.load_default()
        legend_font = ImageFont.load_default()
    return title_font, legend_font


def render_with_legend(grid_img, legend_items, title, subtitle, path, cell_px):
    gw, gh = grid_img.size
    title_px = max(16, int(round(cell_px * 0.55)))
    sub_px = max(11, int(round(cell_px * 0.32)))
    legend_px = max(11, int(round(cell_px * 0.36)))
    swatch = max(18, int(round(cell_px * 0.85)))
    pad = max(28, int(round(cell_px * 0.85)))
    title_to_grid_gap = max(18, int(round(cell_px * 0.5)))
    grid_to_legend_gap = max(20, int(round(cell_px * 0.6)))
    title_to_sub_gap = max(6, int(round(cell_px * 0.15)))
    item_gap = max(18, int(round(cell_px * 0.55)))
    label_gap = max(8, int(round(cell_px * 0.2)))
    border = max(1, int(round(cell_px * 0.05)))
    title_font, legend_font = _load_fonts_sized(title_px, legend_px)
    sub_font = legend_font if abs(sub_px - legend_px) < 2 else (
        _load_fonts_sized(sub_px, sub_px)[1])
    tmp_draw = ImageDraw.Draw(Image.new('RGB', (1, 1)))
    tb = tmp_draw.textbbox((0, 0), title, font=title_font)
    title_h = tb[3] - tb[1]
    title_w = tb[2] - tb[0]
    sub_h = 0
    sub_w = 0
    if subtitle:
        sb = tmp_draw.textbbox((0, 0), subtitle, font=sub_font)
        sub_h = sb[3] - sb[1]
        sub_w = sb[2] - sb[0]
    total_title_h = title_h + (title_to_sub_gap + sub_h if subtitle else 0)
    items_w = []
    for color_hex, label in legend_items:
        bbox = tmp_draw.textbbox((0, 0), label, font=legend_font)
        items_w.append(swatch + label_gap + (bbox[2] - bbox[0]))
    legend_total_w = (sum(items_w) + item_gap * (len(legend_items) - 1)
                      if legend_items else 0)
    canvas_w = max(gw + 2 * pad, legend_total_w + 2 * pad,
                   title_w + 2 * pad, sub_w + 2 * pad)
    canvas_h = (pad + total_title_h + title_to_grid_gap + gh
                + grid_to_legend_gap + swatch + pad)
    img = Image.new('RGB', (canvas_w, canvas_h), (255, 255, 255))
    draw = ImageDraw.Draw(img)
    cur_y = pad
    tb = draw.textbbox((0, 0), title, font=title_font)
    tw = tb[2] - tb[0]
    draw.text(((canvas_w - tw) // 2, cur_y - tb[1]),
              title, fill=(20, 20, 30), font=title_font)
    cur_y += title_h
    if subtitle:
        cur_y += title_to_sub_gap
        sb = draw.textbbox((0, 0), subtitle, font=sub_font)
        sw = sb[2] - sb[0]
        draw.text(((canvas_w - sw) // 2, cur_y - sb[1]),
                  subtitle, fill=(90, 90, 110), font=sub_font)
        cur_y += sub_h
    cur_y += title_to_grid_gap
    gx = (canvas_w - gw) // 2
    gy = cur_y
    draw.rectangle([gx - border, gy - border,
                    gx + gw + border, gy + gh + border],
                   outline=(120, 120, 130), width=border)
    img.paste(grid_img, (gx, gy))
    cur_y = gy + gh + grid_to_legend_gap
    lx = (canvas_w - legend_total_w) // 2
    swatch_border = max(1, border // 2)
    for (color_hex, label), w in zip(legend_items, items_w):
        draw.rectangle([lx, cur_y, lx + swatch, cur_y + swatch],
                       fill=color_hex, outline=(40, 40, 50), width=swatch_border)
        bbox = draw.textbbox((0, 0), label, font=legend_font)
        th = bbox[3] - bbox[1]
        draw.text((lx + swatch + label_gap,
                   cur_y + (swatch - th) // 2 - bbox[1]),
                  label, fill=(20, 20, 30), font=legend_font)
        lx += w + item_gap
    img.save(path, dpi=(300, 300))


def cells_guess(table):
    return [CMAP[KNOWN[n]] if n in KNOWN
            else blend_to_white(CMAP[table[n][0]], GUESS_CONF) for n in CELL_NUMBERS]


def guess_symbols(table):
    return [table[n][0] for n in CELL_NUMBERS]


def cells_model_check():
    return [(CHECK_RIGHT if MODEL_CHECK[n] else CHECK_WRONG) if n in KNOWN
            else DIM_PRED for n in CELL_NUMBERS]


def cells_wanted():
    return [DIM_KNOWN if n in KNOWN else (MAGENTA if is_top(n) else ORANGE)
            for n in CELL_NUMBERS]


def piece_symbols(fill):
    return [KNOWN.get(n) or (PRED_ZONED[n][0] if fill else 'K') for n in CELL_NUMBERS]


def piece_colors(fill):
    return cells_guess(PRED_ZONED) if fill else cells_rgb(grid_known_only())


def compute_facts():
    found = max(count_stickers_found(), STICKERS_FOUND_FALLBACK)
    known = len(KNOWN)
    right = sum(MODEL_CHECK.values())
    return {
        'found': found, 'known': known, 'unknown': 108 - known,
        'repeats': found - known,
        'base': pct(loo_accuracy(zone_guess)),
        'acc_mod54': pct(loo_accuracy(mod54_guess)),
        'acc_model_z': pct(right / known),
        'acc_model_x': pct(loo_accuracy(lambda kn, n: model_predict(n, kn, False)[0])),
        'mc_right': right, 'mc_wrong': known - right,
    }


PRED_ZONED = model_table(KNOWN, True)
PRED_CROSS = model_table(KNOWN, False)
MODEL_CHECK = model_check()
WANTED = [n for n in CELL_NUMBERS if n not in KNOWN]
FACTS = compute_facts()


class App:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.lang: str = DEFAULT_LANG
        self._tr_widgets: list = []
        self._lang_buttons: dict = {}
        self._title_label: tk.Label | None = None
        self._restore_binding = None
        self._drag_x = 0
        self._drag_y = 0
        self._resize_w0 = 0
        self._resize_h0 = 0
        self._resize_x0 = 0
        self._resize_y0 = 0

        root.title(self.tr('app_title'))
        root.overrideredirect(True)
        root.geometry('980x920+50+30')
        root.configure(bg=BG_BASE)

        self._init_styles()

        self.layout_var = tk.StringVar(value='9x12')
        self.cell_var = tk.StringVar(value='64')
        _script_dir = Path(__file__).resolve().parent
        self.out_var = tk.StringVar(value=str(_script_dir / 'samples'))
        self.seed_var = tk.StringVar(value='1')
        self.count_var = tk.StringVar(value='6')
        self.agree_var = tk.StringVar(value='2')
        self.show_numbers_var = tk.BooleanVar(value=False)
        self.show_glyphs_var = tk.BooleanVar(value=True)
        self.status_var = tk.StringVar(value=self.tr('ready_status'))
        self.preview_stats = tk.StringVar(value='')
        self.pill_line1_var = tk.StringVar(value='')
        self.pill_line2_var = tk.StringVar(value='')

        self.active_tab = TAB_KEYS[0]
        self.sidebar_cards: dict = {}
        self._preview_after_id = None
        self.facts = FACTS
        self.piece_fill_var = tk.BooleanVar(value=False)
        self._multi_status = None

        self._build_title_bar(root)
        self._build_header(root)
        self._build_settings_ribbon(root)
        self._build_bottom_bar(root)
        self._build_body(root)
        self._build_resize_grip(root)

        self._update_header_pill()
        self._select_tab(self.active_tab)

    def tr(self, key: str, **kwargs) -> str:
        lang = getattr(self, 'lang', DEFAULT_LANG)
        table = I18N.get(lang, I18N[DEFAULT_LANG])
        template = table.get(key) or I18N[DEFAULT_LANG].get(key, key)
        if kwargs:
            try:
                return template.format(**kwargs)
            except (KeyError, IndexError):
                return template
        return template

    def ttr(self, key: str) -> str:
        return self.tr(key, **self.facts)

    def _layout_for(self, key: str) -> str:
        if key == 'by_piece':
            return PIECE_LAYOUT
        layout = self.layout_var.get()
        return layout if layout in LAYOUTS else '9x12'

    def _layout_tag(self, layout: str) -> str:
        return 'bypiece' if layout == PIECE_LAYOUT else layout

    def _refresh_multi_status(self) -> None:
        if self._multi_status is None:
            return
        try:
            n = int(self.agree_var.get())
        except ValueError:
            return
        cov, acc = multi_check(n)
        self._multi_status.configure(text=self.tr(
            'controls_status_multi_live', n=n, cov=pct(cov), acc=pct(acc),
            base=self.facts['base']))

    def _on_piece_fill(self) -> None:
        self._rebuild_legend_strip(self.active_tab)
        self._update_preview()

    def _add_tr(self, widget: tk.Widget, key: str, **kwargs) -> None:
        self._tr_widgets.append((widget, key, kwargs))
        widget.configure(text=self.tr(key, **kwargs))

    def _set_language(self, lang: str) -> None:
        if lang not in I18N or lang == self.lang:
            return
        self.lang = lang
        for widget, key, kwargs in self._tr_widgets:
            try:
                widget.configure(text=self.tr(key, **kwargs))
            except tk.TclError:
                pass
        try:
            self.root.title(self.tr('app_title'))
        except tk.TclError:
            pass
        if self._title_label is not None:
            self._title_label.configure(text=self.tr('app_title'))
        self.status_var.set(self.tr('ready_status'))
        self._rebuild_sidebar_labels()
        self._refresh_preview_label()
        self._update_header_pill()
        self._select_tab(self.active_tab)
        for code, btn in self._lang_buttons.items():
            active = (code == lang)
            btn.configure(bg=ACCENT if active else BG_PANEL,
                          fg='white' if active else TEXT_SECONDARY)

    def _build_title_bar(self, parent: tk.Misc) -> None:
        self.title_bar = tk.Frame(parent, bg=BG_PANEL, height=36)
        self.title_bar.pack(side='top', fill='x')
        self.title_bar.pack_propagate(False)

        logo_wrap = tk.Frame(self.title_bar, bg=BG_PANEL, cursor='fleur')
        logo_wrap.pack(side='left', padx=(10, 0))

        logo_sq = tk.Frame(logo_wrap, bg=ACCENT, width=22, height=22,
                           cursor='fleur')
        logo_sq.pack(side='left', pady=7)
        logo_sq.pack_propagate(False)

        self._title_label = tk.Label(logo_wrap, text=self.tr('app_title'),
                                     font=('Segoe UI', 10, 'bold'),
                                     bg=BG_PANEL, fg=TEXT_PRIMARY,
                                     cursor='fleur')
        self._title_label.pack(side='left', padx=(10, 0))

        ctrl_frame = tk.Frame(self.title_bar, bg=BG_PANEL)
        ctrl_frame.pack(side='right')

        close_btn = tk.Label(ctrl_frame, text='✕',
                             bg=BG_PANEL, fg=TEXT_PRIMARY,
                             font=('Segoe UI', 11),
                             width=4, height=2, cursor='hand2')
        close_btn.pack(side='right')
        close_btn.bind('<Enter>',
                       lambda e: close_btn.configure(bg='#c83838', fg='white'))
        close_btn.bind('<Leave>',
                       lambda e: close_btn.configure(bg=BG_PANEL,
                                                     fg=TEXT_PRIMARY))
        close_btn.bind('<Button-1>', lambda e: self.root.destroy())

        min_btn = tk.Label(ctrl_frame, text='–',
                           bg=BG_PANEL, fg=TEXT_PRIMARY,
                           font=('Segoe UI', 11),
                           width=4, height=2, cursor='hand2')
        min_btn.pack(side='right')
        min_btn.bind('<Enter>',
                     lambda e: min_btn.configure(bg=BG_HOVER))
        min_btn.bind('<Leave>',
                     lambda e: min_btn.configure(bg=BG_PANEL))
        min_btn.bind('<Button-1>', lambda e: self._minimize())

        lang_frame = tk.Frame(ctrl_frame, bg=BG_PANEL)
        lang_frame.pack(side='right', padx=(0, 14))
        for code in LANGS:
            btn = tk.Label(lang_frame, text=code.upper(),
                           bg=BG_PANEL,
                           fg=TEXT_SECONDARY,
                           font=('Segoe UI', 8, 'bold'),
                           width=4, height=2, cursor='hand2')
            btn.pack(side='left', padx=1)
            btn.bind('<Button-1>',
                     lambda e, c=code: self._set_language(c))

            def _enter(_e, b=btn, c=code):
                if c != self.lang:
                    b.configure(bg=BG_HOVER)

            def _leave(_e, b=btn, c=code):
                if c != self.lang:
                    b.configure(bg=BG_PANEL)

            btn.bind('<Enter>', _enter)
            btn.bind('<Leave>', _leave)
            self._lang_buttons[code] = btn
        active = self._lang_buttons[self.lang]
        active.configure(bg=ACCENT, fg='white')

        for w in (self.title_bar, logo_wrap, logo_sq, self._title_label):
            w.bind('<ButtonPress-1>', self._drag_start)
            w.bind('<B1-Motion>', self._drag_motion)

    def _drag_start(self, event) -> None:
        self._drag_x = event.x_root - self.root.winfo_x()
        self._drag_y = event.y_root - self.root.winfo_y()

    def _drag_motion(self, event) -> None:
        x = event.x_root - self._drag_x
        y = event.y_root - self._drag_y
        self.root.geometry(f'+{x}+{y}')

    def _minimize(self) -> None:
        self.root.overrideredirect(False)
        try:
            self.root.iconify()
        except tk.TclError:
            self.root.overrideredirect(True)
            return
        self._restore_binding = self.root.bind('<Map>',
                                               self._on_restored, add='+')

    def _on_restored(self, event) -> None:
        if event.widget is self.root:
            self.root.overrideredirect(True)
            if self._restore_binding is not None:
                try:
                    self.root.unbind('<Map>', self._restore_binding)
                except tk.TclError:
                    pass
                self._restore_binding = None

    def _build_resize_grip(self, parent: tk.Misc) -> None:
        self.resize_grip = tk.Frame(parent, bg=BG_PANEL, width=16, height=16,
                                    cursor='size_nw_se')
        self.resize_grip.place(relx=1.0, rely=1.0, anchor='se')
        self.resize_grip.bind('<ButtonPress-1>', self._resize_start)
        self.resize_grip.bind('<B1-Motion>', self._resize_motion)

    def _resize_start(self, event) -> None:
        self._resize_w0 = self.root.winfo_width()
        self._resize_h0 = self.root.winfo_height()
        self._resize_x0 = event.x_root
        self._resize_y0 = event.y_root

    def _resize_motion(self, event) -> None:
        dx = event.x_root - self._resize_x0
        dy = event.y_root - self._resize_y0
        new_w = max(920, self._resize_w0 + dx)
        new_h = max(880, self._resize_h0 + dy)
        self.root.geometry(f'{new_w}x{new_h}')

    def _init_styles(self) -> None:
        style = ttk.Style()
        try:
            style.theme_use('clam')
        except tk.TclError:
            pass
        style.configure('TFrame', background=BG_BASE)
        style.configure('TLabel', background=BG_BASE, foreground=TEXT_PRIMARY)
        for name in ('Ribbon.TCombobox', 'Ribbon.TSpinbox'):
            style.configure(name, fieldbackground=BG_INPUT, background=BG_INPUT,
                            foreground=TEXT_PRIMARY, bordercolor=BORDER_SUBTLE,
                            arrowcolor=TEXT_SECONDARY, lightcolor=BG_INPUT,
                            darkcolor=BG_INPUT, insertcolor=TEXT_PRIMARY)
        style.map('Ribbon.TCombobox',
                  fieldbackground=[('readonly', BG_INPUT)],
                  background=[('readonly', BG_INPUT)],
                  foreground=[('readonly', TEXT_PRIMARY)])
        style.configure('Ribbon.TEntry', fieldbackground=BG_INPUT,
                        foreground=TEXT_PRIMARY, bordercolor=BORDER_SUBTLE,
                        insertcolor=TEXT_PRIMARY, lightcolor=BG_INPUT,
                        darkcolor=BG_INPUT)
        style.configure('Accent.Horizontal.TProgressbar',
                        troughcolor=BG_PANEL, bordercolor=BG_PANEL,
                        background=ACCENT, lightcolor=ACCENT, darkcolor=ACCENT_DIM)

    def _build_header(self, parent: tk.Misc) -> None:
        header = tk.Frame(parent, bg=BG_BASE, height=78)
        header.pack(side='top', fill='x', padx=18, pady=(14, 0))
        header.pack_propagate(False)

        left = tk.Frame(header, bg=BG_BASE)
        left.pack(side='left', fill='y')
        self._hdr_title = tk.Label(left, text='',
                                   font=('Segoe UI', 16, 'bold'),
                                   bg=BG_BASE, fg=TEXT_PRIMARY, anchor='w')
        self._hdr_title.pack(anchor='w')
        self._add_tr(self._hdr_title, 'app_title')
        self._hdr_subtitle = tk.Label(left, text='',
                                      font=('Segoe UI', 9),
                                      bg=BG_BASE, fg=TEXT_SECONDARY, anchor='w')
        self._hdr_subtitle.pack(anchor='w', pady=(2, 0))
        self._add_tr(self._hdr_subtitle, 'app_subtitle')

        pill = tk.Frame(header, bg=BG_PANEL, padx=14, pady=8,
                        highlightthickness=1, highlightbackground=BORDER_SUBTLE)
        pill.pack(side='right', anchor='center')
        pill_inner = tk.Frame(pill, bg=BG_PANEL)
        pill_inner.pack()
        tk.Label(pill_inner, textvariable=self.pill_line1_var,
                 font=('Segoe UI', 9),
                 bg=BG_PANEL, fg=TEXT_PRIMARY, anchor='e', justify='right'
                 ).pack(anchor='e')
        tk.Label(pill_inner, textvariable=self.pill_line2_var,
                 font=('Segoe UI', 9),
                 bg=BG_PANEL, fg=TEXT_SECONDARY, anchor='e', justify='right'
                 ).pack(anchor='e', pady=(2, 0))

        for w in (header, left, pill, pill_inner):
            w.bind('<ButtonPress-1>', self._drag_start)
            w.bind('<B1-Motion>', self._drag_motion)

    def _update_header_pill(self) -> None:
        tg, bg_w = zone_weights()
        line1 = '   ·   '.join([
            self.tr('pill_stickers_found', n=self.facts['found']),
            self.tr('pill_lost', n=STICKERS_LOST),
            self.tr('pill_owner_unknown', n=STICKERS_UNKNOWN_OWNER),
        ])
        line2 = '   ·   '.join([
            self.tr('pill_residues_known', n=len(KNOWN)),
            self.tr('pill_top_slash', pct=int(round(tg * 100))),
            self.tr('pill_bottom_slash', pct=int(round(bg_w * 100))),
        ])
        self.pill_line1_var.set(line1)
        self.pill_line2_var.set(line2)

    def _build_settings_ribbon(self, parent: tk.Misc) -> None:
        ribbon = tk.Frame(parent, bg=BG_BASE, height=62)
        ribbon.pack(side='top', fill='x', padx=18, pady=(10, 0))
        ribbon.pack_propagate(False)

        lbl = self._ribbon_label(ribbon, '')
        lbl.pack(side='left', padx=(0, 6))
        self._add_tr(lbl, 'layout_label')
        layout_combo = ttk.Combobox(ribbon, textvariable=self.layout_var,
                                    state='readonly', width=9,
                                    values=list(LAYOUTS),
                                    style='Ribbon.TCombobox')
        layout_combo.pack(side='left', padx=(0, 18))
        layout_combo.bind('<<ComboboxSelected>>',
                          lambda e: self._update_preview())

        lbl = self._ribbon_label(ribbon, '')
        lbl.pack(side='left', padx=(0, 6))
        self._add_tr(lbl, 'cell_size_label')
        ttk.Spinbox(ribbon, from_=16, to=256, increment=16,
                    textvariable=self.cell_var, width=6,
                    style='Ribbon.TSpinbox'
                    ).pack(side='left', padx=(0, 18))

        lbl = self._ribbon_label(ribbon, '')
        lbl.pack(side='left', padx=(0, 6))
        self._add_tr(lbl, 'output_label')
        ttk.Entry(ribbon, textvariable=self.out_var, style='Ribbon.TEntry'
                  ).pack(side='left', fill='x', expand=True, padx=(0, 8))

        browse_btn = self._secondary_button(ribbon, '', self._browse)
        browse_btn.pack(side='left')
        self._add_tr(browse_btn, 'browse_button')

    def _ribbon_label(self, parent: tk.Misc, text: str) -> tk.Label:
        return tk.Label(parent, text=text, font=('Segoe UI', 9),
                        bg=BG_BASE, fg=TEXT_SECONDARY)

    def _primary_button(self, parent: tk.Misc, text: str, cmd) -> tk.Button:
        return tk.Button(parent, text=text, command=cmd,
                         bg=ACCENT, fg='white', bd=0,
                         activebackground=ACCENT_HOVER, activeforeground='white',
                         font=('Segoe UI', 10, 'bold'),
                         padx=18, pady=6, cursor='hand2')

    def _secondary_button(self, parent: tk.Misc, text: str, cmd) -> tk.Button:
        return tk.Button(parent, text=text, command=cmd,
                         bg=BG_CARD, fg=TEXT_PRIMARY, bd=0,
                         activebackground=BG_HOVER, activeforeground=TEXT_PRIMARY,
                         font=('Segoe UI', 9),
                         padx=14, pady=6, cursor='hand2')

    def _build_bottom_bar(self, parent: tk.Misc) -> None:
        bottom = tk.Frame(parent, bg=BG_BASE, height=54)
        bottom.pack(side='bottom', fill='x', padx=18, pady=(8, 14))
        bottom.pack_propagate(False)

        save_btn = self._primary_button(bottom, '', self._save_with_legend)
        save_btn.pack(side='left')
        self._add_tr(save_btn, 'save_legend_button')

        folder_btn = self._secondary_button(bottom, '', self._open_folder)
        folder_btn.pack(side='left', padx=(10, 18))
        self._add_tr(folder_btn, 'open_folder_button')

        show_chk = tk.Checkbutton(bottom, text='',
                                  variable=self.show_numbers_var,
                                  bg=BG_BASE, fg=TEXT_PRIMARY,
                                  activebackground=BG_BASE,
                                  activeforeground=TEXT_PRIMARY,
                                  selectcolor=BG_CARD,
                                  font=('Segoe UI', 9), bd=0,
                                  highlightthickness=0,
                                  cursor='hand2', command=self._update_preview)
        show_chk.pack(side='left')
        self._add_tr(show_chk, 'show_numbers_checkbox')

        self.show_glyphs_check = tk.Checkbutton(
            bottom, variable=self.show_glyphs_var, bg=BG_BASE, fg=TEXT_PRIMARY,
            activebackground=BG_BASE, activeforeground=TEXT_PRIMARY,
            selectcolor=BG_CARD, font=('Segoe UI', 9), bd=0,
            highlightthickness=0, cursor='hand2', command=self._update_preview)
        self.show_glyphs_check.pack(side='left', padx=(0, 12))
        self._add_tr(self.show_glyphs_check, 'show_symbols_checkbox')

        self.progress = ttk.Progressbar(bottom, mode='determinate', length=220,
                                        style='Accent.Horizontal.TProgressbar')
        self.progress.pack(side='right')

        tk.Label(bottom, textvariable=self.status_var,
                 font=('Segoe UI', 9), bg=BG_BASE, fg=TEXT_SECONDARY
                 ).pack(side='right', padx=(0, 14))

    def _build_body(self, parent: tk.Misc) -> None:
        body = tk.Frame(parent, bg=BG_BASE)
        body.pack(side='top', fill='both', expand=True, padx=18, pady=(12, 0))

        sidebar = tk.Frame(body, bg=BG_BASE, width=220)
        sidebar.pack(side='left', fill='y')
        sidebar.pack_propagate(False)
        self._build_sidebar(sidebar)

        content = tk.Frame(body, bg=BG_BASE)
        content.pack(side='left', fill='both', expand=True, padx=(14, 0))

        self.info_card = tk.Frame(content, bg=BG_CARD)
        self.info_card.pack(side='top', fill='x')
        self._info_title = tk.Label(self.info_card, text='',
                                    font=('Segoe UI', 14, 'bold'),
                                    bg=BG_CARD, fg=ACCENT, anchor='w')
        self._info_title.pack(anchor='w', padx=16, pady=(14, 0))
        self._info_subtitle = tk.Label(self.info_card, text='',
                                       font=('Segoe UI', 9),
                                       bg=BG_CARD, fg=TEXT_SECONDARY, anchor='w')
        self._info_subtitle.pack(anchor='w', padx=16, pady=(2, 0))
        self._info_desc = tk.Label(self.info_card, text='',
                                   font=('Segoe UI', 9),
                                   bg=BG_CARD, fg=TEXT_PRIMARY, anchor='nw',
                                   justify='left', wraplength=640)
        self._info_desc.pack(anchor='w', padx=16, pady=(8, 4), fill='x')
        self._info_numbers = tk.Label(self.info_card, text='',
                                      font=('Segoe UI', 8, 'italic'),
                                      bg=BG_CARD, fg=TEXT_DIM, anchor='nw',
                                      justify='left', wraplength=640)
        self._info_numbers.pack(anchor='w', padx=16, pady=(0, 14), fill='x')
        self.info_card.bind('<Configure>', self._on_info_resize)

        self.controls_card = tk.Frame(content, bg=BG_CARD)
        self.controls_card.pack(side='top', fill='x', pady=(10, 0))

        preview_card = tk.LabelFrame(content, text='',
                                     bg=BG_CARD, fg=ACCENT, bd=0,
                                     font=('Segoe UI', 10, 'bold'),
                                     labelanchor='nw', padx=10, pady=8,
                                     highlightthickness=1,
                                     highlightbackground=BORDER_SUBTLE)
        preview_card.pack(side='top', fill='both', expand=True, pady=(10, 0))
        self._preview_card = preview_card
        self._refresh_preview_label()

        self.legend_strip = tk.Frame(preview_card, bg=BG_CARD)
        self.legend_strip.pack(side='bottom', fill='x', pady=(4, 0))

        stats_strip = tk.Frame(preview_card, bg=BG_CARD)
        stats_strip.pack(side='bottom', fill='x', pady=(6, 0))
        tk.Label(stats_strip, textvariable=self.preview_stats,
                 font=('Consolas', 9), bg=BG_CARD, fg=TEXT_SECONDARY,
                 anchor='w').pack(side='left')

        self.preview_canvas = tk.Canvas(preview_card, bg='#000000',
                                        highlightthickness=0,
                                        width=600, height=420)
        self.preview_canvas.pack(side='top', fill='both', expand=True)

        preview_card.bind('<Configure>', self._on_preview_resize)
        self.preview_canvas.bind('<Configure>', self._on_preview_resize)

    def _build_sidebar(self, parent: tk.Frame) -> None:
        hdr = tk.Label(parent, text='', font=('Segoe UI', 8, 'bold'),
                       bg=BG_BASE, fg=TEXT_DIM, anchor='w')
        hdr.pack(anchor='w', padx=4, pady=(2, 6))
        self._add_tr(hdr, 'view_modes_header')
        for key in TAB_KEYS:
            card = tk.Frame(parent, bg=BG_PANEL, height=50, cursor='hand2')
            card.pack(side='top', fill='x', pady=(0, 5))
            card.pack_propagate(False)
            strip = tk.Frame(card, bg=BG_PANEL, width=3)
            strip.pack(side='left', fill='y')
            inner = tk.Frame(card, bg=BG_PANEL)
            inner.pack(side='left', fill='both', expand=True, padx=(10, 6))
            title_lbl = tk.Label(inner, text='',
                                 font=('Segoe UI', 10, 'bold'),
                                 bg=BG_PANEL, fg=TEXT_PRIMARY, anchor='w',
                                 cursor='hand2')
            title_lbl.pack(anchor='w', pady=(6, 0), fill='x')
            sub_lbl = tk.Label(inner, text='',
                               font=('Segoe UI', 8),
                               bg=BG_PANEL, fg=TEXT_DIM, anchor='w',
                               cursor='hand2')
            sub_lbl.pack(anchor='w', pady=(1, 0), fill='x')
            self.sidebar_cards[key] = {
                'card': card, 'strip': strip, 'inner': inner,
                'title': title_lbl, 'sub': sub_lbl,
            }
            title_lbl.configure(text=self.ttr(f'tab_{key}_card_title'))
            sub_lbl.configure(text=self.ttr(f'tab_{key}_card_subtitle'))
            for w in (card, strip, inner, title_lbl, sub_lbl):
                w.bind('<Button-1>', lambda e, k=key: self._select_tab(k))
                w.bind('<Enter>', lambda e, k=key: self._hover_card(k, True))
                w.bind('<Leave>', lambda e, k=key: self._hover_card(k, False))

    def _rebuild_sidebar_labels(self) -> None:
        for key, c in self.sidebar_cards.items():
            c['title'].configure(text=self.ttr(f'tab_{key}_card_title'))
            c['sub'].configure(text=self.ttr(f'tab_{key}_card_subtitle'))

    def _refresh_preview_label(self) -> None:
        if hasattr(self, '_preview_card'):
            self._preview_card.configure(text=f' {self.tr("live_preview")} ')

    def _hover_card(self, key: str, entered: bool) -> None:
        if key == self.active_tab:
            return
        bg = BG_HOVER if entered else BG_PANEL
        c = self.sidebar_cards[key]
        c['card'].configure(bg=bg)
        c['inner'].configure(bg=bg)
        c['title'].configure(bg=bg)
        c['sub'].configure(bg=bg)
        c['strip'].configure(bg=bg)

    def _select_tab(self, key: str) -> None:
        if key not in TAB_META:
            return
        self.active_tab = key
        for k, c in self.sidebar_cards.items():
            active = (k == key)
            card_bg = BG_CARD if active else BG_PANEL
            c['card'].configure(bg=card_bg)
            c['inner'].configure(bg=card_bg)
            c['title'].configure(bg=card_bg,
                                 fg=TEXT_PRIMARY if active else TEXT_SECONDARY)
            c['sub'].configure(bg=card_bg,
                               fg=TEXT_SECONDARY if active else TEXT_DIM)
            c['strip'].configure(bg=ACCENT if active else card_bg)

        self._info_title.configure(text=self.ttr(f'tab_{key}_big_title'))
        self._info_subtitle.configure(text=self.ttr(f'tab_{key}_card_subtitle'))
        self._info_desc.configure(text=self.ttr(f'tab_{key}_description'))
        self._info_numbers.configure(text=self.ttr(f'tab_{key}_numbers_info'))

        self._build_controls_for_tab(key)
        self._rebuild_legend_strip(key)
        self._update_preview()

    def _build_controls_for_tab(self, key: str) -> None:
        for w in self.controls_card.winfo_children():
            w.destroy()
        self._multi_status = None
        inner = tk.Frame(self.controls_card, bg=BG_CARD)
        inner.pack(fill='both', expand=True, padx=14, pady=12)

        if key == 'known_only':
            self._controls_status(inner, self.ttr('controls_status_known_only'))
            self._controls_status(inner, self.ttr('controls_facts'))
            return
        if key == 'by_piece':
            tk.Checkbutton(inner, text=self.tr('piece_fill_checkbox'),
                           variable=self.piece_fill_var,
                           bg=BG_CARD, fg=TEXT_PRIMARY,
                           activebackground=BG_CARD,
                           activeforeground=TEXT_PRIMARY,
                           selectcolor=BG_PANEL, font=('Segoe UI', 9), bd=0,
                           highlightthickness=0, cursor='hand2',
                           command=self._on_piece_fill).pack(anchor='w')
            return
        if key == 'pattern_mod54':
            self._controls_status(inner,
                                  self.ttr('controls_status_pattern_mod54'))
            return
        if key == 'multi_period':
            self._controls_label(inner, self.tr('min_agree_label')
                                 ).pack(side='left', padx=(0, 8))
            sp = ttk.Spinbox(inner, from_=1, to=8,
                             textvariable=self.agree_var, width=6,
                             style='Ribbon.TSpinbox',
                             command=self._update_preview)
            sp.pack(side='left')
            sp.bind('<KeyRelease>', lambda e: self._update_preview())
            self._multi_status = tk.Label(inner, text='', font=('Segoe UI', 9),
                                          bg=BG_CARD, fg=TEXT_SECONDARY,
                                          anchor='w', justify='left')
            self._multi_status.pack(side='left', padx=(16, 0))
            self._refresh_multi_status()
            return
        if key == 'random_sampler':
            self._controls_label(inner, self.tr('seed_label')
                                 ).pack(side='left', padx=(0, 6))
            sp = ttk.Spinbox(inner, from_=0, to=999999,
                             textvariable=self.seed_var, width=10,
                             style='Ribbon.TSpinbox',
                             command=self._update_preview)
            sp.pack(side='left', padx=(0, 18))
            sp.bind('<KeyRelease>', lambda e: self._update_preview())
            self._controls_label(inner, self.tr('samples_label')
                                 ).pack(side='left', padx=(0, 6))
            ttk.Spinbox(inner, from_=1, to=999,
                        textvariable=self.count_var, width=6,
                        style='Ribbon.TSpinbox'
                        ).pack(side='left', padx=(0, 18))
            tk.Button(inner, text=self.tr('reroll_button'),
                      command=self._reroll,
                      bg=BG_HOVER, fg=TEXT_PRIMARY, bd=0,
                      activebackground=ACCENT_DIM, activeforeground='white',
                      font=('Segoe UI', 9), padx=14, pady=4, cursor='hand2'
                      ).pack(side='left')
            return
        if key == 'export_bundle':
            tk.Button(inner, text=self.tr('export_button'),
                      command=self._gen_compare,
                      bg=ACCENT, fg='white', bd=0,
                      activebackground=ACCENT_HOVER, activeforeground='white',
                      font=('Segoe UI', 10, 'bold'),
                      padx=22, pady=8, cursor='hand2'
                      ).pack(side='left')
            self._controls_status(inner,
                                  self.tr('controls_status_export_bundle'),
                                  side='left', padx=(16, 0))
            return
        if key in ('prediction_zoned', 'prediction_cross'):
            table = PRED_ZONED if key == 'prediction_zoned' else PRED_CROSS
            guessed = [table[n][0] for n in CELL_NUMBERS if n not in KNOWN]
            cnt = Counter(guessed)
            acc = self.facts['acc_model_z' if key == 'prediction_zoned'
                             else 'acc_model_x']
            line = self.tr('controls_model_line', guessed=len(guessed),
                           g=cnt.get('G', 0), r=cnt.get('R', 0),
                           y=cnt.get('Y', 0), acc=acc, base=self.facts['base'])
            tk.Label(inner, text=line, font=('Consolas', 9),
                     bg=BG_CARD, fg=TEXT_PRIMARY).pack(anchor='w')
            return
        if key == 'confidence_heatmap':
            for color, label in ((CHECK_RIGHT, self.tr('swatch_model_right')),
                                 (CHECK_WRONG, self.tr('swatch_model_wrong')),
                                 (DIM_PRED, self.tr('swatch_unknown_dark'))):
                swatch = tk.Frame(inner, bg=hex_of(color), width=18, height=18)
                swatch.pack(side='left', padx=(0, 4))
                swatch.pack_propagate(False)
                tk.Label(inner, text=label, font=('Consolas', 9),
                         bg=BG_CARD, fg=TEXT_PRIMARY
                         ).pack(side='left', padx=(0, 14))
            tk.Label(inner, text=self.ttr('controls_check_line'),
                     font=('Consolas', 9), bg=BG_CARD, fg=TEXT_SECONDARY
                     ).pack(side='left', padx=(8, 0))
            return
        if key == 'hard_residues':
            tk.Label(inner, text=self.tr('controls_wanted_header'),
                     font=('Segoe UI', 9), bg=BG_CARD, fg=TEXT_SECONDARY,
                     anchor='w').pack(anchor='w')
            box = tk.Text(inner, height=4, bg=BG_INPUT, fg=TEXT_PRIMARY,
                          font=('Consolas', 8), bd=0, highlightthickness=0,
                          wrap='none')
            lines = []
            for n in WANTED:
                tag = self.tr('wanted_tag_block' if is_top(n) else 'wanted_tag_tail')
                lines.append('{:>3d} ({:<7s}): {}'.format(
                    n, tag, ', '.join(f'#{x}' for x in chains_for(n))))
            box.insert('1.0', '\n'.join(lines))
            box.configure(state='disabled')
            box.pack(anchor='w', fill='x', pady=(4, 0))

    def _controls_label(self, parent: tk.Misc, text: str) -> tk.Label:
        return tk.Label(parent, text=text, font=('Segoe UI', 9),
                        bg=BG_CARD, fg=TEXT_SECONDARY)

    def _controls_status(self, parent: tk.Misc, text: str,
                          side: str = 'top', padx=0) -> None:
        tk.Label(parent, text=text, font=('Segoe UI', 9),
                 bg=BG_CARD, fg=TEXT_SECONDARY, anchor='w', justify='left'
                 ).pack(side=side, anchor='w', padx=padx)

    def _on_preview_resize(self, _event) -> None:
        if self._preview_after_id is not None:
            try:
                self.root.after_cancel(self._preview_after_id)
            except Exception:
                pass
        self._preview_after_id = self.root.after(40, self._update_preview)

    def _on_info_resize(self, event) -> None:
        wrap = max(280, event.width - 40)
        self._info_desc.configure(wraplength=wrap)
        self._info_numbers.configure(wraplength=wrap)

    def _current_grid(self):
        key = self.active_tab
        if key == 'by_piece':
            return piece_symbols(self.piece_fill_var.get())
        if key == 'pattern_mod54':
            return predict_mod54()
        if key == 'multi_period':
            try:
                return predict_multi(int(self.agree_var.get()))
            except (ValueError, AttributeError):
                return predict_multi(2)
        if key == 'random_sampler':
            try:
                return sample_random(int(self.seed_var.get()))
            except (ValueError, AttributeError):
                return sample_random(1)
        if key in ('prediction_zoned', 'confidence_heatmap', 'hard_residues'):
            return guess_symbols(PRED_ZONED)
        if key == 'prediction_cross':
            return guess_symbols(PRED_CROSS)
        return grid_known_only()

    def _cell_visual(self, key: str, n: int, symbol: str):
        known = n in KNOWN
        label = str(n) if (known and self.show_numbers_var.get()) else ''
        pale = hex_of(blend_to_white(CMAP[symbol], GUESS_CONF))
        if key == 'by_piece':
            if known or symbol == 'K':
                return CMAP_HEX[symbol], '', str(n)
            return pale, '', str(n)
        if key in ('prediction_zoned', 'prediction_cross'):
            if known:
                return CMAP_HEX[symbol], '', label
            return pale, '', ''
        if key == 'confidence_heatmap':
            if known:
                return hex_of(CHECK_RIGHT if MODEL_CHECK[n] else CHECK_WRONG), '', str(n)
            return hex_of(DIM_PRED), '', str(n)
        if key == 'hard_residues':
            if known:
                return hex_of(DIM_KNOWN), '', label
            return hex_of(MAGENTA if is_top(n) else ORANGE), '', str(n)
        if key == 'multi_period':
            return CMAP_HEX[symbol], BORDER_SUBTLE, label
        return CMAP_HEX[symbol], '', label

    def _update_preview(self) -> None:
        self._preview_after_id = None
        if not hasattr(self, 'preview_canvas'):
            return
        cv = self.preview_canvas
        cv.delete('all')
        key = self.active_tab
        layout = self._layout_for(key)
        rows, cols = LAYOUTS[layout]
        cells = self._current_grid()

        cw = int(cv.winfo_width())
        ch = int(cv.winfo_height())
        if cw <= 1:
            cw = int(cv['width'])
        if ch <= 1:
            ch = int(cv['height'])
        if cw < 30 or ch < 30:
            return

        piece = layout == PIECE_LAYOUT
        extra = 0.85 if piece else 0.0
        cell = max(1, int(min((cw - 12) / (cols + extra), (ch - 12) / rows)))
        gap = int(round(cell * 0.25)) if piece else 0
        lead = int(round(cell * 0.6)) if piece else 0
        ox = (cw - (cell * cols + gap + lead)) // 2 + lead
        oy = (ch - cell * rows) // 2

        numbers_only = key in ('confidence_heatmap', 'hard_residues')
        for n in CELL_NUMBERS:
            p = n - 1
            r, c = cell_rc(p, layout)
            x = ox + c * cell + (gap if c >= 9 else 0)
            y = oy + r * cell
            symbol = cells[p]
            fill, outline, text = self._cell_visual(key, n, symbol)
            cv.create_rectangle(x, y, x + cell, y + cell,
                                fill=fill, outline=outline)
            glyph = GLYPHS.get(symbol, '')
            shows_glyph = (cell >= 18 and not numbers_only and glyph
                           and self.show_glyphs_var.get())
            if text and cell >= 14:
                size = max(6, min(10, cell // 3))
                if shows_glyph:
                    cv.create_text(x + 3, y + 2, text=text, anchor='nw',
                                   font=('Consolas', size),
                                   fill=_contrast_text_color(fill))
                else:
                    cv.create_text(x + cell // 2, y + cell // 2, text=text,
                                   font=('Consolas', size),
                                   fill=_contrast_text_color(fill))
            if shows_glyph:
                glyph_size = min(cell // 2, 14)
                cv.create_text(x + cell // 2, y + cell // 2,
                               text=glyph,
                               font=('Consolas', glyph_size, 'bold'),
                               fill=_contrast_text_color(fill))
        if piece:
            for r in range(9):
                cv.create_text(ox - lead // 2, oy + r * cell + cell // 2,
                               text=PIECE_LETTERS[r],
                               font=('Consolas', max(7, min(11, cell // 3))),
                               fill=TEXT_SECONDARY)
        self._update_stats(key, cells)
        if key == 'multi_period':
            self._refresh_multi_status()

    def _update_stats(self, key: str, cells) -> None:
        f = self.facts
        if key in ('prediction_zoned', 'prediction_cross'):
            table = PRED_ZONED if key == 'prediction_zoned' else PRED_CROSS
            guessed = [table[n][0] for n in CELL_NUMBERS if n not in KNOWN]
            cnt = Counter(guessed)
            acc = f['acc_model_z' if key == 'prediction_zoned' else 'acc_model_x']
            self.preview_stats.set(
                '{}: {}   {}: {}   G:{} R:{} Y:{}   {}: {}%   {}: {}%'.format(
                    self.tr('stats_known'), len(KNOWN),
                    self.tr('stats_guessed'), len(guessed),
                    cnt.get('G', 0), cnt.get('R', 0), cnt.get('Y', 0),
                    self.tr('stats_check'), acc,
                    self.tr('stats_zone_guess'), f['base']))
            return
        if key == 'confidence_heatmap':
            self.preview_stats.set('{}: {}   {}: {}   {}: {}%   {}: {}%'.format(
                self.tr('stats_right'), f['mc_right'],
                self.tr('stats_wrong'), f['mc_wrong'],
                self.tr('stats_check'), f['acc_model_z'],
                self.tr('stats_zone_guess'), f['base']))
            return
        if key == 'hard_residues':
            block = sum(1 for n in WANTED if is_top(n))
            self.preview_stats.set('{}: {}   {}: {}   {}: {}'.format(
                self.tr('stats_block'), block,
                self.tr('stats_tail'), len(WANTED) - block,
                self.tr('stats_stickers'), 6 * len(WANTED)))
            return
        cnt = Counter(cells)
        self.preview_stats.set('{}: {}   {}: {}   {}: {}   {}: {}'.format(
            self.tr('stats_slash'), cnt.get('G', 0),
            self.tr('stats_dash'), cnt.get('R', 0),
            self.tr('stats_dot'), cnt.get('Y', 0),
            self.tr('stats_unknown'), cnt.get('K', 0)))

    def _legend_items_for(self, key: str):
        kind = TAB_META.get(key, {}).get('legend_kind', 'symbol3')
        pale = hex_of(blend_to_white(CMAP['G'], GUESS_CONF))
        base = [(CMAP_HEX['G'], self.tr('swatch_slash')),
                (CMAP_HEX['R'], self.tr('swatch_dash')),
                (CMAP_HEX['Y'], self.tr('swatch_dot'))]
        if kind == 'symbol3_plus_unk':
            return base + [(CMAP_HEX['K'], self.tr('swatch_unknown_black'))]
        if kind == 'symbol3_plus_lowagree':
            return base + [(CMAP_HEX['K'], self.tr('swatch_no_agreement'))]
        if kind == 'symbol3_guess':
            return base + [(pale, self.tr('swatch_guess'))]
        if kind == 'piece':
            if self.piece_fill_var.get():
                return base + [(pale, self.tr('swatch_guess'))]
            return base + [(CMAP_HEX['K'], self.tr('swatch_unknown_black'))]
        if kind == 'model_check':
            return [(hex_of(CHECK_RIGHT), self.tr('swatch_model_right')),
                    (hex_of(CHECK_WRONG), self.tr('swatch_model_wrong')),
                    (hex_of(DIM_PRED), self.tr('swatch_unknown_dark'))]
        if kind == 'wanted':
            return [(hex_of(MAGENTA), self.tr('swatch_wanted_block')),
                    (hex_of(ORANGE), self.tr('swatch_wanted_tail')),
                    (hex_of(DIM_KNOWN), self.tr('swatch_known'))]
        return list(base)

    def _legend_note_for(self, key: str):
        kind = TAB_META.get(key, {}).get('legend_kind', 'symbol3')
        if kind == 'symbol3_guess' or (kind == 'piece' and self.piece_fill_var.get()):
            return self.tr('legend_note_guess')
        return ''

    def _rebuild_legend_strip(self, key: str) -> None:
        if not hasattr(self, 'legend_strip'):
            return
        for w in self.legend_strip.winfo_children():
            w.destroy()
        items = self._legend_items_for(key)
        note = self._legend_note_for(key)
        max_w = 560
        swatch_px = 12
        gap_px = 4
        item_pad = 14
        char_px = 7
        row = tk.Frame(self.legend_strip, bg=BG_CARD)
        row.pack(side='top', anchor='w', fill='x')
        used = 0
        for color_hex, label in items:
            est_w = swatch_px + gap_px + char_px * len(label) + item_pad
            if used > 0 and used + est_w > max_w:
                row = tk.Frame(self.legend_strip, bg=BG_CARD)
                row.pack(side='top', anchor='w', fill='x', pady=(2, 0))
                used = 0
            sw = tk.Frame(row, bg=color_hex,
                          width=swatch_px, height=swatch_px,
                          highlightthickness=1,
                          highlightbackground=BORDER_SUBTLE)
            sw.pack(side='left', padx=(0, gap_px), pady=1)
            sw.pack_propagate(False)
            tk.Label(row, text=label,
                     font=('Consolas', 9),
                     bg=BG_CARD, fg=TEXT_PRIMARY
                     ).pack(side='left', padx=(0, item_pad))
            used += est_w
        if note:
            note_row = tk.Frame(self.legend_strip, bg=BG_CARD)
            note_row.pack(side='top', anchor='w', fill='x', pady=(2, 0))
            tk.Label(note_row, text=note,
                     font=('Segoe UI', 8, 'italic'),
                     bg=BG_CARD, fg=TEXT_DIM
                     ).pack(side='left')

    def _labels_for_save(self, key: str):
        show_known = bool(self.show_numbers_var.get())
        if key in ('confidence_heatmap', 'by_piece'):
            return {n: str(n) for n in CELL_NUMBERS}
        if key == 'hard_residues':
            labels = {n: str(n) for n in WANTED}
            if show_known:
                labels.update({n: str(n) for n in KNOWN})
            return labels
        if show_known:
            return {n: str(n) for n in KNOWN}
        return None

    def _grid_image_for_active(self, layout: str, cell_px: int):
        key = self.active_tab
        labels = self._labels_for_save(key)
        glyphs = self.show_glyphs_var.get()
        if key == 'by_piece':
            fill = self.piece_fill_var.get()
            return make_grid_image(piece_colors(fill), layout, cell_px, labels,
                                   piece_symbols(fill) if glyphs else None)
        if key in ('prediction_zoned', 'prediction_cross'):
            table = PRED_ZONED if key == 'prediction_zoned' else PRED_CROSS
            return make_grid_image(cells_guess(table), layout, cell_px, labels,
                                   guess_symbols(table) if glyphs else None)
        if key == 'confidence_heatmap':
            return make_grid_image(cells_model_check(), layout, cell_px, labels)
        if key == 'hard_residues':
            return make_grid_image(cells_wanted(), layout, cell_px, labels)
        cells = self._current_grid()
        return make_grid_image(cells_rgb(cells), layout, cell_px, labels,
                               cells if glyphs else None)

    def _title_for_active(self):
        key = self.active_tab
        f = self.facts
        big = self.ttr(f'tab_{key}_big_title')
        sub = self.ttr(f'tab_{key}_card_subtitle')
        check = {'pattern_mod54': f['acc_mod54'], 'prediction_zoned': f['acc_model_z'],
                 'prediction_cross': f['acc_model_x'], 'confidence_heatmap': f['acc_model_z']}
        if key == 'random_sampler':
            sub = f'{sub}  ·  seed = {self.seed_var.get()}'
        elif key == 'multi_period':
            try:
                cov, acc = multi_check(int(self.agree_var.get()))
                sub = (f"{sub}  ·  min agree = {self.agree_var.get()}  ·  "
                       f"{self.tr('stats_check')} {pct(acc)}% / {pct(cov)}%  ·  "
                       f"{self.tr('stats_zone_guess')} {f['base']}%")
            except ValueError:
                pass
        elif key in check:
            sub = (f"{sub}  ·  {self.tr('stats_check')} {check[key]}%  ·  "
                   f"{self.tr('stats_zone_guess')} {f['base']}%")
        if key in ('prediction_zoned', 'prediction_cross'):
            sub = f"{sub}  ·  {self.tr('tail_prediction_numbers')}"
        elif key == 'confidence_heatmap':
            sub = f"{sub}  ·  {self.tr('tail_heatmap_numbers')}"
        elif key == 'hard_residues':
            sub = f"{sub}  ·  {self.tr('tail_hard_numbers')}"
        elif key == 'by_piece':
            sub = f"{sub}  ·  {self.tr('tail_piece_numbers')}"
        return big, sub

    def _save_with_legend(self) -> None:
        cp = self._common()
        if cp is None:
            return
        cs, out_dir = cp
        key = self.active_tab
        if key == 'export_bundle':
            self._gen_compare()
            return
        layout = self._layout_for(key)
        grid_img = self._grid_image_for_active(layout, cs)
        title, subtitle = self._title_for_active()
        items = self._legend_items_for(key)
        path = out_dir / f'with_legend_{key}_{self._layout_tag(layout)}_cs{cs}.png'
        render_with_legend(grid_img, items, title, subtitle, path, cs)
        self.status_var.set(self.tr('status_saved', filename=path.name))

    def _reroll(self) -> None:
        try:
            cur = int(self.seed_var.get())
        except ValueError:
            cur = 0
        self.seed_var.set(str(cur + 1))
        self._update_preview()

    def _browse(self) -> None:
        d = filedialog.askdirectory(initialdir=self.out_var.get())
        if d:
            self.out_var.set(d)

    def _open_folder(self) -> None:
        p = Path(self.out_var.get())
        if p.exists():
            try:
                os.startfile(str(p))
            except Exception:
                pass
        else:
            messagebox.showinfo(self.tr('error_folder_missing_title'),
                                self.tr('error_folder_missing'))

    def _common(self):
        try:
            cell_size = int(self.cell_var.get())
        except ValueError:
            messagebox.showerror(self.tr('error_bad_input_int_title'),
                                 self.tr('error_bad_input_int'))
            return None
        if self.layout_var.get() not in LAYOUTS:
            messagebox.showerror(self.tr('error_bad_layout_title'),
                                 self.tr('error_bad_layout'))
            return None
        out_dir = Path(self.out_var.get())
        out_dir.mkdir(parents=True, exist_ok=True)
        return cell_size, out_dir

    def _gen_known(self) -> None:
        self._save_rgb_grid(cells_rgb(grid_known_only()), 'known_only')

    def _gen_mod54(self) -> None:
        self._save_rgb_grid(cells_rgb(predict_mod54()), 'mod54')

    def _gen_multi(self) -> None:
        try:
            min_a = int(self.agree_var.get())
        except ValueError:
            messagebox.showerror(self.tr('error_bad_input_int_title'),
                                 self.tr('error_bad_input_int'))
            return
        self._save_rgb_grid(cells_rgb(predict_multi(min_a)), f'multi_min{min_a}')

    def _gen_random(self) -> None:
        cp = self._common()
        if cp is None:
            return
        cs, out = cp
        try:
            count = int(self.count_var.get())
            seed_start = int(self.seed_var.get())
        except ValueError:
            messagebox.showerror(self.tr('error_bad_input_int_title'),
                                 self.tr('error_bad_input_int'))
            return
        self.progress['maximum'] = count
        self.progress['value'] = 0
        self.status_var.set(self.tr('status_generating'))
        threading.Thread(
            target=self._random_worker,
            args=(count, cs, seed_start, out, self._layout_for('random_sampler')),
            daemon=True,
        ).start()

    def _random_worker(self, count, cs, seed_start, out, layout):
        for i in range(count):
            seed = seed_start + i
            path = out / f'random_{self._layout_tag(layout)}_seed{seed:03d}.png'
            render(cells_rgb(sample_random(seed)), layout, cs, path)
            self.root.after(0, self._tick, i + 1, count, path.name)
        self.root.after(0, lambda: self.status_var.set(
            self.tr('status_done_count', n=count)))

    def _gen_compare(self) -> None:
        cp = self._common()
        if cp is None:
            return
        cs, out = cp
        layout = self._layout_for('export_bundle')
        numbers = {n: str(n) for n in CELL_NUMBERS}
        bundle = [
            ('known_only', cells_rgb(grid_known_only()), layout, None, None),
            ('mod54', cells_rgb(predict_mod54()), layout, None, None),
            ('multi_min2', cells_rgb(predict_multi(2)), layout, None, None),
            ('multi_min3', cells_rgb(predict_multi(3)), layout, None, None),
            ('random_seed1', cells_rgb(sample_random(1)), layout, None, None),
            ('random_seed2', cells_rgb(sample_random(2)), layout, None, None),
            ('bypiece_known', piece_colors(False), PIECE_LAYOUT, numbers,
             piece_symbols(False)),
            ('bypiece_guesses', piece_colors(True), PIECE_LAYOUT, numbers,
             piece_symbols(True)),
        ]
        for name, colors, lay, labels, symbols in bundle:
            path = out / f'compare_{name}_{self._layout_tag(lay)}.png'
            render(colors, lay, cs, path, labels, symbols)
        self.status_var.set(self.tr('status_done_count', n=len(bundle)))

    def _save_rgb_grid(self, colors, basename: str) -> None:
        cp = self._common()
        if cp is None:
            return
        cs, out = cp
        layout = self._layout_for(self.active_tab)
        path = out / f'{basename}_{self._layout_tag(layout)}.png'
        render(colors, layout, cs, path)
        self.status_var.set(self.tr('status_saved', filename=path.name))

    def _gen_pred_zoned(self) -> None:
        self._save_rgb_grid(cells_guess(PRED_ZONED), 'guess_model_zoned')

    def _gen_pred_cross(self) -> None:
        self._save_rgb_grid(cells_guess(PRED_CROSS), 'guess_model_cross')

    def _gen_heatmap(self) -> None:
        self._save_rgb_grid(cells_model_check(), 'model_check')

    def _gen_hard(self) -> None:
        self._save_rgb_grid(cells_wanted(), 'wanted_stickers')

    def _tick(self, done: int, total: int, name: str) -> None:
        self.progress['value'] = done
        self.status_var.set(self.tr('status_progress', done=done,
                                    total=total, filename=name))


def main() -> None:
    root = tk.Tk()
    App(root)
    root.mainloop()


if __name__ == '__main__':
    main()
