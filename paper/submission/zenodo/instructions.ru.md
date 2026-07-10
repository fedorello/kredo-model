# Zenodo — пошаговая инструкция

Zenodo (zenodo.org) — открытый архив от CERN. Даёт **DOI** сразу после
публикации, без модерации. Самый быстрый шаг — займёт ~10 минут.

> Важно: опубликованную запись **нельзя удалить** (можно только добавлять
> новые версии). Перед нажатием «Publish» проверьте всё по чек-листу внизу.

## Шаги

1. Откройте <https://zenodo.org> → **Sign up**. Быстрее всего — кнопкой
   **«Sign up with GitHub»** (у вас уже есть аккаунт GitHub).
2. Нажмите **«New upload»** (кнопка вверху).
3. Перетащите файлы:
   - `paper/main.pdf` — основной (английский);
   - `paper/main-ru.pdf` — дополнительный (русский перевод).
4. Заполните форму, копируя тексты из [`metadata.en.md`](./metadata.en.md):
   - **Resource type**: Publication → **Preprint**;
   - **Title**, **Description** (аннотация), **Keywords** — из файла;
   - **Creators**: ваше имя, affiliation `Independent Researcher`
     (и ORCID, если завели);
   - **License**: **Creative Commons Attribution 4.0** (CC-BY-4.0) —
     стандарт для открытых препринтов;
   - **Related works**: добавьте ссылку
     `https://github.com/fedorello/kredo-model`
     с отношением **«Is supplemented by»** (код и данные).
5. Нажмите **Publish**.
6. Скопируйте выданный **DOI** (вида `10.5281/zenodo.XXXXXXX`) — он
   пригодится для SSRN, arXiv и README репозитория.

## Опционально: архив кода с собственным DOI

Zenodo умеет автоматически архивировать GitHub-репозиторий:

1. В Zenodo: аватар → **GitHub** → найдите `fedorello/kredo-model` →
   включите переключатель.
2. В GitHub: репозиторий → **Releases** → **Create a new release** →
   тег `v1.0.0` → **Publish release**.
3. Zenodo сам создаст снапшот кода с отдельным DOI.

## Чек-лист перед «Publish»

- [ ] Оба PDF открываются и это последние версии
- [ ] Title без опечаток (скопирован, не набран руками)
- [ ] Имя автора и email верные
- [ ] Лицензия CC-BY-4.0
- [ ] Ссылка на GitHub добавлена
