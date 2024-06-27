INSERT INTO Categories (name, currency) VALUES ('Kaspi', 'KZT'); -- Добавить новую категорию (Kaspi)
INSERT INTO Balance (cat_id, date, value, rate) VALUES (1, '2024-06-27 13:23:00+03', 16700, CAST(0.002 * 1000 AS INTEGER)); -- Добавить баланс на определнную дату (для Kaspi)


SELECT SUM(ROUND(value * rate)/1000) AS total_amount FROM Balance WHERE "date" = '2024-06-27 10:23:00+00'; -- Запрос для вывода суммы по всем категориям за опред. день
SELECT SUM(ROUND(value * rate)/1000) AS total_amount FROM Balance WHERE "date"::date = current_date; --Запрос всех накоплений на текущий момент

SELECT (ROUND(value * rate)/1000), name FROM Balance
FULL OUTER JOIN Categories
ON Categories.id = Balance.cat_id
WHERE "date"::date = current_date; -- Запрос для вывода всех категорий по отдельности на текущий моменты

UPDATE Balance
SET value = 78955500
WHERE "date"::date = current_date AND value = 78900; -- Запрос на изменение суммы в случае ошибки (если запись добавлена сегодня)

DELETE FROM Balance
WHERE "cat_id" = 1 AND "date"::date = current_date; -- Запрос на удаление записи определенной категории (если запись добавлена сегодня)
