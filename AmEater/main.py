import os
import configparser
import requests
from bs4 import BeautifulSoup

def read_settings():
	"""settings.iniを読み込みます"""
	try:
		ini = configparser.ConfigParser()
		ini.read("settings.ini", encoding="utf-8_sig")
		_series = ini["series"]["idlist"]
		series = []
		for i in _series.split(","):
			if i:
				series.append(f"{i.strip()}")

	except Exception as e:
		print(f"{e}\nsettings.ini読み込みエラーだよ～ちゃんと用意してね～")
		exit()
	
	return series

class AmEater:
	"""
	series_idを受け取り、記事内の画像をDLします

	Parameters
	---
	series_id: str
		https://am-our.com/ 以降の、シリーズ記事一覧を含むページurl
	"""
	def __init__(self, series_id):
		self.series_id = series_id
		self.series_name = self.get_writername()
		self.mkdir_chdir()
		self.downloaded_list = self.get_downloaded_list()
		self.article_urls = self.get_article_urls()

	def check_exist(self, response):
		"""指定したシリーズの存在チェック
		series_nameを取得するときに一度アクセスするので直接responseオブジェクトを受け取ることにする"""
		if response.status_code == 404: # 存在しないシリーズ名を指定した場合
			print(f"★ {self.series_id} は存在しないシリーズです")
			return

	def get_writername(self):
		"""シリーズ名（著者名）を取得する"""
		url = f"https://am-our.com/{self.series_id}/"
		response = requests.get(url)
		self.check_exist(response)
		soup = BeautifulSoup(response.text,'lxml')
		seriesname = soup.select(".breadcrumb__item.breadcrumb__item-current")[0].getText()
		return seriesname

	def mkdir_chdir(self):
		"""カレントディレクトリにダウンロード先フォルダの作成と移動"""
		dest_dir = os.path.join(os.getcwd(), self.series_name)
		os.makedirs(dest_dir, exist_ok=True)
		os.chdir(dest_dir)

	def get_downloaded_list(self):
		"""カレントディレクトリのdownloaded.txtの作成と読み込み"""
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
		"""series_idからダウンロード対象となる記事個別URLを取得し、ソート済みリストで返す"""
		article_infos = []
		page_num = 0
		while True:
			page_num += 1
			request_url = f"https://am-our.com/{self.series_id}/page/{page_num}/"
			response = requests.get(request_url)
			if response.status_code == 404: # ページ遷移先がなくなった時
				break

			soup = BeautifulSoup(response.text,'lxml')
			pages = soup.select(".archive_author_top.view-mask, .article_top_center.archive__item.view-mask, .opening-archive-item-custom.view-mask, .archive-item-custom.view-mask")

			while pages:
				try:
					article = pages.pop()
					article_url = article.select(".eyecatch__link.eyecatch__link-mask-latest, .eyecatch__link.eyecatch__link-mask")[0].attrs["href"]
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
	"""
	page_urlとseries_numを受け取り、ダウンロードする

	Parameters
	---
	page_url: str
		個別記事のurl
	series_num: int
		シリーズ内の第何話かを示す数字
	"""
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
		"""記事によって画像urlを含むcssセレクタが異なるのでそれのあれ"""
		response = requests.get(self.page_url)
		soup = BeautifulSoup(response.text,'lxml')

		for cssselector in self.cssselector_list:
			if soup.select(cssselector):
				self.download_with_cssselector(soup, cssselector)
				break
				
	def download_with_cssselector(self, soup, cssselector):
		"""ページ内の画像をDL"""
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
	root_dir = os.path.dirname(os.path.abspath(__file__))
	os.chdir(root_dir)

	writers = read_settings()
	for series_id in writers:
		os.chdir(root_dir)
		Writer = AmEater(series_id)

		print(f"★ --- {Writer.series_name} のダウンロード開始します ---")
		for series_num, url_dict in enumerate(Writer.article_urls, start=1):
			url = url_dict["article_url"]
			Writer.download_images(url, series_num)
		print(f"★ --- {Writer.series_name} のダウンロード完了しました ---")

if __name__ == "__main__":
	print("★ starting am-eater...")
	main()
	print("★ オワリ")