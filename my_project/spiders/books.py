import scrapy
import re


class BooksSpider(scrapy.Spider):
    name = "books"
    allowed_domains = ["books.toscrape.com"]
    start_urls = ["https://books.toscrape.com/"]

    def parse(self, response):
        # Збираємо посилання на детальні сторінки кожної книги
        for book_link in response.css("article.product_pod h3 a::attr(href)").getall():
            yield response.follow(book_link, callback=self.parse_book_details)

        # Пагінація: перехід на наступну сторінку
        next_page = response.css("li.next a::attr(href)").get()
        if next_page:
            yield response.follow(next_page, callback=self.parse)

    def parse_book_details(self, response):
        # Основний контейнер з даними
        main = response.css("div.product_main")

        # Функція для надійного витягування даних з таблиці (UPC)
        def get_table_value(label):
            return response.xpath(f"//th[contains(text(), '{label}')]/following-sibling::td/text()").get()

        # Обробка ціни (видаляємо символ валюти та конвертуємо в число)
        price_raw = main.css("p.price_color::text").get()
        price = float(re.sub(r'[^\d.]', '', price_raw)) if price_raw else 0.0

        # Витягуємо кількість на складі (шукаємо число в тексті)
        stock_text = main.css("p.instock.availability::text").getall()
        stock_text = "".join(stock_text).strip()
        stock_match = re.search(r'(\d+)', stock_text)
        amount_in_stock = int(stock_match.group(1)) if stock_match else 0

        yield {
            "title": main.css("h1::text").get(),
            "price": price,
            "amount_in_stock": amount_in_stock,
            "rating": main.css("p.star-rating::attr(class)").get().replace("star-rating ", ""),
            "category": response.xpath("//ul[@class='breadcrumb']/li[3]/a/text()").get(),
            "description": response.xpath("//div[@id='product_description']/following-sibling::p/text()").get(),
            "upc": get_table_value("UPC"),
        }
