from lxml import etree, html
import requests
import random
import json
from pprint import pprint

from config import USER_AGENTS


class CategoriesIncompleteError(Exception):
	pass


class Scraper:
	def __init__(self):
		""" Initializes all attributes and configurations """

		self.jumia_url = "https://www.jumia.com.ng"
		self.categories_file = "categories.json"
		self.categories = self.load_categories()
		pprint(self.categories)

	def load_categories(self):
		""" Loads all categories from json file or extracts them from the jumia landing page"""
		print("Loading categories ... ")
		with open(self.categories_file) as saved:
			categories = None
			try:
				categories = json.load(saved)
				for data in categories:
					items = list(data.items())[0]
					name, items = items
					if not items:raise CategoriesIncompleteError

			except (json.JSONDecodeError,CategoriesIncompleteError):
				print("Error loading categories, Extracting from Jumia")
				self.extract_categories()
				return self.load_categories()

			return categories


	def random_useragent(func):
		def wrapper(self, *args):
			print(f"Called {func.__name__}")
			random_user_agent = random.choice(USER_AGENTS)
			return func(self, random_user_agent, *args)

		return wrapper

	def get_random_useragent(self):
		return random.choice(USER_AGENTS)

	def save_html_to_file(self, html, filename):
		with open(filename, "w") as save:
			print(html, file=save)

	@random_useragent
	def extract_categories(self, user_agent: str):
		landing_page_response = requests.get(headers={"User-Agent": user_agent}, url=self.jumia_url)
		parser = html.fromstring(landing_page_response.text)
		flyout_container = parser.xpath('//*[@id="jm"]/main/div[1]/div[1]/div[1]/div')
		if len(flyout_container) > 0:
			flyout_container = flyout_container[0]
			a_tags = flyout_container.findall("a")
			categories = []
			for a_tag in a_tags:
				href: str = a_tag.get("href")
				name = a_tag.find("span").text
				if href is not None:
					if href.startswith("/"):
						href = self.jumia_url + href
					sub_categories = self.get_category_subcategory(href)
					categories.append({
						name: sub_categories
					})
			with open("categories.json", "w") as save:
				json.dump(categories, save, indent=4)
		else:
			print("No data found ... RE-STARTING...")
			self.extract_categories()

	@random_useragent
	def get_category_subcategory(self, user_agent, category_link):
		while True:
			a_tags_csslector = "div.row a[data-id^='catalog_category_category']"
			landing_page_response = requests.get(headers={"User-Agent": user_agent}, url=category_link)
			parser = html.fromstring(landing_page_response.text)
			atags = parser.cssselect(a_tags_csslector)
			datas = [{"text": a.find("p").text, "href": a.get("href", "None").split("?")[0]} for a in atags if
			         a.find("p") is not None]
			datas = datas[:12] if len(datas) >= 12 else datas
			if datas: return datas
			user_agent = self.get_random_useragent()


if __name__ == "__main__":
	scraper = Scraper()
# print(result)
