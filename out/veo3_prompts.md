# Veo 3 — вертикальный ролик (мама, флешка, Chill). Версия без триггеров фильтра

## Что изменено против первой версии
Убрано всё, на чём Veo обычно отказывает: возраст персонажа («12 years old», «boy»),
слово Minecraft, длинный блок `Negative:`. Осталась одна короткая строка про субтитры.
Промпты укорочены — чем короче, тем реже отказ.

## Как собирать
- Veo делает ~8 секунд за раз. Это 5 отдельных клипов, склейка в CapCut/Premiere.
- Формат 9:16 выставь настройкой, в тексте он продублирован.
- Промпты на английском — так модель слушается точнее. Реплики в кавычках
  остаются русскими, их не переводи.
- Для одинаковых персонажей копируй блок CHARACTERS дословно в каждый клип,
  а в Flow дополнительно подавай последний кадр предыдущего клипа как стартовый.
- Финальный логотип и русский текст Veo рисует криво — делай карточку в монтажке.

---

## БЛОК ПЕРСОНАЖЕЙ (в каждый промпт, без изменений)

```
CHARACTERS (keep identical in every shot):
GAMER — a cubic voxel-game character, blocky head, messy brown blocky hair,
teal t-shirt, dark blue pants, simple two-pixel eyes.
WOMAN — a cubic voxel-game character, blocky head, dark hair in a bun, red apron
over a grey shirt, same pixel-art style, slightly taller.
STYLE — 3D voxel animation, cubic sandbox-game world, pixelated textures,
soft toy-like lighting, cinematic depth of field, 9:16 vertical.
```

---

## КАДР 1 — она заходит

```
Vertical 9:16 video. 3D blocky voxel animation, cubic characters, pixel-art
textures. A cubic gamer character sits at a blocky computer desk in a dark voxel
bedroom at night, the monitor glowing cyan on his face, RGB strips on the wall.
He leans into the screen, pressing keys, head bobbing. Behind him a door opens
and a cubic woman in a red apron steps in, hands on hips.
Camera: slow push-in over his shoulder, then a small arc into a two-shot.
Lighting: dark room, cold monitor light on him, warm hallway light from the door.
Audio: quiet room tone, mechanical keyboard clicks, a door creak, soft lofi beat.
She says in Russian: "Во что играешь?"
No subtitles, no on-screen text.
```

## КАДР 2 — ответ и подзатыльник

```
Vertical 9:16 video. 3D blocky voxel animation, same characters, same dark
bedroom with a glowing cyan monitor. Close shot: the cubic gamer turns his blocky
head toward the woman and shrugs with one arm. She steps closer and playfully
taps the back of his blocky head; his head wobbles cartoonishly and he rubs it.
Camera: medium close-up on him, a quick handheld snap to her on the tap.
Lighting: cold screen light, warm rim light from the doorway.
Audio: keyboard clicks stop, a soft comedic bonk, a light cartoon whoosh, lofi beat.
He says in Russian: "На фантайме, с дельтой."
No subtitles, no on-screen text.
```

## КАДР 3 — флешка

```
Vertical 9:16 video. 3D blocky voxel animation, same characters, same dark
bedroom lit only by a computer monitor. The cubic woman in a red apron takes a
small glowing cyan-violet USB stick from her apron pocket and holds it out. The
cubic gamer looks up, eyes widening, and reaches for it.
Camera: low angle, slow dolly toward the glowing stick, then a gentle tilt up to
his face, shallow depth of field.
Lighting: the stick is the brightest light in the frame, cyan rim light on both.
Audio: soft magical shimmer, low confident music swell, quiet room tone.
She says in Russian: "На, попробуй лучше это."
No subtitles, no on-screen text.
```

## КАДР 4 — запуск и шок

```
Vertical 9:16 video. 3D blocky voxel animation, same cubic gamer, same bedroom.
He plugs the glowing stick into the blocky PC tower; the screen floods with cyan
and violet light, particles rise around him, his blocky jaw drops and he slowly
leans back in the chair.
Camera: starts tight on the port, snaps to a low front angle on his face as the
light hits, slow push-in with a tiny handheld shake.
Lighting: hard cyan-violet key light sweeping across the dark room, volumetric
dust in the beam.
Audio: a USB connect chime, a rising riser sweep, a deep bass impact, awed breath.
He says in Russian: "Да ладно..."
No subtitles, no on-screen text.
```

## КАДР 5 — дым и финал

```
Vertical 9:16 video. 3D blocky voxel animation, same bedroom. The blocky PC
tower rattles and pops with a cartoonish puff of grey smoke; the cubic gamer
jumps back in his chair with a stunned face, smoke curls to the ceiling, the room
goes dark except for a cyan-violet glow. Then a slow push-in into the dark smoky
room, frame center left empty.
Camera: quick zoom out on the pop, then a slow steady push-in into darkness.
Lighting: a brief warm flash, then deep blue darkness with cyan glow and embers.
Audio: comedic pop and fizzle, smoke hiss, silence, one deep cinematic impact,
clean synth tail. A calm confident male voice-over in Russian at the end:
"Chill. Не просто аура."
No subtitles, no on-screen text.
```

---

## Финальная карточка (не в Veo)
Поверх последнего кадра в монтажке:
- крупно **CHILL**, градиент голубой -> фиолетовый со свечением;
- ниже разрядкой C L I E N T;
- слоган **НЕ ПРОСТО АУРА.**;
- плашка **200 ₽ / МЕСЯЦ**.
Либо подрежь готовую концовку из уже сделанного mp4.

---

## Если всё равно отказ

Диагностика за одну генерацию — прогони голый стиль с нейтральным действием:
`Vertical 9:16, 3D blocky voxel animation. A cubic character waves in a dark room.`
Пошло — виноват текст конкретного кадра. Не пошло — виноват стиль/персонажи.

Замены по убыванию вероятности:
1. Реплика в кадре. Убери строку `He says in Russian: ...` целиком, сделай немой
   клип, голос наложи отдельно (TTS или своим голосом).
2. Подзатыльник (кадр 2) -> `she pats him on the shoulder` или
   `she waves a finger at him`.
3. Дым и хлопок (кадр 5) -> `the screen flickers and goes dark, a thin wisp of
   smoke rises`, без хлопка и искр.
4. Любое упоминание ребёнка. В тексте его нет — не возвращай слова boy, kid,
   son, young, возраст. Только `gamer character`.
5. Слишком длинный промпт — режь описание света и звука, оставляй действие и камеру.
