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
		self.writer_name = self.get_writername()
		self.article_urls = self.get_article_urls()

	def get_writername(self):
		"""
		ライター名を取得する
		"""
		url = f"https://am-our.com/author/{self.writer_id}/"
		response = requests.get(url)
		soup = BeautifulSoup(response.text,'lxml')
		writername = soup.select(".breadcrumb__item.breadcrumb__item-current")[0].getText()
		return writername

	def get_article_urls(self):
		"""
		writer_idからダウンロード対象となる記事個別URLを取得し、ソート済みリストで返す
		"""
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

	def download_images(self, url, series_num):
		"""
		個別ページのurlから画像をダウンロードする
		Parameters
		---
		url: str
			ダウンロードしたい画像へのリンクを含む、個別記事のurl
		series_num: int
			連載の中の第何話目かを示す変数
		"""

		# response = requests.get(url)
		# soup = BeautifulSoup(response.text,'lxml')

		print("★ 書きかけです")
		return
		author = soup.find("meta", attrs={"name": "author"})["content"] # 著者
		series_title = soup.select("#area_main .box-series .post-items .post-title a")[0].getText().rstrip() # シリーズ名
		article_title = soup.select(".article-title")[0].getText().strip() # 記事名
		article_id = article_url.rsplit("/")[-1] # 記事ID

		print(f"★ {article_id=} {article_title} をダウンロードします")

		for idx, elm in enumerate(soup.select(".article-content p img")):
			url = elm.get("src")
			try:
				filename = f"{str(series_num)}_{article_title}({article_id})_{str(idx+1)}.png" # 現在はpng以外の拡張子を想定してない
				# dest = os.path.join(dirname, filename)
				response = requests.get(url)
				image = response.content
				with open(filename, mode="wb") as file:
					file.write(image)
			except Exception as e:
				print(e)

def main():
	print("★ starting am-eater...")
	root_dir = os.path.dirname(os.path.abspath(__file__))
	os.chdir(root_dir)

	writers = read_settings()
	for writer_id in writers:
		Writer = AmEater(writer_id)
		for series_num, url_dict in enumerate(Writer.article_urls, start=1):
			url = url_dict["article_url"]
			Writer.download_images(url, series_num)

		print("オワリ")

if __name__ == "__main__":
	main()

