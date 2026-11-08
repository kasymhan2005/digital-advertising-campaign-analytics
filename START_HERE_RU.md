# Как пользоваться проектом — инструкция на русском

## Что внутри

Третий pet-project: **Digital Advertising Campaign Analytics**. В ZIP лежит твой настоящий `conversion.csv`, поэтому все результаты можно проверить локально. Есть Jupyter Notebook, 6 графиков по реальным данным, Markdown-отчёт, SQL и Streamlit-дашборд.

## Запуск в Windows

1. Распакуй ZIP в удобную папку.
2. В VS Code открой именно папку `digital-advertising-campaign-analytics`.
3. Открой **Terminal → New Terminal**.
4. Выполни:

```powershell
py -m pip install -r requirements.txt
py -m streamlit run app.py
```

Обычно приложение откроется по адресу `http://localhost:8501`. Оно автоматически прочитает `data/raw/conversion.csv`.

## Запуск исследования

Открой `notebooks/01_marketing_eda.ipynb` в VS Code/Jupyter. Все ячейки сохранены с результатами. Для повторного запуска должен присутствовать `data/raw/conversion.csv`.

## Обновление отчётов и проверка

```powershell
py scripts/generate_report.py
py scripts/run_sql.py
py -m pytest -q
```

## Загрузка на GitHub

1. Создай публичный репозиторий `digital-advertising-campaign-analytics`.
2. Через GitHub Desktop скопируй весь проект в локальный репозиторий.
3. **Проверь, что `data/raw/conversion.csv` не помечен для коммита**: лицензия на распространение данных ещё не подтверждена. `.gitignore` специально исключает его. При загрузке перетаскиванием в браузер `.gitignore` может не помочь.
4. Сделай Commit и Push. Для GitHub Actions тесты используют синтетические данные, поэтому исходный CSV им не нужен.
5. В Streamlit Community Cloud выбери этот репозиторий → `main` → `app.py` → Deploy. В облаке по умолчанию будет отображаться **синтетический демо-набор**. Чтобы увидеть настоящие цифры, пользователь должен загрузить разрешённый ему `conversion.csv` через боковую панель.

## Что важно объяснить на собеседовании

- CTR = clicks/impressions; CPC = spent/clicks; CPA = spent/approved purchases.
- Среднее CTR объявлений **не равно** общему CTR кампании: нужны суммы кликов и показов.
- Если Clicks = 0, CPC не равен 0: он не определён.
- У части объявлений покупки превышают клики. Поэтому данные нельзя безоговорочно трактовать как точную пользовательскую воронку.
- Поскольку выручка неизвестна, ROI и ROAS рассчитать нельзя.
- Кампания с наибольшим числом покупок не обязательно имеет лучшую стоимость привлечения.
