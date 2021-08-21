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
		self.mkdir_chdir()
		self.downloaded_list = self.get_downloaded_list()
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

	def mkdir_chdir(self):
		"""
		カレントディレクトリにダウンロード先フォルダの作成と移動
		"""
		dest_dir = os.path.join(os.getcwd(), self.writer_name)
		os.makedirs(dest_dir, exist_ok=True)
		os.chdir(dest_dir)

	def get_downloaded_list(self):
		"""
		カレントディレクトリのdownloaded.txtの作成と読み込み
		"""
		downloaded_txt = os.path.join(os.getcwd(), "downloaded.txt")

		# downloaded.txtの作成
		if not os.path.isfile(downloaded_txt):
			with open(downloaded_txt, mode="w") as f:
				f.write("")

		# downloaded.txtの読み込み
		with open(downloaded_txt, mode="r") as f:
			downloaded_list = list(map(lambda i: i.rstrip(), f.readlines()))

		return downloaded_list

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
			if response.status_code == 404: # ページ遷移先がなくなった時
				break

			soup = BeautifulSoup(response.text,'lxml')
			pages = soup.select(".archive_author_top.view-mask, .article_top_center.archive__item.view-mask")

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

	def download_images(self, page_url, series_num):
		"""
		個別ページのurlから画像をダウンロードする
		但し記事によってはhtmlが異なることに注意

		Parameters
		---
		page_url: str
			ダウンロードしたい画像へのリンクを含む、個別記事のurl
		series_num: int
			連載の中の第何話目かを示す変数
		"""

		if page_url in self.downloaded_list: # ダウンロード済みの場合
			return

		else: # 未ダウンロードの場合
			Download = Downloader(page_url, series_num)
			Download.download_starter()
			self.append_downloaded_txt(page_url)
		return

	def append_downloaded_txt(self, string):
		with open("downloaded.txt", mode="a") as f:
			f.writelines(f"{string}\n")

class Downloader:
	def __init__(self, page_url, series_num):
		self.cssselector_list = [".photo", ".aligncenter", ".wp-block-image"]
		self.page_url = page_url
		self.series_num = series_num
		self.article_title = self.get_article_title()
		self.img_cnt = 1
		print(f"★ {self.article_title} をダウンロードします")

	def get_article_title(self):
		"""記事タイトルの取得"""
		response = requests.get(self.page_url)
		soup = BeautifulSoup(response.text,'lxml')
		article_title = soup.select(".heading.heading-primary")[0].getText()
		article_title = f"{str(self.series_num)}_{article_title}"
		return article_title

	def download_starter(self):
		response = requests.get(self.page_url)
		soup = BeautifulSoup(response.text,'lxml')

		for cssselector in self.cssselector_list:
			if soup.select(cssselector):
				self.download_with_cssselector(soup, cssselector)
				break
				
	def download_with_cssselector(self, soup, cssselector):
		# ページ内の画像をDL
		for img_idx in range(len(soup.select(f"{cssselector} img"))):
			img_url = soup.select(f"{cssselector} img")[img_idx].get("src")
			filename = f"{self.article_title}_{self.img_cnt}.png" # png以外の拡張子が存在する場合は書き方変える必要あり
			image = requests.get(img_url).content
			try:
				with open(filename, mode="wb") as file:
					file.write(image)
			except Exception as e:
				print(e)
				return
			self.img_cnt += 1

		# 次のページがあるなら遷移
		if soup.select(".next_page"):
			self.page_url = soup.select(".next_page_block")[0].get("href")
			self.download_starter()

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

		print("★ オワリ")

if __name__ == "__main__":
	main()

