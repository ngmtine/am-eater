import os
import configparser
import requests
from bs4 import BeautifulSoup

def read_settings():
	"""
	settings.iniを読み込みます
	"""
	try:
		ini = configparser.ConfigParser()
		ini.read("settings.ini", encoding="utf-8_sig")
		writers_ = ini["writers"]["idlist"]
		writers = []
		for i in writers_.split(","):
			if i:
				writers.append(i)
	except Exception as e:
		print(f"{e}\nsettings.ini読み込みエラーだよ～ちゃんと用意してね～")
		exit()
	
	return writers

class AmEater:
	"""ライター固有のID（writer_id）を受け取り、記事内の画像をDLします"""
	
	def __init__(self, writer_id):
		self.writer_id = writer_id
		self.article_urls = self.get_article_urls()

	def get_article_urls(self):
		""" ライター固有のID（writer_id）から、ダウンロード対象のページURLを取得し、リストで返します """

		article_infos = []
		page_num = 0
		while True:
			page_num += 1
			request_url = f"https://am-our.com/author/{self.writer_id}/page/{page_num}/"
			response = requests.get(request_url)
			soup = BeautifulSoup(response.text,'lxml')
			pages = soup.select(".archive_author_top.view-mask, .article_top_center.archive__item.view-mask")

			if pages == []: # ページ遷移先がなくなった時
				break

			while pages:
				try:
					article = pages.pop()
					article_url = article.select(".eyecatch__link.eyecatch__link-mask-latest")[0].attrs["href"]
					article_date = article.select(".dateList__item")[0].contents[0].strip()
					article_infos.append({"article_url": article_url, "article_date": article_date})
				except Exception as e:
					print(e)

		# 投稿日付昇順でソート
		article_infos.sort(key=lambda x: x["article_date"])
		return article_infos

	def downlaod(self):
		print("★ ダウンロードするよ～")	

def main():
	print("★ starting am-eater...")
	root_dir = os.path.dirname(os.path.abspath(__file__))
	os.chdir(root_dir)

	writers = read_settings()

	for writer_id in writers:
		Writer = AmEater(writer_id)
		Writer.download()

		print("オワリ")

if __name__ == "__main__":
	main()

